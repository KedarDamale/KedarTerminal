.PHONY: test check build doctor
test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v
check:
	python3 -m compileall -q src scripts
build:
	python3 scripts/kedar-terminal build
doctor:
	python3 scripts/kedar-terminal doctor
