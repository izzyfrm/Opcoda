"""HTML/CSS/JS task families for Coda's Phase 4 curriculum.

Each family is a function rng -> (task description, code). Pages are complete
documents assembled from sections; the description is generated from the same
choices, so "three feature cards and a contact form" always matches the code.
Every example is validated with opcoda.verify before it reaches the training set.
"""
from __future__ import annotations

import html as _html
from dataclasses import dataclass
from random import Random
from typing import Callable

from web_content import (BUSINESSES, CITIES, FAQS, FIRST_NAMES, FONTS, GENERIC_FEATURES, GENERIC_KINDS,
                         GENERIC_NAME_PARTS, HOURS, LAST_NAMES, PALETTES, PROJECTS, QUIZ_TOPICS, QUOTES, ROLES,
                         TESTIMONIALS, Palette)


@dataclass(frozen=True)
class CodeFamily:
    key: str
    lang: str
    topic: str
    make: Callable[[Random], tuple[str, str]]


FAMILIES: list[CodeFamily] = []


def family(key: str, lang: str, topic: str):
    def register(fn):
        FAMILIES.append(CodeFamily(key, lang, topic, fn))
        return fn
    return register


def esc(text: str) -> str:
    return _html.escape(text, quote=True)


NUM_WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}


def join_parts(parts: list[str]) -> str:
    return parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]


def slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    while "--" in out:
        out = out.replace("--", "-")
    return out.strip("-")


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

class Html:
    def __init__(self):
        self.lines: list[str] = []
        self.level = 0

    def add(self, text: str = "") -> None:
        self.lines.append("  " * self.level + text if text else "")

    def open(self, text: str) -> None:
        self.add(text)
        self.level += 1

    def close(self, text: str) -> None:
        self.level -= 1
        self.add(text)

    def raw(self, block: str) -> None:
        for line in block.split("\n"):
            self.add(line)

    def render(self) -> str:
        return "\n".join(self.lines) + "\n"


class Css:
    def __init__(self):
        self.items: list = []

    def rule(self, selector: str, *decls: str) -> None:
        self.items.append(("rule", selector, [d for d in decls if d]))

    def media(self, query: str, rules: list[tuple[str, list[str]]]) -> None:
        self.items.append(("media", query, rules))

    def raw(self, text: str) -> None:
        self.items.append(("raw", text, None))

    def render(self) -> str:
        out: list[str] = []
        for kind, a, b in self.items:
            if kind == "rule":
                out.append(f"{a} {{")
                out.extend(f"  {d};" for d in b)
                out.append("}")
            elif kind == "media":
                out.append(f"{a} {{")
                for sel, decls in b:
                    out.append(f"  {sel} {{")
                    out.extend(f"    {d};" for d in decls)
                    out.append("  }")
                out.append("}")
            else:
                out.append(a.rstrip("\n"))
            out.append("")
        return "\n".join(out).rstrip("\n") + "\n"


class Theme:
    VAR_NAMES = {"bg": "bg", "surface": "surface", "text": "text", "muted": "muted", "primary": "primary",
                 "on_primary": "on-primary", "border": "border", "accent": "accent"}

    def __init__(self, rng: Random, palette: Palette | None = None):
        self.p = palette or rng.choice(PALETTES)
        self.font, self.font_desc = rng.choice(FONTS)
        self.use_vars = rng.random() < 0.65
        self.radius = rng.choice([4, 6, 8, 10, 12, 16])
        self.width = rng.choice([960, 1040, 1100, 1200])
        self.shadow = rng.random() < 0.5

    def c(self, name: str) -> str:
        return f"var(--{self.VAR_NAMES[name]})" if self.use_vars else getattr(self.p, name)

    def card_shadow(self) -> str:
        if not self.shadow:
            return ""
        return "box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25)" if self.p.dark else "box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06)"

    def base(self, css: Css, buttons: bool = True) -> None:
        if self.use_vars:
            css.rule(":root", *(f"--{v}: {getattr(self.p, k)}" for k, v in self.VAR_NAMES.items()))
        css.rule("*, *::before, *::after", "box-sizing: border-box")
        css.rule("body", "margin: 0", f"font-family: {self.font}", "line-height: 1.6",
                 f"color: {self.c('text')}", f"background: {self.c('bg')}")
        css.rule(".container", f"max-width: {self.width}px", "margin: 0 auto", "padding: 0 24px")
        if buttons:
            css.rule(".button", "display: inline-block", "padding: 12px 22px", f"border-radius: {self.radius}px",
                     f"background: {self.c('primary')}", f"color: {self.c('on_primary')}", "text-decoration: none",
                     "font-weight: 600", "border: none", "cursor: pointer")
            css.rule(".button:hover", "opacity: 0.9")


def document(title: str, css: str, body: Html, script: str | None = None, rng: Random | None = None) -> str:
    slash = " /" if rng is not None and rng.random() < 0.3 else ""
    doc = Html()
    doc.add("<!DOCTYPE html>")
    doc.add('<html lang="en">')
    doc.open("<head>")
    doc.add(f'<meta charset="UTF-8"{slash}>')
    doc.add(f'<meta name="viewport" content="width=device-width, initial-scale=1.0"{slash}>')
    doc.add(f"<title>{esc(title)}</title>")
    doc.open("<style>")
    doc.raw(css.rstrip("\n"))
    doc.close("</style>")
    doc.close("</head>")
    doc.open("<body>")
    for line in body.lines:
        doc.lines.append("  " * doc.level + line if line else "")
    if script:
        doc.open("<script>")
        doc.raw(script.rstrip("\n"))
        doc.close("</script>")
    doc.close("</body>")
    doc.add("</html>")
    return doc.render()


# ---------------------------------------------------------------------------
# Businesses
# ---------------------------------------------------------------------------

@dataclass
class Business:
    kind: str
    name: str
    city: str
    tagline: str
    features: list[tuple[str, str]]
    products: list[tuple[str, float]]
    cta: str
    nav: list[str]
    food: bool


def pick_business(rng: Random) -> Business:
    if rng.random() < 0.25:
        kind = rng.choice(GENERIC_KINDS)
        name = f"{rng.choice(GENERIC_NAME_PARTS[0])} {rng.choice(GENERIC_NAME_PARTS[1])}"
        city = rng.choice(CITIES)
        tagline = rng.choice([f"The friendliest {kind} in {city}.", f"Quality {kind} services you can trust.",
                              f"{city}'s favorite {kind}."])
        features = rng.sample(GENERIC_FEATURES, 6)
        products = [(f"{p} service", price) for p, price in
                    zip(["Basic", "Standard", "Premium", "Express"], sorted(rng.sample(range(20, 400, 5), 4)))]
        return Business(kind, name, city, tagline, features, products,
                        rng.choice(["Get in touch", "Book now", "Get a quote"]), ["Services", "About", "Pricing", "Contact"], False)
    kind = rng.choice(list(BUSINESSES))
    data = BUSINESSES[kind]
    return Business(kind, rng.choice(data["names"]), rng.choice(CITIES), rng.choice(data["taglines"]),
                    rng.sample(data["features"], len(data["features"])), list(data["products"]),
                    rng.choice(data["cta"]), list(data["nav"]), data.get("food", False))


def person(rng: Random) -> str:
    return f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"


def money(value: float) -> str:
    return f"${value:,.0f}" if value >= 100 or value == int(value) else f"${value:,.2f}"


# ---------------------------------------------------------------------------
# Page sections: each writes HTML into `h`, CSS into `css`, returns a description phrase
# ---------------------------------------------------------------------------

def sec_nav(h: Html, css: Css, t: Theme, b: Business, rng: Random) -> str:
    with_button = rng.random() < 0.5
    h.open('<header class="site-header">')
    h.open('<nav class="nav container">')
    h.add(f'<a class="logo" href="#">{esc(b.name)}</a>')
    h.open('<ul class="nav-links">')
    for item in b.nav:
        h.add(f'<li><a href="#{slug(item)}">{esc(item)}</a></li>')
    h.close("</ul>")
    if with_button:
        h.add(f'<a class="button" href="#contact">{esc(b.cta)}</a>')
    h.close("</nav>")
    h.close("</header>")
    sticky = rng.random() < 0.4
    css.rule(".site-header", f"background: {t.c('surface')}", f"border-bottom: 1px solid {t.c('border')}",
             "position: sticky" if sticky else "", "top: 0" if sticky else "")
    css.rule(".nav", "display: flex", "align-items: center", "justify-content: space-between", "gap: 24px",
             "padding-top: 16px", "padding-bottom: 16px")
    css.rule(".logo", "font-weight: 700", "font-size: 1.25rem", f"color: {t.c('text')}", "text-decoration: none")
    css.rule(".nav-links", "display: flex", "gap: 20px", "list-style: none", "margin: 0", "padding: 0")
    css.rule(".nav-links a", f"color: {t.c('muted')}", "text-decoration: none")
    css.rule(".nav-links a:hover", f"color: {t.c('text')}")
    return rng.choice(["a navigation bar", "a header with navigation links", "a top navigation bar"]) + \
        (f' and a "{b.cta}" button' if with_button else "")


def sec_hero(h: Html, css: Css, t: Theme, b: Business, rng: Random) -> str:
    centered = rng.random() < 0.6
    secondary = rng.random() < 0.5
    h.open('<section class="hero">')
    h.open('<div class="container">')
    h.add(f'<p class="eyebrow">{esc(b.kind.capitalize())} in {esc(b.city)}</p>')
    h.add(f"<h1>{esc(b.tagline)}</h1>")
    h.add(f'<p class="lead">Welcome to {esc(b.name)}. {esc(b.features[0][1])}</p>')
    h.open('<div class="hero-actions">')
    h.add(f'<a class="button" href="#contact">{esc(b.cta)}</a>')
    if secondary:
        h.add(f'<a class="button button-outline" href="#{slug(b.nav[0])}">{esc(b.nav[0])}</a>')
    h.close("</div>")
    h.close("</div>")
    h.close("</section>")
    css.rule(".hero", "padding: 96px 0 80px", f"text-align: {'center' if centered else 'left'}")
    css.rule(".eyebrow", f"color: {t.c('primary' if not t.p.dark else 'accent')}", "font-weight: 600",
             "text-transform: uppercase", "letter-spacing: 0.08em", "font-size: 0.85rem", "margin: 0 0 12px")
    css.rule(".hero h1", "font-size: clamp(2rem, 5vw, 3.25rem)", "line-height: 1.15", "margin: 0 0 16px")
    css.rule(".lead", f"color: {t.c('muted')}", "font-size: 1.15rem", "max-width: 40rem",
             "margin: 0 auto 32px" if centered else "margin: 0 0 32px")
    css.rule(".hero-actions", "display: flex", "gap: 12px", "flex-wrap: wrap",
             "justify-content: center" if centered else "")
    if secondary:
        css.rule(".button-outline", "background: transparent", f"color: {t.c('text')}", f"border: 1px solid {t.c('border')}")
    return f'a hero section with a "{b.cta}" button' if rng.random() < 0.6 else "a hero section with a headline and call-to-action"


def sec_features(h: Html, css: Css, t: Theme, b: Business, rng: Random, n: int) -> str:
    title = rng.choice(["Why people choose us", "What we offer", f"Why {b.name}", "Our services"])
    h.open('<section class="features" id="services">')
    h.open('<div class="container">')
    h.add(f"<h2>{esc(title)}</h2>")
    h.open('<div class="grid">')
    for name, text in b.features[:n]:
        h.open('<article class="card">')
        h.add(f"<h3>{esc(name)}</h3>")
        h.add(f"<p>{esc(text)}</p>")
        h.close("</article>")
    h.close("</div>")
    h.close("</div>")
    h.close("</section>")
    css.rule(".features", "padding: 72px 0")
    css.rule(".features h2", "font-size: 2rem", "margin: 0 0 32px", "text-align: center")
    if rng.random() < 0.6:
        css.rule(".grid", "display: grid", "grid-template-columns: repeat(auto-fit, minmax(220px, 1fr))", "gap: 24px")
    else:
        css.rule(".grid", "display: flex", "flex-wrap: wrap", "gap: 24px")
        css.rule(".grid .card", "flex: 1 1 220px")
    css.rule(".card", f"background: {t.c('surface')}", f"border: 1px solid {t.c('border')}",
             f"border-radius: {t.radius}px", "padding: 24px", t.card_shadow())
    css.rule(".card h3", "margin: 0 0 8px")
    css.rule(".card p", "margin: 0", f"color: {t.c('muted')}")
    return f"{NUM_WORDS[n]} feature cards" if rng.random() < 0.6 else f"a section with {NUM_WORDS[n]} services"


