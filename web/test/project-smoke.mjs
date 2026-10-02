import assert from 'node:assert/strict';
import { readFile, writeFile, mkdtemp, unlink, rmdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import ts from 'typescript';
import { projectZip } from '../public/project.js';

const source = await readFile(new URL('../src/project.ts', import.meta.url), 'utf8');
const js = ts.transpile(source, {module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022});
const {projectFiles, projectPreview, extractWebsiteProject} = await import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`);
const extracted = extractWebsiteProject('<html><head><style>body{background:black}</style></head><body><script>document.body.dataset.ready="yes";</script></body></html>');
assert.deepEqual(extracted.map(file => file.path), ['index.html','css/styles.css','js/script.js','README.md']);
assert.ok(projectPreview(extracted[0].content, extracted).includes('<style>body{background:black}</style>'));
const files = [
  {path:'index.html', lang:'html', content:'<head><link rel="stylesheet" href="css/styles.css"></head><body><script src="js/script.js"></script></body>'},
  {path:'css/styles.css', lang:'css', content:'body{background:#111;color:#eee}'},
  {path:'js/script.js', lang:'javascript', content:'document.body.dataset.ready="yes";'},
];
assert.equal(projectFiles([...files,{path:'../escape.txt',content:'bad'},{path:'/absolute.txt',content:'bad'}]).length,3);
const page = projectPreview(files[0].content,files);
assert.ok(page.includes('<style>body{background:#111;color:#eee}</style>'));
assert.ok(page.includes('document.body.dataset.ready="yes";'));
assert.ok(!page.includes('src="js/script.js"'));
const dir = await mkdtemp(join(tmpdir(),'opcoda-zip-test-'));
const archive = join(dir,'project.zip');
try {
  await writeFile(archive,Buffer.from(await projectZip(files).arrayBuffer()));
  const result = spawnSync('python',['-c','import sys,zipfile; z=zipfile.ZipFile(sys.argv[1]); assert z.testzip() is None; assert z.read("opcoda-project/css/styles.css").decode()=="body{background:#111;color:#eee}"; assert len(z.namelist())==3',archive],{encoding:'utf8'});
  assert.equal(result.status,0,result.stderr);
} finally { await unlink(archive); await rmdir(dir); }
console.log('PASS: safe project paths, bundled CSS/JS preview, ZIP extraction and CRC.');
