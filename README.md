# Blue Transformation Dilemma in Dietary PFAS Exposure

This repository contains the portable analysis pipeline, plotting scripts and inputs for the main and Supplementary Information figures, and the seven datasets accompanying the manuscript.

[Portable pipeline](#bluefood-portable-pipeline) · [Figure reproduction](#figure-reproduction) · [Data 1–7](#data-1-to-7)

## BlueFood Portable Pipeline

[Download the pipeline ZIP](pipeline/BlueFood%20Portable%20Pipeline.zip?raw=1) · [Download the data and script guide (Word)](pipeline/BlueFood%20Pipeline%20Data%20and%20Key%20Scripts.docx?raw=1)

### BlueFood Pipeline Data and Key Scripts

The paths below are relative to the extracted pipeline folder. `README.docx` in the archive is the illustrated user guide.

| Workflow | Key files in the pipeline |
| --- | --- |
| Setup and launch | `research/bootstrap.py` creates the Miniforge environment. `research/launch.py`, `research/app.py`, and `research/worker.py` start the dashboard and run the selected stages. |
| US dietary exposure, 2003–2016 | `research/assets/us/code/run_us_exposure.py` and `exposure_model.py` use annual food quantities, trade matrices, food PFAS measurements, and aquatic time trends from `research/assets/us/inputs/`. |
| Global dietary exposure and hazard index, 2020 and 2050 | `research/calculations.py` and `research/assets/global/program/` run the scenarios. Food PFAS data, trade matrices, country populations, and pathway diets are under `research/assets/global/input_file/`. |
| Diet pathways and emissions | `research/assets/global/input_file/diet/` holds the 2020, Low Road (LR), Business as Usual (BAU), and High Road (HR) diets. The CO₂ card in `research/calculations.py` reweights the archived `research/assets/co2/Figure 4a country rates.csv`. Use the same diet file for each pathway when recalculating CO₂ and EDI together. |
| US PFOA and PFOS kinetics | `research/r_runner.R` and `research/assets/r/code/` run the physiologically based kinetic (PBK) model using absolute dietary intake and food bioavailability factors. |
| Serum and health outcomes, 2020 and 2050 | `research/serum_comparison.py` compares measured and modeled serum concentrations. `research/health.py` applies the health models using the NHANES inputs and model definitions in `research/assets/health/`. |
| Input provenance | `research/ASSET_MANIFEST.json` lists the supplied inputs, and `research/SOURCE_PROVENANCE.json` records their origins. |

The EDI calculations use **62 kg** to convert daily intakes to ng/kg body weight/day. The US PBK model uses **70 kg** for physiology and takes intake in ng/person/day.

### Quick start

The portable pipeline runs the analysis from a browser dashboard and saves each run in a local folder. On Windows x64, Miniforge creates a dedicated environment with Python 3.9.19 and R 4.5.2. Setup needs internet access to download dependencies. The illustrated README in the archive explains the controls and shows example results.

1. Install Miniforge for Windows x64.
2. Download and extract the pipeline ZIP into a writable folder.
3. Run `Setup Environment.cmd` and wait for the package checks to finish.
4. Run `Start Pipeline.cmd`. In the dashboard, run **Environment & data**, then select a workflow. For an initial check, select one repeat and one worker before starting the full analysis.
5. Save the tables and figures from **Results** locally, then run `Stop Pipeline.cmd` when finished.

## Figure reproduction

The [main figure folder](figures/main%20figs%201-6/) includes six plotting scripts. The [Supplementary Information figure folder](figures/SI%20figs/) contains 30 figures, including 26 with Python plotting scripts and four supplied as artwork. The [figure guide](figures/README.md) explains how to render individual figures and identifies the artwork and data sources.

Both figure collections use a shared **64-bit CPython 3.12** environment. The setup script creates `.venv-figures` and installs the pinned plotting packages. Open a terminal in `figures` and use the commands below.

| Task | Windows PowerShell | macOS or Linux |
| --- | --- | --- |
| Set up the figure environment | `py -3.12 setup_figure_environment.py` | `python3.12 setup_figure_environment.py` |
| Render the six main figures | `py -3.12 setup_figure_environment.py --plot main` | `python3.12 setup_figure_environment.py --plot main` |
| Render the 26 scripted SI figures | `py -3.12 setup_figure_environment.py --plot si` | `python3.12 setup_figure_environment.py --plot si` |
| Render both sets of scripts | `py -3.12 setup_figure_environment.py --plot all` | `python3.12 setup_figure_environment.py --plot all` |

## Data 1 to 7

| Dataset | Contents |
| --- | --- |
| [Data 1. Correlations between health outcomes and covariates](Data%201_correlation%20between%20outcomes%20and%20coveriates.xlsx) | NHANES associations between candidate covariates and health outcomes, with p-values and corresponding correlation coefficients or t statistics. |
| [Data 2. Correlations between health outcomes and instruments](Data%202_correlation%20between%20outcomes%20and%20instruments.xlsx) | NHANES associations between candidate instrumental variables and health outcomes, with p-values and corresponding correlation coefficients or t statistics. |
| [Data 3. Global PFAS serum concentrations](Data%203_Global%20PFAS%20serum%20concentrations.xlsx) | Measured serum concentrations from studies and national surveys, with modeled country geometric means across seven scenarios. |
| [Data 4. Food greenhouse gas emission intensity](Data%204_Food%20greenhouse%20gas%20emission%20intensity.xlsx) | Greenhouse gas emission factors for aquatic and terrestrial foods, in kg CO₂e per kg of live-weight food. |
| [Data 5. Modeled health outcomes in 2020 and 2050](https://github.com/HIAS-RCEES-FuLab/Support-Blue-Transformation-Dilemma-in-Dietary-PFAS-exposure/releases/tag/data_5) | Workbook and archived double machine learning results, including regional and income-group summaries. |
| [Data 6. Reference list](Data%206_Reference%20list.xlsx) | Reference records with titles, journals, DOIs, and article or report URLs where available. |
| [Data 7. International food trade source-share matrices](Data%207_International%20food%20trade%20source-share%20matrices.xlsx) | Four 47 × 47 matrices for aquatic and terrestrial foods under Trade and Metatrade. Each matrix gives the share of a consuming country’s modeled supply from each supplier. |