def sec_products(h: Html, css: Css, t: Theme, b: Business, rng: Random, n: int) -> str:
    title = "Menu" if b.food else rng.choice(["Prices", "Services and prices", "Popular picks"])
    h.open(f'<section class="menu" id="{slug(title)}">')
    h.open('<div class="container">')
    h.add(f"<h2>{esc(title)}</h2>")
    h.open('<ul class="menu-list">')
    for name, price in b.products[:n]:
        h.open("<li>")
        h.add(f"<span>{esc(name)}</span>")
        h.add(f'<span class="price">{money(price)}</span>')
        h.close("</li>")
    h.close("</ul>")
    h.close("</div>")
    h.close("</section>")
    css.rule(".menu", "padding: 64px 0", f"background: {t.c('surface')}")
    css.rule(".menu h2", "font-size: 2rem", "margin: 0 0 24px")
    css.rule(".menu-list", "list-style: none", "margin: 0", "padding: 0", "max-width: 36rem")
    css.rule(".menu-list li", "display: flex", "justify-content: space-between", "padding: 12px 0",
             f"border-bottom: 1px dashed {t.c('border')}")
    css.rule(".price", "font-weight: 700", f"color: {t.c('primary' if not t.p.dark else 'accent')}")
    return "a menu with prices" if b.food else "a price list"


def sec_testimonial(h: Html, css: Css, t: Theme, b: Business, rng: Random) -> str:
    quote = rng.choice(TESTIMONIALS).format(kind=b.kind, city=b.city, name=b.name)
    h.open('<section class="testimonial">')
    h.open('<div class="container">')
    h.open("<blockquote>")
    h.add(f"<p>&ldquo;{esc(quote)}&rdquo;</p>")
    h.add(f"<cite>{esc(person(rng))}</cite>")
    h.close("</blockquote>")
    h.close("</div>")
    h.close("</section>")
    css.rule(".testimonial", "padding: 64px 0", "text-align: center")
    css.rule(".testimonial blockquote", "margin: 0 auto", "max-width: 40rem")
    css.rule(".testimonial p", "font-size: 1.35rem", "font-style: italic", "margin: 0 0 12px")
    css.rule(".testimonial cite", f"color: {t.c('muted')}", "font-style: normal")
    return rng.choice(["a customer testimonial", "a review quote from a customer"])


def sec_stats(h: Html, css: Css, t: Theme, b: Business, rng: Random) -> str:
    stats = [(f"{rng.randint(3, 25)}", "years in business"), (f"{rng.randint(2, 40)},{rng.randint(100, 999)}", "happy customers"),
             (f"{rng.randint(4, 5)}.{rng.randint(6, 9)}", "average rating")]
    h.open('<section class="stats">')
    h.open('<div class="container stats-grid">')
    for value, label in stats:
        h.open('<div class="stat">')
        h.add(f"<strong>{value}</strong>")
        h.add(f"<span>{label}</span>")
        h.close("</div>")
    h.close("</div>")
    h.close("</section>")
    css.rule(".stats", "padding: 48px 0", f"background: {t.c('primary')}", f"color: {t.c('on_primary')}")
    css.rule(".stats-grid", "display: grid", "grid-template-columns: repeat(3, 1fr)", "gap: 24px", "text-align: center")
    css.rule(".stat strong", "display: block", "font-size: 2.25rem")
    css.rule(".stat span", "opacity: 0.85")
    return "a row of three stats"


def sec_cta(h: Html, css: Css, t: Theme, b: Business, rng: Random) -> str:
    h.open('<section class="cta">')
    h.open('<div class="container">')
    h.add(f"<h2>{esc(rng.choice(['Ready to get started?', 'Come say hello', 'Questions? We would love to help.']))}</h2>")
    h.add(f'<a class="button" href="#contact">{esc(b.cta)}</a>')
    h.close("</div>")
    h.close("</section>")
    css.rule(".cta", "padding: 64px 0", "text-align: center", f"background: {t.c('surface')}",
             f"border-top: 1px solid {t.c('border')}")
    css.rule(".cta h2", "margin: 0 0 20px")
    return "a call-to-action banner"


def sec_contact(h: Html, css: Css, t: Theme, b: Business, rng: Random) -> str:
    with_phone = rng.random() < 0.4
    h.open('<section class="contact" id="contact">')
    h.open('<div class="container">')
    h.add("<h2>Contact us</h2>")
    h.open('<form class="contact-form">')
    h.add('<label for="name">Name</label>')
    h.add('<input id="name" name="name" type="text" required>')
    h.add('<label for="email">Email</label>')
    h.add('<input id="email" name="email" type="email" required>')
    if with_phone:
        h.add('<label for="phone">Phone</label>')
        h.add('<input id="phone" name="phone" type="tel">')
    h.add('<label for="message">Message</label>')
    h.add('<textarea id="message" name="message" rows="5" required></textarea>')
    h.add('<button class="button" type="submit">Send message</button>')
    h.close("</form>")
    h.close("</div>")
    h.close("</section>")
    css.rule(".contact", "padding: 72px 0")
    css.rule(".contact-form", "display: grid", "gap: 8px", "max-width: 32rem")
    css.rule(".contact-form input, .contact-form textarea", "width: 100%", "padding: 10px 12px", "font: inherit",
             f"color: {t.c('text')}", f"background: {t.c('surface')}", f"border: 1px solid {t.c('border')}",
             f"border-radius: {max(4, t.radius - 4)}px", "margin-bottom: 8px")
    css.rule(".contact-form button", "justify-self: start")
    return "a contact form" + (" with a phone field" if with_phone else "")


def sec_faq(h: Html, css: Css, t: Theme, b: Business, rng: Random, n: int = 3) -> str:
    h.open('<section class="faq" id="faq">')
    h.open('<div class="container">')
    h.add("<h2>Frequently asked questions</h2>")
    for q, a in rng.sample(FAQS, n):
        h.open("<details>")
        h.add(f"<summary>{esc(q)}</summary>")
        h.add(f"<p>{esc(a)}</p>")
        h.close("</details>")
    h.close("</div>")
    h.close("</section>")
    css.rule(".faq", "padding: 64px 0")
    css.rule(".faq details", f"border-bottom: 1px solid {t.c('border')}", "padding: 16px 0")
    css.rule(".faq summary", "cursor: pointer", "font-weight: 600")
    css.rule(".faq p", f"color: {t.c('muted')}", "margin: 8px 0 0")
    return "an FAQ section"


def sec_footer(h: Html, css: Css, t: Theme, b: Business, rng: Random) -> str:
    year = rng.choice([2024, 2025, 2026])
    h.open('<footer class="site-footer">')
    h.open('<div class="container">')
    h.add(f"<p>&copy; {year} {esc(b.name)}. {esc(b.city)}.</p>")
    if rng.random() < 0.5:
        h.add('<p><a href="#">Instagram</a> · <a href="#">Facebook</a></p>')
    h.close("</div>")
    h.close("</footer>")
    css.rule(".site-footer", "padding: 32px 0", f"color: {t.c('muted')}", f"border-top: 1px solid {t.c('border')}",
             "text-align: center", "font-size: 0.9rem")
    return "a footer"


def responsive(css: Css, t: Theme, extra: list[tuple[str, list[str]]] | None = None) -> None:
    rules = [(".nav-links", ["display: none"])]
    rules += extra or []
    css.media("@media (max-width: 640px)", rules)


# ---------------------------------------------------------------------------
# Page families
# ---------------------------------------------------------------------------

def _style_phrase(t: Theme, rng: Random) -> str:
    choices = [f" Use {t.p.desc}.", f" Style it with {t.p.desc} and {t.font_desc}.", ""]
    return rng.choice(choices)


@family("landing_page", "html", "pages")
def landing_page(rng: Random) -> tuple[str, str]:
    b = pick_business(rng)
    t = Theme(rng)
    h, css = Html(), Css()
    t.base(css)
    n = rng.choice([3, 3, 4])
    parts = [sec_nav(h, css, t, b, rng)]
    h.open("<main>")
    parts.append(sec_hero(h, css, t, b, rng))
    parts.append(sec_features(h, css, t, b, rng, n))
    extras = rng.sample(["testimonial", "stats", "products", "cta", "contact", "faq"], rng.choice([0, 1, 1, 2]))
    for extra in extras:
        if extra == "testimonial":
            parts.append(sec_testimonial(h, css, t, b, rng))
        elif extra == "stats":
            parts.append(sec_stats(h, css, t, b, rng))
        elif extra == "products":
            parts.append(sec_products(h, css, t, b, rng, rng.choice([3, 4])))
        elif extra == "cta":
            parts.append(sec_cta(h, css, t, b, rng))
        elif extra == "contact":
            parts.append(sec_contact(h, css, t, b, rng))
        else:
            parts.append(sec_faq(h, css, t, b, rng, 3))
    h.close("</main>")
    parts.append(sec_footer(h, css, t, b, rng))
    responsive(css, t)
    code = document(f"{b.name} | {b.kind.capitalize()} in {b.city}", css.render(), h, rng=rng)
    style = _style_phrase(t, rng)
    task = rng.choice([
        f"Build a landing page for {b.name}, a {b.kind} in {b.city}. Include {join_parts(parts)}.{style}",
        f"Create a website for a {b.kind} called {b.name} with {join_parts(parts)}.{style}",
        f"Make a one-page website for {b.name} ({b.kind}, {b.city}). It needs {join_parts(parts)}.{style}",
        f"I need a homepage for my {b.kind}, {b.name}, in {b.city}. Add {join_parts(parts)}.",
        f"Write the HTML and CSS for a {b.kind} website named {b.name}: {join_parts(parts)}.{style}",
        f"Landing page for a {b.kind} in {b.city} called {b.name}.",
        f"Make a website for my {b.kind}.",
    ])
    return task, code


@family("menu_page", "html", "pages")
def menu_page(rng: Random) -> tuple[str, str]:
    b = pick_business(rng)
    t = Theme(rng)
    h, css = Html(), Css()
    t.base(css, buttons=False)
    n = rng.choice([4, 5, 6]) if len(b.products) >= 6 else len(b.products)
    sec_nav_simple(h, css, t, b)
    h.open("<main>")
    h.open('<section class="intro container">')
    h.add(f"<h1>{'Our menu' if b.food else 'Prices'}</h1>")
    h.add(f"<p>{esc(b.tagline)}</p>")
    h.close("</section>")
    part = sec_products(h, css, t, b, rng, n)
    hours = rng.random() < 0.5
    if hours:
        h.open('<section class="hours container">')
        h.add("<h2>Opening hours</h2>")
        h.open("<ul>")
        for day, time in HOURS:
            h.add(f"<li><strong>{day}:</strong> {time}</li>")
        h.close("</ul>")
        h.close("</section>")
        css.rule(".hours", "padding: 48px 24px")
        css.rule(".hours ul", "list-style: none", "padding: 0", f"color: {t.c('muted')}")
    h.close("</main>")
    sec_footer(h, css, t, b, rng)
    css.rule(".intro", "padding-top: 64px", "padding-bottom: 16px")
    css.rule(".intro h1", "font-size: 2.5rem", "margin: 0 0 8px")
    code = document(f"{'Menu' if b.food else 'Prices'} | {b.name}", css.render(), h, rng=rng)
    what = "menu" if b.food else "pricing"
    task = rng.choice([
        f"Create a {what} page for {b.name}, a {b.kind}. Show {NUM_WORDS[n]} items with prices" + (" and the opening hours." if hours else "."),
        f"Make an HTML page that lists the {what} of a {b.kind} called {b.name}" + (", plus opening hours." if hours else "."),
        f"{what.capitalize()} page for a {b.kind} with {part}" + (" and opening hours." if hours else "."),
    ])
    return task, code


