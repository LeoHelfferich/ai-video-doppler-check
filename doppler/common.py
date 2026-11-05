"""Paths and config. No absolute paths: everything is relative to the repo or $DOPPLER_DATA."""
import os, sys
from pathlib import Path

if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11 or newer is required (config.toml is read with tomllib).")
import tomllib

REPO = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("DOPPLER_DATA", REPO / "data")).resolve()
RESULTS = Path(os.environ.get("DOPPLER_RESULTS", REPO / "results")).resolve()
FIGS = Path(os.environ.get("DOPPLER_FIGS", RESULTS / "figures")).resolve()
MANIFEST = REPO / "ai_clips" / "manifest.csv"
PROMPTS = REPO / "ai_clips" / "prompts.tsv"

def config():
    with open(REPO / "config.toml", "rb") as f:
        return tomllib.load(f)

def esc50_root():
    """Directory that holds meta/esc50.csv. Accepts the pinned checkout and an older master.zip unpack."""
    if DATA.is_dir():
        found = [p for p in sorted(DATA.iterdir()) if p.is_dir() and (p / "meta" / "esc50.csv").is_file()]
        for p in found:
            if p.name == "ESC-50":
                return p
        if found:
            return found[0]
    return DATA / "ESC-50"
