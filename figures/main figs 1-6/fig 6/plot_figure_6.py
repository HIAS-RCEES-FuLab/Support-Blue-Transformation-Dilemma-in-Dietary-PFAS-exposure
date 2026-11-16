"""Rebuild Figure 6 from the CSV and GeoJSON files beside this script.

Panels a–c show (HI in Metatrade / HI in Trade) − 1 for each 2050 pathway.
Panel d uses production-weighted aquatic-food concentrations. Panel e shows the
2050 BAU change in Asian aquatic-food market share in percentage points. Panels
f–l show the relative change in modeled effects under Metatrade vs. Trade in
each pathway, using the original directional-agreement flags. The 95% labels
describe the proportion with effects in the same direction. Requires Matplotlib
and NumPy.
"""


import csv
import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcdefaults()

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.path import Path as DrawPath
from matplotlib.patches import PathPatch, Rectangle


HERE = Path(__file__).resolve().parent


def rows(filename):
    with (HERE / filename).open(encoding="utf-8-sig", newline="") as source:
        return list(csv.DictReader(source))


def panel_title(fig, letter, title, x, y, gap=.026):
    fig.text(x, y, letter, weight="bold", fontsize=11.5, ha="left", va="center")
    fig.text(x + gap, y, title, fontsize=11.5, ha="left", va="center")


def _country_code(feature):
    p = feature["properties"]
    for key in ("ISO_A3", "ADM0_A3", "iso_a3"):
        value = p.get(key)
        if isinstance(value,str) and len(value)==3 and value.isalpha():
            return value.upper()
    return None


def _map_path(geometry):
    coords=geometry["coordinates"]
    polys=[coords] if geometry["type"]=="Polygon" else coords
    paths=[]
    for polygon in polys:
        for index,ring in enumerate(polygon):
            points=[(float(x),float(y)) for x,y in ring]
            if len(points)<3:
                continue
            if points[0]!=points[-1]:
                points.append(points[0])
            area=sum(x1*y2-x2*y1 for (x1,y1),(x2,y2) in zip(points,points[1:]))
            if (area>0)==(index!=0):
                points.reverse()
            ops=[DrawPath.MOVETO]+[DrawPath.LINETO]*(len(points)-2)+[DrawPath.CLOSEPOLY]
            paths.append(DrawPath(points,ops))
    return DrawPath.make_compound_path(*paths) if paths else None


def load_boundaries():
    with (HERE/"world_boundaries.geojson").open(encoding="utf-8-sig") as source:
        geo=json.load(source)["features"]
    return [(_country_code(f),_map_path(f["geometry"])) for f in geo if f["geometry"]]


def plot_world(ax,boundaries,values,cmap,norm,tick_size=8.1):
    located=set()
    for code,path in sorted(boundaries,key=lambda item:item[0] in values):
        if path is None:
            continue
        modeled=code in values
        if modeled:
            located.add(code)
        ax.add_patch(PathPatch(path,facecolor=cmap(norm(values[code])) if modeled else "#DBDBDB",
                    edgecolor="#303030" if modeled else "#A7A7A7",
                    linewidth=.42 if modeled else .33,zorder=3 if modeled else 2,
                    joinstyle="round"))
    if not set(values)<=located:
        raise ValueError(f"Countries without matching boundaries: {sorted(set(values)-located)}")
    ax.set(xlim=(-180,180),ylim=(-60,90))
    ax.set_aspect("equal",adjustable="box")
    lng=list(range(-180,181,60))
    lat=list(range(-60,91,30))
    degree=lambda n,pos,neg:f"{abs(n)}°{pos if n>0 else neg if n<0 else ''}"
    ax.set_xticks(lng,[degree(n,"E","W") for n in lng])
    ax.set_yticks(lat,[degree(n,"N","S") for n in lat])
    ax.tick_params(labelsize=tick_size,length=1.7,pad=1.8,width=.55)
    ax.grid(color="#7B7B7B",linestyle=(0,(2,1.6)),lw=.5,alpha=.77,zorder=1)
    for edge in ax.spines.values():
        edge.set_linewidth(.65)
    return ax


def colorbar(fig,rect,cmap,norm,ticks,labels=None,title=None):
    cax=fig.add_axes(rect)
    mappable=plt.cm.ScalarMappable(norm=norm,cmap=cmap)
    legend=fig.colorbar(mappable,cax=cax,ticks=ticks)
    if labels:
        legend.set_ticklabels(labels)
    legend.outline.set_linewidth(.65)
    legend.ax.tick_params(labelsize=8,length=2,pad=2,width=.55)
    if title:
        legend.ax.set_title(title,fontsize=8.3,pad=6)
    return legend