def sec_nav_simple(h: Html, css: Css, t: Theme, b: Business) -> None:
    h.open('<header class="site-header">')
    h.open('<div class="container nav">')
    h.add(f'<a class="logo" href="#">{esc(b.name)}</a>')
    h.add(f'<a class="nav-link" href="#contact">Contact</a>')
    h.close("</div>")
    h.close("</header>")
    css.rule(".site-header", f"border-bottom: 1px solid {t.c('border')}", f"background: {t.c('surface')}")
    css.rule(".nav", "display: flex", "justify-content: space-between", "align-items: center", "padding-top: 16px",
             "padding-bottom: 16px")
    css.rule(".logo", "font-weight: 700", f"color: {t.c('text')}", "text-decoration: none")
    css.rule(".nav-link", f"color: {t.c('muted')}")


@family("pricing_page", "html", "pages")
def pricing_page(rng: Random) -> tuple[str, str]:
    b = pick_business(rng)
    t = Theme(rng)
    h, css = Html(), Css()
    t.base(css)
    plan_names = rng.choice([["Basic", "Pro", "Team"], ["Starter", "Growth", "Business"], ["Free", "Plus", "Premium"],
                             ["Solo", "Studio", "Agency"]])
    prices = sorted(rng.sample([0, 9, 12, 19, 29, 39, 49, 79, 99], 3))
    featured = rng.choice([1, 1, 2])
    perks = rng.sample(["Unlimited projects", "Priority support", "Custom domain", "Team members", "Analytics",
                        "Email support", "Daily backups", "API access", "Advanced reports", "Single sign-on"], 6)
    yearly = rng.random() < 0.3
    h.open("<main>")
    h.open('<section class="pricing container">')
    h.add(f"<h1>{esc(rng.choice(['Simple, honest pricing', 'Choose your plan', 'Plans for every size']))}</h1>")
    h.add(f'<p class="lead">All plans include a {rng.choice([7, 14, 30])}-day free trial.</p>')
    h.open('<div class="plans">')
    for i, (name, price) in enumerate(zip(plan_names, prices)):
        cls = "plan featured" if i == featured else "plan"
        h.open(f'<article class="{cls}">')
        if i == featured:
            h.add('<p class="badge">Most popular</p>')
        h.add(f"<h2>{name}</h2>")
        per = "/year" if yearly else "/month"
        h.add(f'<p class="price">${price * (10 if yearly else 1)}<span>{per}</span></p>')
        h.open("<ul>")
        for perk in perks[: 2 + i * 2]:
            h.add(f"<li>{perk}</li>")
        h.close("</ul>")
        h.add(f'<a class="button" href="#">{"Start free" if price == 0 else "Choose " + name}</a>')
        h.close("</article>")
    h.close("</div>")
    h.close("</section>")
    faq = rng.random() < 0.4
    if faq:
        sec_faq(h, css, t, b, rng, 3)
    h.close("</main>")
    css.rule(".pricing", "padding: 72px 24px", "text-align: center")
    css.rule(".pricing h1", "font-size: 2.5rem", "margin: 0 0 8px")
    css.rule(".lead", f"color: {t.c('muted')}", "margin: 0 0 40px")
    css.rule(".plans", "display: grid", "grid-template-columns: repeat(auto-fit, minmax(240px, 1fr))", "gap: 24px",
             "text-align: left")
    css.rule(".plan", f"background: {t.c('surface')}", f"border: 1px solid {t.c('border')}",
             f"border-radius: {t.radius}px", "padding: 28px", t.card_shadow())
    css.rule(".plan.featured", f"border: 2px solid {t.c('primary')}")
    css.rule(".badge", "display: inline-block", "margin: 0 0 8px", "padding: 2px 10px", "border-radius: 999px",
             "font-size: 0.8rem", f"background: {t.c('primary')}", f"color: {t.c('on_primary')}")
    css.rule(".plan h2", "margin: 0")
    css.rule(".price", "font-size: 2.5rem", "font-weight: 700", "margin: 8px 0 16px")
    css.rule(".price span", "font-size: 1rem", f"color: {t.c('muted')}", "font-weight: 400")
    css.rule(".plan ul", "list-style: none", "padding: 0", "margin: 0 0 24px")
    css.rule(".plan li", "padding: 6px 0", f"border-bottom: 1px solid {t.c('border')}")
    task = rng.choice([
        f"Create a pricing page with three plans: {', '.join(plan_names[:2])} and {plan_names[2]}. Highlight the {plan_names[featured]} plan as most popular" + (" and add an FAQ section." if faq else "."),
        f"Build a pricing table with {plan_names[0]}, {plan_names[1]} and {plan_names[2]} plans, {'yearly' if yearly else 'monthly'} prices, and a feature list for each." + (" Include an FAQ." if faq else ""),
        f"Make a pricing page for a SaaS product with 3 tiers.{_style_phrase(t, rng)}",
    ])
    return task, document(f"Pricing | {b.name}", css.render(), h, rng=rng)


@family("contact_page", "html", "pages")
def contact_page(rng: Random) -> tuple[str, str]:
    b = pick_business(rng)
    t = Theme(rng)
    h, css = Html(), Css()
    t.base(css)
    sec_nav_simple(h, css, t, b)
    h.open("<main>")
    part = sec_contact(h, css, t, b, rng)
    hours = rng.random() < 0.6
    if hours:
        h.open('<section class="visit container">')
        h.add("<h2>Visit us</h2>")
        h.add(f"<address>{rng.randint(10, 999)} {rng.choice(['Main', 'Oak', 'Pine', 'Market', 'River', 'Elm'])} Street<br>{esc(b.city)}</address>")
        h.open("<ul>")
        for day, time in HOURS:
            h.add(f"<li>{day}: {time}</li>")
        h.close("</ul>")
        h.close("</section>")
        css.rule(".visit", "padding-bottom: 64px")
        css.rule(".visit address", "font-style: normal", "margin-bottom: 12px")
        css.rule(".visit ul", "list-style: none", "padding: 0", f"color: {t.c('muted')}")
    h.close("</main>")
    sec_footer(h, css, t, b, rng)
    task = rng.choice([
        f"Create a contact page for {b.name} with {part}" + (", the address and opening hours." if hours else "."),
        f"Make a contact us page for a {b.kind} in {b.city}" + (" with a form, address and hours." if hours else " with a simple form."),
        f"HTML contact form page for {b.name}.{_style_phrase(t, rng)}",
    ])
    return task, document(f"Contact | {b.name}", css.render(), h, rng=rng)


@family("login_page", "html", "forms")
def login_page(rng: Random) -> tuple[str, str]:
    t = Theme(rng)
    brand = rng.choice([f"{rng.choice(GENERIC_NAME_PARTS[0])} {rng.choice(GENERIC_NAME_PARTS[1])}", "Acme", "Nimbus", "Orbit", "Taskly", "Notebook"])
    field = rng.choice(["email", "username"])
    remember = rng.random() < 0.6
    h, css = Html(), Css()
    t.base(css)
    h.open('<main class="auth">')
    h.open('<form class="auth-card">')
    h.add(f"<h1>Sign in to {esc(brand)}</h1>")
    h.add(f'<label for="{field}">{field.capitalize()}</label>')
    h.add(f'<input id="{field}" name="{field}" type="{"email" if field == "email" else "text"}" autocomplete="{field}" required>')
    h.add('<label for="password">Password</label>')
    h.add('<input id="password" name="password" type="password" autocomplete="current-password" required>')
    if remember:
        h.open('<div class="row">')
        h.add('<label class="check"><input type="checkbox" name="remember"> Remember me</label>')
        h.add('<a href="#">Forgot password?</a>')
        h.close("</div>")
    h.add('<button class="button" type="submit">Sign in</button>')
    h.add('<p class="switch">New here? <a href="#">Create an account</a></p>')
    h.close("</form>")
    h.close("</main>")
    css.rule(".auth", "min-height: 100vh", "display: grid", "place-items: center", "padding: 24px")
    css.rule(".auth-card", "width: 100%", "max-width: 380px", "display: grid", "gap: 8px", "padding: 32px",
             f"background: {t.c('surface')}", f"border: 1px solid {t.c('border')}", f"border-radius: {t.radius}px", t.card_shadow())
    css.rule(".auth-card h1", "font-size: 1.5rem", "margin: 0 0 16px")
    css.rule(".auth-card input[type=\"email\"], .auth-card input[type=\"text\"], .auth-card input[type=\"password\"]",
             "padding: 10px 12px", "font: inherit", f"border: 1px solid {t.c('border')}", f"border-radius: {max(4, t.radius - 4)}px",
             f"background: {t.c('bg')}", f"color: {t.c('text')}", "margin-bottom: 8px")
    if remember:
        css.rule(".row", "display: flex", "justify-content: space-between", "align-items: center", "font-size: 0.9rem", "margin-bottom: 8px")
    css.rule(".switch", "text-align: center", f"color: {t.c('muted')}", "font-size: 0.9rem")
    task = rng.choice([
        f"Create a login page for {brand} with {field} and password fields" + (", a remember me checkbox and a forgot password link." if remember else "."),
        f"Make a centered sign in form in HTML and CSS.{_style_phrase(t, rng)}",
        f"Build a login screen with a {field} field, a password field and a sign in button.",
        "login page",
    ])
    return task, document(f"Sign in | {brand}", css.render(), h, rng=rng)


@family("signup_page", "html", "forms")
def signup_page(rng: Random) -> tuple[str, str]:
    t = Theme(rng)
    brand = rng.choice(["Acme", "Nimbus", "Orbit", "Taskly", "Notebook", "Pathway", "Brightdesk"])
    h, css = Html(), Css()
    t.base(css)
    confirm = rng.random() < 0.6
    terms = rng.random() < 0.7
    h.open('<main class="auth">')
    h.open('<form class="auth-card">')
    h.add("<h1>Create your account</h1>")
    for fid, label, typ, ac in [("full-name", "Full name", "text", "name"), ("email", "Email", "email", "email"),
                                ("password", "Password", "password", "new-password")] + \
            ([("confirm-password", "Confirm password", "password", "new-password")] if confirm else []):
        h.add(f'<label for="{fid}">{label}</label>')
        h.add(f'<input id="{fid}" name="{fid}" type="{typ}" autocomplete="{ac}" required>')
    if terms:
        h.add('<label class="check"><input type="checkbox" name="terms" required> I agree to the terms</label>')
    h.add('<button class="button" type="submit">Create account</button>')
    h.add('<p class="switch">Already have an account? <a href="#">Sign in</a></p>')
    h.close("</form>")
    h.close("</main>")
    css.rule(".auth", "min-height: 100vh", "display: grid", "place-items: center", "padding: 24px")
    css.rule(".auth-card", "width: 100%", "max-width: 420px", "display: grid", "gap: 8px", "padding: 32px",
             f"background: {t.c('surface')}", f"border: 1px solid {t.c('border')}", f"border-radius: {t.radius}px")
    css.rule(".auth-card h1", "font-size: 1.5rem", "margin: 0 0 12px")
    css.rule(".auth-card input:not([type=\"checkbox\"])", "padding: 10px 12px", "font: inherit",
             f"border: 1px solid {t.c('border')}", f"border-radius: {max(4, t.radius - 4)}px",
             f"background: {t.c('bg')}", f"color: {t.c('text')}", "margin-bottom: 6px")
    css.rule(".check", "display: flex", "gap: 8px", "align-items: center", "font-size: 0.9rem", "margin: 6px 0 12px")
    css.rule(".switch", "text-align: center", f"color: {t.c('muted')}", "font-size: 0.9rem")
    extras = [x for x, on in (("a confirm password field", confirm), ("a terms checkbox", terms)) if on]
    task = rng.choice([
        f"Create a sign up page for {brand} with name, email and password fields" + (f", {join_parts(extras)}." if extras else "."),
        f"Build a registration form in HTML and CSS" + (f" that includes {join_parts(extras)}." if extras else "."),
        "signup form page",
    ])
    return task, document(f"Sign up | {brand}", css.render(), h, rng=rng)


