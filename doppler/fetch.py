"""Download ESC-50 from its original source. The audio is never redistributed by this repo."""
import io, os, urllib.request, zipfile
from pathlib import Path
from .common import DATA, config, esc50_root

def _complete(root):
    audio = root / "audio"
    return audio.is_dir() and len(list(audio.glob("*.wav"))) == 2000

def main():
    dest = esc50_root()
    if _complete(dest):
        print("ESC-50 already present:", dest)
        return
    url = config()["data"]["esc50_url"]
    print("downloading", url)
    # GitHub answers a bare urllib client with 403.
    req = urllib.request.Request(url, headers={"User-Agent": "ai-video-doppler-check"})
    raw = urllib.request.urlopen(req, timeout=600).read()
    DATA.mkdir(parents=True, exist_ok=True)
    root = DATA.resolve()
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        for info in zf.infolist():
            name = info.filename
            if name.startswith("/") or ".." in Path(name).parts:
                raise SystemExit(f"refusing zip entry {name}")
            target = (root / name).resolve()
            if os.path.commonpath([str(root), str(target)]) != str(root):
                raise SystemExit(f"refusing zip entry {name}")
        zf.extractall(root)
    got = esc50_root()
    n = len(list((got / "audio").glob("*.wav"))) if (got / "audio").is_dir() else 0
    if n != 2000:
        raise SystemExit(f"expected 2000 wav files after extract, found {n} in {got}")
    print("extracted to", got)

if __name__ == "__main__":
    main()