def initial_plot_settings():
    plt.rcParams.update({"font.family":"DejaVu Sans",
                         "figure.facecolor":"white","savefig.facecolor":"white",
                         "axes.unicode_minus":True,"axes.linewidth":.72})



HEALTH_STYLES = {
    "LR": ("o", "#457D4B", -0.20),
    "BAU": ("s", "#28C7C5", 0.0),
    "HR": ("^", "#007BFF", 0.20),
}
ENDPOINT_LABELS = {
    "arthritis incidence": "Arthritis incidence",
    "hypertension incidence": "Hypertension incidence",
    "Direct HDL-Cholesterol": "Direct HDL cholesterol",
    "LDL-Cholesterol": "LDL cholesterol",
    "Systolic Blood pressure": "Systolic blood pressure",
    "Diastolic Blood pressure": "Diastolic blood pressure",
    "Maximum Inflation Levels": "Maximum inflation level",
    "Albumin-Globulin ratio": "Albumin–globulin ratio",
}


def draw_hi_maps(fig, boundaries):
    data = rows("country_metatrade_hi_change_2050.csv")
    assert len(data) == 47
    scale = LinearSegmentedColormap.from_list("hi_metatrade", ["#77AB12", "white", "#E84966"])
    norm = Normalize(-.35, .35, clip=True)
    for letter, pathway, title, bottom in (
        ("a", "LR", "Low Road", .805),
        ("b", "BAU", "Business as Usual", .623),
        ("c", "HR", "High Road", .441),
    ):
        ax = fig.add_axes([.068, bottom, .312, .147])
        values = {row["ISO3"]: float(row[f"Relative_HI_change_{pathway}"]) for row in data}
        plot_world(ax, boundaries, values, scale, norm, tick_size=8.1)
        fig.text(.021, bottom + .141, letter, fontsize=11.5, weight="bold", va="center")
        fig.text(.068, bottom + .152, title, fontsize=9.4, va="bottom")
    fig.text(.050, .982, "Hazard index change from Trade to Metatrade", fontsize=11.6, va="center")
    colorbar(fig, [.409, .830, .006, .095], scale, norm, [-.35, -.175, 0, .175, .35],
             ["−35.0%", "−17.5%", "0%", "17.5%", "35.0%"], "HI change")


def draw_market(fig):
    concentrations = rows("regional_aquatic_pfas_concentrations.csv")
    market = {row["Region_code"]: row for row in rows("asian_market_share_2050_bau.csv")}
    codes = [row["region_code"] for row in concentrations]
    assert set(codes) == set(market) and len(codes) == 8
    bottom, height = .131, .244
    conc = fig.add_axes([.089, bottom, .047, height])
    share = fig.add_axes([.148, bottom, .054, height], sharey=conc)
    change = fig.add_axes([.202, bottom, .172, height], sharey=conc)
    for ax in (conc, share, change):
        ax.set_ylim(len(codes)-.5, -.5)
        ax.tick_params(axis="y", length=0)
        for spine in ax.spines.values():
            spine.set_linewidth(1)
    for ax in (conc, share):
        ax.set_xlim(0, 1)
        ax.set_xticks([])
    conc.set_yticks(range(len(codes)), codes, fontsize=8.25)
    conc.tick_params(axis="y", length=2.25, pad=4)
    share.tick_params(axis="y", labelleft=False)
    change.tick_params(axis="y", labelleft=False)
    change.set_xlim(0, 20)
    change.set_xticks([0, 5, 10, 15, 20])
    change.tick_params(axis="x", labelsize=8, length=2.4, pad=2.8)
    change.set_axisbelow(True)
    change.grid(axis="x", color="#D8D8D8", linewidth=.65)
    blues = plt.get_cmap("Blues")
    for i, row in enumerate(concentrations):
        current = market[row["region_code"]]
        value = float(row["produced_food_mean_pfas_ng_g"])
        baseline = float(current["Trade_share_percent"])
        gain = float(current["Change_percentage_points"])
        conc.add_patch(Rectangle((0, i-.5), 1, 1, ec="#363636", lw=.72, fc=row["fill_hex"]))
        share.add_patch(Rectangle((0, i-.5), 1, 1, ec="#363636", lw=.72, fc=blues(.05+.95*baseline/100)))
        conc.text(.5, i, f"{value:.2f}", ha="center", va="center", weight="bold", fontsize=8)
        share.text(.5, i, f"{baseline:.1f}%", ha="center", va="center", weight="bold",
                   fontsize=8, color="white" if baseline > 60 else "#151515")
        change.axhline(i+.5, color="#545454", lw=.75, zorder=2)
        change.hlines(i, 0, gain, color="#333333", lw=.88)
        change.plot(gain, i, "o", ms=4.25, mfc="#F1AA32", mec="#322A24", mew=.8)
    panel_title(fig, "d", "Aquatic conc.", .025, .392, gap=.023)
    panel_title(fig, "e", "Asian market share", .155, .392, gap=.026)
    conc.set_xlabel("Σ₇PFAS\n(ng/g ww)", fontsize=8.2, labelpad=4)
    share.set_xlabel("Trade\nshare", fontsize=8.2, labelpad=4)
    change.set_xlabel("Increase in Metatrade\n(percentage points)", fontsize=8.2, labelpad=3)