@family("portfolio_page", "html", "pages")
def portfolio_page(rng: Random) -> tuple[str, str]:
    name = person(rng)
    role, skills = rng.choice(ROLES)
    t = Theme(rng)
    h, css = Html(), Css()
    t.base(css)
    projects = rng.sample(PROJECTS, rng.choice([3, 4]))
    with_skills = rng.random() < 0.6
    h.open('<header class="site-header">')
    h.open('<nav class="nav container">')
    h.add(f'<a class="logo" href="#">{esc(name)}</a>')
    h.open('<ul class="nav-links">')
    for item in ["Work", "About", "Contact"]:
        h.add(f'<li><a href="#{item.lower()}">{item}</a></li>')
    h.close("</ul>")
    h.close("</nav>")
    h.close("</header>")
    h.open("<main>")
    h.open('<section class="intro container">')
    h.add(f"<h1>Hi, I'm {esc(name.split()[0])}.</h1>")
    h.add(f'<p class="lead">I am a {role} based in {rng.choice(CITIES)}. I like building simple things that work well.</p>')
    h.close("</section>")
    h.open('<section class="work container" id="work">')
    h.add("<h2>Selected work</h2>")
    h.open('<div class="projects">')
    for title, text in projects:
        h.open('<article class="project">')
        h.add(f"<h3>{esc(title)}</h3>")
        h.add(f"<p>{esc(text)}</p>")
        h.close("</article>")
    h.close("</div>")
    h.close("</section>")
    if with_skills:
        h.open('<section class="about container" id="about">')
        h.add("<h2>Skills</h2>")
        h.open('<ul class="skills">')
        for skill in rng.sample(skills, 5):
            h.add(f"<li>{esc(skill)}</li>")
        h.close("</ul>")
        h.close("</section>")
        css.rule(".skills", "display: flex", "flex-wrap: wrap", "gap: 8px", "list-style: none", "padding: 0")
        css.rule(".skills li", "padding: 4px 12px", "border-radius: 999px", f"border: 1px solid {t.c('border')}")
    h.open('<section class="contact container" id="contact">')
    h.add("<h2>Get in touch</h2>")
    email = f"{name.split()[0].lower()}@example.com"
    h.add(f'<p><a href="mailto:{email}">{email}</a></p>')
    h.close("</section>")
    h.close("</main>")
    css.rule(".site-header", f"border-bottom: 1px solid {t.c('border')}")
    css.rule(".nav", "display: flex", "justify-content: space-between", "align-items: center", "padding-top: 16px", "padding-bottom: 16px")
    css.rule(".logo", "font-weight: 700", f"color: {t.c('text')}", "text-decoration: none")
    css.rule(".nav-links", "display: flex", "gap: 20px", "list-style: none", "margin: 0", "padding: 0")
    css.rule(".nav-links a", f"color: {t.c('muted')}", "text-decoration: none")
    css.rule(".intro", "padding-top: 96px", "padding-bottom: 48px")
    css.rule(".intro h1", "font-size: clamp(2.25rem, 6vw, 3.5rem)", "margin: 0")
    css.rule(".lead", f"color: {t.c('muted')}", "font-size: 1.2rem", "max-width: 36rem")
    css.rule(".work, .about, .contact", "padding-bottom: 56px")
    css.rule(".projects", "display: grid", "grid-template-columns: repeat(auto-fit, minmax(240px, 1fr))", "gap: 20px")
    css.rule(".project", "padding: 24px", f"border-radius: {t.radius}px", f"background: {t.c('surface')}",
             f"border: 1px solid {t.c('border')}")
    css.rule(".project h3", "margin: 0 0 6px")
    css.rule(".project p", "margin: 0", f"color: {t.c('muted')}")
    task = rng.choice([
        f"Build a personal portfolio website for {name}, a {role}. Show {NUM_WORDS[len(projects)]} projects" + (", a skills list" if with_skills else "") + " and contact info.",
        f"Make a simple portfolio page for a {role} with a project grid" + (" and skills." if with_skills else "."),
        f"portfolio website for a {role}.{_style_phrase(t, rng)}",
    ])
    return task, document(f"{name} | {role.capitalize()}", css.render(), h, rng=rng)


@family("not_found_page", "html", "pages")
def not_found_page(rng: Random) -> tuple[str, str]:
    t = Theme(rng)
    h, css = Html(), Css()
    t.base(css)
    big = rng.random() < 0.5
    h.open('<main class="center">')
    h.add('<p class="code">404</p>')
    h.add(f"<h1>{esc(rng.choice(['Page not found', 'This page went missing', 'Nothing to see here']))}</h1>")
    h.add(f"<p>{esc(rng.choice(['The page you are looking for does not exist or was moved.', 'Sorry, we could not find that page.']))}</p>")
    h.add('<a class="button" href="/">Back to home</a>')
    h.close("</main>")
    css.rule(".center", "min-height: 100vh", "display: flex", "flex-direction: column", "align-items: center",
             "justify-content: center", "text-align: center", "padding: 24px")
    css.rule(".code", f"font-size: {'8rem' if big else '5rem'}", "font-weight: 800", "margin: 0", "line-height: 1",
             f"color: {t.c('primary' if not t.p.dark else 'accent')}")
    css.rule(".center h1", "margin: 16px 0 8px")
    css.rule(".center p", f"color: {t.c('muted')}", "margin: 0 0 24px")
    task = rng.choice(["Create a 404 error page with a big 404, a message and a link back home.",
                       f"Make a friendly page not found screen.{_style_phrase(t, rng)}", "404 page in HTML and CSS"])
    return task, document("Page not found", css.render(), h, rng=rng)


@family("team_page", "html", "pages")
def team_page(rng: Random) -> tuple[str, str]:
    b = pick_business(rng)
    t = Theme(rng)
    h, css = Html(), Css()
    t.base(css, buttons=False)
    n = rng.choice([3, 4, 6])
    titles = ["Founder", "Designer", "Engineer", "Manager", "Head Chef", "Coach", "Support Lead", "Photographer", "Marketing"]
    sec_nav_simple(h, css, t, b)
    h.open("<main>")
    h.open('<section class="team container">')
    h.add("<h1>Meet the team</h1>")
    h.open('<div class="team-grid">')
    for _ in range(n):
        who = person(rng)
        initials = "".join(part[0] for part in who.split())
        h.open('<article class="member">')
        h.add(f'<div class="avatar">{initials}</div>')
        h.add(f"<h2>{esc(who)}</h2>")
        h.add(f"<p>{rng.choice(titles)}</p>")
        h.close("</article>")
    h.close("</div>")
    h.close("</section>")
    h.close("</main>")
    css.rule(".team", "padding-top: 64px", "padding-bottom: 64px", "text-align: center")
    css.rule(".team-grid", "display: grid", "grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))", "gap: 24px", "margin-top: 32px")
    css.rule(".member", "padding: 24px", f"background: {t.c('surface')}", f"border: 1px solid {t.c('border')}", f"border-radius: {t.radius}px")
    css.rule(".avatar", "width: 72px", "height: 72px", "margin: 0 auto 12px", "border-radius: 50%", "display: grid",
             "place-items: center", "font-weight: 700", f"background: {t.c('primary')}", f"color: {t.c('on_primary')}")
    css.rule(".member h2", "font-size: 1.1rem", "margin: 0")
    css.rule(".member p", "margin: 4px 0 0", f"color: {t.c('muted')}")
    task = rng.choice([f"Create a team page for {b.name} showing {NUM_WORDS[n]} people with initials avatars, names and job titles.",
                       f"Make a meet the team section with a grid of {n} team member cards.{_style_phrase(t, rng)}"])
    return task, document(f"Team | {b.name}", css.render(), h, rng=rng)


@family("blog_post_page", "html", "pages")
def blog_post_page(rng: Random) -> tuple[str, str]:
    t = Theme(rng)
    topic, heads = rng.choice([
        ("How to start running", ["Start slow", "Get good shoes", "Make it a habit"]),
        ("A beginner's guide to houseplants", ["Pick easy plants", "Water less than you think", "Find the right light"]),
        ("Learning to code in 2026", ["Pick one language", "Build small projects", "Read other people's code"]),
        ("Brewing better coffee at home", ["Use fresh beans", "Weigh everything", "Mind the water temperature"]),
        ("Saving money on groceries", ["Plan your meals", "Shop with a list", "Cook in batches"]),
    ])
    author = person(rng)
    h, css = Html(), Css()
    t.base(css, buttons=False)
    h.open('<article class="post">')
    h.add(f"<h1>{esc(topic)}</h1>")
    h.add(f'<p class="meta">By {esc(author)} · {rng.choice(["March", "June", "September", "November"])} {rng.randint(1, 28)}, {rng.choice([2025, 2026])} · {rng.randint(3, 9)} min read</p>')
    h.add(f"<p>{esc(topic)} is easier than it looks. Here are a few simple ideas that make a real difference.</p>")
    for head in heads:
        h.add(f"<h2>{esc(head)}</h2>")
        h.add(f"<p>{esc(head)} is the first thing most people skip, and the thing that matters most. Keep it simple and stay consistent.</p>")
    quote = rng.random() < 0.5
    if quote:
        h.add("<blockquote>Small steps every day add up to big results.</blockquote>")
        css.rule(".post blockquote", "margin: 24px 0", "padding-left: 16px", f"border-left: 4px solid {t.c('primary')}", "font-style: italic")
    h.close("</article>")
    css.rule(".post", "max-width: 42rem", "margin: 0 auto", "padding: 64px 24px", "font-size: 1.1rem")
    css.rule(".post h1", "font-size: clamp(2rem, 5vw, 2.75rem)", "line-height: 1.2", "margin: 0 0 8px")
    css.rule(".meta", f"color: {t.c('muted')}", "font-size: 0.95rem")
    css.rule(".post h2", "margin-top: 40px")
    task = rng.choice([f'Write a blog post page titled "{topic}" with an author line, {NUM_WORDS[len(heads)]} sections' + (" and a pull quote." if quote else "."),
                       f"Create a readable article page layout for a blog post.{_style_phrase(t, rng)}"])
    return task, document(f"{topic} | Blog", css.render(), h, rng=rng)


@family("faq_page", "html", "pages")
def faq_page(rng: Random) -> tuple[str, str]:
    b = pick_business(rng)
    t = Theme(rng)
    h, css = Html(), Css()
    t.base(css, buttons=False)
    n = rng.choice([4, 5, 6])
    h.open("<main class=\"container\">")
    sec_faq(h, css, t, b, rng, n)
    h.close("</main>")
    task = rng.choice([f"Create an FAQ page with {n} questions using details and summary elements.",
                       f"Make a frequently asked questions page for a {b.kind} with collapsible answers.{_style_phrase(t, rng)}"])
    return task, document(f"FAQ | {b.name}", css.render(), h, rng=rng)


# ---------------------------------------------------------------------------
# Interactive apps (HTML + CSS + JavaScript)
# ---------------------------------------------------------------------------

def app_shell(t: Theme, css: Css, width: int = 420) -> None:
    t.base(css)
    css.rule(".app", "min-height: 100vh", "display: grid", "place-items: center", "padding: 24px")
    css.rule(".panel", "width: 100%", f"max-width: {width}px", "padding: 28px", f"background: {t.c('surface')}",
             f"border: 1px solid {t.c('border')}", f"border-radius: {t.radius}px", t.card_shadow())
    css.rule(".panel h1", "font-size: 1.5rem", "margin: 0 0 16px")


