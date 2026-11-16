"""Rebuild Figure 4 using the CSV and GeoJSON files in this folder.

a uses the plotted LR 0127 series and 2020 world weights in persons for Greece
and Spain. It is also exported as a standalone panel. b uses the original aquatic
consumption and EDI data, and c–e the absolute 2050 Metatrade minus 2020 Trade HI changes. f–l compare
scenario means and quartiles with the archived regional 2020 Trade mean.
Unmodeled areas are gray. Requires Python, Matplotlib and NumPy.
"""


import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcdefaults()

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap, Normalize
from matplotlib.lines import Line2D
from matplotlib.path import Path as DrawPath
from matplotlib.patches import Patch, PathPatch, Rectangle
from matplotlib.ticker import PercentFormatter
from matplotlib.transforms import Bbox


HERE = Path(__file__).resolve().parent
PALETTE_PATHWAY = {"LR": "#D9D576", "BAU": "#DE8E31", "HR": "#CF3B3B"}


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



SCENARIO_LABEL = {"LR":"Low Road","BAU":"Business As Usual","HR":"High Road"}
PATTERNS = {"LR":"o","BAU":"s","HR":"^"}


def draw_intensities(fig):
    data=rows("ghg_emission_intensity.csv")
    world,*countries=data
    x=list(range(len(countries)))
    ax=fig.add_axes([.128,.805,.757,.168])
    ax.set_xlim(-.9,len(x)-.1)
    ax.set_ylim(70,120)
    ax.yaxis.set_major_formatter(PercentFormatter(100,decimals=0))
    ax.set_ylabel("Ratio relative to 2020",fontsize=9)
    ax.set_xticks(x,[r["Country"] for r in countries],rotation=90,fontsize=7.7)
    ax.tick_params(axis="x",length=0,pad=3)
    ax.tick_params(axis="y",length=0,labelsize=8,pad=4)
    ax.grid(axis="x",linestyle="--",color="#C9C9C9",linewidth=.72)
    ax.axhline(100,color="black",lw=1.05,zorder=2)
    base=fig.transFigure.inverted().transform(ax.transData.transform((x[-1],100)))[1]
    fig.text(.888,base-.002,"2020 baseline",fontsize=6.9,va="center")
    for key,color,edge in zip(SCENARIO_LABEL,("#9DD44B","#FFBA50","#FF5C58"),("#538B29","#A76214","#C12620")):
        field=f"{key}_relative_to_2020_pct"
        ax.scatter(x,[float(r[field]) for r in countries],s=17,marker="o",c=color,
                   edgecolor=edge,lw=.7,zorder=5,label=key)
        number=float(world[field])
        ax.axhline(number,ls="--",color=edge,linewidth=1.15,zorder=3)
        fig.text(.888,fig.transFigure.inverted().transform(ax.transData.transform((0,number)))[1],
                 f"{number:.1f}%",fontsize=7.5,va="center")
    handles,labels=ax.get_legend_handles_labels()
    handles.append(Line2D([0,1],[0,0],color="#444444",ls="--",lw=1.15,label="world average"))
    ax.legend(handles=handles,loc="upper left",frameon=False,ncol=4,fontsize=7.8,
              columnspacing=.55,handletextpad=.20,borderpad=.3,handlelength=1.25)


