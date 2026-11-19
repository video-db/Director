"""Egress proxy for the local sandbox: only allowlisted hosts are reachable.

Each run gets its own token in the proxy URL, so a blocked host is reported
back in that run's output and nowhere else.
"""

from __future__ import annotations

import base64
import logging
import os
import secrets
import socket
import socketserver
import tempfile
import threading
from typing import Dict, List, Optional, Set
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

DEFAULT_ALLOWED_HOSTS = ("api.videodb.io", "*.videodb.io")
MAX_HEADER_BYTES = 64 * 1024


def parse_hosts(value: str) -> List[str]:
    return [h.strip().lower().rstrip(".") for h in (value or "").split(",") if h.strip()]


def host_allowed(host: str, patterns: List[str]) -> bool:
    """Exact names, or `*.example.com` for any subdomain of example.com (not example.com itself)."""
    host = host.lower().rstrip(".")
    for pattern in patterns:
        if pattern.startswith("*."):
            if host.endswith(pattern[1:]):
                return True
        elif host == pattern:
            return True
    return False


class EgressProxy:
    """A forwarding proxy for HTTP and HTTPS (CONNECT) that refuses hosts off the allowlist."""

    def __init__(self, allowed: List[str], unix_socket: bool = False):
        self.allowed = allowed
        self._lock = threading.Lock()
        self._runs: Dict[str, Set[str]] = {}

        handler = _handler_for(self)
        self._tcp = _TCPServer(("127.0.0.1", 0), handler)
        self.port = self._tcp.server_address[1]
        self._start(self._tcp)

        self.socket_path: Optional[str] = None
        if unix_socket:
            folder = tempfile.mkdtemp(prefix="director-egress-")
            self.socket_path = os.path.join(folder, "proxy.sock")
            self._unix = _UnixServer(self.socket_path, handler)
            os.chmod(self.socket_path, 0o600)
            self._start(self._unix)

    @staticmethod
    def _start(server):
        threading.Thread(target=server.serve_forever, daemon=True).start()

    def open_run(self) -> str:
        token = secrets.token_hex(16)
        with self._lock:
            self._runs[token] = set()
        return token

    def close_run(self, token: str) -> List[str]:
        """Hosts this run tried to reach and was refused."""
        with self._lock:
            return sorted(self._runs.pop(token, set()))

    def check(self, token: Optional[str], host: str) -> bool:
        if host_allowed(host, self.allowed):
            return True
        with self._lock:
            if token in self._runs:
                self._runs[token].add(host)
        logger.info("Egress proxy blocked %s", host)
        return False


class _TCPServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True


class _UnixServer(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True


def _handler_for(proxy: EgressProxy):
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            head = _read_head(self.rfile)
            if head is None:
                return
            request_line, *header_lines = head.split(b"\r\n")
            try:
                method, target, version = request_line.decode("latin-1").split(" ", 2)
            except ValueError:
                return self._reply(400, "Bad request")
            headers = _headers(header_lines)
            token = _token(headers.get("proxy-authorization", ""))

            if method.upper() == "CONNECT":
                host, _, port = target.rpartition(":")
                host = host.strip("[]")
                if not proxy.check(token, host):
                    return self._blocked(host)
                upstream = _connect(host, int(port or 443))
                if upstream is None:
                    return self._reply(502, f"Could not reach {host}")
                self.wfile.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
                self.wfile.flush()
                return _tunnel(self.connection, upstream, client_buffer=self.rfile)

            url = urlsplit(target)
            host = url.hostname or ""
            if url.scheme != "http" or not host:
                return self._reply(400, "Only absolute http:// URLs or CONNECT are supported")
            if not proxy.check(token, host):
                return self._blocked(host)
            upstream = _connect(host, url.port or 80)
            if upstream is None:
                return self._reply(502, f"Could not reach {host}")
            path = url.path or "/"
            if url.query:
                path += "?" + url.query
            kept = [
                line for line in header_lines
                if line and not line.lower().startswith((b"proxy-", b"connection:"))
            ]  # fmt: skip
            rewritten = [f"{method} {path} {version}".encode("latin-1"), *kept, b"Connection: close", b"", b""]
            upstream.sendall(b"\r\n".join(rewritten))
            _tunnel(self.connection, upstream, client_buffer=self.rfile)

        def _blocked(self, host):
            self._reply(
                403,
                f"Director's network allowlist blocked {host}. "
                "Ask the operator to add it to SANDBOX_ALLOWED_HOSTS.",
            )

        def _reply(self, status, text):
            body = text.encode()
            reason = {400: "Bad Request", 403: "Forbidden", 502: "Bad Gateway"}.get(status, "")
            self.wfile.write(
                f"HTTP/1.1 {status} {reason}\r\nContent-Type: text/plain\r\n"
                f"Content-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode()
                + body
            )

    return Handler


def _read_head(rfile) -> Optional[bytes]:
    data = b""
    while b"\r\n\r\n" not in data:
        line = rfile.readline(MAX_HEADER_BYTES)
        if not line:
            return None
        data += line
        if len(data) > MAX_HEADER_BYTES:
            return None
    return data.split(b"\r\n\r\n", 1)[0]


def _headers(lines) -> Dict[str, str]:
    out = {}
    for line in lines:
        name, _, value = line.decode("latin-1").partition(":")
        out[name.strip().lower()] = value.strip()
    return out


def _token(auth: str) -> Optional[str]:
    """The run token, sent as the proxy URL's password (`run:<token>@`); some clients drop a bare username."""
    scheme, _, value = auth.partition(" ")
    if scheme.lower() != "basic":
        return None
    try:
        return base64.b64decode(value).decode().partition(":")[2] or None
    except (ValueError, UnicodeDecodeError):
        return None


def _connect(host: str, port: int) -> Optional[socket.socket]:
    try:
        return socket.create_connection((host, port), timeout=30)
    except OSError:
        return None


def _tunnel(client: socket.socket, upstream: socket.socket, client_buffer=None):
    """Copy bytes both ways until either side closes."""
    upstream.settimeout(None)
    client.settimeout(None)

    def copy(src_read, dst):
        try:
            while True:
                data = src_read(65536)
                if not data:
                    break
                dst.sendall(data)
        except OSError:
            pass
        finally:
            try:
                dst.shutdown(socket.SHUT_WR)
            except OSError:
                pass

    # Bytes the client already sent sit in the handler's buffered reader.
    reader = client_buffer.read1 if client_buffer is not None else client.recv
    t = threading.Thread(target=copy, args=(upstream.recv, client), daemon=True)
    t.start()
    copy(reader, upstream)
    t.join()
    upstream.close()
