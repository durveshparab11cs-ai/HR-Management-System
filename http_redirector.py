#!/usr/bin/env python
"""
HTTP Redirector on Port 80
===========================
Simple HTTP server that listens on port 80 and forwards all requests to port 8000.
This allows the netsh port proxy rules to function correctly.

Run with administrator privileges.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, urlunparse
import urllib.request
import sys

class HTTPRedirectHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.forward_request()
    
    def do_POST(self):
        self.forward_request()
    
    def do_HEAD(self):
        self.forward_request()
    
    def do_PUT(self):
        self.forward_request()
    
    def do_DELETE(self):
        self.forward_request()
    
    def forward_request(self):
        # Build the target URL (localhost:8000)
        target_url = f"http://localhost:8000{self.path}"
        
        try:
            # Forward the request
            req = urllib.request.Request(target_url)
            
            # Copy headers
            for header, value in self.headers.items():
                if header.lower() not in ['host', 'connection']:
                    req.add_header(header, value)
            
            # Add method
            if self.command in ['POST', 'PUT', 'DELETE']:
                content_length = self.headers.get('Content-Length')
                if content_length:
                    req.add_header('Content-Length', content_length)
                    body = self.rfile.read(int(content_length))
                    req.data = body
            
            req.get_method = lambda: self.command
            
            # Get response
            with urllib.request.urlopen(req, timeout=30) as response:
                # Send response back
                self.send_response(response.status)
                for header, value in response.headers.items():
                    if header.lower() != 'connection':
                        self.send_header(header, value)
                self.end_headers()
                
                # Send body
                self.wfile.write(response.read())
        
        except Exception as e:
            print(f"Error forwarding request: {e}")
            self.send_response(502)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Bad Gateway: Unable to reach origin server")
    
    def log_message(self, format, *args):
        """Suppress noisy logging"""
        return

if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 80), HTTPRedirectHandler)
    print("HTTP Redirector listening on port 80 → localhost:8000")
    print("Running... Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()
