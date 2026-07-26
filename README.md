# helm-values-schema

[![ci](https://github.com/moveeeax/helm-values-schema/actions/workflows/ci.yml/badge.svg)](https://github.com/moveeeax/helm-values-schema/actions/workflows/ci.yml)
[![python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![license: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Give your Helm chart a `values.schema.json` so bad overrides fail fast — before
`helm install` ever renders a template.

`helm-values-schema` reads a chart's `values.yaml`, infers a
[JSON Schema (draft-07)](https://json-schema.org/) from its structure, and lets
you validate user-supplied override files against it. When Helm sees a
`values.schema.json` next to `Chart.yaml` it enforces the schema automatically;
this tool generates that file and gives you the same check in CI.

## Install

```bash
pip install -e .
# or, from a checkout, for development:
pip install -e ".[dev]"
```

## Usage

Generate a schema from a chart's values and write it into the chart:

```bash
helm-values-schema gen ./mychart/values.yaml -o ./mychart/values.schema.json
# or stream it to stdout:
helm-values-schema gen ./mychart/values.yaml > ./mychart/values.schema.json
```

Validate an override file against the generated schema (great in chart CI):

```bash
helm-values-schema validate ./mychart -f overrides.yaml
```

A mismatch is reported per-path and exits non-zero:

```text
$ helm-values-schema validate examples/mychart -f examples/bad-overrides.yaml
examples/bad-overrides.yaml: 3 validation error(s) against examples/mychart/values.schema.json
  - replicaCount: 0 is less than the minimum of 1
  - service.port: 70000 is greater than the maximum of 65535
  - service.type: 'Invalid' is not one of ['ClusterIP', 'NodePort', 'LoadBalancer']
```

With no `-f`, `validate` checks the chart's own `values.yaml` against its schema.

## How types are inferred

| values.yaml            | JSON Schema                                            |
| ---------------------- | ------------------------------------------------------ |
| `replicas: 3`          | `{"type": "integer"}`                                  |
| `ratio: 0.5`           | `{"type": "number"}`                                   |
| `enabled: true`        | `{"type": "boolean"}`                                  |
| `name: nginx`          | `{"type": "string"}`                                   |
| `extra: null`          | `{"type": "null"}`                                     |
| nested map             | `object` with `properties`                             |
| `ports: [80, 443]`     | `array`, `items: {"type": "integer"}`                  |
| `mixed: [1, "two"]`    | `array`, `items: {"type": ["integer", "string"]}`      |

Arrays of maps merge their element schemas, so every key that appears on any
element shows up in `items.properties`. Objects get `additionalProperties: false`
by default, which is what turns a typo like `replcaCount:` into a hard error;
pass `--additional-properties` to allow unknown keys.

## Annotations

Types and structure are inferred, but constraints Helm can't guess — required
fields, enums, numeric bounds, patterns — come from `# @schema` comments on the
key they constrain:

```yaml
replicaCount: 1            # @schema required: true; minimum: 1
image:
  pullPolicy: IfNotPresent # @schema enum: [Always, Never, IfNotPresent]
service:
  port: 80                 # @schema minimum: 1; maximum: 65535
```

Directives are `key: value` pairs separated by `;`. Supported keys: `required`,
`enum`, `type`, `minimum`, `maximum`, `exclusiveMinimum`, `exclusiveMaximum`,
`minLength`, `maxLength`, `pattern`, `format`, `const`, `default`, `description`.

See [`examples/mychart`](examples/mychart) for a full values file and its
generated schema, plus [`examples/overrides.yaml`](examples/overrides.yaml) and
[`examples/bad-overrides.yaml`](examples/bad-overrides.yaml).

## Development

```bash
make install   # editable install with dev deps
make test      # run the unit tests
make example   # regenerate + validate the example schema
```

## License

MIT — see [LICENSE](LICENSE).
