"""Parse ``# @schema`` annotations out of a raw ``values.yaml`` document.

PyYAML discards comments, so constraints that can't be inferred from a value —
``required``, ``enum``, numeric bounds, an explicit ``type`` — are read straight
from the source text. An annotation lives in a trailing comment on the key it
constrains::

    replicaCount: 1            # @schema required: true; minimum: 1
    image:
      pullPolicy: IfNotPresent # @schema enum: [Always, Never, IfNotPresent]

Directives are ``key: value`` pairs separated by ``;``. Each value is parsed as a
YAML scalar/sequence, so ``true``, ``0``, ``"str"`` and ``[a, b]`` all work. The
parser tracks indentation to build the dotted path (``image.pullPolicy``) that
ties an annotation back to a node in the inferred schema.
"""

from __future__ import annotations

import re
from typing import Any, Dict

import yaml

_KEY_RE = re.compile(r"^(?P<key>[\w.\-/]+)\s*:(?:\s|$)")
_ANNOTATION_RE = re.compile(r"#\s*@schema\s+(?P<body>.+?)\s*$")

# Directives that map straight onto a schema node.
_KEYWORDS = {
    "enum",
    "type",
    "minimum",
    "maximum",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "minLength",
    "maxLength",
    "pattern",
    "format",
    "description",
    "default",
    "const",
}


def parse_directives(body: str) -> Dict[str, Any]:
    """Turn ``required: true; enum: [a, b]`` into a directive dict."""
    directives: Dict[str, Any] = {}
    for part in body.split(";"):
        part = part.strip()
        if not part or ":" not in part:
            continue
        name, _, raw = part.partition(":")
        name = name.strip()
        raw = raw.strip()
        try:
            value = yaml.safe_load(raw)
        except yaml.YAMLError:
            value = raw
        if name == "required":
            directives["required"] = bool(value)
        elif name in _KEYWORDS:
            directives[name] = value
    return directives


def parse_annotations(text: str) -> Dict[str, Dict[str, Any]]:
    """Map dotted key paths to their parsed ``@schema`` directives."""
    annotations: Dict[str, Dict[str, Any]] = {}
    stack = []  # list of (indent, key)

    for raw_line in text.splitlines():
        if not raw_line.strip():
            continue
        stripped = raw_line.lstrip(" ")
        indent = len(raw_line) - len(stripped)

        # Skip full-line comments and sequence items (list scalars have no key).
        if stripped.startswith("#") or stripped.startswith("- "):
            continue

        match = _KEY_RE.match(stripped)
        if not match:
            continue
        key = match.group("key")

        while stack and stack[-1][0] >= indent:
            stack.pop()
        stack.append((indent, key))

        ann = _ANNOTATION_RE.search(raw_line)
        if ann:
            directives = parse_directives(ann.group("body"))
            if directives:
                path = ".".join(k for _, k in stack)
                annotations[path] = directives

    return annotations


def apply_annotations(
    schema: Dict[str, Any], annotations: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """Apply parsed directives onto the inferred ``schema`` in place."""
    for path, directives in annotations.items():
        segments = path.split(".")
        node = schema
        ok = True
        for segment in segments:
            props = node.get("properties") if isinstance(node, dict) else None
            if not props or segment not in props:
                ok = False
                break
            node = props[segment]
        if not ok:
            continue

        for name, value in directives.items():
            if name == "required":
                continue
            node[name] = value

        if directives.get("required"):
            parent = schema
            for segment in segments[:-1]:
                parent = parent["properties"][segment]
            required = parent.setdefault("required", [])
            leaf = segments[-1]
            if leaf not in required:
                required.append(leaf)

    return schema
