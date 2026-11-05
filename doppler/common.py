"""Paths and config. No absolute paths: everything is relative to the repo or $DOPPLER_DATA."""
import os, tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("DOPPLER_DATA", REPO / "data")).resolve()
RESULTS = Path(os.environ.get("DOPPLER_RESULTS", REPO / "results")).resolve()
FIGS = Path(os.environ.get("DOPPLER_FIGS", RESULTS / "figures")).resolve()

def config():
    with open(REPO / "config.toml", "rb") as f:
        return tomllib.load(f)
