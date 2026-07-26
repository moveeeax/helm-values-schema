"""Infer a JSON Schema (draft-07) from parsed Helm ``values.yaml`` data.

The inference is deliberately structural: every value in the document maps to a
schema node. Scalars become typed leaves, maps become ``object`` schemas with
``properties``, and arrays become ``array`` schemas whose ``items`` schema is the
merge of every element's schema. Mixed element types collapse into a JSON Schema
type union so ``[1, "two"]`` yields ``{"type": ["integer", "string"]}``.
"""

from __future__ import annotations

from typing import Any, Dict, List

SCHEMA_DRAFT = "http://json-schema.org/draft-07/schema#"

# Order used when serialising a type union so output is deterministic.
_TYPE_ORDER = ["null", "boolean", "integer", "number", "string", "array", "object"]


def _scalar_type(value: Any) -> str:
    # bool must be checked before int: in Python ``bool`` is a subclass of ``int``.
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    raise TypeError("unsupported scalar type: %r" % type(value))


def infer_schema(value: Any, *, additional_properties: bool = False) -> Dict[str, Any]:
    """Return the JSON Schema node describing ``value``."""
    if isinstance(value, dict):
        properties: Dict[str, Any] = {}
        for key, item in value.items():
            properties[str(key)] = infer_schema(
                item, additional_properties=additional_properties
            )
        return {
            "type": "object",
            "properties": properties,
            "additionalProperties": additional_properties,
        }

    if isinstance(value, list):
        if not value:
            return {"type": "array"}
        item_schemas = [
            infer_schema(v, additional_properties=additional_properties) for v in value
        ]
        return {"type": "array", "items": merge_schemas(item_schemas)}

    return {"type": _scalar_type(value)}


def _collect_types(schema: Dict[str, Any], out: List[str]) -> None:
    t = schema.get("type")
    if isinstance(t, list):
        for item in t:
            if item not in out:
                out.append(item)
    elif t is not None and t not in out:
        out.append(t)


def merge_schemas(schemas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge a list of schema nodes into a single node.

    Objects merge property-by-property (recursively), arrays merge their item
    schemas, and scalars collapse into a sorted type union.
    """
    if not schemas:
        return {}
    if len(schemas) == 1:
        return schemas[0]

    types: List[str] = []
    for schema in schemas:
        _collect_types(schema, types)

    if types == ["object"]:
        merged_props: Dict[str, Any] = {}
        additional = False
        for schema in schemas:
            if schema.get("additionalProperties"):
                additional = True
            for key, prop in schema.get("properties", {}).items():
                if key in merged_props:
                    merged_props[key] = merge_schemas([merged_props[key], prop])
                else:
                    merged_props[key] = prop
        return {
            "type": "object",
            "properties": merged_props,
            "additionalProperties": additional,
        }

    if types == ["array"]:
        item_schemas = [s["items"] for s in schemas if "items" in s]
        if item_schemas:
            return {"type": "array", "items": merge_schemas(item_schemas)}
        return {"type": "array"}

    ordered = sorted(types, key=lambda t: _TYPE_ORDER.index(t) if t in _TYPE_ORDER else 99)
    if len(ordered) == 1:
        return {"type": ordered[0]}
    return {"type": ordered}
