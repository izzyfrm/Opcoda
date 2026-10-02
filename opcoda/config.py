from dataclasses import dataclass


@dataclass
class CodaConfig:
    vocab_size: int = 256
    block_size: int = 256
    n_layer: int = 4
    n_head: int = 4
    n_embd: int = 256
    dropout: float = 0.0


PROFILES = {
    # Start here on CPU. ~3.2M parameters.
    "smoke": CodaConfig(n_layer=4, n_head=4, n_embd=256, block_size=256),
    # Move here only after the full pipeline works reliably. ~11M parameters.
    "coda-10m": CodaConfig(n_layer=6, n_head=6, n_embd=384, block_size=256),
    # CPU training will be much slower. Intended for later hardware upgrades.
    "coda-25m": CodaConfig(n_layer=8, n_head=8, n_embd=512, block_size=384),
}
