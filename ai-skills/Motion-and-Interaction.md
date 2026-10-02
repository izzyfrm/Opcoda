# Motion and interaction

Keywords: animation, animations, transition, transitions, interactive, JavaScript, JS, portfolio, website

- Give motion a job: reveal the page structure, confirm a hover or focus action, or open a menu. Keep common transitions around 150–300ms.
- For entry animations, start content visible by default. Add a JavaScript-enabled class only after setup succeeds, then reveal with `IntersectionObserver`; pages must still be usable without JavaScript.
- Respect `@media (prefers-reduced-motion: reduce)` and `matchMedia('(prefers-reduced-motion: reduce)')`. Disable movement while preserving visibility.
- Animate opacity and transform for smooth performance. Avoid continuous movement, flashing, scroll hijacking, or long delays before content appears.
- If the user explicitly asks for JavaScript, include a small working behavior tied to real elements. A script containing only comments or no-op handlers does not meet the request.
- Mobile navigation buttons need an accessible name, `aria-expanded`, a real target, and working open/close behavior.
