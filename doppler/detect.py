"""Transparent Doppler-curve detector: low-frequency spectrogram, ridge tracking, monotone-descent test."""
import subprocess
import numpy as np
from scipy import signal, stats
from scipy.ndimage import median_filter, uniform_filter1d

SR = 44100

def fft_length(sr, target_bin_hz):
    # Next power of two at or above sr/target_bin_hz, so each bin is at most target_bin_hz wide.
    # At 44.1 kHz and 2.5 Hz that is 32768 samples, which is 1.35 Hz, not 2.5.
    return int(2 ** np.ceil(np.log2(sr / target_bin_hz)))

def load_audio(path):
    """Decode any audio/video file to mono float32 at 44.1 kHz with ffmpeg."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()

def spectrogram(x, cfg):
    s = cfg["spectrogram"]
    nper = fft_length(SR, s["target_bin_hz"])
    hop = int(SR * s["hop_s"])
    x = np.pad(x, nper // 2)
    f, t, Z = signal.stft(x, SR, window="hann", nperseg=nper, noverlap=nper - hop, boundary=None, padded=False)
    t = t - (nper // 2) / SR
    keep = (f >= s["fmin_hz"]) & (f <= s["fmax_hz"])
    S = 20 * np.log10(np.abs(Z[keep]) + 1e-10)
    return f[keep], t, S

def ridges(f, t, S, cfg):
    r = cfg["ridge"]; df = f[1] - f[0]; dt = t[1] - t[0]
    W = S - median_filter(S, size=(max(3, int(r["whiten_width_hz"] / df) | 1), 1), mode="nearest")
    max_jump = r["max_jump_hz_per_s"] * dt
    tracks, active = [], []
    for j in range(S.shape[1]):
        col = W[:, j]
        pk, pr = signal.find_peaks(col, prominence=r["peak_prominence_db"])
        pk = pk[np.argsort(-pr["prominences"])][: r["max_peaks_per_frame"]]
        # parabolic interpolation for sub-bin frequency
        fr = []
        for k in pk:
            if 0 < k < len(col) - 1:
                a, b, c = col[k - 1], col[k], col[k + 1]
                d = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) != 0 else 0
                fr.append(f[k] + d * df)
            else:
                fr.append(f[k])
        used = set(); new_active = []
        for tr in active:
            last_f = tr["f"][-1]; gap = j - tr["j"][-1]
            cands = [(abs(ff - last_f), i) for i, ff in enumerate(fr) if i not in used and abs(ff - last_f) <= max_jump * gap]
            if cands:
                _, i = min(cands); used.add(i); tr["f"].append(fr[i]); tr["j"].append(j); new_active.append(tr)
            elif gap <= r["max_gap_frames"]:
                new_active.append(tr)
            else:
                tracks.append(tr)
        for i, ff in enumerate(fr):
            if i not in used:
                new_active.append({"f": [ff], "j": [j]})
        active = new_active
    tracks += active
    return [{"t": t[np.array(tr["j"])], "f": np.array(tr["f"])} for tr in tracks if len(tr["j"]) > 2], W

def qualifies(tr, cfg):
    d = cfg["doppler"]
    tt, ff = tr["t"], tr["f"]
    dur = tt[-1] - tt[0]
    if dur < d["min_duration_s"]:
        return False, {}
    fs = uniform_filter1d(ff, size=min(d["smooth_frames"], len(ff)), mode="nearest")
    n = max(1, len(fs) // 5)
    ratio = np.median(fs[:n]) / np.median(fs[-n:])
    # A constant series has no rank correlation, and spearmanr warns on it.
    rho = 0.0 if np.ptp(fs) == 0 else stats.spearmanr(tt, fs).statistic
    mono = np.mean(np.diff(fs) <= 1e-9)
    jitter = float(np.std(ff - uniform_filter1d(ff, size=min(2 * d["smooth_frames"] + 1, len(ff)), mode="nearest")))
    info = dict(duration_s=dur, ratio=ratio, spearman=rho, monotone=mono, f_start=float(np.median(fs[:n])),
                f_end=float(np.median(fs[-n:])), jitter_hz=jitter, t0=float(tt[0]), t1=float(tt[-1]))
    ok = ratio >= d["min_ratio_start_end"] and rho <= d["max_spearman"] and mono >= d["min_monotone_frac"] and jitter <= d["max_jitter_hz"]
    return bool(ok), info

def analyze(path, cfg):
    x = load_audio(path)
    f, t, S = spectrogram(x, cfg)
    trs, W = ridges(f, t, S, cfg)
    q = []
    for tr in trs:
        ok, info = qualifies(tr, cfg)
        if ok:
            tr.update(info); q.append(tr)
    q.sort(key=lambda r: -r["duration_s"])
    return dict(f=f, t=t, S=S, tracks=q, has_doppler=len(q) >= cfg["doppler"]["min_tracks"])
