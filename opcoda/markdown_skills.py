"""Select small, editable project guides for a generation request."""
import re
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent / "ai-skills"
MAX_FILE_CHARS = 4000
MAX_GUIDANCE_CHARS = 8500
STOP = {"about", "build", "create", "make", "website", "page", "code", "html", "css", "javascript", "with", "this", "that", "from", "your", "please"}


def _words(value: str) -> set[str]:
    words = set(re.findall(r"[a-z]{3,}", value.lower())) - STOP
    if words & {"style", "styles", "styling", "stylish"}:
        words.add("style")
    if words & {"background", "backgrounds"}:
        words.add("background")
    if words & {"animation", "animations", "animate"}:
        words.add("animation")
    return words


def markdown_guidance(prompt: str, language: str, directory: Path = SKILLS_DIR) -> str:
    """Read only local Markdown. Re-read on each call so edits apply to new requests."""
    if language not in {"html", "css", "javascript"} or not directory.is_dir():
        return ""
    terms = _words(prompt)
    matches = []
    for path in directory.glob("*.md"):
        if path.name.lower() == "readme.md" or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")[:MAX_FILE_CHARS]
        except (OSError, UnicodeError):
            continue
        header = " ".join(content.splitlines()[:4])
        score = len(terms & _words(path.stem + " " + header))
        if score:
            matches.append((score, path.name, content))
    matches.sort(key=lambda item: (-item[0], item[1]))
    return "\n\n".join(f"Guide: {name}\n{content}" for _, name, content in matches[:5])[:MAX_GUIDANCE_CHARS]
