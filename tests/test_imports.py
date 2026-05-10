"""Smoke tests for the `foresight` package and its subpackages.

These verify that the agreed layout (single top-level `foresight` package
with `core`, `agents`, `api`, `worker` subpackages) actually resolves under
the installed/editable environment. Catches regressions of the E1.S2
single-package contract.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "foresight",
        "foresight.core",
        "foresight.agents",
        "foresight.api",
        "foresight.worker",
    ],
)
def test_subpackage_importable(module_name: str) -> None:
    """Each subpackage must import cleanly and have a non-empty docstring."""
    module = importlib.import_module(module_name)
    assert module.__doc__, f"{module_name} must ship a module docstring."


def test_foresight_version() -> None:
    import foresight

    assert isinstance(foresight.__version__, str)
    assert foresight.__version__ == "0.1.0"
