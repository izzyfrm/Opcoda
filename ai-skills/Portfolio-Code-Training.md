# Portfolio code example and quality bar

Keywords: portfolio, personal website, software engineer, developer, HTML, CSS, JavaScript

Use this as a pattern, adapting names, links, theme, and sections to the request. Do not copy placeholder text into the result.

## Structure

```html
<header class="site-header"><div class="container"><a class="brand" href="#top">Person Name</a><nav aria-label="Main navigation"><a href="#projects">Projects</a><a href="#contact">Contact</a></nav></div></header>
<main id="top"><section class="hero container" aria-labelledby="hero-title"><p class="eyebrow">Software Engineer</p><h1 id="hero-title">Person Name</h1><p class="intro">A concise, factual introduction when provided.</p><a class="text-link" href="#projects">Explore projects</a></section><section id="projects" class="container" aria-labelledby="projects-title"><h2 id="projects-title">Selected work</h2><div class="project-grid"><article class="project"><h3>Actual project name</h3><a href="https://example.com" target="_blank" rel="noopener noreferrer">View project <span aria-hidden="true">↗</span></a></article></div></section></main>
```

## CSS pattern

Define `:root` colors and spacing. Set `box-sizing: border-box`. Give `body` a deliberate background, text color, font, and line height. Use `.container { width: min(1100px, calc(100% - 40px)); margin-inline: auto; }`. Use `clamp()` for the hero heading, grid/flex for projects, a real mobile breakpoint, visible `:focus-visible`, and a reduced-motion media query. Do not link to a stylesheet that does not exist. The app will extract inline `<style>` into `css/styles.css`.

## JavaScript pattern

Only add JavaScript when it adds working behavior. For requested animations, use `IntersectionObserver` for progressive enhancement, and ensure all content remains visible without JavaScript. Honor `matchMedia('(prefers-reduced-motion: reduce)')`. Avoid dead buttons and animation loops. The app will extract inline `<script>` into `js/script.js`.

## Completion checks

Return a complete `<!doctype html>` document with `<html>`, `<head>`, `<body>`, and closing tags. Include meaningful CSS and requested JS. Keep every supplied link exact. Do not invent project descriptions or contact information. Check that the preview works without network access and that the mobile layout has no horizontal overflow.
