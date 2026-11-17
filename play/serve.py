# Static server for play/. Follows the symlinks in this folder.
# python3 play/serve.py [port]  ->  http://localhost:5302/chope.html
import http.server, os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
class H(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, '.glb': 'model/gltf-binary', '.js': 'text/javascript', '.mjs': 'text/javascript'}
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')  # a refresh picks up new glbs
        super().end_headers()
    def log_message(self, *a): pass
class S(http.server.ThreadingHTTPServer):
    request_queue_size = 256  # the default 5 resets connections when the page fetches 100+ files at once
    daemon_threads = True
port = int(sys.argv[1]) if len(sys.argv) > 1 else 5302
print(f'http://localhost:{port}/chope.html', flush=True)
S(('', port), H).serve_forever()
