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
DIRECT_PROBE_TIMEOUT_SECONDS = 2.0


@dataclass(frozen=True)
class DiscoveredChamber:
    address: str
    model: str
    serial_number: str


class DiscoveryProbeError(RuntimeError):
    """A specific, user-actionable read-only identity failure at one IP."""


def _safe_private_network(network):
    try:
        parsed = ipaddress.ip_network(network, strict=False)
    except ValueError as exc:
        raise ValueError("Enter one private IPv4 address (e.g. 192.168.1.10) or CIDR (e.g. 192.168.1.0/24)") from exc
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


def _probe(address: str, timeout_s: float, *, diagnostic: bool = False):
    """Use only driver GET CHAMBER INFO, optionally describing an IP failure.

    No write commands are sent. Scanning CIDRs remains quiet about each
    non-device; single-host tests produce human-readable diagnostics.
    """
    chamber = None
    try:
        chamber = ClimateChamber(address, 15.0, 35.0, timeout=timeout_s)
        model = str(chamber.test_system_type).strip()
        serial = str(chamber.serial_number).strip()
        # Protect the existing serial-pin validation; an arbitrary open
        # TCP listener must never be represented as a chamber.
        if not model or len(model) > 120 or not serial.isalnum() or len(serial) > 80:
            if diagnostic:
                raise DiscoveryProbeError(
                    "Device responded on TCP 2049 but its model/serial identity "
                    "is missing or not usable for the chamber serial pin.")
            return None
        return DiscoveredChamber(address, model, serial)
    except DiscoveryProbeError:
        raise
    except (socket.timeout, TimeoutError) as exc:
        if diagnostic:
            raise DiscoveryProbeError(
                "TCP 2049 or the chamber identity reply timed out. Confirm the "
                "server can reach this IP; the controller may be responding slowly.") from exc
    except ConnectionRefusedError as exc:
        if diagnostic:
            raise DiscoveryProbeError(
                "TCP 2049 connection refused. Check chamber network setup and "
                "S!MPAC/SimServ TCP service.") from exc
    except (ConnectionError, OSError) as exc:
        if diagnostic:
            raise DiscoveryProbeError(
                "TCP 2049 connection failed or closed. Check network route, "
                "firewall and controller communication settings.") from exc
    except (RuntimeError, ValueError, IndexError, TypeError, UnicodeError) as exc:
        if diagnostic:
            raise DiscoveryProbeError(
                "TCP 2049 connected, but the S!MPAC GET CHAMBER INFO "
                "identity response was invalid or unavailable.") from exc
    finally:
        if chamber is not None:
            try:
                chamber.disconnect()
            except OSError:
                pass
    return None

def discover_chambers(network: str | None = None) -> list[DiscoveredChamber]:
    """Probe one private IP or scan a selected subnet/local private networks.

    Manual invocation only. Global 12s watchdog, 16 workers, per-operation
    350ms CIDR and 2s direct-IP socket timeout, 512 candidate limit.\n    Incomplete scans return partial
    results rather than keeping the GUI busy indefinitely. No public targets.
    """
    # A single IPv4 address is a /32: do not scan its whole /24 by accident.
    # A longer timeout is justified when the operator knows the exact endpoint.
    explicit = _safe_private_network(network) if network else None
    if explicit is not None and explicit.prefixlen == 32:
        host = str(explicit.network_address)
        result = _probe(host, DIRECT_PROBE_TIMEOUT_SECONDS, diagnostic=True)
        return [result] if result is not None else []
    networks = (explicit,) if explicit is not None else _automatic_networks()
    if not networks:
        raise ValueError(
            "No private local IPv4 network found. Enter the chamber's private "
            "IP or a private /24 subnet to search.")
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
        # Compatible with Python 3.7/3.8 (shutdown(cancel_futures) is 3.9+).
        for future in futures:
            future.cancel()
        pool.shutdown(wait=False)
    return sorted(found, key=lambda item: int(ipaddress.IPv4Address(item.address)))
