"""SI text 2.2-fig 1 — PFAS concentrations at aquatic-food sampling sites.

Source: five worksheets in 7 PFAS concs at sites.xlsx. The adjacent
Natural Earth 1:50m water geometry is bundled as gzipped GeoJSON and preserves
the original 0.045-degree topology-preserving simplification. PFOA and PFDoA
legends retain the archived breaks (0.1, 0.3, 1 and 3 ng/g).

Inputs are in the adjacent data folder. Run with Python, Matplotlib,
NumPy and pandas installed.
"""


import gzip
import json
from pathlib import Path



import matplotlib
matplotlib.use("Agg")
matplotlib.rcdefaults()

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.patches import Patch, PathPatch
from matplotlib.path import Path as MapPath
from matplotlib.lines import Line2D


HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FOODS = ["Freshwater", "Demersal", "Pelagic", "Crustaceans", "Molluscs"]
ANALYTES = ["Sum", "PFHxS", "PFOS", "PFOA", "PFNA", "PFDA", "PFUnDA", "PFDoA"]


def save(fig, name, dpi=300):
    for ext in ("png", "pdf"):
        fig.savefig(HERE / f"{name}.{ext}", dpi=dpi, facecolor="white")
    plt.close(fig)
    print(name, flush=True)


def load_water_layers():
    with gzip.open(DATA / "natural_earth_50m_water.geojson.gz", "rt", encoding="utf-8") as source:
        features = json.load(source)["features"]
    layers = {feature["properties"]["layer"]: feature["geometry"]["coordinates"]
              for feature in features}
    ocean = polygon_patches(layers["ocean"])
    rivers = layers["rivers_lake_centerlines"]
    lakes = polygon_patches(layers["lakes"])
    return ocean, rivers, lakes


def polygon_patches(polygons):
    return [PathPatch(MapPath.make_compound_path(*(MapPath(ring) for ring in polygon)))
            for polygon in polygons]


def plot_maps():
    water = "#80B2ED"
    land = "#EDEDED"
    ocean, rivers, lakes = load_water_layers()
    points = pd.read_csv(DATA / "site_concentrations.csv")
    fig, axes = plt.subplots(10, 4, figsize=(16, 21))
    fig.subplots_adjust(left=.045, right=.99, top=.982, bottom=.043, wspace=.23, hspace=.5)
    swatches = ["#FFEB65", "#FFAE45", "#FF631F", "#DB0000", "#940000"]
    markers = {"*": "Market", "D": "Inland waters", "o": "Marine waters"}
    for j, analyte in enumerate(ANALYTES):
        start, col = divmod(j, 4)
        start *= len(FOODS)
        breaks = [1, 3, 10, 30] if analyte == "Sum" else [.1, .3, 1, 3]
        if analyte == "PFOS":
            breaks = [.7, 2.1, 7, 21]
        for k, food in enumerate(FOODS):
            ax = axes[start+k, col]
            ax.set_facecolor(land)
            ax.add_collection(PatchCollection(ocean, facecolor=water, edgecolor=land,
                                              linewidth=.18, rasterized=True))
            ax.add_collection(LineCollection(rivers, colors=water, linewidths=.28, rasterized=True))
            ax.add_collection(PatchCollection(lakes, facecolor=water, rasterized=True))
            frame = points.loc[points.food.eq(food)].dropna(subset=["lon", "lat", analyte])
            for marker in markers:
                group = frame.loc[frame.marker.eq(marker)]
                level = np.searchsorted(breaks, group[analyte], side="left")
                ax.scatter(group.lon, group.lat, c=np.asarray(swatches)[level], marker=marker,
                           s=9 if marker == "*" else 5.5, linewidths=0, zorder=5)
            ax.set(xlim=(-180, 180), ylim=(-90, 90), aspect="equal",
                   xticks=range(-150, 151, 50), yticks=[-50, 0, 50],
                   title=f"{food} {'Σ7PFAS' if analyte == 'Sum' else analyte}")
            ax.tick_params(labelsize=6, length=2, pad=1.5)
            ax.grid(color="white", alpha=.27, linewidth=.3)
            if k == 0:
                ax.text(-.10, 1.03, chr(65+j), transform=ax.transAxes, fontweight="bold", fontsize=13)
                labels = [f"≤{breaks[0]:g}", *[f"{a:g}–{b:g}" for a, b in zip(breaks, breaks[1:])],
                          f">{breaks[-1]:g}"]
                ax.legend([Patch(color=c) for c in swatches], labels, title="ng/g ww", loc="lower left",
                          fontsize=6.2, title_fontsize=6.2, frameon=False, borderaxespad=.35,
                          handlelength=.8, handletextpad=.35, labelspacing=.15)
    fig.legend([Line2D([], [], marker=m, linestyle="", color="#7d8879") for m in markers],
               list(markers.values()), loc="lower center", bbox_to_anchor=(.5, .014), ncol=3, frameon=False)
    save(fig, "SI_2.2_Fig_1_site_concentration_maps", dpi=250)


if __name__ == "__main__":
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "pdf.fonttype": 42})
    plot_maps()
