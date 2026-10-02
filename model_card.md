# Coda 1.0 — development model card

**Project:** Opcoda  
**Model:** Coda 1.0  
**Status:** experimental / from-scratch training project

The opcoda.cc coding assistant currently uses `llama3.2:3b` locally through Ollama because the from-scratch Coda checkpoints did not pass the held-out coding tests. This card describes the research model, not the current website backend.

## Goal

Build a compact coding-focused language model without relying on a pretrained language model or external inference provider.

## Initial focus

- Python
- JavaScript
- HTML
- CSS
- code completion
- simple repair/debugging later

## Tokenizer

The first checkpoints use a 256-token UTF-8 byte tokenizer. This keeps the first training pipeline fully local and dependency-light. A trained Opcoda BPE tokenizer is a later milestone.

## Evaluation rule

A checkpoint is not considered "better" just because its output looks convincing. Opcoda should track held-out loss plus executable coding tests that never appear in training data.

## Data policy

Use code you own, code you intentionally create for training, or datasets/repos whose licenses permit the intended use. Track sources and licenses as the dataset grows.
