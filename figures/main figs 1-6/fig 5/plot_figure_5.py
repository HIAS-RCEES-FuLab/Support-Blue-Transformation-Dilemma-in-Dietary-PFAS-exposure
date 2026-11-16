"""Rebuild the four panels of Figure 5 from the local CSV and GeoJSON files.

The manuscript artwork and archived plotting input use the percentage change
in HI for panel a. Its manuscript caption describes EDI. The CSV preserves both
values, and this script uses HI to reproduce the artwork. Panel b uses the
archived EDI source shares. Panel c aggregates aquatic PFAS flows, excludes
domestic flows and displays the five largest importing countries. Panel d uses
the archived top-ten exporter impacts. Requires Matplotlib and NumPy.
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
from matplotlib.patches import Patch, PathPatch, Rectangle


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



FOOD_SOURCES = (
    ("Imported_aquatic_share","import aquatic","#D6772D"),
    ("Domestic_aquatic_share","domestic aquatic","#FFD6AD"),
    ("Imported_terrestrial_share","import terrestrial","#D4C764"),
    ("Domestic_terrestrial_share","domestic terrestrial","#F0FAC1"),
)
REGION_LABELS = {"United States":"USA","Canada":"CAN","China":"CHN","Norway":"NOR",
                 "Germany":"DEU","Japan":"JPN","Korea":"KOR","France":"FRA",
                 "Europe":"Europe+","Asia":"Asia-","Latin America":"LA","Africa":"AF",
                 "Oceania":"OA","North America":"North America"}
SANKEY_COLORS = {"United States":"#A0C792","Canada":"#62A197","China":"#9F585A",
                  "Norway":"#B2AD26","Germany":"#D4BB2B","Europe":"#D0D95E",
                  "Asia":"#E99690","Latin America":"#D48A2F","Africa":"#696969",
                  "Oceania":"#AF6625","North America":"#6F9060","Japan":"#B87591",
                  "Korea":"#C77E63","France":"#9BA949"}
EXPORT_REGION = {"United States":"North America","Canada":"North America","China":"Asia",
                 "Norway":"Europe","Germany":"Europe"}


def draw_hi_map(fig,boundary):
    data=rows("country_trade_hi_edi_2020.csv")
    values={r["ISO3"]:float(r["Relative_HI_change"]) for r in data}
    assert len(values)==47
    cmap=LinearSegmentedColormap.from_list("trade_hi",[(0,"#3B5926"),(.25,"#FFFFFF"),
                                                                (.50,"#C10404"),(1,"#4F000C")])
    norm=Normalize(-.5,1.5,clip=True)
    plot_world(fig.add_axes([.087,.706,.360,.252]),boundary,values,cmap,norm,tick_size=8.3)
    colorbar(fig,[.471,.766,.006,.143],cmap,norm,[-.5,0,.5,1,1.5],
             ["−50%","0%","50%","100%","150%"],"HI change")


def draw_contribution(fig):
    data=rows("country_edi_source_shares.csv")
    assert len(data)==47
    ax=fig.add_axes([.742,.033,.195,.868])
    y=np.arange(len(data))
    left=np.zeros(len(data))
    for key,label,color in FOOD_SOURCES:
        width=np.array([float(row[key]) for row in data])
        ax.barh(y,width,left=left,height=.93,color=color,edgecolor="#4D4949",linewidth=.6)
        for i,share in enumerate(width):
            if share>=.055:
                ax.text(left[i]+share/2,i,f"{100*share:.0f}%",ha="center",va="center",
                        fontsize=5.8,color="#5E5A53")
        left+=width
    assert np.allclose(left,1,rtol=0,atol=1e-9)
    ax.set_ylim(len(data)-.5,-.5)
    ax.set_xlim(0,1)
    ax.set_yticks(y,[row["Country"] for row in data],fontsize=7.7)
    ax.set_xticks(np.linspace(0,1,6),[f"{i}%" for i in range(0,101,20)])
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")
    ax.tick_params(axis="both",length=0,pad=4)
    ax.tick_params(axis="x",labelsize=8)
    ax.set_xlabel("Share of EDI",fontsize=9,labelpad=6)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.legend(handles=[Patch(fc=color,ec="#4D4949",label=label) for _,label,color in FOOD_SOURCES],
               fontsize=8.4,loc="upper left",bbox_to_anchor=(.534,.921),frameon=False,
               handlelength=1.1,handletextpad=.45,labelspacing=.35,borderpad=0)


def bands_for(flows,groups,idx,other_rank,scale):
    cursor=.123
    bands,links={},{}
    for group in groups:
        start=cursor
        current=sorted((pair for pair in flows if pair[idx]==group),key=lambda pair:other_rank[pair[1-idx]])
        for pair in current:
            stop=cursor+flows[pair]*scale
            links[pair]=(cursor,stop)
            cursor=stop
        bands[group]=(start,cursor,(cursor-start)/scale)
    return bands,links


def bounded_groups(ax,bands,groupings,y,above):
    for group,names in groupings.items():
        start=bands[names[0]][0]
        end=bands[names[-1]][1]
        color=SANKEY_COLORS[group]
        bottom=y+.052 if above else y-.052
        ax.annotate("", xy=(end, y), xytext=(start, y),
                    arrowprops={"arrowstyle":"<->", "color":color, "lw":.72,
                                "mutation_scale":5.2, "shrinkA":0, "shrinkB":0})
        for x in (start,end):
            ax.plot((x,x),(y-.013,y+.013),color=color,lw=.65)
            ax.plot((x,x),(y,bottom),color=color,lw=.65)
        mid=(start+end)/2
        if group=="Oceania":
            mid+=.013 if above else .002
        if group=="Africa" and not above:
            mid+=.018
        ax.text(mid,y-.025 if above else y+.030,REGION_LABELS[group],ha="center",
                va="center",fontsize=7.3)


def draw_trade_flows(fig):
    data=rows("aquatic_pfas_trade_flows_2020.csv")
    flows={(r["Exporter"],r["Importer"]):float(r["Amount_kg_year"]) for r in data}
    ex_order={r["Exporter"]:int(r["Exporter_order"]) for r in data}
    im_order={r["Importer"]:int(r["Importer_order"]) for r in data}
    import_regions={r["Importer"]:r["Importer_region"] for r in data}
    scale=.792/sum(flows.values())
    exporters=sorted(ex_order,key=ex_order.__getitem__)
    importers=sorted(im_order,key=im_order.__getitem__)
    exports,starts=bands_for(flows,exporters,0,im_order,scale)
    imports,ends=bands_for(flows,importers,1,ex_order,scale)
    ax=fig.add_axes([.019,.327,.621,.318],xlim=(0,1),ylim=(1,0))
    ax.set_axis_off()
    yt,yb,h=.159,.790,.055
    for pair in sorted(flows,key=flows.__getitem__,reverse=True):
        l0,r0=starts[pair]
        l1,r1=ends[pair]
        source_y,target_y=yt+h,yb
        bend=.56*(target_y-source_y)
        outline=DrawPath([(l0,source_y),(l0,source_y+bend),(l1,target_y-bend),(l1,target_y),
                          (r1,target_y),(r1,target_y-bend),(r0,source_y+bend),(r0,source_y),(l0,source_y)],
                         [DrawPath.MOVETO,*[DrawPath.CURVE4]*3,DrawPath.LINETO,
                          *[DrawPath.CURVE4]*3,DrawPath.CLOSEPOLY])
        ax.add_patch(PathPatch(outline,fc=SANKEY_COLORS[pair[0]],alpha=.57,ec="none"))
    for is_export,bands,y in ((True,exports,yt),(False,imports,yb)):
        for name,(left,right,amount) in bands.items():
            ax.add_patch(Rectangle((left,y),right-left,h,facecolor=SANKEY_COLORS[name],
                                   edgecolor="#3E3E3E",linewidth=.47,zorder=2))
            x=(left+right)/2
            tops={"Norway":.697,"Germany":.738,"Africa":.899,"Oceania":.949}
            bottoms={"Asia":.561,"France":.595,"North America":.835,
                     "Latin America":.879,"Oceania":.915,"Africa":.949}
            x=(tops if is_export else bottoms).get(name,x)
            ax.text(x,y-.033 if is_export else y+h+.027,f"{amount:.1f}",
                    ha="center",va="center",fontsize=7.55)
            is_individual=name in (EXPORT_REGION if is_export else
                      {"China","Japan","Korea","France","United States"})
            if is_individual:
                ax.text(x,y-.071 if is_export else y+h+.067,REGION_LABELS[name],
                        ha="center",va="center",fontsize=6.1)
    ex_groups,im_groups=defaultdict(list),defaultdict(list)
    for n in exporters: ex_groups[EXPORT_REGION.get(n,n)].append(n)
    for n in importers: im_groups[import_regions[n]].append(n)
    bounded_groups(ax,exports,ex_groups,.064,True)
    bounded_groups(ax,imports,im_groups,.948,False)
    ax.annotate("",xy=(.082,yb+h),xytext=(.082,yt),arrowprops={"arrowstyle":"-|>","lw":1.5,"color":"black"})
    ax.text(.081,yt-.018,"export\n(kg/year)",ha="center",va="bottom",fontsize=7.4)
    ax.text(.081,yb+h+.012,"import\n(kg/year)",ha="center",va="top",fontsize=7.4)
    ax.text(.057,(yt+yb+h)/2,"PFAS",rotation=90,ha="center",va="center",fontsize=7.4)


def draw_change_by_exporter(fig):
    records=rows("exporter_pfas_intake_changes.csv")
    ax=fig.add_axes([.125,.099,.497,.167])
    y=np.arange(len(records))
    ax.set_xlim(-9,2)
    ax.set_ylim(len(records)-.5,-.5)
    settings=(("Africa","#898989"),("Asia","#FFC1BC"),("Europe","#DDE888"),
              ("Latin America","#DAA25F"),("North America","#96B08A"),("Oceania","#B47A40"))
    levels=np.zeros((2,len(records)))
    for region,color in settings:
        values=np.array([float(row[region]) for row in records])
        axis=values>=0
        left=np.where(axis,levels[0],levels[1])
        ax.barh(y,values,left=left,fc=color,ec="#E7E7E7",linewidth=.55,height=.84)
        levels[0]+=np.where(axis,values,0)
        levels[1]+=np.where(axis,0,values)
    ax.axvline(0,color="black",linewidth=1.3)
    ax.set_xticks(range(-9,3))
    ax.set_yticks(y,[row["Exporter"] for row in records],fontsize=7.8)
    ax.tick_params(length=2,pad=2,labelsize=7.8)
    ax.tick_params(axis="y", pad=8)
    for i,row in enumerate(records):
        high=float(row["Exporter_aquatic_Sum7_ng_g_wet_weight"])>2
        ax.plot(-.015,i,"o",transform=ax.get_yaxis_transform(),clip_on=False,
                markersize=4.3,markeredgecolor="#555555",markeredgewidth=.67,
                markerfacecolor="#C85B10" if high else "#75A948",zorder=4)
    ax.set_xlabel("Change in regional PFAS intake (kg/year)",fontsize=8.8,labelpad=3)
    handles=[Patch(fc=color,label={"Europe":"Europe+","Asia":"Asia-"}.get(k,k)) for k,color in reversed(settings)]
    fig.legend(handles=handles,loc="upper center",bbox_to_anchor=(.376,.055),ncol=3,frameon=False,
               fontsize=6.8,handlelength=1.2,handletextpad=.4,columnspacing=1.0,labelspacing=.34,
               title="Import regions",title_fontsize=7.25)
    markers=[Line2D([0],[0],marker="o",color="#555555",markerfacecolor=col,
             linestyle="",markersize=4.3,markeredgewidth=.67,label=label)
             for col,label in (("#C85B10",">2 ng/g ww"),("#75A948","<2 ng/g ww"))]
    fig.legend(handles=markers,loc="upper left",bbox_to_anchor=(.019,.088),frameon=False,
               title="Exporter mean Σ₇PFAS",title_fontsize=7,fontsize=6.9,
               handlelength=1.0,handletextpad=.35,labelspacing=.32,borderpad=.3)


def main():
    initial_plot_settings()
    fig=plt.figure(figsize=(11.2,8.32))
    panel_title(fig,"a","HI change from No Trade to Trade in 2020",.064,.981,gap=.052)
    panel_title(fig,"b","Source contributions to exposure",.542,.981,gap=.122)
    panel_title(fig,"c","Aquatic PFAS flows in international trade",.063,.667,gap=.080)
    panel_title(fig,"d","Aquatic exports that reduced PFAS exposure",.064,.301,gap=.092)
    draw_hi_map(fig,load_boundaries())
    draw_contribution(fig)
    draw_trade_flows(fig)
    draw_change_by_exporter(fig)
    fig.savefig(HERE/"figure 5.png",dpi=300)
    plt.close(fig)


if __name__=="__main__":
    main()

