"""Export SI Text 7 Fig. 1 from the exact artwork embedded in the current SI.

The audit CSVs list the recovered observations and medians. Only part of the
historical cohort selection is recoverable, including possible swapped labels
for Africa and South America in panel b. The embedded artwork retains its
historical labels. Requires Pillow.
"""

from pathlib import Path
import shutil

from PIL import Image


HERE = Path(__file__).resolve().parent


def main():
    source = HERE / "source artwork.png"
    stem = HERE / "SI_7_Fig_1_measured_serum_original"
    shutil.copyfile(source, stem.with_suffix(".png"))
    with Image.open(source) as original:
        foreground = original.convert("RGBA")
        background = Image.new("RGBA", foreground.size, "white")
        background.alpha_composite(foreground)
        background.convert("RGB").save(stem.with_suffix(".pdf"), resolution=130.0)


if __name__ == "__main__":
    main()
