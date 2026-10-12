"""Deterministic transport/STOP tests: NO physical chamber access."""
import socket
import unittest
from unittest.mock import patch

from VotschTechnikClimateChamber.ClimateChamber import (
    ClimateChamber, StopNotVerified, create_command_string,
)
from VotschTechnikClimateChamber.transport import (
    ChamberTransportError, connect_socket, exchange_frame,
)


class FakeSocket:
    def __init__(self, response=b"1\xb6OK\r", fail_connect=False):
        self.payload = bytearray(response)
        self.commands = []
        self.timeout = None
        self.closed = False
        self.fail_connect = fail_connect
        self.connect_timeout = None

    def settimeout(self, value):
        self.timeout = value

    def connect(self, address):
        self.connect_timeout = self.timeout
        if self.fail_connect:
            raise socket.timeout("connect timed out")

    def sendall(self, request):
        self.commands.append(request)

    def recv(self, amount):
        if not self.payload:
            return b""
        chunk = bytes(self.payload[:amount])
        del self.payload[:amount]
        return chunk

    def close(self):
        self.closed = True


class TransportTests(unittest.TestCase):
    def test_timeout_is_set_before_connect(self):
        fake = FakeSocket()
        with patch("VotschTechnikClimateChamber.transport.socket.socket", return_value=fake):
            self.assertIs(connect_socket("127.0.0.1", 2049, 0.2), fake)
        self.assertEqual(fake.connect_timeout, 0.2)

    def test_failed_connect_closes_socket(self):
        fake = FakeSocket(fail_connect=True)
        with patch("VotschTechnikClimateChamber.transport.socket.socket", return_value=fake):
            with self.assertRaises(socket.timeout):
                connect_socket("127.0.0.1", 2049, 0.2)
        self.assertTrue(fake.closed)

    def test_split_response_reads_through_cr(self):
        fake = FakeSocket(b"1\xb625.4\r")
        self.assertEqual(exchange_frame(fake, b"11004\xb61\r", 1), b"1\xb625.4\r")
        self.assertEqual(fake.commands, [b"11004\xb61\r"])

    def test_incomplete_response_closes_ambiguous_session(self):
        fake = FakeSocket(b"1\xb6partial")
        with self.assertRaises(ChamberTransportError) as raised:
            exchange_frame(fake, b"11001\xb61\r", 1)
        self.assertTrue(raised.exception.command_may_have_executed)
        self.assertTrue(fake.closed)

    def test_oversize_frame_fails_closed(self):
        fake = FakeSocket(b"1\xb6" + b"x" * 100)
        with self.assertRaises(ChamberTransportError):
            exchange_frame(fake, b"11004\xb61\r", 1, max_frame=8)
        self.assertTrue(fake.closed)

    def test_reject_protocol_argument_injection(self):
        with self.assertRaises(ValueError):
            create_command_string("11001", "25\r11001")


class CommandTests(unittest.TestCase):
    def new_chamber(self):
        chamber = object.__new__(ClimateChamber)
        chamber._temperature_min = -40.0
        chamber._temperature_max = 100.0
        chamber._temp_round = 2
        return chamber

    def test_status_only_success_response_is_valid(self):
        chamber = self.new_chamber()
        chamber.query_command_low_level = lambda *args: b"1\r"
        self.assertEqual(chamber.query("START MANUAL_MODE", 1, 0), [])

    def test_non_finite_and_boolean_rejected_before_io(self):
        chamber = self.new_chamber()
        chamber.query = lambda *args: self.fail("No hardware call expected")
        for value in (float("nan"), float("inf"), True, "-inf", "abc"):
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                chamber.temperature_set_point = value

    def test_numeric_string_is_converted_to_finite_float(self):
        chamber = self.new_chamber()
        seen = []
        chamber.query = lambda *args: seen.append(args)
        chamber.temperature_set_point = "25.5"
        self.assertEqual(seen, [("SET CONTROL_VARIABLE SET_POINT", 1, "25.5")])

    def test_stop_attempts_write_without_status_precheck(self):
        chamber = self.new_chamber()
        observed = []
        def query(*args):
            observed.append(args[0])
            if args[0] == "GET DIGITAL_OUT VALUE":
                return ["0"]
            return ["1"]
        chamber.query = query
        chamber.stop()
        self.assertEqual(observed, ["START MANUAL_MODE", "GET DIGITAL_OUT VALUE"])

    def test_failed_readback_is_not_reported_as_stopped(self):
        chamber = self.new_chamber()
        def query(*args):
            if args[0] == "GET DIGITAL_OUT VALUE":
                raise OSError("link lost")
            return ["1"]
        chamber.query = query
        with self.assertRaises(StopNotVerified):
            chamber.stop()

    def test_unknown_write_is_not_reported_as_stopped(self):
        chamber = self.new_chamber()
        chamber.query = lambda *args: (_ for _ in ()).throw(TimeoutError("lost ack"))
        with self.assertRaises(StopNotVerified):
            chamber.stop()


if __name__ == "__main__":
    unittest.main()
