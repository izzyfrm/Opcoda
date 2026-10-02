"""Bounded, local UI/UX Pro Max retrieval for Coda's small context window."""
import csv
import re
from functools import lru_cache
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent / "model-skills" / "ui-ux-pro-max"
UI_WORDS = re.compile(r"\b(ui|ux|interface|component|page|website|dashboard|form|button|layout|frontend|navigation)\b", re.I)
BASE = (
    "UI/UX Pro Max guidance: prioritize accessibility, usable interactions and responsive layout. "
    "Use semantic HTML, visible input labels, keyboard focus, readable contrast, and comfortable touch targets. "
    "Use consistent spacing and typography; avoid horizontal overflow. Honor reduced motion. "
    "Prefer restrained decoration and functional controls. Follow the user's requested visual direction."
)


@lru_cache(maxsize=4)
def rows(filename: str) -> tuple[dict, ...]:
    with (SKILL_DIR / "data" / filename).open(encoding="utf-8-sig", newline="") as source:
        return tuple(csv.DictReader(source))


def ui_guidance(prompt: str, language: str) -> str:
    """Use catalog recommendations as context, never execute skill scripts or user input."""
    if language not in ("html", "css") and not (language == "javascript" and UI_WORDS.search(prompt)):
        return ""
    if not (SKILL_DIR / "SKILL.md").is_file():
        return ""
    terms = set(re.findall(r"[a-z]{3,}", prompt.lower())) - {"the", "and", "with", "for", "that", "this", "write", "create", "make"}
    guidance = [BASE]
    catalogs = (
        ("ux-guidelines.csv", ("Issue", "Description"), ("Issue", "Do", "Don't"), 2),
        ("styles.csv", ("Style Category",), ("Style Category", "CSS/Technical Keywords"), 1),
        ("colors.csv", ("Product Type",), ("Product Type", "Background", "Foreground", "Primary", "On Primary"), 1),
    )
    for filename, search_fields, output_fields, limit in catalogs:
        try:
            matches = []
            for row in rows(filename):
                if row.get("Status", "active") != "active":
                    continue
                words = set(re.findall(r"[a-z]{3,}", " ".join(row.get(k, "") for k in search_fields).lower()))
                score = len(terms & words)
                if score:
                    matches.append((score, row))
            for _, row in sorted(matches, key=lambda item: item[0], reverse=True)[:limit]:
                recommendation = "; ".join(f"{key}: {row[key]}" for key in output_fields if row.get(key))
                guidance.append(recommendation[:400])
        except (OSError, csv.Error):
            continue
    return "\n".join(guidance)[:1800]
