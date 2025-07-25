import http.server
import socketserver
import urllib.parse

PORT = 8000


class OAuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        code = params.get("code", [""])[0]
        if code:
            print(f"\nAuthorization Code: {code}\n")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(
                b"Authorization code received. You may close this window.")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No authorization code found.")

    def log_message(self, format, *args):
        pass  # Suppress default logging


with socketserver.TCPServer(("", PORT), OAuthHandler) as httpd:
    print(f"Listening on http://localhost:{PORT}")
    httpd.serve_forever()
