"""Download ESC-50 from its original source. The audio is never redistributed by this repo."""
import io, urllib.request, zipfile
from .common import DATA, config

def main():
    dest = DATA / "ESC-50-master"
    if (dest / "audio").is_dir() and len(list((dest / "audio").glob("*.wav"))) == 2000:
        print("ESC-50 already present:", dest); return
    url = config()["data"]["esc50_url"]
    print("downloading", url)
    raw = urllib.request.urlopen(url, timeout=600).read()
    DATA.mkdir(parents=True, exist_ok=True)
    zipfile.ZipFile(io.BytesIO(raw)).extractall(DATA)
    print("extracted to", dest)

if __name__ == "__main__":
    main()
