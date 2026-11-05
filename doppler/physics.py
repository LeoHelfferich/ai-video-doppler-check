"""Physics checks on detected curves.
1) Harmonic consistency: a moving source shifts every harmonic by the same factor, so f2(t)/f1(t) is constant.
2) Speed: f_approach/f_recede = (c+v)/(c-v)  =>  v = c (R-1)/(R+1).
3) Shape: fit the straight-line fly-by model f(t) = f0 / (1 + v^2 (t-t0) / (c sqrt(v^2 (t-t0)^2 + d^2)))."""
import numpy as np
from scipy.optimize import curve_fit

def speed_from_ratio(R, c):
    return c * (R - 1) / (R + 1)

def flyby(t, f0, v, t0, d, c=343.0):
    x = v * (t - t0)
    return f0 / (1 + (v / c) * x / np.sqrt(x ** 2 + d ** 2))

def fit_flyby(tr, c):
    t, f = tr["t"], tr["f"]
    p0 = [np.median(f), 40.0, np.median(t), 50.0]
    try:
        p, _ = curve_fit(lambda tt, f0, v, t0, d: flyby(tt, f0, v, t0, d, c), t, f, p0=p0,
                         bounds=([5, 0.5, t[0] - 20, 1], [400, 300, t[-1] + 20, 2000]), maxfev=20000)
    except Exception:
        return None
    pred = flyby(t, *p, c=c)
    ss_res = np.sum((f - pred) ** 2); ss_tot = np.sum((f - f.mean()) ** 2) + 1e-12
    lin = np.polyval(np.polyfit(t, f, 1), t); r2_lin = 1 - np.sum((f - lin) ** 2) / ss_tot
    return dict(f0=p[0], v=p[1], t0=p[2], d=p[3], r2=1 - ss_res / ss_tot, r2_linear=r2_lin)

def harmonic_pairs(tracks, cfg):
    ph = cfg["physics"]; ov = cfg["doppler"]["harmonic_overlap_s"]
    out = []
    for i in range(len(tracks)):
        for j in range(len(tracks)):
            a, b = tracks[i], tracks[j]
            if i == j or np.median(b["f"]) <= np.median(a["f"]):
                continue
            lo, hi = max(a["t"][0], b["t"][0]), min(a["t"][-1], b["t"][-1])
            if hi - lo < ov:
                continue
            tg = np.arange(lo, hi, 0.05)
            r = np.interp(tg, b["t"], b["f"]) / np.interp(tg, a["t"], a["f"])
            cv = float(np.std(r) / np.mean(r)); rm = float(np.mean(r))
            out.append(dict(f_low=float(np.median(a["f"])), f_high=float(np.median(b["f"])), ratio=rm, cv=cv,
                            constant=cv <= ph["harmonic_ratio_cv_max"],
                            integer=abs(rm - round(rm)) / rm <= ph["harmonic_ratio_integer_tol"], overlap_s=hi - lo))
    return out

def check(res, cfg, harmonic_tracks=None):
    ph = cfg["physics"]; c = ph["c_m_s"]
    trs = res["tracks"]
    if not trs:
        return {}
    main = trs[0]
    v_ratio = speed_from_ratio(main["ratio"], c)
    fit = fit_flyby(main, c)
    pairs = harmonic_pairs(harmonic_tracks if harmonic_tracks is not None else trs, cfg)
    return dict(v_ratio=v_ratio, v_ratio_plausible=ph["v_plausible_min"] <= v_ratio <= ph["v_plausible_max"],
                fit=fit, n_pairs=len(pairs), n_const_pairs=sum(p["constant"] for p in pairs),
                median_cv=float(np.median([p["cv"] for p in pairs])) if pairs else None,
                best_pair=min(pairs, key=lambda p: p['cv']) if pairs else None, pairs=pairs)
