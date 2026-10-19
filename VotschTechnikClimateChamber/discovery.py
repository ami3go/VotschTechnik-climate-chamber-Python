"""Bounded, read-only S!MPAC/LabEvent discovery for administrator opt-in use.

This module is part of the vendor driver: GUI code must not implement a
separate chamber transport. No control/setpoint/STOP commands are sent.
Discovery cannot authorize connecting to or controlling physical hardware.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError, as_completed
from dataclasses import dataclass
import ipaddress
import socket
import time

from .ClimateChamber import ClimateChamber

_RFC1918 = tuple(ipaddress.IPv4Network(value) for value in (
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"))
MAX_HOSTS = 512
MAX_WORKERS = 16
MAX_SCAN_SECONDS = 12.0
PROBE_TIMEOUT_SECONDS = 0.35


@dataclass(frozen=True)
class DiscoveredChamber:
    address: str
    model: str
    serial_number: str


def _safe_private_network(network):
    try:
        parsed = ipaddress.ip_network(network, strict=False)
    except ValueError as exc:
        raise ValueError("Enter a valid private IPv4 CIDR (e.g. 192.168.1.0/24)") from exc
    if (not isinstance(parsed, ipaddress.IPv4Network)
            or parsed.prefixlen < 24
            or not any(parsed.subnet_of(allowed) for allowed in _RFC1918)):
        raise ValueError("Discovery is restricted to RFC1918 IPv4 /24 or narrower networks")
    return parsed


def _automatic_networks():
    """Identify server-side IPv4 interfaces without transmitting discovery packets."""
    addresses = set()
    try:
        for entry in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            addresses.add(entry[4][0])
    except OSError:
        pass
    # UDP connect merely selects a route; it sends no datagram.
    for destination in ("10.255.255.254", "172.31.255.254", "192.168.255.254"):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect((destination, 9))
                addresses.add(sock.getsockname()[0])
        except OSError:
            continue
    networks = set()
    for address in addresses:
        try:
            networks.add(_safe_private_network(f"{address}/24"))
        except ValueError:
            continue
    return tuple(sorted(networks, key=lambda item: (int(item.network_address), item.prefixlen)))


def _probe(address: str, timeout_s: float):
    """Only supported driver GET CHAMBER INFO queries; always close the socket."""
    chamber = None
    try:
        chamber = ClimateChamber(address, 15.0, 35.0, timeout=timeout_s)
        model = str(chamber.test_system_type).strip()
        serial = str(chamber.serial_number).strip()
        # Reject false-positive TCP listeners and identity values unusable by
        # the GUI's existing fail-closed serial pin.
        if not model or len(model) > 120 or not serial.isalnum() or len(serial) > 80:
            return None
        return DiscoveredChamber(address, model, serial)
    except (OSError, TimeoutError, ValueError, RuntimeError, IndexError, TypeError):
        return None
    finally:
        if chamber is not None:
            try:
                chamber.disconnect()
            except OSError:
                pass


def discover_chambers(network: str | None = None) -> list[DiscoveredChamber]:
    """Scan a selected private subnet, or up to two local private /24 networks.

    Manual invocation only. Global 12s watchdog, 16 workers, per-operation
    350ms socket timeout, 512 candidate limit. Incomplete scans return partial
    results rather than keeping the GUI busy indefinitely. No public targets.
    """
    networks = (_safe_private_network(network),) if network else _automatic_networks()
    if not networks:
        raise ValueError("No private local IPv4 network found; enter a /24 CIDR manually")
    addresses = sorted({str(host) for subnet in networks for host in subnet.hosts()},
                       key=lambda value: int(ipaddress.IPv4Address(value)))
    if len(addresses) > MAX_HOSTS:
        raise ValueError("Scan exceeds 512 hosts; select a smaller private subnet")
    if not addresses:
        return []
    deadline = time.monotonic() + MAX_SCAN_SECONDS
    pool = ThreadPoolExecutor(max_workers=MAX_WORKERS, thread_name_prefix="votsch-discover")
    futures = [pool.submit(_probe, address, PROBE_TIMEOUT_SECONDS) for address in addresses]
    found = []
    try:
        try:
            for future in as_completed(futures, timeout=max(0.0, deadline - time.monotonic())):
                result = future.result()
                if result is not None:
                    found.append(result)
        except TimeoutError:
            # Watchdog: return independently verified devices seen so far.
            pass
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    return sorted(found, key=lambda item: int(ipaddress.IPv4Address(item.address)))
