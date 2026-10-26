"""The figure at the top of warehouse-planning.ipynb: what the plan decides, and what
the forecast error does to one warehouse. Writes warehouse-planning.svg next to this
file, and warehouse-planning.de.svg, the same figure in German for quicopt.com.
Run from the repo root:  .venv/bin/python use-cases/figures/warehouse-planning.py
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

for f in Path.home().glob("Library/Fonts/FiraSans-*.otf"):
    font_manager.fontManager.addfont(str(f))
plt.rcParams.update({"font.family": "Fira Sans", "font.size": 10, "svg.fonttype": "path",
                     "svg.hashsalt": "warehouse-planning",   # the same ids on every run, so a rerun is no diff
                     "axes.edgecolor": "#b5b5b5", "xtick.color": "#b5b5b5", "xtick.labelcolor": "#5c5c5c"})

BLUE, ORANGE, INK, MUTED, PALE = "#2d5faa", "#eb6834", "#333333", "#7a7a7a", "#c9d5ea"

# Network 11, drawn exactly as the notebook's network(11) draws it.
SITES, REGIONS = 5, 8
rng = np.random.default_rng(11)
site_xy = rng.uniform([0, 0], [600, 800], (SITES, 2))
region_xy = rng.uniform([0, 0], [600, 800], (REGIONS, 2))
forecast = rng.uniform(60, 140, REGIONS)
capacity = rng.uniform(200, 350, SITES)

# The plan for the forecast in the calm market (the notebook's plan_for_forecast(11, calm)).
open_sites = [0, 1, 4]
serves = [4, 1, 0, 4, 4, 1, 4, 0]
SHOWN = 0                                            # the warehouse whose load is drawn on the right

# Every word in the figure, per language. {cap}, {need} and {over} are numbers of
# pallets as count() writes them, {price} is in EUR.
TEXT = {
    "en": {
        "warehouse": "warehouse",
        "unused": "unused site",
        "region": "customer region",
        "decide": "You choose which sites get a warehouse,\nand which warehouse serves each region.",
        "header": "The warehouse on site {site} in 100,000 simulated years",
        "subtitle": "It holds {cap} thousand pallets a year. Its regions need {need} on average, in both markets.",
        "calm": "In a calm market, forecasts miss by about 15%.",
        "turned": "In a turned market, forecasts miss by about 30%,\nand demand in all regions rises and falls together.",
        "over": "On average, {over} thousand pallets\na year don't fit. Each one\ncosts EUR {price} extra.",
        "capacity": "capacity",
        "axis": "demand in a year, thousand pallets",
    },
    "de": {
        "warehouse": "Lager",
        "unused": "ungenutzter Standort",
        "region": "Kundenregion",
        "decide": "Sie legen fest, an welchen Standorten ein Lager steht\nund welches Lager welche Region beliefert.",
        "header": "Das Lager an Standort {site} über 100.000 simulierte Jahre",
        "subtitle": "Es fasst {cap} Paletten im Jahr.\nDie Regionen, die es beliefert, brauchen im Schnitt {need}, in beiden Märkten.",
        "calm": "Im ruhigen Markt liegen die Prognosen um etwa 15 % daneben.",
        "turned": "Im gekippten Markt liegen die Prognosen um etwa 30 % daneben,\nund die Nachfrage aller Regionen steigt und fällt gemeinsam.",
        "over": "Im Schnitt finden {over} Paletten\nim Jahr keinen Platz. Jede davon\nkostet {price} EUR extra.",
        "capacity": "Kapazität",
        "axis": "Bedarf in einem Jahr, in Tausend Paletten",
    },
}


def count(thousands, lang):
    """A number of pallets, given in thousands, as the figure writes it: "264" in
    English, where the text adds "thousand", and "264.000" in German."""
    if lang == "de":
        return f"{round(thousands) * 1000:,}".replace(",", ".")
    return f"{thousands:.0f}"


def years(error, rho, n=100_000, seed=11 + 2000):
    rng = np.random.default_rng(seed)
    own = rng.standard_normal((n, REGIONS))
    shared = rng.standard_normal((n, 1))
    swing = np.sqrt(1 - rho) * own + np.sqrt(rho) * shared
    return np.maximum(forecast + error * forecast * swing, 0.0)


# The shown warehouse's load, year by year, in both markets: (TEXT key, overflow price, load).
cap = capacity[SHOWN]
mine = [r for r in range(REGIONS) if serves[r] == SHOWN]
need = sum(forecast[mine])
markets = [("calm", 40, years(0.15, 0.0)[:, mine].sum(axis=1)),
           ("turned", 80, years(0.30, 0.5)[:, mine].sum(axis=1))]
for _, _, load in markets:
    assert round(load.mean()) == round(need)        # the same average in both markets


def draw(lang):
    text = TEXT[lang]
    fig = plt.figure(figsize=(10, 6.0))

    # --- the map ----------------------------------------------------------
    ax = fig.add_axes([0.01, 0.03, 0.40, 0.85])
    ax.set_xlim(-30, 630)
    ax.set_ylim(-30, 830)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.add_patch(plt.Rectangle((-30, -30), 660, 860, facecolor="#f5f5f3", edgecolor="none", zorder=0))

    for r in range(REGIONS):
        (x0, y0), (x1, y1) = region_xy[r], site_xy[serves[r]]
        ax.plot([x0, x1], [y0, y1], color=BLUE, lw=1.6, alpha=0.55, zorder=1, solid_capstyle="round")
    ax.scatter(*region_xy.T, s=(forecast / 10) ** 2 * 2.4, color=INK, edgecolor="white", linewidth=2, zorder=3)
    for s in range(SITES):
        is_open = s in open_sites
        ax.scatter(*site_xy[s], marker="s", s=190, zorder=5, linewidth=2 if is_open else 1.6,
                   color=BLUE if is_open else "white", edgecolor="white" if is_open else MUTED)
        ax.text(*site_xy[s], str(s), color="white" if is_open else MUTED, ha="center", va="center",
                fontsize=9, fontweight="semibold", zorder=6)

    def label(xy, words, offset, color=INK, **kw):
        ax.annotate(words, xy, xytext=offset, textcoords="offset points", fontsize=9, color=color,
                    zorder=7, linespacing=1.3, **kw)

    label(site_xy[4], text["warehouse"], (-14, 0), ha="right", va="center")
    label(site_xy[2], text["unused"], (12, 0), ha="left", va="center", color=MUTED)
    label(region_xy[2], text["region"], (16, 0), ha="left", va="center")
    ax.plot([0, 100], [-8, -8], color=MUTED, lw=1.5)
    ax.text(50, 2, "100 km", ha="center", va="bottom", fontsize=8, color=MUTED)
    ax.text(0, 1.035, text["decide"], transform=ax.transAxes, fontsize=10.5, color=INK,
            fontweight="medium", va="bottom")

    # --- one warehouse's load, year by year --------------------------------
    width = 8.0
    edges = cap + width * np.arange(-40, 41)           # capacity falls on a bin edge
    axes = [fig.add_axes([0.47, 0.50, 0.51, 0.25]), fig.add_axes([0.47, 0.10, 0.51, 0.25])]
    fig.text(0.47, 0.885, text["header"].format(site=SHOWN),
             fontsize=10.5, color=INK, fontweight="medium", va="bottom")
    fig.text(0.47, 0.872, text["subtitle"].format(cap=count(cap, lang), need=count(need, lang)), fontsize=9, color=MUTED, va="top",
             linespacing=1.4)                          # hangs from the header: one line or two
    peak = 0
    for a, (market, price, load) in zip(axes, markets):
        share = np.histogram(load, edges)[0] / len(load)
        peak = max(peak, share.max())
        left = edges[:-1]
        a.bar(left, share, width=width, align="edge", color=np.where(left >= cap, ORANGE, PALE),
              edgecolor="white", linewidth=0.8)
        a.axvline(cap, color=INK, lw=1.5)
        over = np.maximum(load - cap, 0)
        a.set_title(text[market], loc="left", fontsize=9.5, color=INK, pad=4)
        a.text(cap + 7, 0.97, text["over"].format(over=count(over.mean(), lang), price=price),
               transform=a.get_xaxis_transform(), ha="left", va="top", fontsize=8.5, color=INK, linespacing=1.3)
        a.text(cap - 7, 0.97, text["capacity"], transform=a.get_xaxis_transform(),
               ha="right", va="top", fontsize=8.5, color=INK)
        a.set_yticks([])
        for side in ("left", "right", "top"):
            a.spines[side].set_visible(False)
        a.set_xlim(cap - 220, cap + 220)
    for a in axes:
        a.set_ylim(0, peak * 1.6)
    axes[1].set_xlabel(text["axis"], color=MUTED, fontsize=8.5)
    return fig


for lang in TEXT:
    fig = draw(lang)
    path = Path(__file__).with_suffix(".svg" if lang == "en" else f".{lang}.svg")
    fig.savefig(path, metadata={"Date": None})       # no timestamp, so a rerun is no diff
    if "--png" in sys.argv:                            # a raster copy, to look at
        fig.savefig(path.with_suffix(".png"), dpi=150)
    plt.close(fig)
