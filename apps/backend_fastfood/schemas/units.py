"""Discrete-unit quantities; digit strings keep older POS payloads compatible."""
from typing import Annotated
from pydantic import BeforeValidator


def parse_units(value):
    if type(value) is int:
        return value
    if isinstance(value, str) and value.isascii() and value.isdigit():
        return int(value)
    raise ValueError("Quantity must be a whole integer; decimal quantities are not accepted.")


Units = Annotated[int, BeforeValidator(parse_units)]
