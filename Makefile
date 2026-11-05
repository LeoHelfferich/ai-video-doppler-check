PY ?= python
DATA ?= data
export DOPPLER_DATA = $(DATA)
all: fetch manifest run
fetch:
	$(PY) -m doppler.fetch
manifest:
	$(PY) -m doppler.manifest
run:
	$(PY) -m doppler.run
.PHONY: all fetch manifest run
