"""Rebuild ai_clips/manifest.csv from the videos in data/ai/.

Prompts stay in ai_clips/prompts.tsv (id, group, prompt, tab-separated). The videos are not in git.
A clip already listed in the manifest keeps its generated_on date.
"""
import csv, datetime, hashlib, json, subprocess
from .common import DATA, MANIFEST, PROMPTS

def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_type,codec_name,sample_rate,channels,duration",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    a = [s for s in json.loads(out)["streams"] if s.get("codec_type") == "audio"]
    return a[0] if a else None

def main():
    if not PROMPTS.is_file():
        raise SystemExit(f"missing {PROMPTS}")
    prompts = {}
    for line in PROMPTS.read_text().splitlines():
        if line.strip():
            i, g, p = line.split("\t", 2)
            prompts[i] = (g, p)
    ai = DATA / "ai"
    mp4s = sorted(ai.glob("*.mp4")) if ai.is_dir() else []
    if not mp4s:
        raise SystemExit(
            f"no mp4 files in {ai}. The generated clips are not in the git repository; put them there and rerun.")
    old = {}
    if MANIFEST.is_file():
        with MANIFEST.open(newline="") as f:
            old = {r["file"]: r for r in csv.DictReader(f)}
    rows = []
    for mp4 in mp4s:
        if mp4.stem not in prompts:
            raise SystemExit(f"{mp4.name} has no row in {PROMPTS}")
        g, p = prompts[mp4.stem]
        a = probe(mp4)
        date = old.get(mp4.name, {}).get("generated_on") or datetime.date.fromtimestamp(mp4.stat().st_mtime).isoformat()
        rows.append(dict(file=mp4.name, group=g, generator="Grok Imagine (text-to-video, 10 s, 480p)",
                         generated_on=date, sha256=hashlib.sha256(mp4.read_bytes()).hexdigest(),
                         has_audio=bool(a), audio_codec=a and a["codec_name"],
                         sample_rate=a and a["sample_rate"], channels=a and a["channels"],
                         audio_duration_s=a and a.get("duration"), prompt=p))
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "clips,", sum(not r["has_audio"] for r in rows), "silent, wrote", MANIFEST)

if __name__ == "__main__":
    main()
