"""Deterministic local discovery tests; all sockets/probes are mocked."""
from __future__ import annotations

import ipaddress
import socket
import unittest
from unittest.mock import patch

from VotschTechnikClimateChamber import discovery
from VotschTechnikClimateChamber.discovery import DiscoveredChamber, DiscoveryProbeError


class DiscoveryTests(unittest.TestCase):
    def test_rejects_public_loopback_ipv6_and_large_scan(self):
        for network in ("8.8.8.0/24", "127.0.0.0/24", "169.254.0.0/24",
                        "192.168.0.0/16", "10.0.0.0/23", "::1/128", "garbage"):
            with self.subTest(network=network), self.assertRaises(ValueError):
                discovery.discover_chambers(network)

    def test_discovers_only_driver_identified_chambers(self):
        seen = []
        def probe(ip, timeout):
            seen.append((ip, timeout))
            return DiscoveredChamber(ip, "LabEvent", "ABC123") if ip == "192.168.4.2" else None
        with patch.object(discovery, "_probe", side_effect=probe):
            result = discovery.discover_chambers("192.168.4.0/30")
        self.assertEqual(result, [DiscoveredChamber("192.168.4.2", "LabEvent", "ABC123")])
        self.assertEqual({ip for ip, _ in seen}, {"192.168.4.1", "192.168.4.2"})
        self.assertTrue(all(timeout == discovery.PROBE_TIMEOUT_SECONDS for _, timeout in seen))

    def test_single_ip_uses_one_longer_probe_only(self):
        seen = []
        def fake_probe(ip, timeout, *, diagnostic=False):
            seen.append((ip, timeout, diagnostic))
            return DiscoveredChamber(ip, "LabEvent T", "ABC123")
        with patch.object(discovery, "_probe", side_effect=fake_probe):
            result = discovery.discover_chambers("192.168.4.42")
        self.assertEqual(result, [DiscoveredChamber("192.168.4.42", "LabEvent T", "ABC123")])
        self.assertEqual(seen, [("192.168.4.42", discovery.DIRECT_PROBE_TIMEOUT_SECONDS, True)])

    def test_direct_ip_failed_connection_gives_actionable_diagnostic(self):
        class Refused:
            def __init__(self, *args, **kwargs):
                raise ConnectionRefusedError("refused")
        with patch.object(discovery, "ClimateChamber", Refused):
            with self.assertRaisesRegex(DiscoveryProbeError, "TCP 2049 connection refused"):
                discovery.discover_chambers("10.1.2.3")

    def test_direct_ip_timeout_gives_actionable_diagnostic(self):
        class TimedOut:
            def __init__(self, *args, **kwargs):
                raise socket.timeout("unreachable")
        with patch.object(discovery, "ClimateChamber", TimedOut):
            with self.assertRaisesRegex(DiscoveryProbeError, "timed out"):
                discovery.discover_chambers("10.1.2.3")

    def test_invalid_protocol_identified_separately_from_tcp_connection(self):
        class MalformedReply:
            def __init__(self, *args, **kwargs):
                self.closed = False
            @property
            def test_system_type(self):
                raise RuntimeError("unexpected reply")
            def disconnect(self):
                self.closed = True
        with patch.object(discovery, "ClimateChamber", MalformedReply):
            with self.assertRaisesRegex(DiscoveryProbeError, "S!MPAC GET CHAMBER INFO"):
                discovery.discover_chambers("172.16.5.2")

    def test_subnet_scan_keeps_unresponsive_hosts_nonfatal(self):
        with patch.object(discovery, "ClimateChamber", side_effect=ConnectionRefusedError):
            self.assertEqual(discovery.discover_chambers("192.168.22.0/30"), [])

    def test_automatic_scan_uses_only_detected_private_network(self):
        with patch.object(discovery, "_automatic_networks", return_value=(
                ipaddress.IPv4Network("10.44.2.0/30"),)):
            with patch.object(discovery, "_probe", return_value=None) as probe:
                self.assertEqual(discovery.discover_chambers(), [])
        self.assertEqual(probe.call_count, 2)

    def test_probe_is_read_only_and_always_disconnects(self):
        class FakeDriver:
            instances = []
            def __init__(self, ip, low, high, timeout):
                self.ip = ip
                self.closed = False
                self.instances.append(self)
            @property
            def test_system_type(self):
                return "LabEvent T"
            @property
            def serial_number(self):
                return "ABC123"
            def disconnect(self):
                self.closed = True
        with patch.object(discovery, "ClimateChamber", FakeDriver):
            result = discovery._probe("10.1.1.3", 0.2)
        self.assertEqual(result, DiscoveredChamber("10.1.1.3", "LabEvent T", "ABC123"))
        self.assertTrue(FakeDriver.instances[0].closed)

    def test_bad_identity_not_claimed_as_chamber(self):
        class BadDriver:
            def __init__(self, *args, **kwargs): pass
            @property
            def test_system_type(self): return "Some TCP server"
            @property
            def serial_number(self): return "bad serial"
            def disconnect(self): pass
        with patch.object(discovery, "ClimateChamber", BadDriver):
            self.assertIsNone(discovery._probe("10.1.1.5", 0.2))


if __name__ == "__main__":
    unittest.main()
