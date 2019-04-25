.PHONY: docs

docs:
	PYTHONPATH=. pydocmd simple pitcrew.task++  pitcrew.context++ > docs/api.md

.PHONY: build

build:
	./env/bin/pyinstaller pitcrew.spec
