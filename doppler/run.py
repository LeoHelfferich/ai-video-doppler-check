"""Single entry point: python -m doppler.run  -> results/*.csv, results/summary.json, results/figures/*.png"""
import copy, csv, json
import numpy as np
from . import figures, physics
from .common import DATA, RESULTS, FIGS, MANIFEST, config, esc50_root
from .detect import analyze
from .verify import verify_ai

def clip_list(cfg):
    d = cfg["data"]
    esc = esc50_root()
    meta_path = esc / "meta" / "esc50.csv"
    if not meta_path.is_file():
        raise SystemExit(f"ESC-50 metadata not found at {meta_path}. Run: python -m doppler.fetch")
    with meta_path.open(newline="") as f:
        meta = list(csv.DictReader(f))
    out = [("real_plane", m["category"], esc / "audio" / m["filename"]) for m in
           sorted(meta, key=lambda m: m["filename"]) if m["category"] == d["real_plane_class"]]
    for c in d["real_noplane_classes"]:
        fs = sorted(m["filename"] for m in meta if m["category"] == c)
        o = d["real_noplane_offset"]
        out += [("real_noplane", c, esc / "audio" / f) for f in fs[o:o + d["real_noplane_per_class"]]]
    with MANIFEST.open(newline="") as f:
        ai_rows = list(csv.DictReader(f))
    for r in ai_rows:
        if r["has_audio"] == "True":
            out.append(("ai_plane" if r["group"] == "P" else "ai_noplane", "grok_imagine", DATA / "ai" / r["file"]))
    return out

def main():
    cfg = config()
    verify_ai()
    RESULTS.mkdir(parents=True, exist_ok=True); FIGS.mkdir(parents=True, exist_ok=True)
    rows, keep = [], {}
    hcfg = copy.deepcopy(cfg); ht = cfg["physics"]["harmonic_tracking"]
    hcfg["doppler"]["max_jitter_hz"] = ht["max_jitter_hz"]; hcfg["ridge"]["max_jump_hz_per_s"] = ht["max_jump_hz_per_s"]
    for group, cls, path in clip_list(cfg):
        res = analyze(path, cfg); ph = physics.check(res, cfg, analyze(path, hcfg)["tracks"]) if res["has_doppler"] else {}
        m = res["tracks"][0] if res["tracks"] else {}
        fit = ph.get("fit") or {}
        rows.append(dict(group=group, cls=cls, file=path.name, has_doppler=res["has_doppler"],
                         n_tracks=len(res["tracks"]), f_start=m.get("f_start"), f_end=m.get("f_end"),
                         duration_s=m.get("duration_s"), ratio=m.get("ratio"),
                         v_ratio=ph.get("v_ratio"), v_fit=fit.get("v"), r2_fit=fit.get("r2"), r2_linear=fit.get("r2_linear"),
                         n_pairs=ph.get("n_pairs"), n_const_pairs=ph.get("n_const_pairs"), median_ratio_cv=ph.get("median_cv"),
                         best_pair_ratio=(ph.get("best_pair") or {}).get("ratio"), best_pair_cv=(ph.get("best_pair") or {}).get("cv")))
        keep[(group, path.name)] = res
        print(group, path.name, res["has_doppler"], len(res["tracks"]))
    with open(RESULTS / "per_clip.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    def grp(g): return [r for r in rows if r["group"] == g]
    S = {}
    for g in ["real_plane", "real_noplane", "ai_plane", "ai_noplane"]:
        R = grp(g); D = [r for r in R if r["has_doppler"]]
        # A fit on the speed bound is the ceiling of the search, not a measured speed.
        v_fit_kept = [r["v_fit"] for r in D if r["v_fit"] is not None and not physics.speed_at_bound(r["v_fit"])]
        S[g] = dict(n=len(R), doppler=len(D), multi_harmonic=sum((r["n_pairs"] or 0) > 0 for r in D),
                    const_ratio=sum((r["n_const_pairs"] or 0) > 0 for r in D),
                    v_ratio_median=float(np.median([r["v_ratio"] for r in D])) if D else None,
                    v_fit_median=float(np.median(v_fit_kept)) if v_fit_kept else None,
                    v_fit_at_bound=sum(r["v_fit"] is not None and physics.speed_at_bound(r["v_fit"]) for r in D),
                    r2_fit_median=float(np.median([r["r2_fit"] for r in D if r["r2_fit"] is not None])) if D else None,
                    best_cv_median=float(np.median([r["best_pair_cv"] for r in D if r["best_pair_cv"] is not None]))
                    if any(r["best_pair_cv"] is not None for r in D) else None,
                    cv_median=float(np.median([r["median_ratio_cv"] for r in D if r["median_ratio_cv"] is not None]))
                    if any(r["median_ratio_cv"] is not None for r in D) else None)
    ai = grp("ai_plane") + grp("ai_noplane"); real = grp("real_plane") + grp("real_noplane")
    rule = dict(
        real_noplane_called_ai=[S["real_noplane"]["n"] - S["real_noplane"]["doppler"], S["real_noplane"]["n"]],
        real_plane_called_ai=[S["real_plane"]["n"] - S["real_plane"]["doppler"], S["real_plane"]["n"]],
        real_all_called_ai=[sum(not r["has_doppler"] for r in real), len(real)],
        ai_called_real=[sum(r["has_doppler"] for r in ai), len(ai)],
        ai_plane_called_real=[S["ai_plane"]["doppler"], S["ai_plane"]["n"]],
        baseline_always_real=dict(real_called_ai=[0, len(real)], ai_called_real=[len(ai), len(ai)]),
        baseline_coin=dict(real_called_ai=0.5, ai_called_real=0.5))
    summary = dict(groups=S, rule=rule, config=cfg)
    json.dump(summary, open(RESULTS / "summary.json", "w"), indent=2, default=float)
    print(json.dumps(dict(groups=S, rule=rule), indent=2, default=float))
    figures.make_all(rows, S, rule, keep, FIGS, cfg)

if __name__ == "__main__":
    main()
