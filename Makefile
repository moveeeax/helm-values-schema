.PHONY: install test lint example clean

install:
	python -m pip install -e ".[dev]"

test:
	pytest -q

# Regenerate the committed example schema and confirm the sample values pass.
example:
	helm-values-schema gen examples/mychart/values.yaml -o examples/mychart/values.schema.json
	helm-values-schema validate examples/mychart

clean:
	rm -rf build dist *.egg-info src/*.egg-info .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