def _get(rng: Random, ident: str) -> str:
    return f'document.getElementById("{ident}")' if rng.random() < 0.5 else f'document.querySelector("#{ident}")'


@family("counter_app", "html", "apps")
def counter_app(rng: Random) -> tuple[str, str]:
    t = Theme(rng)
    step = rng.choice([1, 1, 1, 5, 10])
    floor = rng.random() < 0.4
    title = rng.choice(["Counter", "Click counter", "Tally counter"])
    h, css = Html(), Css()
    app_shell(t, css, 360)
    h.open('<main class="app">')
    h.open('<div class="panel counter">')
    h.add(f"<h1>{title}</h1>")
    h.add('<p id="count" class="count">0</p>')
    h.open('<div class="controls">')
    h.add(f'<button class="button" id="decrement" type="button">-{step}</button>')
    h.add(f'<button class="button" id="increment" type="button">+{step}</button>')
    h.close("</div>")
    h.add('<button class="reset" id="reset" type="button">Reset</button>')
    h.close("</div>")
    h.close("</main>")
    css.rule(".counter", "text-align: center")
    css.rule(".count", "font-size: 4rem", "font-weight: 700", "margin: 8px 0 24px", "font-variant-numeric: tabular-nums")
    css.rule(".controls", "display: flex", "gap: 12px", "justify-content: center")
    css.rule(".reset", "margin-top: 16px", "background: none", "border: none", f"color: {t.c('muted')}", "cursor: pointer", "text-decoration: underline")
    var = rng.choice(["count", "total", "value"])
    lo = f"Math.max(0, {var} - {step})" if floor else f"{var} - {step}"
    js = f"""const display = {_get(rng, "count")};
let {var} = 0;

function render() {{
  display.textContent = {var};
}}

{_get(rng, "increment")}.addEventListener("click", () => {{
  {var} += {step};
  render();
}});

{_get(rng, "decrement")}.addEventListener("click", () => {{
  {var} = {lo};
  render();
}});

{_get(rng, "reset")}.addEventListener("click", () => {{
  {var} = 0;
  render();
}});
"""
    task = rng.choice([f"Make a counter app with increment, decrement and reset buttons" + (f" that change the count by {step}" if step != 1 else "") + (". The count should never go below zero." if floor else "."),
                       f"Build a simple click counter in HTML, CSS and JavaScript.{_style_phrase(t, rng)}",
                       "counter with plus and minus buttons"])
    return task, document(title, css.render(), h, js, rng)


@family("todo_app", "html", "apps")
def todo_app(rng: Random) -> tuple[str, str]:
    t = Theme(rng)
    persist = rng.random() < 0.4
    show_count = rng.random() < 0.5
    title = rng.choice(["To-do list", "My tasks", "Todo", "Things to do"])
    h, css = Html(), Css()
    app_shell(t, css, 460)
    h.open('<main class="app">')
    h.open('<div class="panel">')
    h.add(f"<h1>{title}</h1>")
    h.open('<form id="todo-form" class="todo-form">')
    h.add('<input id="todo-input" type="text" placeholder="Add a task" autocomplete="off" required>')
    h.add('<button class="button" type="submit">Add</button>')
    h.close("</form>")
    h.add('<ul id="todo-list" class="todo-list"></ul>')
    if show_count:
        h.add('<p id="remaining" class="remaining"></p>')
    h.close("</div>")
    h.close("</main>")
    css.rule(".todo-form", "display: flex", "gap: 8px", "margin-bottom: 16px")
    css.rule(".todo-form input", "flex: 1", "padding: 10px 12px", "font: inherit", f"border: 1px solid {t.c('border')}",
             f"border-radius: {max(4, t.radius - 4)}px", f"background: {t.c('bg')}", f"color: {t.c('text')}")
    css.rule(".todo-list", "list-style: none", "margin: 0", "padding: 0")
    css.rule(".todo-list li", "display: flex", "align-items: center", "gap: 10px", "padding: 10px 0", f"border-bottom: 1px solid {t.c('border')}")
    css.rule(".todo-list li.done span", "text-decoration: line-through", f"color: {t.c('muted')}")
    css.rule(".todo-list span", "flex: 1")
    css.rule(".delete", "background: none", "border: none", f"color: {t.c('muted')}", "cursor: pointer", "font-size: 1.1rem")
    if show_count:
        css.rule(".remaining", f"color: {t.c('muted')}", "font-size: 0.9rem", "margin: 12px 0 0")
    load = 'JSON.parse(localStorage.getItem("todos") || "[]")' if persist else "[]"
    save = '\n  localStorage.setItem("todos", JSON.stringify(todos));' if persist else ""
    count = """
  const left = todos.filter((todo) => !todo.done).length;
  remaining.textContent = `${left} ${left === 1 ? "task" : "tasks"} left`;""" if show_count else ""
    js = f"""const form = {_get(rng, "todo-form")};
const input = {_get(rng, "todo-input")};
const list = {_get(rng, "todo-list")};
{'const remaining = ' + _get(rng, "remaining") + ';' + chr(10) if show_count else ''}let todos = {load};

function render() {{
  list.innerHTML = "";
  todos.forEach((todo, index) => {{
    const item = document.createElement("li");
    item.className = todo.done ? "done" : "";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = todo.done;
    checkbox.addEventListener("change", () => {{
      todo.done = checkbox.checked;
      render();
    }});

    const text = document.createElement("span");
    text.textContent = todo.text;

    const remove = document.createElement("button");
    remove.className = "delete";
    remove.textContent = "×";
    remove.setAttribute("aria-label", "Delete task");
    remove.addEventListener("click", () => {{
      todos.splice(index, 1);
      render();
    }});

    item.append(checkbox, text, remove);
    list.append(item);
  }});{count}{save}
}}

form.addEventListener("submit", (event) => {{
  event.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  todos.push({{ text, done: false }});
  input.value = "";
  render();
}});

render();
"""
    extras = [x for x, on in (("a count of remaining tasks", show_count), ("saving to localStorage", persist)) if on]
    task = rng.choice([f"Build a to-do list app where you can add, check off and delete tasks" + (f", with {join_parts(extras)}." if extras else "."),
                       f"Make a todo app in HTML, CSS and JavaScript.{_style_phrase(t, rng)}" + (" Save the tasks in localStorage." if persist else ""),
                       "todo list app" + (" that remembers tasks after a reload" if persist else "")])
    return task, document(title, css.render(), h, js, rng)


@family("tabs_app", "html", "apps")
def tabs_app(rng: Random) -> tuple[str, str]:
    t = Theme(rng)
    labels = rng.choice([["Overview", "Features", "Pricing"], ["Profile", "Settings", "Billing"], ["Day 1", "Day 2", "Day 3"],
                         ["HTML", "CSS", "JavaScript"], ["Description", "Reviews", "Shipping"]])
    h, css = Html(), Css()
    app_shell(t, css, 520)
    h.open('<main class="app">')
    h.open('<div class="panel">')
    h.open('<div class="tabs" role="tablist">')
    for i, label in enumerate(labels):
        selected = "true" if i == 0 else "false"
        h.add(f'<button class="tab" role="tab" aria-selected="{selected}" data-tab="{slug(label)}">{label}</button>')
    h.close("</div>")
    for i, label in enumerate(labels):
        hidden = "" if i == 0 else " hidden"
        h.open(f'<section class="tab-panel" id="{slug(label)}" role="tabpanel"{hidden}>')
        h.add(f"<h2>{label}</h2>")
        h.add(f"<p>This is the {label.lower()} panel. Put your {label.lower()} content here.</p>")
        h.close("</section>")
    h.close("</div>")
    h.close("</main>")
    css.rule(".tabs", "display: flex", "gap: 4px", f"border-bottom: 1px solid {t.c('border')}", "margin-bottom: 16px")
    css.rule(".tab", "padding: 10px 16px", "border: none", "background: none", f"color: {t.c('muted')}", "font: inherit",
             "cursor: pointer", "border-bottom: 2px solid transparent")
    css.rule('.tab[aria-selected="true"]', f"color: {t.c('text')}", f"border-bottom-color: {t.c('primary')}", "font-weight: 600")
    css.rule(".tab-panel h2", "margin-top: 0")
    js = """const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".tab-panel");

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((other) => other.setAttribute("aria-selected", "false"));
    panels.forEach((panel) => (panel.hidden = true));
    tab.setAttribute("aria-selected", "true");
    document.getElementById(tab.dataset.tab).hidden = false;
  });
});
"""
    task = rng.choice([f"Create tabs with JavaScript for {', '.join(labels[:2])} and {labels[2]}. Clicking a tab shows its panel.",
                       f"Make an accessible tabs component in HTML, CSS and JS.{_style_phrase(t, rng)}", "tabs component"])
    return task, document("Tabs", css.render(), h, js, rng)


@family("modal_app", "html", "apps")
def modal_app(rng: Random) -> tuple[str, str]:
    t = Theme(rng)
    title = rng.choice(["Subscribe to our newsletter", "Are you sure?", "Welcome!", "Special offer"])
    h, css = Html(), Css()
    t.base(css)
    h.open('<main class="page">')
    h.add('<button class="button" id="open-modal" type="button">Open modal</button>')
    h.close("</main>")
    h.open('<div class="overlay" id="overlay" hidden>')
    h.open('<div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title">')
    h.add(f'<h2 id="modal-title">{esc(title)}</h2>')
    h.add("<p>This dialog closes when you press Escape, click outside, or use the close button.</p>")
    h.add('<button class="button" id="close-modal" type="button">Close</button>')
    h.close("</div>")
    h.close("</div>")
    css.rule(".page", "min-height: 100vh", "display: grid", "place-items: center")
    css.rule(".overlay", "position: fixed", "inset: 0", "display: grid", "place-items: center", "padding: 24px",
             "background: rgba(0, 0, 0, 0.5)")
    css.rule(".overlay[hidden]", "display: none")
    css.rule(".modal", "width: 100%", "max-width: 420px", "padding: 28px", f"background: {t.c('surface')}",
             f"border-radius: {t.radius}px")
    css.rule(".modal h2", "margin-top: 0")
    js = f"""const overlay = {_get(rng, "overlay")};
const openButton = {_get(rng, "open-modal")};
const closeButton = {_get(rng, "close-modal")};

function openModal() {{
  overlay.hidden = false;
  closeButton.focus();
}}

function closeModal() {{
  overlay.hidden = true;
  openButton.focus();
}}

openButton.addEventListener("click", openModal);
closeButton.addEventListener("click", closeModal);

overlay.addEventListener("click", (event) => {{
  if (event.target === overlay) closeModal();
}});

document.addEventListener("keydown", (event) => {{
  if (event.key === "Escape" && !overlay.hidden) closeModal();
}});
"""
    task = rng.choice([f'Make a modal popup titled "{title}" that opens with a button and closes with Escape, a close button, or clicking outside.',
                       f"Create a modal dialog in HTML, CSS and JavaScript.{_style_phrase(t, rng)}", "popup modal with javascript"])
    return task, document("Modal", css.render(), h, js, rng)


