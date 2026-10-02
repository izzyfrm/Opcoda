export interface ProjectFile { path: string; content: string; lang: string }

/** Compatibility for model servers that return standalone HTML without files. */
export function extractWebsiteProject(html: string): ProjectFile[] {
  const assets: ProjectFile[] = [];
  let styles = 0;
  let scripts = 0;
  const document = html.replace(/<style\b([^>]*)>([\s\S]*?)<\/style\s*>/gi, (_tag, attrs: string, content: string) => {
    const path = `css/styles${styles++ ? `-${styles}` : ""}.css`;
    assets.push({path, content, lang: "css"});
    return `<link rel="stylesheet" href="${path}"${attrs}>`;
  }).replace(/<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi, (tag, attrs: string, content: string) => {
    if (/\bsrc\s*=/i.test(attrs) || /\btype\s*=\s*["'](?:application\/ld\+json|application\/json|importmap)["']/i.test(attrs) || !content.trim()) return tag;
    const path = `js/script${scripts++ ? `-${scripts}` : ""}.js`;
    assets.push({path, content, lang: "javascript"});
    return `<script src="${path}"${attrs}></script>`;
  });
  return [{path: "index.html", content: document, lang: "html"}, ...assets,
    {path: "README.md", lang: "text", content: "# Website project\n\nExtract the ZIP and open index.html. Keep the css/ and js/ folders alongside it.\n"}];
}

export function projectFiles(value: unknown): ProjectFile[] {
  if (!Array.isArray(value)) return [];
  const seen = new Set<string>();
  let total = 0;
  return value.slice(0, 16).flatMap((file) => {
    if (!file || typeof file.path !== "string" || typeof file.content !== "string") return [];
    const path = file.path;
    if (!/^[a-zA-Z0-9_./-]+$/.test(path) || path.startsWith("/") || path.split("/").some((part: string) => !part || part === "." || part === "..") || seen.has(path)) return [];
    total += file.content.length;
    if (total > 100_000) return [];
    seen.add(path);
    return [{ path, content: file.content, lang: String(file.lang || "text") }];
  });
}

export function projectPreview(html: string, files: ProjectFile[]): string {
  const lookup = (path: string) => files.find(file => file.path === path.replace(/^\.\//, "").split(/[?#]/)[0]);
  html = html.replace(/<link\b[^>]*>/gi, tag => {
    if (!/rel\s*=\s*["']stylesheet["']/i.test(tag)) return tag;
    const path = tag.match(/href\s*=\s*["']([^"']+)["']/i)?.[1];
    const file = path && lookup(path);
    return file ? `<style>${file.content.replace(/<\/style/gi, "<\\/style")}</style>` : tag;
  });
  return html.replace(/<script\b([^>]*)>\s*<\/script\s*>/gi, (tag, attrs: string) => {
    const path = attrs.match(/src\s*=\s*["']([^"']+)["']/i)?.[1];
    const file = path && lookup(path);
    if (!file) return tag;
    const rest = attrs.replace(/\bsrc\s*=\s*["'][^"']+["']/i, "");
    return `<script${rest}>${file.content.replace(/<\/script/gi, "<\\/script")}</script>`;
  });
}
