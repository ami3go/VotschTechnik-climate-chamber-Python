import unittest

import VotschTechnikClimateChamber as package
from VotschTechnikClimateChamber.ClimateChamber import ClimateChamber


class PackageTests(unittest.TestCase):
    def test_public_api(self):
        self.assertIs(package.ClimateChamber, ClimateChamber)
        self.assertEqual(package.__version__, "0.2.0")

    def test_command_name_translation(self):
        self.assertEqual(
            package.translate_command_name_to_command_number(
                "get control_variable actual_value"
            ),
            "11004",
        )

    def test_command_encoding(self):
        self.assertEqual(
            package.create_command_string("11004", 1),
            b"11004\xb61\xb61\r",
        )


if __name__ == "__main__":
    unittest.main()
