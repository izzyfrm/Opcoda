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


def guide_id(path: Path) -> str:
    return "guide-" + re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-")


def _guide_files(directory: Path):
    if not directory.is_dir():
        return
    for path in sorted(directory.glob("*.md")):
        if path.name.lower() == "readme.md" or not path.is_file():
            continue
        try:
            yield path, path.read_text(encoding="utf-8")[:MAX_FILE_CHARS]
        except (OSError, UnicodeError):
            continue


def list_guides(directory: Path = SKILLS_DIR) -> list[dict]:
    """Name and one-line summary of every guide, for the website's Skills settings."""
    guides = []
    for path, content in _guide_files(directory):
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        title = next((line.lstrip("# ").strip() for line in lines if line.startswith("#")), path.stem.replace("-", " "))
        summary = next((line.lstrip("-* ").strip() for line in lines
                        if not line.startswith("#") and not line.lower().startswith("keywords:")), "")
        summary = re.sub(r"`([^`]*)`", r"\1", summary)
        guides.append({"id": guide_id(path), "name": title[:60],
                       "description": summary[:157] + "…" if len(summary) > 160 else summary})
    return guides


def markdown_guidance(prompt: str, language: str, directory: Path = SKILLS_DIR,
                      overrides: dict[str, bool] | None = None) -> str:
    """Read only local Markdown. Re-read on each call so edits apply to new requests.

    Guides are picked by matching words in the request. `overrides` comes from the
    user's Skills settings: True always includes a guide, False never does.
    """
    if language not in {"html", "css", "javascript"}:
        return ""
    overrides = overrides or {}
    terms = _words(prompt)
    matches = []
    for path, content in _guide_files(directory):
        choice = overrides.get(guide_id(path))
        if choice is False:
            continue
        header = " ".join(content.splitlines()[:4])
        score = 100 if choice else len(terms & _words(path.stem + " " + header))
        if score:
            matches.append((score, path.name, content))
    matches.sort(key=lambda item: (-item[0], item[1]))
    return "\n\n".join(f"Guide: {name}\n{content}" for _, name, content in matches[:5])[:MAX_GUIDANCE_CHARS]
