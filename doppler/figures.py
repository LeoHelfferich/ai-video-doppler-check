"""Post graphics: 1080x1350 (4:5), light Apple-Keynote style, German labels."""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# Light Keynote palette (aligned with Leo's approved Fehler-drin visuals)
BG = "#FAF9F6"
FG = "#1D1D1F"
MUTED = "#6E6E73"
TRACK = "#ECEAE5"
LINE = "#E3E1DC"
ACC_ERR = "#C7463A"      # calm red for false alarms / errors
ACC_AI = "#0A7EA4"       # calm teal/blue for AI / detector curve
ACC_OK = "#2F6F4E"       # calm green for "curve found" on real
BASELINE = "#8E8E93"

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.facecolor": BG,
    "text.color": FG,
    "axes.labelcolor": FG,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.edgecolor": LINE,
    "font.family": "Inter",
    "font.size": 20,
})

SIZE = (10.8, 13.5)
DPI = 100
DPI2 = 200  # 2160x2700
SOURCE = "Daten: ESC-50 (Piczak 2015, CC BY-NC 3.0, Freesound) und eigene Grok-Imagine-Clips"

# White → warm dark: energy reads as dark ink on paper; teal curve stays clear
_SPEC_CMAP = LinearSegmentedColormap.from_list(
    "paper_spec",
    ["#FAF9F6", "#F0E6D8", "#D4B896", "#8B6B4A", "#3D2E22", "#1A1410"],
)


def _spec(ax, res, overlay=True, fmax=250):
    S = res["S"]
    f = res["f"]
    t = res["t"]
    vmax = np.percentile(S, 99.5)
    vmin = vmax - 45
    ax.pcolormesh(t, f, S, shading="auto", cmap=_SPEC_CMAP, vmin=vmin, vmax=vmax, rasterized=True)
    if overlay:
        for k, tr in enumerate(res["tracks"]):
            ax.plot(tr["t"], tr["f"], color=ACC_AI, lw=3.5 if k == 0 else 2.2, alpha=0.95,
                    solid_capstyle="round")
    ax.set_ylim(20, fmax)
    ax.set_xlim(t[0], t[-1])
    ax.set_facecolor(BG)
    for spine in ax.spines.values():
        spine.set_color(LINE)
        spine.set_linewidth(1.2)


