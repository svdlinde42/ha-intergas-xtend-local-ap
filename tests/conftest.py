"""Shared pytest configuration for the Intergas Xtend tests.

Run the suite on Linux (WSL or CI). Home Assistant core imports Unix-only modules
such as fcntl and does not load on Windows.
"""

from __future__ import annotations
