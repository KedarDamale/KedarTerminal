.DEFAULT_GOAL := help
PYTHON ?= python3
MODE ?= animated
# Optional: make update PROFILE=.cache/profile FRAMES=.cache/frames
PROFILE ?=
FRAMES ?=
CLI = $(PYTHON) scripts/kedar-terminal $(if $(PROFILE),--profile "$(PROFILE)") $(if $(FRAMES),--frames "$(FRAMES)")

.PHONY: help deps setup set update install build doctor launch static test check
help:
	@echo 'make setup  Install Ubuntu dependencies, sync profile, prepare frames, and check setup'
	@echo 'make update Apply changed files and rebuild frames only when needed'
	@echo 'make launch Open the animated terminal; make static opens the static theme'
	@echo 'Close managed terminal windows before setup/update. Run make as your own user.'
deps:
	sudo apt-get update
	sudo apt-get install -y kitty fish starship fonts-firacode fonts-noto-core python3-pil fontconfig
setup:
	$(MAKE) deps
	$(MAKE) update
set: setup
update:
	$(CLI) install
	$(CLI) build --if-needed
	$(CLI) doctor
install:
	$(CLI) install
launch:
	$(CLI) launch --mode "$(MODE)"
static:
	$(CLI) launch --mode static
test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v
check:
	$(PYTHON) -m compileall -q src scripts
build:
	$(CLI) build --if-needed
doctor:
	$(CLI) doctor
