"""Plot the four panels of Figure 3 and save figure 3.png at 300 dpi.

Run with Python, matplotlib, numpy and networkx installed. The CSV and GeoJSON input files sit beside this script.

a: 2020 sheet of summary food emissions.xlsx, 47 countries in plot order.
b: arithmetic mean sum-of-seven HI in 2020 Trade. Full precision comes from
   the archived 0105 total_exposure summary and matches the historical map
   workbook expo risks.xlsx, sheet 2020, Sum. Each country value rounds to
   the current SI Table 2 entry. Gray land has no independent estimate in the
   47-country dataset. The historical map also coloured Taiwan using China's
   estimate; this redraw leaves that extra map entry gray.
c: 'to plot' sheet of positive and negtive counts.xlsx, 23 endpoints. Markers
   show direction agreement in the simulated population. The bars share a
   continuous linear percentage axis.
d: current 60% Figure 3d source, including albumin/globulin ratio and study LDL.
   See indicator_network_references.txt for the evidence behind the links.
"""

import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcdefaults()

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, PathPatch
from matplotlib.path import Path as DrawingPath
import networkx as nx
import numpy as np


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "figure 3.png"
HI_COLOURS = ["#AFC99C", "#FFFFFF", "#FFBFC0", "#D63235", "#AB0003", "#700002", "#000000"]
HI_CMAP = LinearSegmentedColormap.from_list("figure_3b", HI_COLOURS)
HI_NORM = Normalize(vmin=0, vmax=6, clip=True)
PALETTE = {"hepatic": "#ff9999", "renal": "#DBD084", "cardiovascular": "#ffcc99",
           "immune": "#DB6FAB", "source": "#95a5a6"}
COUNTRY_LABELS = {"Korea": "South Korea", "SouthKorea":"South Korea", "SouthKorea ": "South Korea"}
HEADINGS = [(1.13,.34,"Hepatic","#9D4D58"),(7.86,.33,"Renal","#7C7130"),
            (.75,4.57,"CVD","#C56607"),(6.03,4.64,"Immune","#7E2053")]