def draw_consumption(fig):
    data=rows("aquatic_consumption_and_exposure.csv")
    values={(r["Income_group"],r["Scenario"],r["Measure"],r["Seafood_group"]):float(r["Value"]) for r in data}
    ax=fig.add_axes([.113,.518,.352,.163])
    scenarios=("2020","LR","BAU","HR")
    groups=("Other Seafood","Marine Fish","Freshwater Fish")
    measure_names=tuple(dict.fromkeys(r["Measure"] for r in data))
    assert len(measure_names)==2
    colors=(("#C7E6C4","#97C78A","#63A365"),("#FDC7C9","#FF989B","#E4787B"))
    for j,income in enumerate(("Middle income","High income")):
        for i,scenario in enumerate(scenarios):
            for k,measure in enumerate(("consumption",next(name for name in measure_names if name!="consumption"))):
                x=j*4.7+i+(.165 if k else -.165)
                bottom=0
                for group,color in zip(groups,colors[k]):
                    y=values[income,scenario,measure,group]*(10 if k else 1)
                    ax.bar(x,y,bottom=bottom,width=.32,color=color,linewidth=0,zorder=3)
                    bottom+=y
    ax.set(xlim=(-.62,8.35),ylim=(0,60))
    ax.set_xticks([*range(4),*(4.7+i for i in range(4))],[*scenarios,*scenarios])
    ax.tick_params(axis="both",length=0,labelsize=7.7,pad=3)
    ax.set_ylabel("Consumption per capita (kg/year)",fontsize=8.4,labelpad=2.5)
    right=ax.secondary_yaxis("right",functions=(lambda a:a/10,lambda a:a*10))
    right.set_ylabel("Σ₇PFAS EDI (ng/kg bw/day)",fontsize=8.4,labelpad=4)
    right.tick_params(length=0,pad=3,labelsize=7.7)
    ax.grid(axis="y",color="#A5CCA2",linestyle="--",linewidth=.62)
    ax.text(.242,-.125,"middle income",transform=ax.transAxes,ha="center",va="top",fontsize=7.9)
    ax.text(.755,-.125,"high income",transform=ax.transAxes,ha="center",va="top",fontsize=7.9)
    ax.plot((.5,.5),(0,-.19),transform=ax.transAxes,color="black",lw=.65,clip_on=False)
    for j,group in enumerate(reversed(groups)):
        y=.93-.096*j
        k=2-j
        for i,x in enumerate((.591,.684)):
            ax.add_patch(Rectangle((x,y-.024),.038,.052,transform=ax.transAxes,fc=colors[i][k],ec="none"))
        ax.text(.738,y,group.replace(" Fish","").lower(),transform=ax.transAxes,fontsize=7.0,va="center")
    ax.text(.609,.62,"consume",transform=ax.transAxes,ha="center",va="center",fontsize=7.1)
    ax.text(.704,.62,"EDI",transform=ax.transAxes,ha="center",va="center",fontsize=7.1)


def draw_scenarios(fig,boundary):
    data=rows("country_hi_scenario_change.csv")
    palette = np.loadtxt(HERE/"hi_map_colors.csv", delimiter=",", skiprows=1) / 255
    cmap = ListedColormap(palette)
    norm=Normalize(-1.5,3,clip=True)
    fig.text(.742,.722,"Hazard index change from 2020 to 2050",ha="center",va="center",fontsize=11.3)
    for y,(letter,scenario) in zip((.565,.401,.237),zip("cde",SCENARIO_LABEL)):
        fig.text(.546,y+.143,letter,fontsize=11.5,weight="bold",va="center")
        fig.text(.746,y+.139,SCENARIO_LABEL[scenario],fontsize=9.4,ha="center",va="center")
        values = {r["ISO3"]: float(r[f"Delta_HI_{scenario}"]) for r in data}
        assert len(values) == 47
        plot_world(fig.add_axes([.600,y,.314,.131]),boundary,values,cmap,norm,tick_size=7.4)
    colorbar(fig,[.516,.586,.006,.095],cmap,norm,[-1.5,0,1.5,3],
             ["−1.5","0.0","1.5","3.0"],"ΔHI")


