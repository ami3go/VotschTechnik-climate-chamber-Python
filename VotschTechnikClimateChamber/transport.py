"""Bounded S!MPAC TCP transport. No automatic retries of writes.

Protocol framing uses carriage return as in create_command_string.
Unexpected or incomplete replies close the socket to prevent desynchronization.
This must be confirmed on the exact supported firmware during HIL certification.
"""
from __future__ import annotations

import math
import socket
import time


class ChamberTransportError(RuntimeError):
    """Transport lost synchronization; the last command MAY have executed."""

    def __init__(self, message: str, *, command_may_have_executed: bool = False):
        super().__init__(message)
        self.command_may_have_executed = command_may_have_executed


def connect_socket(ip: str, port: int, timeout: float):
    if isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("A positive finite socket timeout is required")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(timeout)  # Must precede connect!
        sock.connect((ip, port))
        return sock
    except BaseException:
        sock.close()
        raise


def exchange_frame(sock, request: bytes, timeout: float, max_frame: int = 4096) -> bytes:
    """Send one request and receive exactly one CR-terminated response.

    All reads share one monotonic deadline; a missing delimiter, EOF, or
    oversized reply invalidates the session. Never retry a write here.
    """
    if not request.endswith(b"\r"):
        raise ValueError("Request must end with CR")
    if not 1 <= max_frame <= 65536:
        raise ValueError("Invalid maximum response size")
    if isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("A positive finite timeout is required")
    deadline = time.monotonic() + timeout
    attempted = False
    try:
        attempted = True
        sock.sendall(request)
        response = bytearray()
        while len(response) <= max_frame:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Response deadline expired")
            sock.settimeout(remaining)
            chunk = sock.recv(1)
            if not chunk:
                raise ConnectionError("Connection closed before response terminator")
            # Some controllers emit CRLF. Ignore one residual LF at frame start.
            if not response and chunk == b"\n":
                continue
            response.extend(chunk)
            if chunk == b"\r":
                sock.settimeout(timeout)
                return bytes(response)
        raise ValueError("Response exceeds maximum frame length")
    except (OSError, TimeoutError, ValueError) as exc:
        sock.close()
        raise ChamberTransportError(
            f"Communication failed; command outcome may be unknown: {exc}",
            command_may_have_executed=attempted,
        ) from exc