def _save(fig, path: Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # 1x PNG (1080x1350)
    fig.savefig(path, dpi=DPI, facecolor=BG, edgecolor="none")
    # 2x PNG
    stem = path.with_suffix("")
    fig.savefig(Path(f"{stem}@2x.png"), dpi=DPI2, facecolor=BG, edgecolor="none")
    # SVG (spectrograms stay rasterized inside)
    fig.savefig(Path(f"{stem}.svg"), facecolor=BG, edgecolor="none")
    plt.close(fig)


def hero(res, rows, path):
    fig = plt.figure(figsize=SIZE, dpi=DPI)
    fig.text(0.06, 0.94, "KI-Video.", fontsize=58, fontweight="bold", color=FG, va="top")
    fig.text(0.06, 0.875, "Doppler-Kurve trotzdem da.", fontsize=40, fontweight="bold",
             color=ACC_AI, va="top")
    fig.text(0.06, 0.812,
             "Tonspur eines Grok-Imagine-Clips, 20 bis 250 Hz.\n"
             "Türkis: vom Detektor gefundene fallende Kurve.",
             fontsize=21, color=MUTED, va="top", linespacing=1.4)
    ax = fig.add_axes([0.11, 0.335, 0.83, 0.365])
    _spec(ax, res)
    ax.set_xlabel("Zeit (s)", fontsize=18)
    ax.set_ylabel("Frequenz (Hz)", fontsize=18)
    ax.tick_params(labelsize=15)
    r = rows
    fig.text(0.06, 0.210, f"{r['f_start']:.0f} Hz", fontsize=46, fontweight="bold", color=FG)
    fig.text(0.30, 0.215, "→", fontsize=40, color=MUTED)
    fig.text(0.38, 0.210, f"{r['f_end']:.0f} Hz", fontsize=46, fontweight="bold", color=FG)
    dur = str(round(r["duration_s"], 1)).replace(".", ",")
    fig.text(0.06, 0.155, f"fallende Tonhöhe in {dur} s", fontsize=22, color=MUTED)
    fig.text(0.06, 0.072,
             "Die virale Regel „keine Doppler-Kurve heißt KI“\n"
             "hätte dieses Video als echt durchgewunken.",
             fontsize=24, color=FG, linespacing=1.35)
    fig.text(0.06, 0.03, SOURCE, fontsize=13, color=MUTED)
    _save(fig, path)


def grid(panels, path):
    fig = plt.figure(figsize=SIZE, dpi=DPI)
    fig.text(0.06, 0.955, "Vier Tonspuren, ein Detektor", fontsize=40, fontweight="bold",
             color=FG, va="top")
    fig.text(0.06, 0.905, "Türkis = gefundene fallende Doppler-Kurve", fontsize=21,
             color=ACC_AI, va="top")
    pos = [
        [0.09, 0.50, 0.38, 0.31],
        [0.58, 0.50, 0.38, 0.31],
        [0.09, 0.09, 0.38, 0.31],
        [0.58, 0.09, 0.38, 0.31],
    ]
    for (title, sub, res, found), p in zip(panels, pos):
        ax = fig.add_axes(p)
        _spec(ax, res)
        ax.set_title(title, loc="left", fontsize=22, fontweight="bold", pad=34, color=FG)
        ax.text(0, 1.04, sub, transform=ax.transAxes, fontsize=15,
                color=ACC_AI if found else ACC_ERR, fontweight="600")
        ax.set_xlabel("Zeit (s)", fontsize=14)
        ax.set_ylabel("Hz", fontsize=14)
        ax.tick_params(labelsize=12)
    fig.text(0.06, 0.03, SOURCE, fontsize=13, color=MUTED)
    _save(fig, path)


def bars(rule, path):
    fig = plt.figure(figsize=SIZE, dpi=DPI)
    fig.text(0.06, 0.955, "Was die Regel wirklich misst", fontsize=40, fontweight="bold",
             color=FG, va="top")
    fig.text(0.06, 0.905, "Regel: „Keine Doppler-Kurve heißt KI.“", fontsize=24,
             color=MUTED, va="top")

    # Ascending by rate; coin-flip baseline included
    items = [
        ("KI mit Flugzeug im Prompt\nals echt durchgewunken",
         rule["ai_plane_called_real"], ACC_AI, False),
        ("Zum Vergleich: Münzwurf\nfalsch bei",
         [1, 2], BASELINE, True),
        ("Echt, mit Flugzeug\nals KI markiert",
         rule["real_plane_called_ai"], ACC_ERR, False),
        ("Echt, ohne Flugzeug\nals KI markiert",
         rule["real_noplane_called_ai"], ACC_ERR, False),
    ]
    # Sort ascending by fraction (order is free)
    items.sort(key=lambda x: x[1][0] / x[1][1])

    ax = fig.add_axes([0.06, 0.14, 0.88, 0.70])
    ax.axis("off")
    for i, (lab, (k, n), col, is_coin) in enumerate(items):
        y = 1 - i * 0.25
        ax.text(0, y, lab, fontsize=22, va="top", color=FG, linespacing=1.3,
                transform=ax.transAxes)
        ax.add_patch(plt.Rectangle((0, y - 0.17), 1.0, 0.055, color=TRACK,
                                   transform=ax.transAxes, linewidth=0))
        ax.add_patch(plt.Rectangle((0, y - 0.17), k / n, 0.055, color=col,
                                   transform=ax.transAxes, linewidth=0))
        txt = "50 %" if is_coin else f"{k} von {n}"
        ax.text(1.0, y, txt, fontsize=34, fontweight="bold", va="top", ha="right",
                color=col, transform=ax.transAxes)

    fig.text(0.06, 0.075,
             "Die Regel erkennt vor allem: Flugzeug nah genug oder nicht.\n"
             "KI erkennt sie nicht.",
             va="bottom", linespacing=1.35, fontsize=20, color=FG)
    fig.text(0.06, 0.03, SOURCE, fontsize=13, color=MUTED)
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
        return ("Kurve gefunden", True) if r["has_doppler"] else ("keine Kurve, Regel sagt: KI", False)

    s_rp, f_rp = lab(rp)
    s_rn, f_rn = lab(rn)
    s_ap, f_ap = lab(ap)
    s_an, f_an = lab(an)
    grid(
        [
            ("Echt, Flugzeug", s_rp, keep[("real_plane", rp["file"])], f_rp),
            ("Echt, nur Wind", s_rn, keep[("real_noplane", rn["file"])], f_rn),
            ("KI, Flugzeug", s_ap, keep[("ai_plane", ap["file"])], f_ap),
            ("KI, Park ohne Flugzeug", s_an, keep[("ai_noplane", an["file"])], f_an),
        ],
        out / "02_raster_echt_vs_ki.png",
    )
    bars(rule, out / "03_fehlerquoten_regel.png")
