# Figure reproduction

*Main figures 1–6 and Supplementary Information figures*

## Figure folders

Clone this repository or download it as a ZIP and extract it to a writable folder. Open the `figures` directory. The [main figure collection](main%20figs%201-6/) contains Figures 1–6. The [SI figure collection](SI%20figs/) contains 30 figure folders, of which 26 include plotting scripts. Keep each script with its supplied inputs.

## Environment

Both collections use the same 64-bit CPython 3.12 environment. Use Windows (x64), macOS 13 or later (Intel or Apple silicon), or Linux (x64 or ARM64 with glibc 2.28 or later). On Linux, Python needs the `venv` module and pip bootstrapping.

The setup script creates `.venv-figures` and installs pinned versions of Matplotlib, NumPy, pandas, SciPy, pwlf, NetworkX, openpyxl, Pillow, and fontTools. The first setup needs internet access to download the packages. Rendering then uses the local data and artwork and can run from a terminal.

## Set up and render

Open a terminal in the folder containing `setup_figure_environment.py`. If the Python launcher shown below is unavailable, use `python` after confirming it runs 64-bit CPython 3.12.

| Task | Windows PowerShell | macOS or Linux |
| --- | --- | --- |
| Set up the plotting environment | `py -3.12 setup_figure_environment.py` | `python3.12 setup_figure_environment.py` |
| Render all six main figures | `py -3.12 setup_figure_environment.py --plot main` | `python3.12 setup_figure_environment.py --plot main` |
| Render the 26 scripted SI figures | `py -3.12 setup_figure_environment.py --plot si` | `python3.12 setup_figure_environment.py --plot si` |
| Render both collections of scripts | `py -3.12 setup_figure_environment.py --plot all` | `python3.12 setup_figure_environment.py --plot all` |

## Render a single figure

After setup, use Python from the same `.venv-figures` environment. The commands below show Main Figure 3 and SI Figure 5. Each script writes its output in its own folder.

**Windows PowerShell**

```powershell
.\.venv-figures\Scripts\python.exe "main figs 1-6/fig 3/plot_figure_3.py"
.\.venv-figures\Scripts\python.exe "SI figs/SI fig 5/plot SI fig 5.py"
```

**macOS or Linux**

```sh
./.venv-figures/bin/python "main figs 1-6/fig 3/plot_figure_3.py"
./.venv-figures/bin/python "SI figs/SI fig 5/plot SI fig 5.py"
```

## Supplementary artwork and figure notes

- The site concentration maps use the included Natural Earth geometry.
- Four SI figures are supplied as artwork. SI Text 2.1 Figure 1 is a PDF, SI Text 4.1 Figure 1 and SI Text 6.1 Figure 1 are PowerPoint files, and SI Text 6.3 Figure 1 is an SVG.
- SI Text 6.2 Figure 1 assembles the recovered plot panels.
- SI Text 7 Figure 1 exports the original artwork and a separate partial data audit.
