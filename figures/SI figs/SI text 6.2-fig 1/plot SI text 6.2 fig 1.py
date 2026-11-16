"""Reproduce SI Text 6.2 Figure 1 from its local inputs.

The source consists of the 15 recoverable raster panels, assembled in their archived order.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcdefaults()

import matplotlib.pyplot as plt
from hashlib import sha256
from io import BytesIO
import zipfile
from PIL import Image


HERE = Path(__file__).resolve().parent


def save_figure(figure: plt.Figure, directory: Path, basename: str, dpi: int) -> None:
    figure.savefig(directory / f"{basename}.png", dpi=dpi, facecolor="white")
    figure.savefig(directory / f"{basename}.pdf", facecolor="white")
    plt.close(figure)


def plot_feature_count_panels(provenance: dict, directory: Path, dpi: int) -> None:
    """Reassemble the archived raster plots with their original outcome labels."""
    figure, axes = plt.subplots(5, 3, figsize=(7.12, 8.3))
    figure.subplots_adjust(left=0.067, right=0.986, bottom=0.054, top=0.967, wspace=0.065, hspace=0.17)
    with zipfile.ZipFile(HERE / "original_feature_count_panels.zip") as assets:
        for index, (axis, panel) in enumerate(zip(axes.flat, provenance["panels"], strict=True)):
            source = assets.read(panel["archive_member"])
            if sha256(source).hexdigest() != panel["source_sha256"]:
                raise ValueError(f"Original panel checksum mismatch: {panel['outcome']}")
            with Image.open(BytesIO(source)) as original:
                picture = original.convert("RGBA")
                if picture.height == 264:
                    # These files include a redundant title above the axes. Keep the
                    # top tick text on the left and every pixel within the plot frame.
                    picture = picture.crop((0, 16, picture.width, picture.height))
                    picture.paste((255, 255, 255, 255), (58, 0, picture.width, 5))
                axis.imshow(picture, interpolation="none")
            axis.set_axis_off()
            axis.set_anchor("N")
            axis.set_title(panel["outcome"], fontsize=8.8, fontweight="bold", pad=2.2)
            axis.text(0.01, 1.015, panel["original_panel_label"], transform=axis.transAxes,
                      va="bottom", ha="left", fontsize=9.5, fontweight="bold")
            if index % 3 == 0:
                axis.text(-0.065, 0.53, "F1", transform=axis.transAxes,
                          rotation=90, va="center", ha="center", fontsize=9.5)
    figure.supxlabel("Number of predictors", y=0.016, fontsize=9.5)
    save_figure(figure, directory, "SI_Text_6_2_Fig_1_F1_by_predictor_count", dpi)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE)
    parser.add_argument("--dpi", type=int, default=600)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "pdf.fonttype": 42, "axes.linewidth": 0.8})
    provenance = json.loads((HERE / "provenance.json").read_text(encoding="utf-8"))
    plot_feature_count_panels(provenance, args.output_dir, args.dpi)


if __name__ == "__main__":
    main()
