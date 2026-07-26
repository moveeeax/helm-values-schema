from helm_values_schema.generate import generate_schema
from helm_values_schema.validate import load_yaml, validate_values

VALUES = """
replicaCount: 1  # @schema required: true; minimum: 1
image:
  repository: nginx
  pullPolicy: IfNotPresent  # @schema enum: [Always, Never, IfNotPresent]
service:
  port: 80
"""


def _schema():
    return generate_schema(VALUES)


def test_matching_values_validate_clean():
    errors = validate_values(load_yaml(VALUES), _schema())
    assert errors == []


def test_type_mismatch_is_caught():
    bad = load_yaml("replicaCount: 1\nimage:\n  repository: nginx\n  pullPolicy: IfNotPresent\nservice:\n  port: not-a-number\n")
    errors = validate_values(bad, _schema())
    assert any("service.port" in e for e in errors)


def test_enum_violation_is_caught():
    bad = load_yaml("replicaCount: 1\nimage:\n  repository: nginx\n  pullPolicy: Sometimes\nservice:\n  port: 80\n")
    errors = validate_values(bad, _schema())
    assert any("image.pullPolicy" in e for e in errors)


def test_minimum_violation_is_caught():
    bad = load_yaml("replicaCount: 0\nimage:\n  repository: nginx\n  pullPolicy: Always\nservice:\n  port: 80\n")
    errors = validate_values(bad, _schema())
    assert any("replicaCount" in e for e in errors)


def test_unknown_key_rejected_by_default():
    bad = load_yaml("replicaCount: 1\nimage:\n  repository: nginx\n  pullPolicy: Always\nservice:\n  port: 80\ntypo: 1\n")
    errors = validate_values(bad, _schema())
    assert errors  # additionalProperties: false flags the stray key


def test_unknown_key_allowed_when_additional_properties():
    schema = generate_schema(VALUES, additional_properties=True)
    values = load_yaml("replicaCount: 1\nimage:\n  repository: nginx\n  pullPolicy: Always\nservice:\n  port: 80\nextra: 1\n")
    assert validate_values(values, schema) == []


def test_gen_then_validate_roundtrip():
    schema = _schema()
    assert validate_values(load_yaml(VALUES), schema) == []
