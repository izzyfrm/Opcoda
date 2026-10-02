import math
import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import CodaConfig


class KVCache:
    """Preallocated key/value cache for fast generation (one slot per layer)."""

    def __init__(self, cfg: CodaConfig, batch: int, device, dtype=torch.float32):
        head_dim = cfg.n_embd // cfg.n_head
        shape = (cfg.n_layer, batch, cfg.n_head, cfg.block_size, head_dim)
        self.k = torch.zeros(shape, device=device, dtype=dtype)
        self.v = torch.zeros(shape, device=device, dtype=dtype)
        self.length = 0

    def repeat(self, n: int) -> None:
        """After prefilling one prompt, copy its cache to n parallel samples."""
        self.k = self.k.repeat(1, n, 1, 1, 1)
        self.v = self.v.repeat(1, n, 1, 1, 1)


class CausalSelfAttention(nn.Module):
    def __init__(self, cfg: CodaConfig):
        super().__init__()
        assert cfg.n_embd % cfg.n_head == 0
        self.n_head = cfg.n_head
        self.head_dim = cfg.n_embd // cfg.n_head
        self.qkv = nn.Linear(cfg.n_embd, 3 * cfg.n_embd)
        self.proj = nn.Linear(cfg.n_embd, cfg.n_embd)
        self.dropout = nn.Dropout(cfg.dropout)

    def forward(self, x: torch.Tensor, cache: KVCache | None = None, layer: int = 0) -> torch.Tensor:
        b, t, c = x.shape
        q, k, v = self.qkv(x).chunk(3, dim=-1)
        q = q.view(b, t, self.n_head, self.head_dim).transpose(1, 2)
        k = k.view(b, t, self.n_head, self.head_dim).transpose(1, 2)
        v = v.view(b, t, self.n_head, self.head_dim).transpose(1, 2)

        if cache is None:
            # PyTorch's fused/scaled attention handles the causal mask for us.
            y = F.scaled_dot_product_attention(
                q, k, v, dropout_p=self.dropout.p if self.training else 0.0, is_causal=True
            )
        else:
            start = cache.length
            cache.k[layer, :, :, start : start + t] = k
            cache.v[layer, :, :, start : start + t] = v
            keys = cache.k[layer, :, :, : start + t]
            values = cache.v[layer, :, :, : start + t]
            if t == 1:
                y = F.scaled_dot_product_attention(q, keys, values)
            else:
                mask = torch.ones(t, start + t, dtype=torch.bool, device=x.device).tril(diagonal=start)
                y = F.scaled_dot_product_attention(q, keys, values, attn_mask=mask)
        y = y.transpose(1, 2).contiguous().view(b, t, c)
        return self.dropout(self.proj(y))


