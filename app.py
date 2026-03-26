#!/usr/bin/env python3
import subprocess, threading, socket
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 4022

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silence access logs

    def do_GET(self):
        # expects /udp/239.1.1.18:3030
        if not self.path.startswith('/udp/'):
            self.send_error(400, 'Bad request')
            return

        target = self.path[5:]  # strip /udp/
        udp_url = f'udp://@{target}'

        self.send_response(200)
        self.send_header('Content-Type', 'video/mp2t')
        self.send_header('Transfer-Encoding', 'chunked')
        self.end_headers()

        cmd = [
            'ffmpeg', '-hide_banner', '-loglevel', 'error',
            '-i', udp_url,
            '-c', 'copy',
            '-f', 'mpegts',
            'pipe:1'
        ]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            while True:
                chunk = proc.stdout.read(4096)
                if not chunk:
                    break
                self.wfile.write(chunk)
        except Exception:
            pass
        finally:
            proc.kill()

print(f'UDP→HTTP proxy running on port {PORT}')
HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()
