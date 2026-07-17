# helm-values-schema

> Give your Helm chart a values.schema.json so bad overrides fail fast.

**Status:** 🚧 In development

## Overview

Generate a JSON Schema from a Helm chart's values.yaml to validate user-supplied values.

## Features

- Infer types/structure from `values.yaml` (including nested maps and arrays)
- Emit a draft-07 `values.schema.json`
- Support annotations/overrides for required fields and enums
- Validate a sample values file against the generated schema
- CLI usable in chart CI

## Stack

Python 3.11, PyYAML, `jsonschema`.

## Usage

```bash
helm-values-schema gen ./mychart/values.yaml > mychart/values.schema.json
helm-values-schema validate ./mychart -f overrides.yaml
```

## License

MIT
