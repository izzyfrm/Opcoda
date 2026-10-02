"""Turn standalone websites into portable projects without discarding their assets."""
import re


def website_project(html: str) -> list[dict[str, str]]:
    files = []
    styles = []
    scripts = []

    def style(match):
        styles.append(match.group(1))
        return '<link rel="stylesheet" href="css/styles.css">' if len(styles) == 1 else ''

    def script(match):
        attrs, content = match.groups()
        # Preserve module/JSON scripts; combining these changes execution semantics.
        if re.search(r'\b(src|type)\s*=', attrs, re.I):
            return match.group(0)
        scripts.append(content)
        return ''

    document = re.sub(r'<style\b[^>]*>(.*?)</style\s*>', style, html, flags=re.I | re.S)
    document = re.sub(r'<script\b([^>]*)>(.*?)</script\s*>', script, document, flags=re.I | re.S)
    if scripts:
        tag = '<script src="js/script.js"></script>'
        document = re.sub(r'</body\s*>', lambda m: tag + '\n' + m.group(0), document, count=1, flags=re.I) if re.search(r'</body\s*>', document, re.I) else document + tag
    files.append({'path': 'index.html', 'content': document, 'lang': 'html'})
    if styles:
        files.append({'path': 'css/styles.css', 'content': '\n'.join(styles).strip() + '\n', 'lang': 'css'})
    if scripts:
        files.append({'path': 'js/script.js', 'content': '\n;\n'.join(scripts).strip() + '\n', 'lang': 'javascript'})
    files.append({'path': 'README.md', 'content': '# Generated website\n\nExtract the ZIP, then open index.html in your browser. Keep css/ and js/ next to index.html when present.\n\nReview generated code before publishing. No package installation is required.\n', 'lang': 'text'})
    return files


def missing_assets(html: str) -> list[str]:
    """Standalone output may not depend on ungenerated local styles/scripts/images."""
    refs = re.findall(r'<(?:link|script|img)\b[^>]*?\b(?:src|href)\s*=\s*[\"\']([^\"\']+)', html, re.I)
    return [ref for ref in refs if not re.match(r'^(?:data:|https?:|//|#|blob:)', ref, re.I)]
