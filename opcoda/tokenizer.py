class ByteTokenizer:
    """A dependency-free UTF-8 byte tokenizer.

    Every byte value 0..255 is a token. It is deliberately simple for the
    first Coda checkpoint: no external tokenizer model and no pretrained vocab.
    Later, Opcoda can replace this with its own trained BPE tokenizer.
    """

    vocab_size = 256

    def encode(self, text: str) -> list[int]:
        return list(text.encode("utf-8"))

    def decode(self, tokens: list[int]) -> str:
        return bytes(tokens).decode("utf-8", errors="replace")
