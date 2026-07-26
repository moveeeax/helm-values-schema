"""Generate a complete ``values.schema.json`` document from a values file."""

from __future__ import annotations

import json
from typing import Any, Dict

import yaml

from .annotations import apply_annotations, parse_annotations
from .infer import SCHEMA_DRAFT, infer_schema


def generate_schema(
    text: str,
    *,
    title: str = "Helm values schema",
    additional_properties: bool = False,
    use_annotations: bool = True,
) -> Dict[str, Any]:
    """Build a draft-07 schema from the raw text of a ``values.yaml`` file."""
    data = yaml.safe_load(text)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError("top-level values.yaml must be a mapping")

    schema = infer_schema(data, additional_properties=additional_properties)
    schema["$schema"] = SCHEMA_DRAFT
    schema["title"] = title

    if use_annotations:
        annotations = parse_annotations(text)
        apply_annotations(schema, annotations)

    # Put the meta keys first for readable output.
    ordered = {"$schema": schema.pop("$schema"), "title": schema.pop("title")}
    ordered.update(schema)
    return ordered


def dumps(schema: Dict[str, Any]) -> str:
    """Serialise a schema to stable, pretty JSON with a trailing newline."""
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