@family("theme_toggle_app", "html", "apps")
def theme_toggle_app(rng: Random) -> tuple[str, str]:
    light = rng.choice([p for p in PALETTES if not p.dark])
    dark = rng.choice([p for p in PALETTES if p.dark])
    remember = rng.random() < 0.5
    h, css = Html(), Css()
    css.rule(":root", f"--bg: {light.bg}", f"--text: {light.text}", f"--surface: {light.surface}", f"--border: {light.border}")
    css.rule("body.dark", f"--bg: {dark.bg}", f"--text: {dark.text}", f"--surface: {dark.surface}", f"--border: {dark.border}")
    css.rule("body", "margin: 0", "min-height: 100vh", "display: grid", "place-items: center", "font-family: system-ui, sans-serif",
             "background: var(--bg)", "color: var(--text)", "transition: background 0.2s, color 0.2s")
    css.rule(".card", "padding: 32px", "border-radius: 12px", "background: var(--surface)", "border: 1px solid var(--border)", "text-align: center")
    css.rule("#theme-toggle", "padding: 10px 18px", "border-radius: 999px", "border: 1px solid var(--border)", "background: var(--bg)",
             "color: var(--text)", "font: inherit", "cursor: pointer")
    h.open('<main class="card">')
    h.add("<h1>Light and dark mode</h1>")
    h.add('<button id="theme-toggle" type="button">Switch to dark mode</button>')
    h.close("</main>")
    restore = """
if (localStorage.getItem("theme") === "dark") {
  document.body.classList.add("dark");
}
""" if remember else ""
    save = '\n  localStorage.setItem("theme", isDark ? "dark" : "light");' if remember else ""
    js = f"""const toggle = {_get(rng, "theme-toggle")};
{restore}
function updateLabel() {{
  const isDark = document.body.classList.contains("dark");
  toggle.textContent = isDark ? "Switch to light mode" : "Switch to dark mode";
}}

toggle.addEventListener("click", () => {{
  const isDark = document.body.classList.toggle("dark");{save}
  updateLabel();
}});

updateLabel();
"""
    task = rng.choice(["Add a dark mode toggle button to a page" + (" and remember the choice in localStorage." if remember else "."),
                       "Make a light/dark theme switcher with CSS variables and JavaScript.", "dark mode toggle"])
    return task, document("Theme toggle", css.render(), h, js, rng)


@family("char_counter_app", "html", "apps")
def char_counter_app(rng: Random) -> tuple[str, str]:
    t = Theme(rng)
    limit = rng.choice([140, 200, 280, 500])
    h, css = Html(), Css()
    app_shell(t, css, 520)
    h.open('<main class="app">')
    h.open('<div class="panel">')
    h.add('<label for="message"><h1>Write a message</h1></label>')
    h.add(f'<textarea id="message" rows="6" maxlength="{limit}" placeholder="Start typing..."></textarea>')
    h.add(f'<p id="counter" class="counter">0 / {limit}</p>')
    h.close("</div>")
    h.close("</main>")
    css.rule("textarea", "width: 100%", "padding: 12px", "font: inherit", f"border: 1px solid {t.c('border')}",
             f"border-radius: {max(4, t.radius - 4)}px", f"background: {t.c('bg')}", f"color: {t.c('text')}", "resize: vertical")
    css.rule(".counter", "text-align: right", f"color: {t.c('muted')}", "margin: 8px 0 0")
    css.rule(".counter.warning", "color: #d97706")
    css.rule(".counter.limit", "color: #dc2626", "font-weight: 600")
    warn = int(limit * 0.9)
    js = f"""const textarea = {_get(rng, "message")};
const counter = {_get(rng, "counter")};
const limit = {limit};

textarea.addEventListener("input", () => {{
  const length = textarea.value.length;
  counter.textContent = `${{length}} / ${{limit}}`;
  counter.classList.toggle("warning", length >= {warn} && length < limit);
  counter.classList.toggle("limit", length >= limit);
}});
"""
    task = rng.choice([f"Make a textarea with a live character counter that allows {limit} characters and changes color near the limit.",
                       f"Character counter for a text box ({limit} max) using JavaScript."])
    return task, document("Character counter", css.render(), h, js, rng)


@family("stopwatch_app", "html", "apps")
def stopwatch_app(rng: Random) -> tuple[str, str]:
    t = Theme(rng)
    h, css = Html(), Css()
    app_shell(t, css, 380)
    h.open('<main class="app">')
    h.open('<div class="panel stopwatch">')
    h.add("<h1>Stopwatch</h1>")
    h.add('<p id="time" class="time">00:00.0</p>')
    h.open('<div class="controls">')
    h.add('<button class="button" id="start" type="button">Start</button>')
    h.add('<button class="button" id="reset" type="button">Reset</button>')
    h.close("</div>")
    h.close("</div>")
    h.close("</main>")
    css.rule(".stopwatch", "text-align: center")
    css.rule(".time", "font-size: 3.5rem", "font-weight: 700", "font-variant-numeric: tabular-nums", "margin: 8px 0 24px")
    css.rule(".controls", "display: flex", "gap: 12px", "justify-content: center")
    js = f"""const display = {_get(rng, "time")};
const startButton = {_get(rng, "start")};
const resetButton = {_get(rng, "reset")};

let elapsed = 0;
let timer = null;

function format(ms) {{
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  const tenths = Math.floor((ms % 1000) / 100);
  return `${{String(minutes).padStart(2, "0")}}:${{String(seconds).padStart(2, "0")}}.${{tenths}}`;
}}

startButton.addEventListener("click", () => {{
  if (timer) {{
    clearInterval(timer);
    timer = null;
    startButton.textContent = "Start";
    return;
  }}
  const startedAt = Date.now() - elapsed;
  timer = setInterval(() => {{
    elapsed = Date.now() - startedAt;
    display.textContent = format(elapsed);
  }}, 100);
  startButton.textContent = "Stop";
}});

resetButton.addEventListener("click", () => {{
  clearInterval(timer);
  timer = null;
  elapsed = 0;
  display.textContent = format(0);
  startButton.textContent = "Start";
}});
"""
    task = rng.choice(["Build a stopwatch with start/stop and reset buttons that shows minutes, seconds and tenths.",
                       f"Make a stopwatch app in JavaScript.{_style_phrase(t, rng)}", "stopwatch"])
    return task, document("Stopwatch", css.render(), h, js, rng)


@family("tip_calculator_app", "html", "apps")
def tip_calculator_app(rng: Random) -> tuple[str, str]:
    t = Theme(rng)
    default_tip = rng.choice([15, 18, 20])
    h, css = Html(), Css()
    app_shell(t, css, 400)
    h.open('<main class="app">')
    h.open('<form class="panel calc" id="tip-form">')
    h.add("<h1>Tip calculator</h1>")
    for fid, label, val, step in [("bill", "Bill amount", "", "0.01"), ("tip", "Tip %", str(default_tip), "1"), ("people", "People", "1", "1")]:
        h.add(f'<label for="{fid}">{label}</label>')
        value = f' value="{val}"' if val else ""
        h.add(f'<input id="{fid}" type="number" min="{1 if fid == "people" else 0}" step="{step}"{value}>')
    h.add('<p class="result">Each person pays <strong id="per-person">$0.00</strong></p>')
    h.close("</form>")
    h.close("</main>")
    css.rule(".calc", "display: grid", "gap: 6px")
    css.rule(".calc input", "padding: 10px 12px", "font: inherit", f"border: 1px solid {t.c('border')}",
             f"border-radius: {max(4, t.radius - 4)}px", f"background: {t.c('bg')}", f"color: {t.c('text')}", "margin-bottom: 8px")
    css.rule(".result", "font-size: 1.1rem", "margin: 8px 0 0")
    js = f"""const form = {_get(rng, "tip-form")};
const output = {_get(rng, "per-person")};

function calculate() {{
  const bill = parseFloat(form.bill.value) || 0;
  const tip = parseFloat(form.tip.value) || 0;
  const people = Math.max(1, parseInt(form.people.value, 10) || 1);
  const total = bill * (1 + tip / 100);
  output.textContent = `$${{(total / people).toFixed(2)}}`;
}}

form.addEventListener("input", calculate);
calculate();
"""
    task = rng.choice([f"Create a tip calculator with bill amount, tip percentage (default {default_tip}%) and number of people that shows what each person pays.",
                       "Make a tip calculator web app with HTML, CSS and JavaScript.", "tip calculator"])
    return task, document("Tip calculator", css.render(), h, js, rng)


@family("temperature_converter_app", "html", "apps")
def temperature_converter_app(rng: Random) -> tuple[str, str]:
    t = Theme(rng)
    h, css = Html(), Css()
    app_shell(t, css, 400)
    h.open('<main class="app">')
    h.open('<div class="panel converter">')
    h.add("<h1>Temperature converter</h1>")
    h.add('<label for="celsius">Celsius</label>')
    h.add('<input id="celsius" type="number" step="any" value="0">')
    h.add('<label for="fahrenheit">Fahrenheit</label>')
    h.add('<input id="fahrenheit" type="number" step="any" value="32">')
    h.close("</div>")
    h.close("</main>")
    css.rule(".converter", "display: grid", "gap: 6px")
    css.rule(".converter input", "padding: 10px 12px", "font: inherit", "font-size: 1.25rem", f"border: 1px solid {t.c('border')}",
             f"border-radius: {max(4, t.radius - 4)}px", f"background: {t.c('bg')}", f"color: {t.c('text')}", "margin-bottom: 10px")
    js = f"""const celsius = {_get(rng, "celsius")};
const fahrenheit = {_get(rng, "fahrenheit")};

function round(value) {{
  return Math.round(value * 10) / 10;
}}

celsius.addEventListener("input", () => {{
  if (celsius.value === "") return;
  fahrenheit.value = round(parseFloat(celsius.value) * 9 / 5 + 32);
}});

fahrenheit.addEventListener("input", () => {{
  if (fahrenheit.value === "") return;
  celsius.value = round((parseFloat(fahrenheit.value) - 32) * 5 / 9);
}});
"""
    task = rng.choice(["Make a Celsius to Fahrenheit converter that updates both fields as you type.",
                       "Temperature converter web page with JavaScript."])
    return task, document("Temperature converter", css.render(), h, js, rng)


@family("quiz_app", "html", "apps")
def quiz_app(rng: Random) -> tuple[str, str]:
    t = Theme(rng)
    topic = rng.choice(list(QUIZ_TOPICS))
    questions = QUIZ_TOPICS[topic]
    h, css = Html(), Css()
    app_shell(t, css, 520)
    h.open('<main class="app">')
    h.open('<div class="panel quiz">')
    h.add(f"<h1>{topic.capitalize()} quiz</h1>")
    h.add('<p id="question" class="question"></p>')
    h.add('<div id="answers" class="answers"></div>')
    h.add('<p id="score" class="score"></p>')
    h.close("</div>")
    h.close("</main>")
    css.rule(".question", "font-size: 1.2rem", "font-weight: 600")
    css.rule(".answers", "display: grid", "gap: 8px")
    css.rule(".answers button", "padding: 12px", "font: inherit", "text-align: left", f"border: 1px solid {t.c('border')}",
             f"border-radius: {max(4, t.radius - 4)}px", f"background: {t.c('bg')}", f"color: {t.c('text')}", "cursor: pointer")
    css.rule(".answers button:hover", f"border-color: {t.c('primary')}")
    css.rule(".score", f"color: {t.c('muted')}")
    items = ",\n".join(
        "  {\n" + f"    text: {json_str(q)},\n    options: [{', '.join(json_str(o) for o in opts)}],\n    answer: {ans},\n" + "  }"
        for q, opts, ans in questions)
    js = f"""const questions = [
{items},
];

const questionEl = {_get(rng, "question")};
const answersEl = {_get(rng, "answers")};
const scoreEl = {_get(rng, "score")};
let current = 0;
let score = 0;

function showQuestion() {{
  const item = questions[current];
  questionEl.textContent = item.text;
  answersEl.innerHTML = "";
  item.options.forEach((option, index) => {{
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = option;
    button.addEventListener("click", () => choose(index));
    answersEl.append(button);
  }});
  scoreEl.textContent = `Question ${{current + 1}} of ${{questions.length}}`;
}}

function choose(index) {{
  if (index === questions[current].answer) score++;
  current++;
  if (current < questions.length) {{
    showQuestion();
  }} else {{
    questionEl.textContent = "Quiz complete!";
    answersEl.innerHTML = "";
    scoreEl.textContent = `You scored ${{score}} out of ${{questions.length}}.`;
  }}
}}

showQuestion();
"""
    task = rng.choice([f"Make a multiple choice {topic} quiz with {NUM_WORDS[len(questions)]} questions that shows the score at the end.",
                       f"Build a quiz app in JavaScript about {topic}."])
    return task, document(f"{topic.capitalize()} quiz", css.render(), h, js, rng)


