# Visual style system

Keywords: style, styles, styling, portfolio, design, website, CSS

- Before writing components, define CSS variables for page background, surface, text, muted text, border, accent, and spacing. Use them throughout the page.
- Design hierarchy with a deliberate font scale, line height, measure, and spacing rhythm. Body text should be about 15–18px; headings should have distinct levels without becoming oversized.
- Use a centered max-width container and align the header, hero, sections, and footer to the same edges. Give primary sections breathing room.
- Style every visible state: links, buttons, navigation, hover, `:focus-visible`, and narrow screens. Default blue underlined links indicate unfinished styling unless that is the intended design.
- Use grids for repeated project or feature items and stack them at a mobile breakpoint. Avoid horizontal overflow and tiny tap targets.
- Avoid the generic AI template look: no gradient text, oversized rounded cards, repeated meaningless badges, or decorative UI without a purpose.
- Ensure the final HTML embeds substantial CSS in `<style>`. Never refer to a local stylesheet that was not created.
