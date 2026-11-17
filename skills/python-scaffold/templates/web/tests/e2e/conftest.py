"""Live server for browser tests.

One Granian process per test, on a free port, torn down afterwards. The app
store is in memory, so a fresh process is an empty app: no state leaks between
specs. E2E tests are excluded from the default run by the marker in
``pyproject.toml``; run them with ``uv run pytest -m e2e``.
"""

import socket
import subprocess
import sys
import time
import urllib.request
from collections.abc import Iterator

import pytest


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_until_up(url: str, process: subprocess.Popen[bytes], timeout: float = 20.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"server exited before accepting connections: {process.returncode}")
        try:
            with urllib.request.urlopen(url, timeout=0.5):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError(f"server did not start within {timeout}s")


@pytest.fixture
def server_url() -> Iterator[str]:
    port = _free_port()
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "granian",
            "--interface",
            "asgi",
            "{{PACKAGE}}.asgi:application",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    try:
        _wait_until_up(url, process)
        yield url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
