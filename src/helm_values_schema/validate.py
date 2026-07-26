"""Validate a values document against a generated JSON Schema."""

from __future__ import annotations

from typing import Any, Dict, List

import yaml
from jsonschema import Draft7Validator


class ValidationError(Exception):
    """Raised for problems that stop validation from running at all."""


def _format_path(path) -> str:
    if not path:
        return "(root)"
    out = ""
    for part in path:
        if isinstance(part, int):
            out += "[%d]" % part
        else:
            out += ("." if out else "") + str(part)
    return out


def validate_values(values: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Return a list of human-readable error strings (empty when valid)."""
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(values), key=lambda e: list(e.path))
    return ["%s: %s" % (_format_path(e.path), e.message) for e in errors]


def load_yaml(text: str) -> Dict[str, Any]:
    data = yaml.safe_load(text)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValidationError("values document must be a mapping")
    return data
