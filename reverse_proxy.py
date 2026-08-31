#!/usr/bin/env python3
"""
Simple reverse proxy for smarthrms.online
Routes all traffic from port 80/443 to localhost:8000 (Flask app)
"""

import socket
import ssl
import threading
import sys
from urllib.request import urlopen
from urllib.error import URLError

def proxy_handler(client_socket, is_https=False):
    """Handle HTTP/HTTPS proxy connections"""
    try:
        # Read request from client
        request_data = b""
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            request_data += chunk
            if b"\r\n\r\n" in request_data:
                break
        
        # Parse request
        request_str = request_data.decode('latin-1')
        lines = request_str.split('\r\n')
        request_line = lines[0]
        
        # Forward to Flask app on port 8000
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('127.0.0.1', 8000))
        sock.sendall(request_data)
        
        # Receive response
        response_data = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_data += chunk
        sock.close()
        
        # Send response to client
        client_socket.sendall(response_data)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

def start_http_server():
    """Start HTTP proxy on port 80"""
    print("[HTTP] Starting HTTP reverse proxy on port 80...")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 80))
    server.listen(5)
    print("[HTTP] ✓ Listening on port 80")
    
    while True:
        client, addr = server.accept()
        threading.Thread(target=proxy_handler, args=(client, False), daemon=True).start()

def start_https_server():
    """Start HTTPS proxy on port 443"""
    print("[HTTPS] Starting HTTPS reverse proxy on port 443...")
    
    # Create SSL context
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    # Create self-signed cert if needed
    cert_file = "C:\\nginx-1.31.3\\cert.pem"
    key_file = "C:\\nginx-1.31.3\\key.pem"
    
    try:
        context.load_cert_chain(cert_file, key_file)
    except:
        print("[HTTPS] ⚠ SSL certificate not found, using HTTP only")
        return
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 443))
    server.listen(5)
    
    wrapped_server = context.wrap_socket(server, server_side=True)
    print("[HTTPS] ✓ Listening on port 443")
    
    while True:
        try:
            client, addr = wrapped_server.accept()
            threading.Thread(target=proxy_handler, args=(client, True), daemon=True).start()
        except:
            pass

if __name__ == "__main__":
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  Smart HRMS Reverse Proxy - Production Mode               ║")
    print("║  Routes smarthrms.online traffic to localhost:8000        ║")
    print("╚════════════════════════════════════════════════════════════╝\n")
    
    # Start both servers
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    https_thread = threading.Thread(target=start_https_server, daemon=True)
    
    http_thread.start()
    https_thread.start()
    
    print("\n✓ Reverse proxy started")
    print("✓ Port 80 → localhost:8000")
    print("✓ Port 443 → localhost:8000")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        print("\n✓ Shutting down...")
        sys.exit(0)
