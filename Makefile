.PHONY: docs

docs:
	PYTHONPATH=. pydocmd simple crew.task++  crew.context++ > docs/api.md

.PHONY: build

build: env
	./env/bin/pyinstaller crew.spec
