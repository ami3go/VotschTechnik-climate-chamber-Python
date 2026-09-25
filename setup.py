"""Compatibility shim for tools that still invoke ``setup.py`` directly.

Package metadata and build configuration live in ``pyproject.toml``.
"""

from setuptools import setup


if __name__ == "__main__":
    setup()