def json_str(text: str) -> str:
    import json
    return json.dumps(text)


@family("quote_generator_app", "html", "apps")
def quote_generator_app(rng: Random) -> tuple[str, str]:
    t = Theme(rng)
    quotes = rng.sample(QUOTES, 4)
    h, css = Html(), Css()
    app_shell(t, css, 520)
    h.open('<main class="app">')
    h.open('<figure class="panel quote-box">')
    h.add('<blockquote id="quote"></blockquote>')
    h.add('<figcaption id="author"></figcaption>')
    h.add('<button class="button" id="new-quote" type="button">New quote</button>')
    h.close("</figure>")
    h.close("</main>")
    css.rule(".quote-box", "margin: 0", "text-align: center")
    css.rule("#quote", "font-size: 1.4rem", "margin: 0 0 12px")
    css.rule("#author", f"color: {t.c('muted')}", "margin-bottom: 24px")
    items = ",\n".join(f"  {{ text: {json_str(q)}, author: {json_str(a)} }}" for q, a in quotes)
    js = f"""const quotes = [
{items},
];

const quoteEl = {_get(rng, "quote")};
const authorEl = {_get(rng, "author")};
let last = -1;

function showRandomQuote() {{
  let index = Math.floor(Math.random() * quotes.length);
  if (index === last) index = (index + 1) % quotes.length;
  last = index;
  quoteEl.textContent = `"${{quotes[index].text}}"`;
  authorEl.textContent = `— ${{quotes[index].author}}`;
}}

{_get(rng, "new-quote")}.addEventListener("click", showRandomQuote);
showRandomQuote();
"""
    task = rng.choice(["Make a random quote generator with a button that shows a new quote and its author.",
                       "Random quote web app using JavaScript."])
    return task, document("Quote generator", css.render(), h, js, rng)


@family("search_filter_app", "html", "apps")
def search_filter_app(rng: Random) -> tuple[str, str]:
    t = Theme(rng)
    things, items = rng.choice([("fruits", ["Apple", "Banana", "Cherry", "Mango", "Orange", "Peach", "Pear", "Plum"]),
                                ("cities", ["Austin", "Boston", "Chicago", "Denver", "Miami", "Seattle", "Toronto", "Dublin"]),
                                ("languages", ["Python", "JavaScript", "Rust", "Go", "Ruby", "Swift", "Kotlin", "TypeScript"]),
                                ("animals", ["Cat", "Dog", "Horse", "Otter", "Panda", "Rabbit", "Tiger", "Whale"])])
    h, css = Html(), Css()
    app_shell(t, css, 420)
    h.open('<main class="app">')
    h.open('<div class="panel">')
    h.add(f"<h1>Search {things}</h1>")
    h.add(f'<input id="search" type="search" placeholder="Type to filter..." aria-label="Search {things}">')
    h.open('<ul id="items" class="items">')
    for item in items:
        h.add(f"<li>{item}</li>")
    h.close("</ul>")
    h.add('<p id="empty" class="empty" hidden>No matches.</p>')
    h.close("</div>")
    h.close("</main>")
    css.rule("#search", "width: 100%", "padding: 10px 12px", "font: inherit", f"border: 1px solid {t.c('border')}",
             f"border-radius: {max(4, t.radius - 4)}px", f"background: {t.c('bg')}", f"color: {t.c('text')}")
    css.rule(".items", "list-style: none", "padding: 0", "margin: 12px 0 0")
    css.rule(".items li", "padding: 8px 0", f"border-bottom: 1px solid {t.c('border')}")
    css.rule(".empty", f"color: {t.c('muted')}")
    js = f"""const search = {_get(rng, "search")};
const items = document.querySelectorAll("#items li");
const empty = {_get(rng, "empty")};

search.addEventListener("input", () => {{
  const query = search.value.trim().toLowerCase();
  let visible = 0;
  items.forEach((item) => {{
    const match = item.textContent.toLowerCase().includes(query);
    item.hidden = !match;
    if (match) visible++;
  }});
  empty.hidden = visible > 0;
}});
"""
    task = rng.choice([f"Make a list of {things} with a search box that filters the list as you type and shows a message when nothing matches.",
                       f"Live search filter for a list of {things} in JavaScript."])
    return task, document(f"Search {things}", css.render(), h, js, rng)


@family("color_generator_app", "html", "apps")
def color_generator_app(rng: Random) -> tuple[str, str]:
    h, css = Html(), Css()
    css.rule("body", "margin: 0", "min-height: 100vh", "display: grid", "place-items: center", "font-family: system-ui, sans-serif",
             "background: #1f2937", "transition: background 0.3s")
    css.rule(".panel", "padding: 32px", "border-radius: 16px", "background: rgba(255, 255, 255, 0.92)", "text-align: center")
    css.rule("#hex", "font-family: ui-monospace, monospace", "font-size: 2rem", "margin: 0 0 16px")
    css.rule("button", "padding: 10px 18px", "border-radius: 8px", "border: none", "background: #111827", "color: #ffffff",
             "font: inherit", "cursor: pointer", "margin: 0 4px")
    copy = rng.random() < 0.5
    h.open('<main class="panel">')
    h.add('<p id="hex">#1F2937</p>')
    h.add('<button id="generate" type="button">New color</button>')
    if copy:
        h.add('<button id="copy" type="button">Copy</button>')
    h.close("</main>")
    copy_js = f"""
{_get(rng, "copy")}.addEventListener("click", async () => {{
  await navigator.clipboard.writeText(hex.textContent);
}});
""" if copy else ""
    js = f"""const hex = {_get(rng, "hex")};

function randomColor() {{
  const value = Math.floor(Math.random() * 0xffffff);
  return `#${{value.toString(16).padStart(6, "0").toUpperCase()}}`;
}}

{_get(rng, "generate")}.addEventListener("click", () => {{
  const color = randomColor();
  document.body.style.background = color;
  hex.textContent = color;
}});
{copy_js}"""
    task = rng.choice(["Build a random color generator that changes the background and shows the hex code" + (", with a copy button." if copy else "."),
                       "random background color button in javascript"])
    return task, document("Color generator", css.render(), h, js, rng)


@family("form_validation_app", "html", "apps")
def form_validation_app(rng: Random) -> tuple[str, str]:
    t = Theme(rng)
    min_len = rng.choice([6, 8, 10])
    h, css = Html(), Css()
    app_shell(t, css, 420)
    h.open('<main class="app">')
    h.open('<form class="panel signup" id="signup" novalidate>')
    h.add("<h1>Create account</h1>")
    for fid, label, typ in [("name", "Name", "text"), ("email", "Email", "email"), ("password", "Password", "password")]:
        h.add(f'<label for="{fid}">{label}</label>')
        h.add(f'<input id="{fid}" name="{fid}" type="{typ}">')
        h.add(f'<p class="error" id="{fid}-error"></p>')
    h.add('<button class="button" type="submit">Sign up</button>')
    h.add('<p class="success" id="success" hidden>Thanks! Your account was created.</p>')
    h.close("</form>")
    h.close("</main>")
    css.rule(".signup", "display: grid", "gap: 4px")
    css.rule(".signup input", "padding: 10px 12px", "font: inherit", f"border: 1px solid {t.c('border')}",
             f"border-radius: {max(4, t.radius - 4)}px", f"background: {t.c('bg')}", f"color: {t.c('text')}")
    css.rule(".signup input.invalid", "border-color: #dc2626")
    css.rule(".error", "min-height: 1.2em", "margin: 0 0 6px", "font-size: 0.85rem", "color: #dc2626")
    css.rule(".success", "color: #16a34a", "font-weight: 600")
    js = f"""const form = {_get(rng, "signup")};
const success = {_get(rng, "success")};

const rules = {{
  name: (value) => (value.trim() ? "" : "Please enter your name."),
  email: (value) => (/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(value) ? "" : "Please enter a valid email."),
  password: (value) => (value.length >= {min_len} ? "" : "Password must be at least {min_len} characters."),
}};

form.addEventListener("submit", (event) => {{
  event.preventDefault();
  let valid = true;
  for (const [field, check] of Object.entries(rules)) {{
    const input = form.elements[field];
    const message = check(input.value);
    document.getElementById(`${{field}}-error`).textContent = message;
    input.classList.toggle("invalid", Boolean(message));
    if (message) valid = false;
  }}
  success.hidden = !valid;
  if (valid) form.reset();
}});
"""
    task = rng.choice([f"Create a sign up form with JavaScript validation: name is required, email must be valid, password needs at least {min_len} characters. Show an error under each field.",
                       "Form validation example in HTML, CSS and JavaScript."])
    return task, document("Form validation", css.render(), h, js, rng)


@family("dice_app", "html", "apps")
def dice_app(rng: Random) -> tuple[str, str]:
    t = Theme(rng)
    dice = rng.choice([1, 2])
    h, css = Html(), Css()
    app_shell(t, css, 360)
    h.open('<main class="app">')
    h.open('<div class="panel dice">')
    h.add("<h1>Dice roller</h1>")
    h.open('<div class="faces">')
    for i in range(dice):
        h.add(f'<span class="die" id="die-{i + 1}">1</span>')
    h.close("</div>")
    h.add('<p id="total" class="total"></p>' if dice > 1 else "")
    h.add('<button class="button" id="roll" type="button">Roll</button>')
    h.close("</div>")
    h.close("</main>")
    h.lines = [line for line in h.lines if line.strip()]
    css.rule(".dice", "text-align: center")
    css.rule(".faces", "display: flex", "gap: 16px", "justify-content: center", "margin-bottom: 16px")
    css.rule(".die", "width: 72px", "height: 72px", "display: grid", "place-items: center", "font-size: 2rem", "font-weight: 700",
             f"border: 2px solid {t.c('text')}", "border-radius: 12px")
    total = '\n  document.getElementById("total").textContent = `Total: ${total}`;' if dice > 1 else ""
    js = f"""const dice = document.querySelectorAll(".die");

function rollDie() {{
  return Math.floor(Math.random() * 6) + 1;
}}

{_get(rng, "roll")}.addEventListener("click", () => {{
  let total = 0;
  dice.forEach((die) => {{
    const value = rollDie();
    die.textContent = value;
    total += value;
  }});{total}
}});
"""
    task = rng.choice([f"Make a dice roller with {'two dice and a total' if dice > 1 else 'one die'} and a roll button.", "dice roller app"])
    return task, document("Dice roller", css.render(), h, js, rng)


# ---------------------------------------------------------------------------
# CSS components
# ---------------------------------------------------------------------------

def css_theme(rng: Random) -> Palette:
    return rng.choice([p for p in PALETTES])


@family("css_buttons", "css", "components")
def css_buttons(rng: Random) -> tuple[str, str]:
    p = css_theme(rng)
    radius = rng.choice([4, 6, 8, 999])
    cls = rng.choice(["btn", "button"])
    css = Css()
    css.rule(f".{cls}", "display: inline-flex", "align-items: center", "justify-content: center", "gap: 8px", "padding: 10px 20px",
             "font: inherit", "font-weight: 600", f"border-radius: {radius}px", "border: 1px solid transparent", "cursor: pointer",
             "transition: background 0.15s, transform 0.15s")
    css.rule(f".{cls}-primary", f"background: {p.primary}", f"color: {p.on_primary}")
    css.rule(f".{cls}-primary:hover", "filter: brightness(1.1)")
    css.rule(f".{cls}-secondary", "background: transparent", f"color: {p.text}", f"border-color: {p.border}")
    css.rule(f".{cls}-secondary:hover", f"background: {p.surface}")
    css.rule(f".{cls}:active", "transform: translateY(1px)")
    css.rule(f".{cls}:focus-visible", f"outline: 3px solid {p.accent}", "outline-offset: 2px")
    css.rule(f".{cls}:disabled", "opacity: 0.5", "cursor: not-allowed")
    task = rng.choice([f"Write CSS for .{cls}-primary and .{cls}-secondary buttons with hover, active, focus and disabled states.",
                       f"Style a set of buttons in CSS ({'pill shaped' if radius == 999 else f'{radius}px corners'}) using {p.desc}."])
    return task, css.render()


