.PHONY: docs

docs:
	PYTHONPATH=. pydocmd simple crew.task++  crew.context++ > docs/api.md
