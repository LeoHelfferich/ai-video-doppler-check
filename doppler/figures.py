"""Post graphics: 1080x1350 (4:5), dark theme, German labels.

These files are the graphics for the post. The English statement of the same numbers is docs/index.html.
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Dark palette, slightly calmer than neon v1
BG = "#0B0F17"
FG = "#F2F4F8"
MUTED = "#8A93A6"
EDGE = "#2A3142"
TRACK = "#1A2130"
ACC = "#3DB8D1"
ACC2 = "#D65A7A"
BASELINE = "#7A8499"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.facecolor": BG,
    "text.color": FG,
    "axes.labelcolor": MUTED,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.edgecolor": EDGE,
    "font.family": "DejaVu Sans",
    "font.size": 20,
})

SIZE = (10.8, 13.5)
DPI = 100
DPI2 = 200
SOURCE = "Daten: ESC-50 (Piczak 2015, CC BY-NC 3.0, Freesound) und eigene Grok-Imagine-Clips"


def _spec(ax, res, overlay=True, fmax=250):
    S, f, t = res["S"], res["f"], res["t"]
    vmax = np.percentile(S, 99.5)
    vmin = vmax - 45
    ax.pcolormesh(t, f, S, shading="auto", cmap="magma", vmin=vmin, vmax=vmax, rasterized=True)
    if overlay:
        for k, tr in enumerate(res["tracks"]):
            ax.plot(tr["t"], tr["f"], color=ACC, lw=3.4 if k == 0 else 2.0, alpha=0.95,
                    solid_capstyle="round")
    ax.set_ylim(20, fmax)
    ax.set_xlim(t[0], t[-1])
    ax.set_facecolor(BG)
    for spine in ax.spines.values():
        spine.set_color(EDGE)
        spine.set_linewidth(1.2)


def _save(fig, path: Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=DPI, facecolor=BG, edgecolor="none")
    stem = path.with_suffix("")
    fig.savefig(Path(f"{stem}@2x.png"), dpi=DPI2, facecolor=BG, edgecolor="none")
    fig.savefig(Path(f"{stem}.svg"), facecolor=BG, edgecolor="none")
    plt.close(fig)


def hero(res, rows, path):
    fig = plt.figure(figsize=SIZE, dpi=DPI)
    fig.text(0.06, 0.945, "KI-Video.", fontsize=56, fontweight="bold", color=FG, va="top")
    fig.text(0.06, 0.878, "Fallende Tonhöhe trotzdem da.", fontsize=40, fontweight="bold",
             color=ACC, va="top")
    fig.text(0.06, 0.808, "Grok-Imagine-Clip · Cyan = fallende Tonhöhe",
             fontsize=20, color=MUTED, va="top")
    # Clear air under subtitle before plot top / 250 tick
    ax = fig.add_axes([0.12, 0.355, 0.80, 0.375])
    _spec(ax, res)
    ax.set_xlabel("Zeit (s)", fontsize=17, labelpad=12)
    ax.set_ylabel("Frequenz (Hz)", fontsize=17, labelpad=12)
    ax.tick_params(labelsize=14, pad=6)
    r = rows
    # Clear air under x-label before big Hz
    fig.text(0.06, 0.205, f"{r['f_start']:.0f} Hz", fontsize=46, fontweight="bold", color=FG)
    fig.text(0.30, 0.210, "→", fontsize=40, color=MUTED)
    fig.text(0.38, 0.205, f"{r['f_end']:.0f} Hz", fontsize=46, fontweight="bold", color=FG)
    dur = str(round(r["duration_s"], 1)).replace(".", ",")
    fig.text(0.06, 0.145, f"fallende Tonhöhe in {dur} s", fontsize=22, color=MUTED)
    fig.text(0.06, 0.068,
             "Der virale Doppler-Check („keine Doppler-Kurve heißt KI“)\n"
             "hätte dieses Video als echt durchgewunken.",
             fontsize=23, color=FG, linespacing=1.45)
    fig.text(0.06, 0.028, SOURCE, fontsize=12, color=MUTED)
    _save(fig, path)


def grid(panels, path):
    fig = plt.figure(figsize=SIZE, dpi=DPI)
    fig.text(0.06, 0.955, "Vier Tonspuren, ein Detektor", fontsize=38, fontweight="bold",
             color=FG, va="top")
    fig.text(0.06, 0.898, "Cyan = gefundene fallende Tonhöhe", fontsize=20,
             color=ACC, va="top")
    # Smaller panels + more title pad so status never crowds the plot
    pos = [
        [0.09, 0.525, 0.36, 0.255],
        [0.58, 0.525, 0.36, 0.255],
        [0.09, 0.125, 0.36, 0.255],
        [0.58, 0.125, 0.36, 0.255],
    ]
    for (title, sub, res, found), p in zip(panels, pos):
        ax = fig.add_axes(p)
        _spec(ax, res)
        ax.set_title(title, loc="left", fontsize=20, fontweight="bold", pad=52, color=FG)
        ax.text(0, 1.10, sub, transform=ax.transAxes, fontsize=14,
                color=ACC if found else ACC2)
        ax.set_xlabel("Zeit (s)", fontsize=13, labelpad=8)
        ax.set_ylabel("Hz", fontsize=13, labelpad=8)
        ax.tick_params(labelsize=11, pad=4)
    fig.text(0.06, 0.028, SOURCE, fontsize=12, color=MUTED)
    _save(fig, path)


def bars(rule, path):
    fig = plt.figure(figsize=SIZE, dpi=DPI)
    fig.text(0.06, 0.955, "Was dieser Check\nwirklich zählt", fontsize=36, fontweight="bold",
             color=FG, va="top", linespacing=1.15)
    # ~0.03 fig ≈ 40 px at 1x below second title line
    fig.text(0.06, 0.845, "Check: „Keine fallende Tonhöhe heißt KI.“", fontsize=22,
             color=MUTED, va="top")

    items = [
        ("KI mit Flugzeug im Prompt\nals echt durchgewunken",
         rule["ai_plane_called_real"], ACC, False),
        ("Zum Vergleich: Münzwurf\nfalsch bei",
         [1, 2], BASELINE, True),
        ("Echt, mit Flugzeug\nals KI markiert",
         rule["real_plane_called_ai"], ACC2, False),
        ("Echt, ohne Flugzeug\nals KI markiert",
         rule["real_noplane_called_ai"], ACC2, False),
    ]
    items.sort(key=lambda x: x[1][0] / x[1][1])

    # Shifted down with the subtitle; leave room above credit
    ax = fig.add_axes([0.06, 0.09, 0.88, 0.68])
    ax.axis("off")
    for i, (lab, (k, n), col, is_coin) in enumerate(items):
        y = 0.98 - i * 0.235
        ax.text(0, y, lab, fontsize=22, va="top", color=FG, linespacing=1.4,
                transform=ax.transAxes)
        # Bar well below the two-line label
        ax.add_patch(plt.Rectangle((0, y - 0.165), 1.0, 0.050, color=TRACK,
                                   transform=ax.transAxes, linewidth=0, clip_on=False))
        ax.add_patch(plt.Rectangle((0, y - 0.165), k / n, 0.050, color=col,
                                   transform=ax.transAxes, linewidth=0, clip_on=False))
        txt = "50 %" if is_coin else f"{k} von {n}"
        ax.text(1.0, y, txt, fontsize=34, fontweight="bold", va="top", ha="right",
                color=col, transform=ax.transAxes)

    fig.text(0.06, 0.028, SOURCE, fontsize=12, color=MUTED)
    _save(fig, path)


def make_all(rows, S, rule, keep, out, cfg):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    ai_hits = sorted(
        [r for r in rows if r["group"] == "ai_plane" and r["has_doppler"]],
        key=lambda r: -(r["duration_s"] or 0),
    )
    if ai_hits:
        h = ai_hits[0]
        hero(keep[("ai_plane", h["file"])], h, out / "01_hero_ki_doppler.png")

    def pick(g, want):
        c = [r for r in rows if r["group"] == g and r["has_doppler"] == want]
        c.sort(key=lambda r: -(r["duration_s"] or 0))
        return c[0] if c else [r for r in rows if r["group"] == g][0]

    rp = pick("real_plane", True)
    rn = [r for r in rows if r["group"] == "real_noplane" and r["cls"] == "wind"][0]
    rest = sorted(ai_hits[1:], key=lambda r: -(r["r2_fit"] or 0))
    ap = rest[0] if rest else pick("ai_plane", True)
    an = pick("ai_noplane", False)

    def lab(r):
        if r["has_doppler"]:
            return "Tonhöhe gefunden", True
        return "keine, Check sagt: KI", False

    panels = []
    for title, r, key in [
        ("Echt, Flugzeug", rp, ("real_plane", rp["file"])),
        ("Echt, nur Wind", rn, ("real_noplane", rn["file"])),
        ("KI, Flugzeug", ap, ("ai_plane", ap["file"])),
        ("KI, Park ohne Flugzeug", an, ("ai_noplane", an["file"])),
    ]:
        s, found = lab(r)
        panels.append((title, s, keep[key], found))
    grid(panels, out / "02_raster_echt_vs_ki.png")
    bars(rule, out / "03_fehlerquoten_regel.png")
