import unittest
from unittest.mock import patch
import json

from opcoda.project import website_project, missing_assets


class ProjectTests(unittest.TestCase):
    def test_assets_are_split_and_linked(self):
        files = website_project('<html><head><style>body{color:red}</style></head><body><script>console.log(1)</script></body></html>')
        paths = {f['path']: f['content'] for f in files}
        self.assertEqual(paths['css/styles.css'], 'body{color:red}\n')
        self.assertIn('js/script.js', paths['index.html'])
        self.assertEqual(set(missing_assets(paths['index.html'])), {'css/styles.css', 'js/script.js'})
        self.assertIn('README.md', paths)

    def test_missing_asset_detected(self):
        self.assertEqual(missing_assets('<link rel="stylesheet" href="styles.css"><img src="photo.png">'), ['styles.css', 'photo.png'])

    def test_missing_stylesheet_repaired_in_generation(self):
        import server
        html = '<!doctype html><html><head><title>Test</title><link rel="stylesheet" href="styles.css"></head><body><main><h1>Portfolio</h1></main></body></html>'
        css = 'body{margin:0;background:#111;color:#eee;font:16px/1.6 system-ui}main{max-width:1000px;margin:auto;padding:48px}h1{font-size:48px}a{color:inherit}a:focus-visible{outline:2px solid white}@media(max-width:600px){main{padding:24px}h1{font-size:32px}}'
        replies = [html, css]
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return json.dumps({'message': {'content': replies.pop(0)}, 'done_reason': 'stop', 'eval_count': 100}).encode()
        with patch('server.urllib.request.urlopen', side_effect=lambda *a, **k: Response()):
            result = server.generate_ollama(server.GenerateRequest(prompt='Build a dark portfolio', language='html'))
        self.assertFalse(missing_assets(result['text']))
        self.assertIn('css/styles.css', [f['path'] for f in result['files']])
        self.assertTrue(next(c['ok'] for c in result['checks']['checks'] if c['name'] == 'Responsive layout'))


if __name__ == '__main__':
    unittest.main()
