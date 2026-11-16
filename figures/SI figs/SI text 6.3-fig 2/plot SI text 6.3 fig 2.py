"""Redraw SI Text 6.3 Figure 2 from the accompanying CSV data."""

import csv
from pathlib import Path



HERE = Path(__file__).resolve().parent


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main():
    data = HERE
    output = HERE
    import matplotlib

    matplotlib.use("Agg")
    matplotlib.rcdefaults()

    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "axes.titleweight": "normal",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.75,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
        }
    )
    blue = "#176795"
    output.mkdir(parents=True, exist_ok=True)

    def finish(figure, name):
        figure.savefig(output / f"{name}.png", dpi=300)
        figure.savefig(output / f"{name}.pdf")
        plt.close(figure)

    def decorate(axis, letter, title):
        axis.set_title(f"{letter}   {title}", loc="left", pad=8)
        axis.grid(axis="y", color="#dce3e8", linewidth=0.6)
        axis.set_axisbelow(True)

    outcomes = {"BPQ020": "Hypertension", "MCQ160A": "Arthritis"}
    loss = read_csv(data / "training_loss.csv")
    fig, axes = plt.subplots(2, 1, figsize=(7.0, 5.7), layout="constrained")
    for axis, letter, (label, disease) in zip(axes, "ab", outcomes.items()):
        series = [row for row in loss if row["outcome"] == label]
        epoch = [int(row["epoch"]) for row in series]
        values = [float(row["loss"]) for row in series]
        axis.plot(epoch, values, color=blue, linewidth=1.5)
        axis.set_xlim(0, max(epoch))
        axis.set_ylim((0.67, 0.83) if label == "BPQ020" else (0.45, 0.57))
        axis.set_xlabel("Training epoch")
        axis.set_ylabel("Training loss")
        decorate(axis, letter, f"{disease} ({label})")
    finish(fig, "SI_6.3_Fig_2_training_loss")



if __name__ == "__main__":
    main()
