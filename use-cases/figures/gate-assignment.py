"""The figure at the top of gate-assignment.ipynb: the terminal of a bank of 48 flights,
and two walks between gates with their lengths. Writes gate-assignment.svg (English)
and gate-assignment.de.svg (German) next to this file.
Run from the repo root:  .venv/bin/python use-cases/figures/gate-assignment.py
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
                     "svg.hashsalt": "gate-assignment"})   # the same ids on every run, so a rerun is no diff

BLUE, ORANGE, INK, MUTED, BUILDING = "#2d5faa", "#eb6834", "#333333", "#7a7a7a", "#e4e4e1"

GATES = 48
GATES_PER_PIER = 24
WITHIN_PIER = (14, 21)        # the walk drawn in blue
TO_OTHER_PIER = (5, 30)       # the walk drawn in orange
SIDE = 26.0                   # a gate is drawn this far from the middle of its pier, in metres

# Every word in the figure, per language.
TEXT = {
    "en": {
        "pier": "pier {p}",
        "spine": "spine",
        "title": "You choose the gate of every flight.",
        "terminal": "A bank of 48 flights has 48 gates: two piers on a spine,\n"
                    "each pier with 12 pairs of gates that face each other.",
        "walk": "Connecting passengers walk from the gate\nof their arrival to the gate of their departure.",
        "within": "Within a pier",
        "other": "To another pier, by way of the spine",
        "route": "from gate {start} to gate {end}: {metres:.0f} m",
    },
    "de": {
        "pier": "Pier {p}",
        "spine": "Hauptgang",
        "title": "Sie wählen das Gate jedes Flugs.",
        "terminal": "Eine Welle mit 48 Flügen hat 48 Gates: zwei Piers\n"
                    "am Hauptgang, jeder Pier mit 12 Paaren von Gates,\n"
                    "die einander gegenüberliegen.",
        "walk": "Umsteigepassagiere laufen vom Gate ihrer Ankunft\nzum Gate ihres Abflugs.",
        "within": "Innerhalb eines Piers",
        "other": "Zu einem anderen Pier, über den Hauptgang",
        "route": "von Gate {start} zu Gate {end}: {metres:.0f} m",
    },
}

gate = np.arange(GATES)
pier = gate // GATES_PER_PIER
along_pier = 60.0 + 70.0 * ((gate % GATES_PER_PIER) // 2)       # metres from the spine along the pier to the gate
gate_x = 150.0 * pier + np.where(gate % 2 == 0, -SIDE, SIDE)


def walking_distances():
    """Metres between every two gates, computed as the notebook's walking_distances(48) computes them.

    Returns:
        Square array: entry [g, h] is the walk from gate g to gate h.
    """
    same_pier = pier[:, None] == pier[None, :]
    within_pier = np.abs(along_pier[:, None] - along_pier[None, :]) + 30.0
    along_spine = 150.0 * np.abs(pier[:, None] - pier[None, :])
    between_piers = along_pier[:, None] + along_spine + along_pier[None, :] + 100.0
    distance = np.where(same_pier, within_pier, between_piers)
    np.fill_diagonal(distance, 0.0)
    return distance


def walk_line(start, end):
    """The line drawn for a walk: from a gate to the middle of its pier, along the pier, by way of
    the spine if the other gate is on another pier, and on to that gate.

    Args:
        start: Gate where the walk begins.
        end: Gate where it ends.

    Returns:
        The x and the y coordinates of the corners of the line, in metres.
    """
    middle_start, middle_end = 150.0 * pier[start], 150.0 * pier[end]
    xs = [gate_x[start], middle_start]
    ys = [along_pier[start], along_pier[start]]
    if pier[start] != pier[end]:
        xs += [middle_start, middle_end]
        ys += [0.0, 0.0]
    xs += [middle_end, gate_x[end]]
    ys += [along_pier[end], along_pier[end]]
    return xs, ys


def draw(lang):
    """Draw the terminal, the two walks and the text beside them.

    Args:
        lang: Key of TEXT, the language of the words in the figure.

    Returns:
        The finished matplotlib figure.
    """
    text = TEXT[lang]
    distance = walking_distances()
    fig = plt.figure(figsize=(8.4, 5.2))
    ax = fig.add_axes([0.02, 0.03, 0.46, 0.86])
    ax.set_xlim(-120, 270)
    ax.set_ylim(-75, 880)
    ax.axis("off")

    # the building: the spine, and a pier for every 24 gates
    ax.plot([-95, 245], [0, 0], color=BUILDING, lw=13, solid_capstyle="round", zorder=0)
    for p in range(pier.max() + 1):
        ax.plot([150 * p, 150 * p], [0, along_pier.max() + 22], color=BUILDING, lw=13, solid_capstyle="round", zorder=0)
        ax.text(150 * p, along_pier.max() + 48, text["pier"].format(p=p), ha="center", va="bottom", fontsize=9, color=MUTED)
    ax.text(75, -30, text["spine"], ha="center", va="top", fontsize=9, color=MUTED)

    # the gates, each with its number
    walked = set(WITHIN_PIER) | set(TO_OTHER_PIER)
    for g in gate:
        on_a_walk = g in walked
        ax.scatter(gate_x[g], along_pier[g], marker="s", s=118, zorder=3, linewidth=1.2,
                   color=INK if on_a_walk else "white", edgecolor=INK if on_a_walk else "#b5b5b5")
        ax.text(gate_x[g], along_pier[g] - 1, str(g), ha="center", va="center", fontsize=6.3, zorder=4,
                color="white" if on_a_walk else MUTED, fontweight="medium" if on_a_walk else "regular")

    for (start, end), color in ((WITHIN_PIER, BLUE), (TO_OTHER_PIER, ORANGE)):
        ax.plot(*walk_line(start, end), color=color, lw=2.6, zorder=2, solid_capstyle="round", solid_joinstyle="round")

    # the text beside the terminal
    fig.text(0.50, 0.86, text["title"], fontsize=11.5, color=INK,
             fontweight="medium", va="top")
    fig.text(0.50, 0.80, text["terminal"], fontsize=9.5, color=MUTED, va="top", linespacing=1.45)
    fig.text(0.50, 0.63, text["walk"], fontsize=9.5, color=INK, va="top", linespacing=1.45)
    rows = ((0.48, BLUE, WITHIN_PIER, text["within"]),
            (0.34, ORANGE, TO_OTHER_PIER, text["other"]))
    for y, color, (start, end), words in rows:
        fig.add_artist(plt.Line2D([0.50, 0.535], [y - 0.012, y - 0.012], color=color, lw=2.6,
                                  solid_capstyle="round"))
        fig.text(0.55, y, words, fontsize=9.5, color=INK, fontweight="medium", va="top")
        fig.text(0.55, y - 0.05, text["route"].format(start=start, end=end, metres=distance[start, end]),
                 fontsize=9.5, color=MUTED, va="top")
    return fig


for lang in TEXT:
    fig = draw(lang)
    path = Path(__file__).with_suffix(".svg" if lang == "en" else f".{lang}.svg")
    fig.savefig(path, metadata={"Date": None})       # no timestamp, so a rerun is no diff
    if "--png" in sys.argv:                            # a raster copy, to look at
        fig.savefig(path.with_suffix(".png"), dpi=150)
    plt.close(fig)
