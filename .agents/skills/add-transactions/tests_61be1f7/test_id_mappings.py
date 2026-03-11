"""Tests for id_mappings.yml contents and regex validity.

Uses pydantic-yaml models to parse and validate file structure, then
ensures every declared regular expression compiles.
"""

import re

import pytest
from anyio import Path
from pydantic import BaseModel, RootModel
from pydantic_yaml import parse_yaml_raw_as

"""Public symbols exported by this module (none)."""
__all__ = ()


class IdMapping(BaseModel):
    """Model representing the mapping for a single payee, including order and regex patterns."""

    orders: list[list[str]] = []
    regex: dict[str, str] = {}


class Mappings(RootModel[dict[str, IdMapping]]):
    """Root model wrapping the mapping of payees to id mappings."""


async def load_id_mappings() -> Mappings:
    """Load and validate the YAML file as a root model."""
    path = Path(__file__).parents[1] / "id_mappings.yml"
    text = await path.read_text(encoding="utf-8")
    return parse_yaml_raw_as(Mappings, text)


@pytest.mark.anyio
async def test_all_regex_compile() -> None:
    """Every regex string in the file must compile successfully."""
    mappings_root = await load_id_mappings()
    mappings = mappings_root.root
    for payee, entry in mappings.items():
        # verify model types were correctly populated
        assert isinstance(entry.orders, list)
        assert isinstance(entry.regex, dict)
        for name, pattern in entry.regex.items():
            assert isinstance(pattern, str), (
                f"pattern for {payee}.{name} is not a string (got {type(pattern)})"
            )
            try:
                re.compile(pattern)
            except re.error as exc:
                pytest.fail(f"invalid regex for {payee}.{name}: {exc}")
