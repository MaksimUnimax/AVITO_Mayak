from __future__ import annotations

import socket
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from scripts.runtime.run_rf24_command_idempotency import wait_for_api

LISTENER = textwrap.dedent(
    """
    import json
    import socketserver
    import sys
    import time

    port, source_sha, delay = int(sys.argv[1]), sys.argv[2], float(sys.argv[3])
    time.sleep(delay)

    class Handler(socketserver.BaseRequestHandler):
        def handle(self):
            self.request.recv(4096)
            body = json.dumps({"source_sha": source_sha}).encode()
            self.request.sendall(
                b"HTTP/1.1 200 OK\\r\\nContent-Type: application/json\\r\\n"
                + f"Content-Length: {len(body)}\\r\\nConnection: close\\r\\n\\r\\n".encode()
                + body
            )

    with socketserver.TCPServer(("127.0.0.1", port), Handler) as server:
        server.serve_forever()
    """
)


def available_port() -> int:
    """Allocate a fixture-only listener port outside the RF24 acceptance range."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def stop(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def test_real_delayed_listener_survives_prebind_refusal_and_becomes_ready(tmp_path: Path) -> None:
    port = available_port()
    source_sha = "a" * 40
    process = subprocess.Popen(
        [sys.executable, "-c", LISTENER, str(port), source_sha, "0.6"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        shell=False,
    )
    started = time.monotonic()
    try:
        with pytest.raises(OSError):
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                pass
        observed_before_bind = time.monotonic()
        result = wait_for_api(process, f"http://127.0.0.1:{port}", source_sha, tmp_path / "api.log")
        assert result["source_sha"] == source_sha
        assert observed_before_bind - started < 0.6
        assert time.monotonic() - started >= 0.5
    finally:
        stop(process)
    assert process.poll() is not None
    with pytest.raises(OSError):
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            pass


def test_real_listener_wrong_source_sha_is_terminal(tmp_path: Path) -> None:
    port = available_port()
    process = subprocess.Popen(
        [sys.executable, "-c", LISTENER, str(port), "b" * 40, "0"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
        shell=False,
    )
    try:
        with pytest.raises(RuntimeError, match="source SHA mismatch"):
            wait_for_api(process, f"http://127.0.0.1:{port}", "a" * 40, tmp_path / "api.log")
    finally:
        stop(process)