def source_rows(name):
    with (HERE / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def heading(fig, letter, title, x, y, gap=.042):
    fig.text(x,y,letter,weight="bold",fontsize=12,ha="left",va="center")
    fig.text(x+gap,y,title,fontsize=12,ha="left",va="center")


def plot_emissions(fig, data):
    ax=fig.add_axes([.114,.760,.811,.204])
    x=np.arange(len(data))
    aquatic=np.array([float(r["Aquatic_kg_CO2e_per_capita_year"]) for r in data])
    terrestrial=np.array([float(r["Terrestrial_kg_CO2e_per_capita_year"]) for r in data])
    ax.bar(x,terrestrial,width=.68,color="#74965B",linewidth=0,zorder=3)
    ax.bar(x,aquatic,bottom=terrestrial,width=.68,color="#F29A9D",linewidth=0,zorder=3)
    ax.set_xlim(-1,len(data))
    ax.set_ylim(0,2100)
    ax.set_yticks([0,500,1000,1500,2000])
    ax.set_xticks(x, [COUNTRY_LABELS.get(row["Country"],row["Country"]) for row in data],
                  fontsize=8.2, rotation=90)
    ax.tick_params(axis="x",length=0,pad=4)
    ax.tick_params(axis="y",length=0,pad=5,labelsize=8.8)
    ax.grid(axis="x",color="#D7D7D7",lw=.65,linestyle="--",zorder=0)
    ax.set_ylabel("Emission (kg CO₂-eq/year/cap)",fontsize=9.4,labelpad=6)
    ax.legend(handles=[Patch(fc="#F29A9D",label="aquatic"),Patch(fc="#74965B",label="terrestrial")],
              frameon=False,loc="upper left",ncol=2,borderpad=.28,handlelength=1.15,
              columnspacing=1.25,fontsize=9.5)
    for spine in ax.spines.values():
        spine.set_linewidth(1.05)


def _read_country_hi():
    read = source_rows("country_hi_2020_trade.csv")
    values = {row["ISO3"]: float(row["HI_2020_Trade"]) for row in read}
    if len(values) != len(read) or len(values) != 47:
        raise ValueError(f"Expected 47 unique country HI values, got {len(values)}.")
    if any(not len(iso) == 3 or not math.isfinite(value) or value < 0
           for iso, value in values.items()):
        raise ValueError("Invalid ISO3 code or hazard index in country_hi_2020_trade.csv.")
    return values


def _country_code(feature):
    props = feature["properties"]
    for key in ("ISO_A3", "ADM0_A3", "iso_a3"):
        value = props.get(key)
        if isinstance(value, str) and value.isalpha() and len(value) == 3:
            return value.upper()
    return None


def _closed_ring(coordinates, *, is_hole):
    points = [(float(pair[0]), float(pair[1])) for pair in coordinates]
    if not points or len(points) < 3:
        return None
    if points[0] != points[-1]:
        points.append(points[0])
    signed_area = sum(x1 * y2 - x2 * y1 for ((x1, y1), (x2, y2)) in zip(points, points[1:]))
    if (signed_area > 0) == is_hole:
        points.reverse()
    path_codes = [DrawingPath.MOVETO] + [DrawingPath.LINETO] * (len(points) - 2) + [DrawingPath.CLOSEPOLY]
    return DrawingPath(points, path_codes)


def _country_path(geometry):
    if not geometry:
        return None
    kind = geometry["type"]
    if kind == "Polygon":
        polygons = [geometry["coordinates"]]
    elif kind == "MultiPolygon":
        polygons = geometry["coordinates"]
    else:
        raise ValueError(f"Unsupported world polygon: {kind}")
    rings = []
    for polygon in polygons:
        for index, coordinates in enumerate(polygon):
            ring = _closed_ring(coordinates, is_hole=index != 0)
            if ring is not None:
                rings.append(ring)
    return DrawingPath.make_compound_path(*rings) if rings else None


def _latlon(value, positive, negative):
    return f"{abs(value)}°{positive if value > 0 else negative if value < 0 else ''}"


def _draw_map_legend(fig, rect, font_size):
    left, bottom, width, height = rect
    bar_x = left + width * 0.916
    bar_width = width * 0.012
    bar_y = bottom + height * 0.277
    bar_height = height * 0.520
    bar = fig.add_axes((bar_x, bar_y, bar_width, bar_height))
    bounds = [step / 100 for step in range(551)]
    bar.pcolormesh(
        [0, 1], bounds, [[(a + b) / 2] for a, b in zip(bounds, bounds[1:])],
        cmap=HI_CMAP, norm=HI_NORM, shading="flat", antialiased=False,
        edgecolors="face", linewidth=0,
    )
    bar.set(xticks=[], yticks=range(6), ylim=(0, 5.5))
    bar.yaxis.tick_right()
    bar.tick_params(axis="y", width=.5, length=2, pad=2, labelsize=font_size)
    for spine in bar.spines.values():
        spine.set_linewidth(.6)

    gap = height * .021
    top = fig.add_axes((bar_x, bar_y + bar_height + gap, bar_width, height * .059))
    fig.text(bar_x + bar_width / 2, bar_y + bar_height + gap + height * .087,
             "HI", ha="center", va="bottom", fontsize=font_size)
    top.set_facecolor("#000000")
    top.set(xticks=[], yticks=[18], ylim=(17, 18))
    top.yaxis.tick_right()
    top.tick_params(axis="y", width=.5, length=2, pad=2, labelsize=font_size)
    for spine in top.spines.values():
        spine.set_linewidth(.6)
    # Short diagonal strokes mark the omitted legend interval (5.5–17.0).
    for axis, y in [(bar, 1), (top, 0)]:
        axis.plot((-.25, 1.25), (y - .01, y + .01), color="#FFFFFF", lw=2.0,
                  transform=axis.transAxes, zorder=5, clip_on=False)
        axis.plot((-.25, 1.25), (y - .01, y + .01), color="#333333", lw=.5,
                  transform=axis.transAxes, zorder=6, clip_on=False)


def draw_map(fig, rect, *, font_size):
    """Draw panel 3b in a figure-fraction rectangle (left, bottom, width, height)."""
    values = _read_country_hi()
    with (HERE/"fig3b_world_boundaries.geojson").open(encoding="utf-8-sig") as source:
        features = json.load(source)["features"]
    left, bottom, width, height = rect
    panel_rect = (left + width * .100, bottom + height * .133, width * .783, height * .77)
    ax = fig.add_axes(panel_rect)
    ax.set_facecolor("#FFFFFF")
    located = set()
    for feature in sorted(features, key=lambda feature: _country_code(feature) in values):
        code = _country_code(feature)
        path = _country_path(feature["geometry"])
        if path is None:
            continue
        modeled = code in values
        if modeled:
            located.add(code)
        ax.add_patch(PathPatch(
            path, facecolor=HI_CMAP(HI_NORM(values[code])) if modeled else "#DBDBDB",
            edgecolor="#262626" if modeled else "#A6A6A6",
            linewidth=.42 if modeled else .34, joinstyle="round",
            zorder=3 if modeled else 2,
        ))
    missing = set(values) - located
    if missing:
        raise ValueError("Country boundaries were not matched for " + ", ".join(sorted(missing)))

    longitude = list(range(-180, 181, 60))
    latitude = list(range(-60, 91, 30))
    ax.set_xlim(-180, 180)
    ax.set_ylim(-60, 90)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks(longitude, [_latlon(value, "E", "W") for value in longitude])
    ax.set_yticks(latitude, [_latlon(value, "N", "S") for value in latitude])
    ax.tick_params(labelsize=font_size, length=2.1, width=.65, pad=2)
    ax.grid(which="major", color="#797979", linestyle=(0, (2, 1.6)), linewidth=.52, alpha=.78, zorder=1)
    for spine in ax.spines.values():
        spine.set_color("#202020")
        spine.set_linewidth(.65)
    _draw_map_legend(fig, rect, font_size)


def plot_outcomes(fig, data):
    y=np.arange(len(data))
    positive=np.array([float(r["Percent_increase"])/100 for r in data])
    negative=-np.array([float(r["Percent_decrease"])/100 for r in data])
    increase,decrease="#E57373","#81C784"
    ax = fig.add_axes([.590, .075, .132, .514])
    ax.barh(y, positive, height=.60, color=increase, linewidth=0, zorder=2)
    ax.barh(y, negative, height=.60, color=decrease, linewidth=0, zorder=2)
    ax.set_xlim(-1.12, 1.12)
    ax.set_ylim(len(y)+.43, -1.12)
    ax.set_xticks([-1, -.50, 0, .50, 1], ["−100%", "−50%", "0%", "50%", "100%"],
                  rotation=42, ha="right")
    ax.set_yticks(y, [])
    ax.tick_params(axis="x", length=2.3, pad=2.2, labelsize=8.1)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="y", lw=.65, linestyle="--", color="#CECECE", zorder=1)
    for side in ("left", "right"):
        ax.spines[side].set_visible(False)
    for side in ("top", "bottom"):
        ax.spines[side].set_linewidth(.75)

    for threshold in (-.90, .90):
        ax.axvline(threshold, color="#737373", linestyle="--", linewidth=.85, zorder=3)
    ax.axvline(0, color="black", linewidth=.9, zorder=3)
    for i, row in enumerate(data):
        agreement = float(row["Majority_direction_agreement_percent"])
        if agreement > 90:
            ax.plot(1.073, i, "o", markersize=4.25, markeredgewidth=.82, color="black",
                    markerfacecolor="black" if agreement > 95 else "white", zorder=4)
        ax.text(1.19, i, row["Indicator"], transform=ax.get_yaxis_transform(),
                fontsize=8.28, va="center", ha="left")

    for x,face,label,y0 in ((.592,"black",">95%",.618),(.592,"white",">90%",.603)):
        fig.add_artist(Line2D([x],[y0],transform=fig.transFigure,marker="o",markersize=4.3,
                             linestyle="",markerfacecolor=face,markeredgecolor="black",
                             markeredgewidth=.8))
        fig.text(x+.011,y0,label,fontsize=7.9,va="center")
    for color,label,y0 in ((increase,"Population share with a modeled increase",.618),
                           (decrease,"Population share with a modeled decrease",.603)):
        fig.add_artist(Line2D([.665],[y0],transform=fig.transFigure,marker="s",markersize=5.4,
                             linestyle="",markerfacecolor=color,markeredgecolor=color))
        fig.text(.677,y0,label,fontsize=8.0,va="center")
    fig.text(.655,.025,"Simulated population (%)",fontsize=8.0,ha="center")


