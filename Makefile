PY ?= python3
DATA ?= data
export DOPPLER_DATA = $(DATA)
all: fetch run
fetch:
	$(PY) -m doppler.fetch
manifest:
	$(PY) -m doppler.manifest
verify:
	$(PY) -m doppler.verify
run:
	$(PY) -m doppler.run
pages:
	mkdir -p docs/figures
	cp results/figures/01_hero_ki_doppler.png results/figures/02_raster_echt_vs_ki.png results/figures/03_fehlerquoten_regel.png docs/figures/
.PHONY: all fetch manifest verify run pages