def draw_health_axis(ax,data,*,world=False,show_labels=False):
    endpoint={int(r["Endpoint_order"]):r["Endpoint"] for r in data}
    count=len(endpoint)
    ax.axhspan(.5,2.5,color="#999999",linewidth=0)
    ax.set_ylim(count+1.05,.0)
    ax.set_xlim(-250,250)
    axis_ticks=[-200,-100,0,100,200] if world else [-200,0,200]
    ax.set_xticks(axis_ticks,[f"{v:.0f}%" for v in axis_ticks])
    ax.tick_params(axis="x",length=1.6,pad=2,labelsize=6.9)
    ax.set_yticks(list(range(1,count+1)),[endpoint[i] if show_labels else "" for i in range(1,count+1)])
    ax.tick_params(axis="y",length=0,pad=3,labelsize=7.0 if world else 6.6)
    ax.grid(axis="x",ls=":",color="#707070",lw=.54,zorder=0)
    y_offset={"LR":-.22,"BAU":0,"HR":.22}
    for r in data:
        scenario=r["Scenario"]
        y=int(r["Endpoint_order"])+y_offset[scenario]
        color=PALETTE_PATHWAY[scenario]
        fill=r["Filled_marker"]=="1"
        ax.hlines(y,float(r["Range_left_percent"]),float(r["Range_right_percent"]),
                  color=color,alpha=.9 if fill else .34,linewidth=1.35,zorder=2)
        ax.plot(float(r["Mean_change_percent"]),y,marker=PATTERNS[scenario],linestyle="none",
                markerfacecolor=color if fill else "white",markeredgecolor=color,
                markersize=4.3 if world else 3.6,markeredgewidth=.74,zorder=3)


def draw_outcomes(fig):
    data=rows("fig4_health_outcomes.csv")
    world=[r for r in data if r["Panel"]=="f"]
    handles = [
        Line2D([0], [0], marker=PATTERNS[scenario], color=PALETTE_PATHWAY[scenario],
               linestyle="", markersize=5.3, label=label)
        for scenario, label in SCENARIO_LABEL.items()
    ]
    handles.extend([
        Line2D([0], [0], marker="o", color="#777777", linestyle="", markersize=4.6, label="Mean"),
        Line2D([0, 1], [0, 0], color="#999999", lw=1.1, label="25th–75th percentiles"),
        Patch(fc="#999999", label="Disease outcome"),
        Line2D([0], [0], marker="o", markerfacecolor="white", color="#777777", linestyle="",
               markersize=4.6, label="P10–P90 includes zero"),
        Line2D([0], [0], marker="o", color="#777777", linestyle="", markersize=4.6,
               label="P10–P90 excludes zero"),
    ])
    fig.text(.153,.470,"Modeled health outcomes",fontsize=11.3)
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(.153, .442),
               ncol=4, fontsize=6.35, frameon=False, borderaxespad=0,
               labelspacing=.37, columnspacing=1.2, handlelength=1.1, handletextpad=.43)
    fig.text(.153,.430,"f",weight="bold",fontsize=11)
    fig.text(.333,.430,"World",ha="center",fontsize=9.2)
    draw_health_axis(fig.add_axes([.153,.248,.367,.173]),world,world=True,show_labels=True)
    fig.text(.337,.226,"Percentage change relative to the 2020 Trade mean",ha="center",fontsize=7.6)
    region_titles=("Latin America","North America","Northern Europe","Eastern Europe","East Asia","South & SE Asia")
    for index,(letter,region) in enumerate(zip("ghijkl",region_titles)):
        x=.153+index*.1295
        fig.text(x,.210,letter,weight="bold",fontsize=10)
        fig.text(x+.019,.210,region,fontsize=8.1)
        draw_health_axis(fig.add_axes([x,.038,.118,.163]),
                         [r for r in data if r["Panel"]==letter],show_labels=index==0)
    fig.text(.535,.014,"Percentage change relative to the 2020 Trade mean",ha="center",fontsize=8.0)


def main():
    initial_plot_settings()
    fig=plt.figure(figsize=(10.1,11.35))
    panel_title(fig,"a","Food average emission intensity relative to 2020",.079,.986,gap=.177)
    draw_intensities(fig)
    width, height = fig.get_size_inches()
    panel_a_bounds = Bbox.from_extents(.060 * width, .718 * height, .966 * width, .997 * height)
    fig.savefig(HERE / "figure 4a.png", dpi=300, bbox_inches=panel_a_bounds)

    panel_title(fig,"b","Aquatic consumption and exposure",.079,.714,gap=.041)
    draw_consumption(fig)
    draw_scenarios(fig,load_boundaries())
    draw_outcomes(fig)
    fig.savefig(HERE/"figure 4.png",dpi=300)
    plt.close(fig)


if __name__=="__main__":
    main()

