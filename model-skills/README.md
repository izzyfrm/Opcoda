# Opcoda model skills

`ui-ux-pro-max` is vendored from https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
(`.claude/skills/ui-ux-pro-max`, MIT license).

Coda's Ollama request builder uses `opcoda/ui_skill.py` to retrieve compact
recommendations from the bundled UX, style, and color catalogs for HTML/CSS
and UI-related JavaScript requests. Retrieval stays local, executes no skill
scripts, and adds at most 1,800 characters to the system prompt to fit the
4,096-token context. Explicit user design requirements take priority.

This is inference-time guidance, not model training. The complete upstream
skill is retained for reference; the small local model does not execute its
multi-step agent workflow. Backend-only requests do not receive UI guidance.
