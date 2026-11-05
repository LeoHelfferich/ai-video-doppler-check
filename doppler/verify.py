"""Check data/ai/*.mp4 against the sha256 column in ai_clips/manifest.csv."""
import csv, hashlib
from .common import DATA, MANIFEST

def manifest_rows():
    if not MANIFEST.is_file():
        raise SystemExit(f"missing {MANIFEST}")
    with MANIFEST.open(newline="") as f:
        return list(csv.DictReader(f))

def diff_checksums(rows, digests):
    """digests maps a filename to its sha256. A missing file is absent from the map."""
    missing, mismatched = [], []
    for r in rows:
        got = digests.get(r["file"])
        if got is None:
            missing.append(r["file"])
        elif got != r["sha256"]:
            mismatched.append((r["file"], got))
    return missing, mismatched

def verify_ai():
    rows = manifest_rows()
    digests = {}
    for r in rows:
        path = DATA / "ai" / r["file"]
        if path.is_file():
            digests[r["file"]] = hashlib.sha256(path.read_bytes()).hexdigest()
    missing, mismatched = diff_checksums(rows, digests)
    if not missing and not mismatched:
        print(len(rows), "generated clips match", MANIFEST)
        return
    lines = ["The files in data/ai/ do not match ai_clips/manifest.csv."]
    if missing:
        lines.append("Missing:")
        lines += [f"  {name}" for name in missing]
        lines.append("Those videos are not in the git repository. Put the originals in data/ai/.")
    if mismatched:
        lines.append("sha256 mismatch:")
        lines += [f"  {name} is {digest}" for name, digest in mismatched]
    raise SystemExit("\n".join(lines))

def main():
    verify_ai()

if __name__ == "__main__":
    main()
