"""Build data/ai/manifest.csv: file, group, prompt, generation date, sha256, audio stream info.
Input: data/ai/*.mp4 and data/ai/prompts.tsv (id<TAB>group<TAB>prompt)."""
import csv, datetime, hashlib, json, subprocess
from .common import DATA

def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_type,codec_name,sample_rate,channels,duration",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    a = [s for s in json.loads(out)["streams"] if s.get("codec_type") == "audio"]
    return a[0] if a else None

def main():
    ai = DATA / "ai"
    prompts = {}
    for line in (ai / "prompts.tsv").read_text().splitlines():
        if line.strip():
            i, g, p = line.split("\t", 2); prompts[i] = (g, p)
    old = {}
    if (ai / "manifest.csv").exists():
        old = {r["file"]: r for r in csv.DictReader(open(ai / "manifest.csv"))}
    rows = []
    for mp4 in sorted(ai.glob("*.mp4")):
        g, p = prompts[mp4.stem]
        a = probe(mp4)
        date = old.get(mp4.name, {}).get("generated_on") or \
            datetime.date.fromtimestamp(mp4.stat().st_mtime).isoformat()
        rows.append(dict(file=mp4.name, group=g, generator="Grok Imagine (text-to-video, 10 s, 480p)",
                         generated_on=date, sha256=hashlib.sha256(mp4.read_bytes()).hexdigest(),
                         has_audio=bool(a), audio_codec=a and a["codec_name"],
                         sample_rate=a and a["sample_rate"], channels=a and a["channels"],
                         audio_duration_s=a and a.get("duration"), prompt=p))
    with open(ai / "manifest.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(len(rows), "clips,", sum(not r["has_audio"] for r in rows), "silent")

if __name__ == "__main__":
    main()
