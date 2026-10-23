"""Public package interface for Votsch/Weiss climate chamber control."""

from .ClimateChamber import (
    COMMANDS_DICT,
    COMMANDS_LIST,
    GRADIENT_DOWN_LIMITS_C_PER_MIN,
    GRADIENT_UP_LIMITS_C_PER_MIN,
    ClimateChamber,
    DigitalOutputError,
    DigitalOutputReadbackError,
    StopNotVerified,
    create_command_string,
    translate_command_name_to_command_number,
)

__version__ = "0.3.0"

__all__ = [
    "COMMANDS_DICT",
    "COMMANDS_LIST",
    "GRADIENT_DOWN_LIMITS_C_PER_MIN",
    "GRADIENT_UP_LIMITS_C_PER_MIN",
    "ClimateChamber",
    "DigitalOutputError",
    "DigitalOutputReadbackError",
    "StopNotVerified",
    "create_command_string",
    "translate_command_name_to_command_number",
]