@family("css_card", "css", "components")
def css_card(rng: Random) -> tuple[str, str]:
    p = css_theme(rng)
    radius = rng.choice([8, 12, 16])
    lift = rng.random() < 0.6
    css = Css()
    css.rule(".card", f"background: {p.surface}", f"border: 1px solid {p.border}", f"border-radius: {radius}px", "padding: 24px",
             "box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08)", "transition: transform 0.2s, box-shadow 0.2s" if lift else "")
    if lift:
        css.rule(".card:hover", "transform: translateY(-4px)", "box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12)")
    css.rule(".card-title", "margin: 0 0 8px", "font-size: 1.25rem", f"color: {p.text}")
    css.rule(".card-text", "margin: 0", f"color: {p.muted}", "line-height: 1.6")
    task = rng.choice([f"Write CSS for a .card with {radius}px rounded corners, a soft shadow and 24px padding" + (", lifting slightly on hover." if lift else "."),
                       "card component styles in CSS"])
    return task, css.render()


@family("css_navbar", "css", "components")
def css_navbar(rng: Random) -> tuple[str, str]:
    p = css_theme(rng)
    sticky = rng.random() < 0.5
    css = Css()
    css.rule(".navbar", "display: flex", "align-items: center", "justify-content: space-between", "padding: 16px 24px",
             f"background: {p.surface}", f"border-bottom: 1px solid {p.border}", "position: sticky" if sticky else "", "top: 0" if sticky else "",
             "z-index: 10" if sticky else "")
    css.rule(".navbar .brand", "font-weight: 700", f"color: {p.text}", "text-decoration: none")
    css.rule(".navbar ul", "display: flex", "gap: 20px", "list-style: none", "margin: 0", "padding: 0")
    css.rule(".navbar a", f"color: {p.muted}", "text-decoration: none")
    css.rule(".navbar a:hover, .navbar a.active", f"color: {p.primary}")
    css.media("@media (max-width: 600px)", [(".navbar ul", ["display: none"])])
    task = rng.choice([f"Style a .navbar with a brand on the left and links on the right" + (", sticky at the top" if sticky else "") + ", hiding the links on small screens.",
                       "responsive navbar css"])
    return task, css.render()


@family("css_center", "css", "layout")
def css_center(rng: Random) -> tuple[str, str]:
    method = rng.choice(["flex", "grid"])
    css = Css()
    css.rule("html, body", "height: 100%", "margin: 0")
    if method == "flex":
        css.rule(".center", "min-height: 100vh", "display: flex", "align-items: center", "justify-content: center")
    else:
        css.rule(".center", "min-height: 100vh", "display: grid", "place-items: center")
    css.rule(".center > .box", "padding: 32px", "border-radius: 12px", "background: #ffffff", "box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1)")
    task = rng.choice([f"How do I center a div horizontally and vertically with CSS {method}?", f"Center a .box in the middle of the page using {method}."])
    return task, css.render()


@family("css_grid_layout", "css", "layout")
def css_grid_layout(rng: Random) -> tuple[str, str]:
    cols = rng.choice([2, 3, 4])
    gap = rng.choice([16, 20, 24])
    css = Css()
    css.rule(".grid", "display: grid", f"grid-template-columns: repeat({cols}, 1fr)", f"gap: {gap}px")
    css.media("@media (max-width: 900px)", [(".grid", ["grid-template-columns: repeat(2, 1fr)"])])
    css.media("@media (max-width: 560px)", [(".grid", ["grid-template-columns: 1fr"])])
    task = rng.choice([f"Make a responsive CSS grid with {cols} columns on desktop, 2 on tablets and 1 on phones with a {gap}px gap.",
                       f"responsive {cols} column grid css"])
    return task, css.render()


@family("css_alerts", "css", "components")
def css_alerts(rng: Random) -> tuple[str, str]:
    css = Css()
    css.rule(".alert", "padding: 12px 16px", "border-radius: 8px", "border: 1px solid transparent", "margin-bottom: 12px")
    for name, bg, fg, border in [("success", "#ecfdf3", "#166534", "#bbf7d0"), ("warning", "#fffbeb", "#92400e", "#fde68a"),
                                 ("error", "#fef2f2", "#991b1b", "#fecaca"), ("info", "#eff6ff", "#1e40af", "#bfdbfe")]:
        css.rule(f".alert-{name}", f"background: {bg}", f"color: {fg}", f"border-color: {border}")
    task = rng.choice(["Write CSS for alert boxes: .alert-success, .alert-warning, .alert-error and .alert-info.", "alert message styles in css"])
    return task, css.render()


@family("css_spinner", "css", "animation")
def css_spinner(rng: Random) -> tuple[str, str]:
    size = rng.choice([24, 32, 40, 48])
    color = rng.choice(["#2563eb", "#16a34a", "#f97316", "#e11d48", "#0d9488"])
    speed = rng.choice([0.6, 0.8, 1])
    css = Css()
    css.rule(".spinner", f"width: {size}px", f"height: {size}px", "border: 4px solid rgba(0, 0, 0, 0.1)", f"border-top-color: {color}",
             "border-radius: 50%", f"animation: spin {speed}s linear infinite")
    css.raw("@keyframes spin {\n  to {\n    transform: rotate(360deg);\n  }\n}")
    task = rng.choice([f"Create a {size}px CSS loading spinner using @keyframes.", "css loading spinner animation"])
    return task, css.render()


@family("css_form", "css", "components")
def css_form(rng: Random) -> tuple[str, str]:
    p = css_theme(rng)
    css = Css()
    css.rule(".form", "display: grid", "gap: 16px", "max-width: 420px")
    css.rule(".form label", "display: grid", "gap: 6px", "font-weight: 600", f"color: {p.text}")
    css.rule(".form input, .form textarea, .form select", "padding: 10px 12px", "font: inherit", f"color: {p.text}", f"background: {p.surface}",
             f"border: 1px solid {p.border}", "border-radius: 8px")
    css.rule(".form input:focus, .form textarea:focus, .form select:focus", f"outline: none", f"border-color: {p.primary}",
             "box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2)")
    css.rule(".form button", "justify-self: start", "padding: 10px 20px", "border: none", "border-radius: 8px", f"background: {p.primary}",
             f"color: {p.on_primary}", "font: inherit", "font-weight: 600", "cursor: pointer")
    task = rng.choice(["Style a .form with labeled inputs, a textarea, a select and a submit button, with a clear focus state.", "nice form input styles css"])
    return task, css.render()


@family("css_table", "css", "components")
def css_table(rng: Random) -> tuple[str, str]:
    p = css_theme(rng)
    striped = rng.random() < 0.6
    css = Css()
    css.rule(".table", "width: 100%", "border-collapse: collapse", "font-size: 0.95rem")
    css.rule(".table th, .table td", "padding: 12px 16px", "text-align: left", f"border-bottom: 1px solid {p.border}")
    css.rule(".table th", f"background: {p.surface}", "font-weight: 600")
    if striped:
        css.rule(".table tbody tr:nth-child(even)", "background: rgba(0, 0, 0, 0.03)")
    css.rule(".table tbody tr:hover", "background: rgba(0, 0, 0, 0.06)")
    task = rng.choice(["Style an HTML .table with padding, borders" + (", striped rows" if striped else "") + " and a row hover color.", "table styles css"])
    return task, css.render()


@family("css_toggle_switch", "css", "components")
def css_toggle_switch(rng: Random) -> tuple[str, str]:
    color = rng.choice(["#22c55e", "#2563eb", "#f97316", "#e11d48"])
    css = Css()
    css.rule(".switch", "position: relative", "display: inline-block", "width: 52px", "height: 30px")
    css.rule(".switch input", "opacity: 0", "width: 0", "height: 0")
    css.rule(".slider", "position: absolute", "inset: 0", "background: #cbd5e1", "border-radius: 999px", "cursor: pointer", "transition: background 0.2s")
    css.rule(".slider::before", 'content: ""', "position: absolute", "width: 24px", "height: 24px", "left: 3px", "top: 3px",
             "background: #ffffff", "border-radius: 50%", "transition: transform 0.2s")
    css.rule(".switch input:checked + .slider", f"background: {color}")
    css.rule(".switch input:checked + .slider::before", "transform: translateX(22px)")
    css.rule(".switch input:focus-visible + .slider", f"outline: 2px solid {color}", "outline-offset: 2px")
    task = rng.choice(["Make an iOS style toggle switch with only CSS using a checkbox.", "css toggle switch"])
    return task, css.render()


@family("css_dark_theme", "css", "theming")
def css_dark_theme(rng: Random) -> tuple[str, str]:
    light = rng.choice([p for p in PALETTES if not p.dark])
    dark = rng.choice([p for p in PALETTES if p.dark])
    css = Css()
    css.rule(":root", f"--bg: {light.bg}", f"--text: {light.text}", f"--muted: {light.muted}", f"--primary: {light.primary}", f"--border: {light.border}")
    css.media("@media (prefers-color-scheme: dark)", [(":root", [f"--bg: {dark.bg}", f"--text: {dark.text}", f"--muted: {dark.muted}",
                                                                   f"--primary: {dark.primary}", f"--border: {dark.border}"])])
    css.rule("body", "margin: 0", "background: var(--bg)", "color: var(--text)", "font-family: system-ui, sans-serif")
    css.rule("a", "color: var(--primary)")
    css.rule("hr", "border: none", "border-top: 1px solid var(--border)")
    task = rng.choice(["Set up CSS variables for light and dark mode that follow the system preference.", "dark mode css variables"])
    return task, css.render()


@family("css_progress", "css", "components")
def css_progress(rng: Random) -> tuple[str, str]:
    color = rng.choice(["#2563eb", "#16a34a", "#f97316", "#7c3aed"])
    css = Css()
    css.rule(".progress", "height: 10px", "background: #e5e7eb", "border-radius: 999px", "overflow: hidden")
    css.rule(".progress-bar", "height: 100%", f"background: {color}", "border-radius: inherit", "transition: width 0.3s ease")
    task = rng.choice(["CSS for a rounded .progress bar whose .progress-bar width shows the progress.", "progress bar css"])
    return task, css.render()


@family("css_badges", "css", "components")
def css_badges(rng: Random) -> tuple[str, str]:
    css = Css()
    css.rule(".badge", "display: inline-block", "padding: 2px 10px", "border-radius: 999px", "font-size: 0.75rem", "font-weight: 600", "line-height: 1.6")
    for name, bg, fg in [("gray", "#f3f4f6", "#374151"), ("green", "#dcfce7", "#166534"), ("blue", "#dbeafe", "#1e40af"), ("red", "#fee2e2", "#991b1b")]:
        css.rule(f".badge-{name}", f"background: {bg}", f"color: {fg}")
    task = rng.choice(["Write CSS for small pill badges in gray, green, blue and red.", "badge styles css"])
    return task, css.render()


@family("css_hero", "css", "layout")
def css_hero(rng: Random) -> tuple[str, str]:
    p = css_theme(rng)
    css = Css()
    css.rule(".hero", "min-height: 70vh", "display: grid", "place-items: center", "text-align: center", "padding: 64px 24px",
             f"background: linear-gradient(135deg, {p.primary}, {p.accent})", f"color: {p.on_primary}")
    css.rule(".hero h1", "font-size: clamp(2.5rem, 6vw, 4rem)", "margin: 0 0 16px", "line-height: 1.1")
    css.rule(".hero p", "font-size: 1.2rem", "max-width: 36rem", "margin: 0 auto 24px", "opacity: 0.9")
    task = rng.choice(["Style a full-width .hero section with a gradient background, a large responsive heading and centered text.", "hero section css"])
    return task, css.render()
