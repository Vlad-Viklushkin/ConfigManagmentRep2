PYTHON ?= python3
CONFIG ?= config.toml

export PYTHONPATH := src

.PHONY: run test demo-errors clean

run:
	$(PYTHON) -m depviz --config $(CONFIG)

test:
	$(PYTHON) -m unittest discover -s tests -v

demo-errors:
	@for f in examples/invalid/*.toml; do \
		echo "== $$f"; \
		$(PYTHON) -m depviz --config $$f; \
		echo "код завершения: $$?"; \
	done; true

clean:
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