def draw_health_panel(ax, records, endpoint_labels, wide, show_labels):
    y = np.arange(1, len(endpoint_labels)+1)
    ax.axhspan(.5, 2.5, color="#D0D0D0", linewidth=0)
    ax.axvline(0, color="#5A5A5A", linewidth=.72)
    ax.set_xlim(-25, 25)
    ax.set_ylim(len(y)+.5, .5)
    ticks = [-20, -10, 0, 10, 20] if wide else [-20, 0, 20]
    ax.set_xticks(ticks, [f"{t}%".replace("-", "−") for t in ticks])
    ax.set_yticks(y, endpoint_labels if show_labels else [""]*len(y))
    ax.tick_params(axis="x", labelsize=8.1, length=2.2, pad=2.2)
    ax.tick_params(axis="y", labelsize=8.1, length=0, pad=3)
    ax.grid(color="#B1B1B1", lw=.54, linestyle=(0, (1, 2)))
    for row in records:
        marker, color, offset = HEALTH_STYLES[row["Scenario"]]
        ax.plot(float(row["Mean_change_percent"]), int(row["Endpoint_order"])+offset,
                marker=marker, linestyle="", ms=4.7,
                markerfacecolor=color if row["Filled_marker"] == "1" else "white",
                markeredgecolor=color, markeredgewidth=.84)


def draw_health(fig):
    data = rows("fig6_health_outcomes.csv")
    by_panel = defaultdict(list)
    for row in data:
        by_panel[row["Panel"]].append(row)
    endpoints = {int(row["Endpoint_order"]): row["Endpoint"] for row in by_panel["f"]}
    labels = [ENDPOINT_LABELS.get(endpoint, endpoint) for _, endpoint in sorted(endpoints.items())]
    fig.text(.600, .982, "Health outcomes from Trade to Metatrade", fontsize=11.6, va="center")
    for letter, x, y, w in (
        ("f", .587, .747, .371),
        ("g", .587, .500, .113),
        ("h", .716, .500, .113),
        ("i", .845, .500, .113),
        ("j", .587, .253, .113),
        ("k", .716, .253, .113),
        ("l", .845, .253, .113),
    ):
        records = by_panel[letter]
        assert len(records) == 45
        wide = letter == "f"
        height = .201
        ax = fig.add_axes([x, y, w, height])
        draw_health_panel(ax, records, labels, wide=wide, show_labels=letter in "fgj")
        title = "SSA" if letter == "l" else records[0]["Region"]
        fig.text(x, y+height+.014, letter, weight="bold", fontsize=11, va="center")
        fig.text(x+.018, y+height+.014, title, fontsize=9.4, va="center")
        if wide:
            handles = [Line2D([], [], marker=m, color=c, linestyle="", ms=5.3, label=s)
                       for s, (m, c, _) in HEALTH_STYLES.items()]
            handles.extend(
                Line2D([], [], marker="o", markerfacecolor=fill, color="#575757", linestyle="",
                       ms=5.3, label=label)
                for fill, label in (("white", "<95% same direction"), ("#575757", "≥95% same direction"))
            )
            ax.legend(handles=handles, ncol=2, fontsize=7.2, frameon=True, framealpha=.94,
                      facecolor="white", edgecolor="white", loc="lower right", borderpad=.2,
                      columnspacing=.65, handletextpad=.2, labelspacing=.3)
    fig.text(.772, .214, "Percentage change from Trade to Metatrade", ha="center", fontsize=8.8)


def main():
    initial_plot_settings()
    fig = plt.figure(figsize=(10.5, 10.2))
    draw_hi_maps(fig, load_boundaries())
    draw_market(fig)
    draw_health(fig)
    fig.savefig(HERE/"figure 6.png", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    main()

