.PHONY: docs

docs:
	PYTHONPATH=. pydocmd simple pitcrew.task++  pitcrew.context++ pitcrew.file++ > docs/api.md

.PHONY: build

build:
	./env/bin/pyinstaller pitcrew.spec
