# Background design

Keywords: background, backgrounds, dark, black, portfolio, landing page, website

- A requested background must visibly cover the entire viewport. Set `body { min-height: 100vh; background: var(--page-bg); color: var(--text); }`, and give `html` a matching background to avoid white overscroll.
- For an all-black style, use a near-black base such as `#090a0b`, a slightly lighter surface such as `#111316`, restrained borders such as `#2a2c30`, and off-white text. Do not put black text on a black surface.
- Add visual depth through a subtle tonal shift, hairline grid, fine divider, or controlled highlight only when it supports the content. Do not default to purple gradients, blobs, or glass panels.
- If the request asks for an image background, include the image only if a working asset is available in the output. The preview has no network access. Otherwise use CSS shapes, gradients, or textures that work offline.
- Keep text readable over a visual background. Use an opaque or near-opaque backing where needed and check contrast on mobile.
- Apply background treatments consistently to header, hero, content, and footer; avoid one unstyled white section breaking the theme.
