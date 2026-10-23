"""Typed numbered-output and gradient API tests with a mocked transport.

No sockets or physical chamber access: ``query`` is replaced with a recorder.
"""
import time
import unittest
from unittest.mock import patch

from VotschTechnikClimateChamber import (
    GRADIENT_DOWN_LIMITS_C_PER_MIN,
    GRADIENT_UP_LIMITS_C_PER_MIN,
    ClimateChamber,
    DigitalOutputError,
    DigitalOutputReadbackError,
)


class TypedDigitalOutputTests(unittest.TestCase):
    def new_chamber(self, responses=None):
        chamber = object.__new__(ClimateChamber)
        chamber._temperature_min = -40.0
        chamber._temperature_max = 100.0
        chamber._temp_round = 2
        self.calls = []
        replies = dict(responses or {})

        def query(command, *args):
            self.calls.append((command, args))
            return replies.get((command, args), ["0"])

        chamber.query = query
        return chamber

    def test_read_returns_strict_bool(self):
        chamber = self.new_chamber({("GET DIGITAL_OUT VALUE", (2,)): ["1"]})
        self.assertIs(chamber.read_digital_output(2), True)
        self.assertEqual(self.calls, [("GET DIGITAL_OUT VALUE", (2,))])

        chamber = self.new_chamber({("GET DIGITAL_OUT VALUE", (7,)): ["0"]})
        self.assertIs(chamber.read_digital_output(7), False)

    def test_malformed_readback_is_not_guessed(self):
        for reply in (["2"], [], ["TRUE"], [""], ["1\r"]):
            with self.subTest(reply=reply):
                chamber = self.new_chamber({("GET DIGITAL_OUT VALUE", (2,)): reply})
                with self.assertRaises(DigitalOutputReadbackError):
                    chamber.read_digital_output(2)

    def test_number_and_state_are_validated_before_io(self):
        chamber = self.new_chamber()
        for number in (0, 65, -1, True, 2.0, "2", None):
            with self.subTest(number=number):
                with self.assertRaises(DigitalOutputError):
                    chamber.read_digital_output(number)
                with self.assertRaises(DigitalOutputError):
                    chamber.set_digital_output(number, True)
        for state in (1, 0, "1", None, 1.0):
            with self.subTest(state=state), self.assertRaises(DigitalOutputError):
                chamber.set_digital_output(2, state)
        self.assertEqual(self.calls, [])

    def test_write_sends_typed_request(self):
        chamber = self.new_chamber()
        chamber.set_digital_output(7, True)
        chamber.set_digital_output(8, False)
        self.assertEqual(self.calls, [
            ("SET DIGITAL_OUT VALUE", (7, 1)),
            ("SET DIGITAL_OUT VALUE", (8, 0)),
        ])

    def test_device_reported_output_count(self):
        chamber = self.new_chamber({("GET DIGITAL_OUT NUMBER_OF", ()): ["16"]})
        self.assertEqual(chamber.number_of_digital_outputs, 16)
        self.assertEqual(self.calls, [("GET DIGITAL_OUT NUMBER_OF", ())])
        for reply in (["0"], ["65"], ["x"], [], [""]):
            with self.subTest(reply=reply):
                chamber = self.new_chamber({("GET DIGITAL_OUT NUMBER_OF", ()): reply})
                with self.assertRaises(DigitalOutputError):
                    chamber.number_of_digital_outputs

    def test_device_reported_output_name(self):
        chamber = self.new_chamber({("GET DIGITAL_OUT NAME", (8,)): ["  Dryer  "]})
        self.assertEqual(chamber.digital_output_name(8), "Dryer")
        self.assertEqual(self.calls, [("GET DIGITAL_OUT NAME", (8,))])
        for reply in ([], [""], ["   "]):
            with self.subTest(reply=reply):
                chamber = self.new_chamber({("GET DIGITAL_OUT NAME", (8,)): reply})
                with self.assertRaises(DigitalOutputError):
                    chamber.digital_output_name(8)
        with self.assertRaises(DigitalOutputError):
            self.new_chamber().digital_output_name(0)

    def test_legacy_properties_delegate_to_typed_mapping(self):
        chamber = self.new_chamber()
        self.assertIs(chamber.is_running, False)
        self.assertIs(chamber.dryer, False)
        self.assertIs(chamber.compressed_air, False)
        self.assertEqual(self.calls, [
            ("GET DIGITAL_OUT VALUE", (1,)),
            ("GET DIGITAL_OUT VALUE", (8,)),
            ("GET DIGITAL_OUT VALUE", (7,)),
        ])

        self.calls.clear()
        with patch.object(time, "sleep"):
            chamber.dryer = True
            chamber.compressed_air = False
        self.assertEqual(self.calls, [
            ("SET DIGITAL_OUT VALUE", (8, 1)),
            ("SET DIGITAL_OUT VALUE", (7, 0)),
        ])
        with self.assertRaises(DigitalOutputError):
            chamber.dryer = 1


class TypedGradientTests(unittest.TestCase):
    def new_chamber(self):
        chamber = object.__new__(ClimateChamber)
        chamber._temperature_min = -40.0
        chamber._temperature_max = 100.0
        chamber._temp_round = 2
        self.calls = []
        chamber.query = lambda command, *args: self.calls.append((command, args)) or ["0"]
        return chamber

    def test_limits_are_exposed_read_only(self):
        chamber = self.new_chamber()
        self.assertEqual(GRADIENT_UP_LIMITS_C_PER_MIN, (0.01, 5.0))
        self.assertEqual(GRADIENT_DOWN_LIMITS_C_PER_MIN, (0.01, 3.5))
        self.assertEqual(chamber.gradient_up_range, (0.01, 5.0))
        self.assertEqual(chamber.gradient_down_range, (0.01, 3.5))
        self.assertEqual(self.calls, [])

    def test_out_of_range_gradients_never_reach_io(self):
        chamber = self.new_chamber()
        for value in (0.0, 5.01, float("inf"), float("nan"), True):
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                chamber.gradient_up = value
        for value in (0.0, 3.51, float("-inf"), "hot"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                chamber.gradient_down = value
        self.assertEqual(self.calls, [])

    def test_valid_gradients_send_manual_commands(self):
        chamber = self.new_chamber()
        chamber.gradient_up = 2.5
        chamber.gradient_down = "1.5"
        self.assertEqual(self.calls, [
            ("SET GRADIENT_UP VALUE", (1, "2.5")),
            ("SET GRADIENT_DOWN VALUE", (1, "1.5")),
        ])


if __name__ == "__main__":
    unittest.main()
