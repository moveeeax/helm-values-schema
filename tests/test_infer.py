import yaml

from helm_values_schema.infer import infer_schema, merge_schemas


def _schema(text):
    return infer_schema(yaml.safe_load(text))


def test_scalar_types():
    text = """
    name: nginx
    replicas: 3
    ratio: 0.5
    enabled: true
    extra: null
    """
    props = _schema(text)["properties"]
    assert props["name"] == {"type": "string"}
    assert props["replicas"] == {"type": "integer"}
    assert props["ratio"] == {"type": "number"}
    assert props["enabled"] == {"type": "boolean"}
    assert props["extra"] == {"type": "null"}


def test_bool_is_not_integer():
    # bool subclasses int in Python; the inferrer must not report it as integer.
    assert infer_schema(True) == {"type": "boolean"}
    assert infer_schema(1) == {"type": "integer"}


def test_nested_maps():
    text = """
    image:
      repository: nginx
      tag: "1.25"
      pull:
        policy: IfNotPresent
    """
    schema = _schema(text)
    image = schema["properties"]["image"]
    assert image["type"] == "object"
    assert image["properties"]["repository"] == {"type": "string"}
    pull = image["properties"]["pull"]
    assert pull["type"] == "object"
    assert pull["properties"]["policy"] == {"type": "string"}


def test_homogeneous_array():
    schema = _schema("ports: [80, 443, 8080]")
    ports = schema["properties"]["ports"]
    assert ports["type"] == "array"
    assert ports["items"] == {"type": "integer"}


def test_array_of_objects_merges_properties():
    text = """
    containers:
      - name: a
        image: nginx
      - name: b
        port: 80
    """
    items = _schema(text)["properties"]["containers"]["items"]
    assert items["type"] == "object"
    props = items["properties"]
    assert set(props) == {"name", "image", "port"}
    assert props["port"] == {"type": "integer"}


def test_mixed_scalar_array_becomes_union():
    schema = _schema("mixed: [1, two, 3.0]")
    items = schema["properties"]["mixed"]["items"]
    assert items["type"] == ["integer", "number", "string"]


def test_array_with_null_element():
    schema = _schema("maybe: [1, null]")
    assert schema["properties"]["maybe"]["items"]["type"] == ["null", "integer"]


def test_empty_array_has_no_items():
    schema = _schema("empty: []")
    assert schema["properties"]["empty"] == {"type": "array"}


def test_additional_properties_flag_propagates():
    schema = infer_schema({"a": {"b": 1}}, additional_properties=True)
    assert schema["additionalProperties"] is True
    assert schema["properties"]["a"]["additionalProperties"] is True


def test_merge_single_schema_is_identity():
    assert merge_schemas([{"type": "string"}]) == {"type": "string"}