class MLP(nn.Module):
    def __init__(self, cfg: CodaConfig):
        super().__init__()
        self.fc = nn.Linear(cfg.n_embd, 4 * cfg.n_embd)
        self.proj = nn.Linear(4 * cfg.n_embd, cfg.n_embd)
        self.dropout = nn.Dropout(cfg.dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.dropout(self.proj(F.gelu(self.fc(x))))


class Block(nn.Module):
    def __init__(self, cfg: CodaConfig):
        super().__init__()
        self.ln1 = nn.LayerNorm(cfg.n_embd)
        self.attn = CausalSelfAttention(cfg)
        self.ln2 = nn.LayerNorm(cfg.n_embd)
        self.mlp = MLP(cfg)

    def forward(self, x: torch.Tensor, cache: KVCache | None = None, layer: int = 0) -> torch.Tensor:
        x = x + self.attn(self.ln1(x), cache, layer)
        x = x + self.mlp(self.ln2(x))
        return x


class Coda(nn.Module):
    def __init__(self, cfg: CodaConfig):
        super().__init__()
        self.cfg = cfg
        self.token_emb = nn.Embedding(cfg.vocab_size, cfg.n_embd)
        self.pos_emb = nn.Embedding(cfg.block_size, cfg.n_embd)
        self.blocks = nn.ModuleList([Block(cfg) for _ in range(cfg.n_layer)])
        self.ln_f = nn.LayerNorm(cfg.n_embd)
        self.lm_head = nn.Linear(cfg.n_embd, cfg.vocab_size, bias=False)
        self.lm_head.weight = self.token_emb.weight
        self.apply(self._init_weights)

    def _init_weights(self, module: nn.Module) -> None:
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, idx: torch.Tensor, targets: torch.Tensor | None = None, cache: KVCache | None = None):
        b, t = idx.shape
        start = cache.length if cache is not None else 0
        if start + t > self.cfg.block_size:
            raise ValueError(f"sequence length {start + t} exceeds block size {self.cfg.block_size}")

        pos = torch.arange(start, start + t, device=idx.device)
        x = self.token_emb(idx) + self.pos_emb(pos)[None, :, :]
        for i, block in enumerate(self.blocks):
            x = block(x, cache, i)
        if cache is not None:
            cache.length += t
        logits = self.lm_head(self.ln_f(x))

        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))
        return logits, loss

    @torch.no_grad()
    def generate(
        self,
        idx: torch.Tensor,
        max_new_tokens: int,
        temperature: float = 0.8,
        top_k: int | None = 40,
        stop: list[list[int]] | None = None,
    ) -> torch.Tensor:
        """Sample tokens. With ``stop`` (token sequences), batch-size-1 generation
        ends as soon as the new tokens end with any stop sequence."""
        self.eval()
        start = idx.size(1)
        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.cfg.block_size :]
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / max(temperature, 1e-5)
            if top_k is not None:
                k = min(top_k, logits.size(-1))
                values, _ = torch.topk(logits, k)
                logits[logits < values[:, [-1]]] = -float("inf")
            probs = F.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            idx = torch.cat((idx, next_token), dim=1)
            if stop and idx.size(0) == 1:
                generated = idx[0, start:].tolist()
                if any(s and generated[-len(s):] == s for s in stop):
                    break
        return idx

    @torch.no_grad()
    def sample(
        self,
        prompt: list[int],
        max_new_tokens: int,
        token_bytes,
        n: int = 1,
        temperature: float = 0.6,
        top_k: int | None = 40,
        stop: list[str] | None = None,
    ) -> list[dict]:
        """Draw n continuations of one prompt in parallel using a KV cache.

        token_bytes(id) -> bytes lets stop strings be matched on decoded text, so they work
        with any tokenizer. Returns [{"ids": [...], "finished": bool}] per sample.
        """
        self.eval()
        device = next(self.parameters()).device
        max_new_tokens = max(0, min(max_new_tokens, self.cfg.block_size - len(prompt)))
        stops = [s.encode("utf-8") for s in (stop or []) if s]
        tail = max((len(s) for s in stops), default=0) + 16

        cache = KVCache(self.cfg, 1, device)
        logits, _ = self(torch.tensor([prompt], dtype=torch.long, device=device), cache=cache)
        cache.repeat(n)
        logits = logits[:, -1, :].expand(n, -1)

        out = [{"ids": [], "finished": False, "text": b""} for _ in range(n)]
        for _ in range(max_new_tokens):
            scaled = logits / max(temperature, 1e-5)
            if top_k is not None:
                values, _ = torch.topk(scaled, min(top_k, scaled.size(-1)))
                scaled = scaled.masked_fill(scaled < values[:, [-1]], -float("inf"))
            next_tokens = torch.multinomial(F.softmax(scaled, dim=-1), num_samples=1)
            for i, token in enumerate(next_tokens[:, 0].tolist()):
                sample = out[i]
                if sample["finished"]:
                    continue
                sample["ids"].append(token)
                sample["text"] += token_bytes(token)
                if stops and any(s in sample["text"][-tail:] for s in stops):
                    sample["finished"] = True
            if all(s["finished"] for s in out):
                break
            logits, _ = self(next_tokens, cache=cache)
            logits = logits[:, -1, :]
        for sample in out:
            sample.pop("text")
        return out

    def parameter_count(self) -> int:
        return sum(p.numel() for p in self.parameters())
