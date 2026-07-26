"""Command-line entry point for ``helm-values-schema``."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional

from . import __version__
from .generate import dumps, generate_schema
from .validate import ValidationError, load_yaml, validate_values

SCHEMA_FILENAME = "values.schema.json"
VALUES_FILENAME = "values.yaml"


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _cmd_gen(args: argparse.Namespace) -> int:
    text = _read(args.values)
    schema = generate_schema(
        text,
        title=args.title,
        additional_properties=args.additional_properties,
        use_annotations=not args.no_annotations,
    )
    out = dumps(schema)
    if args.output and args.output != "-":
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(out)
        print("wrote %s" % args.output, file=sys.stderr)
    else:
        sys.stdout.write(out)
    return 0


def _resolve_validate_paths(args: argparse.Namespace):
    target = args.chart
    if os.path.isdir(target):
        schema_path = args.schema or os.path.join(target, SCHEMA_FILENAME)
        values_path = args.file or os.path.join(target, VALUES_FILENAME)
    else:
        # A schema file was passed directly; -f then supplies the values.
        schema_path = args.schema or target
        values_path = args.file
        if values_path is None:
            raise ValidationError("pass a values file with -f when validating a schema file")
    return schema_path, values_path


def _cmd_validate(args: argparse.Namespace) -> int:
    schema_path, values_path = _resolve_validate_paths(args)
    if not os.path.exists(schema_path):
        raise ValidationError(
            "schema not found at %s (run `helm-values-schema gen` first)" % schema_path
        )
    if not os.path.exists(values_path):
        raise ValidationError("values file not found at %s" % values_path)

    schema = json.loads(_read(schema_path))
    values = load_yaml(_read(values_path))
    errors = validate_values(values, schema)

    if errors:
        print(
            "%s: %d validation error(s) against %s"
            % (values_path, len(errors), schema_path),
            file=sys.stderr,
        )
        for message in errors:
            print("  - %s" % message, file=sys.stderr)
        return 1

    print("%s: valid against %s" % (values_path, schema_path))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="helm-values-schema",
        description="Generate and enforce a JSON Schema for Helm chart values.",
    )
    parser.add_argument("--version", action="version", version="%(prog)s " + __version__)
    sub = parser.add_subparsers(dest="command")

    gen = sub.add_parser("gen", help="infer a values.schema.json from a values.yaml")
    gen.add_argument("values", help="path to values.yaml")
    gen.add_argument("-o", "--output", help="write schema here instead of stdout")
    gen.add_argument("--title", default="Helm values schema", help="schema title")
    gen.add_argument(
        "--additional-properties",
        action="store_true",
        help="allow keys not present in values.yaml (default: reject them)",
    )
    gen.add_argument(
        "--no-annotations",
        action="store_true",
        help="ignore `# @schema` comment annotations",
    )
    gen.set_defaults(func=_cmd_gen)

    val = sub.add_parser("validate", help="validate values against a schema")
    val.add_argument("chart", help="chart directory (or a schema file)")
    val.add_argument("-f", "--file", help="values file to validate (default: <chart>/values.yaml)")
    val.add_argument("--schema", help="schema file (default: <chart>/values.schema.json)")
    val.set_defaults(func=_cmd_validate)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help(sys.stderr)
        return 2
    try:
        return args.func(args)
    except (ValidationError, ValueError, OSError) as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
