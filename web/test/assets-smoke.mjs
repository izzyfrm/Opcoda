// Run against wrangler dev so the Worker's asset allowlist is exercised.
import assert from 'node:assert/strict';
const base = process.argv[2] || 'http://127.0.0.1:8787';
for (const [path, type] of [['/', 'text/html'], ['/app.css', 'text/css'], ['/workspace.css', 'text/css'], ['/workspace-ascii.svg', 'image/svg+xml']]) {
  const response = await fetch(new URL(path, base));
  assert.equal(response.status, 200, `${path} must be served by the Worker`);
  assert.ok(response.headers.get('content-type')?.includes(type), `${path} must have ${type} content type`);
  assert.ok((await response.text()).length > 0, `${path} must not be empty`);
}
assert.equal((await fetch(new URL('/unknown-asset.css', base))).status, 404);
console.log('PASS: workspace assets served with correct MIME types; unknown files return 404.');
