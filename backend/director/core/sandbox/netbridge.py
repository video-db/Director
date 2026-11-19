"""Runs inside bubblewrap's private network: forwards 127.0.0.1:<port> to the egress proxy's socket, then runs the command.

Usage: python netbridge.py <socket> <port> -- <command...>
Standard library only, since it runs with no access to the user's packages.
"""

import socket
import subprocess
import sys
import threading


def pipe(src, dst):
    try:
        while True:
            data = src.recv(65536)
            if not data:
                break
            dst.sendall(data)
    except OSError:
        pass
    finally:
        for s in (src, dst):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass


def serve(listener, sock_path):
    while True:
        client, _ = listener.accept()
        upstream = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            upstream.connect(sock_path)
        except OSError:
            client.close()
            continue
        threading.Thread(target=pipe, args=(client, upstream), daemon=True).start()
        threading.Thread(target=pipe, args=(upstream, client), daemon=True).start()


def main(argv):
    sock_path, port, sep, *command = argv
    if sep != "--" or not command:
        sys.exit("usage: netbridge.py <socket> <port> -- <command...>")
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", int(port)))
    listener.listen(64)
    threading.Thread(target=serve, args=(listener, sock_path), daemon=True).start()
    sys.exit(subprocess.call(command))


if __name__ == "__main__":
    main(sys.argv[1:])
