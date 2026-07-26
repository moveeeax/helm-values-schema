from helm_values_schema.annotations import parse_annotations
from helm_values_schema.generate import generate_schema


def test_parse_simple_annotation():
    text = "replicaCount: 1  # @schema required: true; minimum: 1\n"
    ann = parse_annotations(text)
    assert ann["replicaCount"] == {"required": True, "minimum": 1}


def test_parse_nested_path():
    text = (
        "image:\n"
        "  pullPolicy: IfNotPresent  # @schema enum: [Always, Never, IfNotPresent]\n"
    )
    ann = parse_annotations(text)
    assert ann["image.pullPolicy"]["enum"] == ["Always", "Never", "IfNotPresent"]


def test_required_and_enum_applied_to_schema():
    text = (
        "replicaCount: 1  # @schema required: true\n"
        "image:\n"
        "  pullPolicy: IfNotPresent  # @schema enum: [Always, Never, IfNotPresent]\n"
    )
    schema = generate_schema(text)
    assert schema["required"] == ["replicaCount"]
    assert (
        schema["properties"]["image"]["properties"]["pullPolicy"]["enum"]
        == ["Always", "Never", "IfNotPresent"]
    )


def test_type_override():
    # An empty-ish value that we want to force to a specific type.
    text = 'tag: ""  # @schema type: string; pattern: "^v?[0-9]"\n'
    schema = generate_schema(text)
    tag = schema["properties"]["tag"]
    assert tag["type"] == "string"
    assert tag["pattern"] == "^v?[0-9]"


def test_annotation_for_unknown_key_is_ignored():
    text = "known: 1  # @schema required: true\n"
    schema = generate_schema(text)
    # Nothing references a missing key, so required only lists what exists.
    assert schema.get("required") == ["known"]


def test_no_annotations_flag_disables_parsing():
    text = "replicaCount: 1  # @schema required: true\n"
    schema = generate_schema(text, use_annotations=False)
    assert "required" not in schema
