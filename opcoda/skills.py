"""Skills: short instructions the user switches on in Settings -> Skills.

Each skill adds one line to the system prompt for the languages it lists. Keep prompts
concrete and checkable; a small model follows "do X" far better than "be good at X".
The website shows name, description, group and languages; the prompt text never leaves
this machine.
"""

ALL = ("html", "css", "javascript", "python")
WEB = ("html", "css")
CODE = ("javascript", "python")

SKILLS = [
    # --- Quality -----------------------------------------------------------------------
    {"id": "examples", "group": "Quality", "name": "Usage example", "default": True, "langs": CODE,
     "description": "Ends scripts with a small demo that prints real output, so Run shows something.",
     "prompt": "Finish with a short runnable demo that calls the main code with realistic example values and prints the results "
               "(in Python under if __name__ == \"__main__\":). Never read input() or files."},
    {"id": "tests", "group": "Quality", "name": "Built-in tests", "default": False, "langs": CODE,
     "description": "Adds assert-based checks for normal and edge cases to the demo.",
     "prompt": "In the demo, add 4-6 assert checks (Python assert / JavaScript console.assert) covering normal input and edge cases "
               "such as empty input, one item and invalid values, then print 'All tests passed'."},
    {"id": "errors", "group": "Quality", "name": "Careful error handling", "default": False, "langs": CODE,
     "description": "Validates input and fails with clear error messages.",
     "prompt": "Validate arguments and raise/throw specific errors (ValueError, TypeError, RangeError) with clear messages "
               "instead of failing silently or returning wrong values."},
    {"id": "stdlib", "group": "Quality", "name": "No dependencies", "default": True, "langs": ALL,
     "description": "Standard library and plain browser APIs only, so everything runs in the sandbox.",
     "prompt": "Use only the language's standard library and built-in browser APIs: no pip/npm packages, CDNs, frameworks or external files."},
    {"id": "performance", "group": "Quality", "name": "Efficient algorithms", "default": False, "langs": CODE,
     "description": "Picks the right data structure and notes the time complexity.",
     "prompt": "Choose efficient algorithms and data structures (sets/dicts for lookups, no needless nested loops) and state the "
               "time complexity of the main function in one short comment."},
    # --- Style ------------------------------------------------------------------------
    {"id": "clean", "group": "Style", "name": "Clean code", "default": True, "langs": ALL,
     "description": "Descriptive names, small focused functions and consistent formatting.",
     "prompt": "Use descriptive names, small single-purpose functions, consistent 4-space (Python) or 2-space (web) indentation, "
               "and no dead code or unused variables."},
    {"id": "comments", "group": "Style", "name": "Explain with comments", "default": False, "langs": ALL,
     "description": "Short comments on the parts that aren't obvious.",
     "prompt": "Add brief comments that explain non-obvious decisions. Do not comment every line."},
    {"id": "docstrings", "group": "Style", "name": "Docstrings", "default": False, "langs": CODE,
     "description": "Every function documents its arguments and what it returns.",
     "prompt": "Give every function a docstring (Python) or JSDoc block (JavaScript) describing its purpose, arguments and return value."},
    {"id": "types", "group": "Style", "name": "Typed code", "default": False, "langs": CODE,
     "description": "Python type hints and JSDoc types on functions.",
     "prompt": "Add type hints to every Python function signature, or JSDoc @param/@returns types to every JavaScript function."},
    {"id": "beginner", "group": "Style", "name": "Beginner friendly", "default": False, "langs": ALL,
     "description": "Simple, readable constructs instead of clever one-liners.",
     "prompt": "Write for a beginner: plain loops and if-statements over clever one-liners, one idea per line, "
               "and a comment before each section saying what it does."},
    {"id": "modern-js", "group": "Style", "name": "Modern JavaScript", "default": True, "langs": ("html", "javascript"),
     "description": "const/let, arrow functions, template literals and addEventListener.",
     "prompt": "Use modern JavaScript: const/let (never var), arrow functions for callbacks, template literals, === comparisons, "
               "and addEventListener instead of inline onclick attributes."},
    # --- Web design -------------------------------------------------------------------
    {"id": "accessible", "group": "Web design", "name": "Accessible by default", "default": True, "langs": ("html", "css", "javascript"),
     "description": "Semantic HTML, labelled controls, strong contrast and visible focus states.",
     "prompt": "Use semantic landmarks and headings in order, label every form control, give images alt text, keep text contrast "
               "at WCAG AA, make everything keyboard-usable, and show a visible :focus-visible style."},
    {"id": "responsive", "group": "Web design", "name": "Mobile-friendly layouts", "default": True, "langs": WEB,
     "description": "Layouts that work from phone to desktop without sideways scrolling.",
     "prompt": "Design mobile-first: fluid widths with a max-width container, grid/flex that wraps, and at least one media query. "
               "Nothing may overflow horizontally at 360px wide."},
    {"id": "design-tokens", "group": "Web design", "name": "Design tokens", "default": False, "langs": WEB,
     "description": "All colours, spacing and radii come from CSS variables.",
     "prompt": "Define every colour, spacing step, radius and font size as a CSS custom property on :root and use only those variables."},
    {"id": "motion", "group": "Web design", "name": "Subtle motion", "default": False, "langs": WEB,
     "description": "Gentle hover and entrance animations that respect reduced motion.",
     "prompt": "Add subtle 150-300ms transitions for hover/focus and a gentle entrance animation, disabled under prefers-reduced-motion: reduce."},
    {"id": "dark", "group": "Web design", "name": "Dark theme first", "default": False, "langs": WEB,
     "description": "Pages default to a dark colour scheme unless you ask otherwise.",
     "prompt": "Unless the request names colours, use a dark theme: near-black background, light text, one restrained accent."},
    {"id": "light", "group": "Web design", "name": "Light theme first", "default": False, "langs": WEB,
     "description": "Pages default to a clean light colour scheme unless you ask otherwise.",
     "prompt": "Unless the request names colours, use a light theme: white or off-white background, near-black text, one restrained accent."},
    {"id": "theme-toggle", "group": "Web design", "name": "Light/dark toggle", "default": False, "langs": ("html",),
     "description": "Pages get a working light/dark switch that follows the system setting.",
     "prompt": "Include a light/dark theme toggle button that switches CSS variables, starts from prefers-color-scheme, and remembers the choice in localStorage."},
    {"id": "seo", "group": "Web design", "name": "SEO-ready pages", "default": False, "langs": ("html",),
     "description": "Meta description, social preview tags and a sensible heading outline.",
     "prompt": "Add a meta description, Open Graph title/description tags, one <h1>, a logical heading outline and descriptive link text."},
    # --- Apps -------------------------------------------------------------------------
    {"id": "save-state", "group": "Apps", "name": "Remember data", "default": True, "langs": ("html", "javascript"),
     "description": "Apps keep the user's data in localStorage between visits.",
     "prompt": "For apps with user data (lists, scores, settings), save it to localStorage on every change and load it on start, "
               "wrapping storage access in try/catch."},
    {"id": "validation", "group": "Apps", "name": "Form validation", "default": False, "langs": ("html", "javascript"),
     "description": "Required fields, inline error messages and no bad submissions.",
     "prompt": "Validate forms before submitting: mark required fields, show a clear inline error next to each invalid field, "
               "and prevent submission until everything is valid."},
    {"id": "empty-states", "group": "Apps", "name": "Empty & error states", "default": False, "langs": ("html",),
     "description": "Apps show helpful messages when there's nothing to show or something fails.",
     "prompt": "Design empty, loading and error states: when a list is empty or an action fails, show a short helpful message instead of a blank area."},
    {"id": "keyboard", "group": "Apps", "name": "Keyboard shortcuts", "default": False, "langs": ("html",),
     "description": "Common actions work from the keyboard, like Enter to add and Escape to cancel.",
     "prompt": "Support keyboard use for the main actions: Enter submits, Escape cancels or closes, and focus moves sensibly after each action."},
]
BY_ID = {s["id"]: s for s in SKILLS}


def skill_prompts(overrides: dict[str, bool], lang: str) -> str:
    chosen = [s for s in SKILLS if overrides.get(s["id"], s["default"]) and lang in s["langs"]]
    # Contradictory themes: the explicit choice (an override) wins, otherwise dark.
    ids = {s["id"] for s in chosen}
    if {"dark", "light"} <= ids:
        chosen = [s for s in chosen if s["id"] != ("dark" if overrides.get("light") and not overrides.get("dark") else "light")]
    return "\n".join("- " + s["prompt"] for s in chosen)


def catalog() -> list[dict]:
    return [{k: s[k] for k in ("id", "name", "description", "default", "group")} | {"langs": list(s["langs"]), "kind": "builtin"}
            for s in SKILLS]