def plot_network(fig, nodes, links):
    rect=[.043,.021,.480,.357]
    ax=fig.add_axes(rect)
    ax.set(xlim=(0,9),ylim=(7,0),aspect="equal",anchor="W")
    ax.set_axis_off()
    info={row["Node"]:row for row in nodes}
    graph=nx.Graph()
    graph.add_edges_from((row["from_code"],row["to_code"]) for row in links)
    assert set(graph)==set(info) and nx.is_connected(graph)
    positions={key:(float(row["X"]),float(row["Y"])) for key,row in info.items()}
    width_inches=min(rect[2]*fig.get_figwidth(),rect[3]*fig.get_figheight()*9/7)
    ratio=width_inches/5.4
    area=[(300+(5 if key=="PFAS" else graph.degree[key])**3*100)*(.60*ratio)**2 for key in graph]
    nx.draw_networkx_nodes(graph,positions,node_size=area,
                           node_color=[PALETTE[info[key]["Domain"]] for key in graph],
                           alpha=.85,edgecolors="none",linewidths=0,ax=ax)
    distance=nx.shortest_path_length(graph,source="PFAS")
    farthest=max(distance.values())
    for a,b in graph.edges:
        portion=min(distance[a],distance[b])/farthest
        nx.draw_networkx_edges(graph,positions,edgelist=[(a,b)],
                               width=(5-4.5*portion)*.60*ratio,
                               alpha=max(.60-.30*portion,.10),edge_color="gray",ax=ax)
    for key,row in info.items():
        x,y=positions[key]
        context=row["Context"]=="1"
        ax.text(x,y,row["Label"],fontsize=(9 if context else 12)*ratio,
                fontweight="normal" if context else "bold",
                fontstyle="italic" if context else "normal",
                ha="center",va="center",zorder=5)
    for x,y,label,color in HEADINGS:
        ax.text(x,y,label,fontsize=20*ratio,fontweight="bold",color=color,
                ha="center",va="center",zorder=10)


def main():
    plt.rcParams.update({"font.family":"DejaVu Sans","figure.facecolor":"white",
                         "savefig.facecolor":"white","axes.facecolor":"white"})
    emissions=source_rows("food_ghg_emissions_2020.csv")
    outcomes=source_rows("health_outcomes_2020.csv")
    assert len(emissions)==47 and len(outcomes)==23
    fig=plt.figure(figsize=(10.2,10.2))
    heading(fig,"a","Food-sourced GHG emissions per capita in 2020",.046,.982,gap=.071)
    heading(fig,"b","Hazard index",.047,.643)
    heading(fig,"c","Population health outcomes",.577,.643,gap=.045)
    heading(fig,"d","Relationships among health outcomes",.046,.395)
    plot_emissions(fig,emissions)
    draw_map(fig,[.041,.419,.520,.212],font_size=8.2)
    plot_outcomes(fig,outcomes)
    plot_network(fig,source_rows("indicator_network_nodes.csv"),source_rows("indicator_network_links.csv"))
    fig.savefig(OUTPUT,dpi=300)
    plt.close(fig)


if __name__=="__main__":
    main()

