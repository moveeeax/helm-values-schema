import json

import pytest

from helm_values_schema.cli import main

VALUES = (
    "replicaCount: 1  # @schema required: true; minimum: 1\n"
    "image:\n"
    "  repository: nginx\n"
    "  pullPolicy: IfNotPresent  # @schema enum: [Always, Never, IfNotPresent]\n"
    "service:\n"
    "  port: 80\n"
)


@pytest.fixture()
def chart(tmp_path):
    (tmp_path / "values.yaml").write_text(VALUES)
    return tmp_path


def test_gen_to_stdout(chart, capsys):
    rc = main(["gen", str(chart / "values.yaml")])
    assert rc == 0
    schema = json.loads(capsys.readouterr().out)
    assert schema["$schema"].endswith("draft-07/schema#")
    assert schema["required"] == ["replicaCount"]


def test_gen_to_file_and_validate(chart, capsys):
    schema_path = chart / "values.schema.json"
    assert main(["gen", str(chart / "values.yaml"), "-o", str(schema_path)]) == 0
    assert schema_path.exists()
    assert main(["validate", str(chart)]) == 0
    assert "valid against" in capsys.readouterr().out


def test_validate_catches_bad_override(chart):
    assert main(["gen", str(chart / "values.yaml"), "-o", str(chart / "values.schema.json")]) == 0
    bad = chart / "bad.yaml"
    bad.write_text("replicaCount: 1\nimage:\n  repository: nginx\n  pullPolicy: Sometimes\nservice:\n  port: 80\n")
    assert main(["validate", str(chart), "-f", str(bad)]) == 1


def test_missing_schema_errors(chart):
    assert main(["validate", str(chart)]) == 2


def test_no_subcommand_returns_usage():
    assert main([]) == 2
