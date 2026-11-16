# Pipeline Data and Key Scripts

*Companion guide for the Blue Transformation manuscript*

[Download the pipeline ZIP](BlueFood%20Portable%20Pipeline.zip?raw=1) · [Quick start](../README.md#quick-start)

This guide identifies the inputs, scripts, and main outputs of the BlueFood Portable Pipeline. Paths are relative to the pipeline folder. Where a section names a directory, file names in its table are relative to that directory.

## Analysis settings

| Component | Setting |
| --- | --- |
| 2050 pathway diets | Use the same food quantities for a given pathway in the CO₂ and EDI calculations. Low Road (LR), Business as Usual (BAU), and High Road (HR) each have their own diet table. Trade and Metatrade use the same consumption quantities for a given pathway. |
| Dietary exposure | Use 62 kg for stimated daily intakes (EDIs), including the US historical series and the 2020 and 2050 scenarios. Divide daily intake in ng/person/day by 62 to report ng/kg body weight/day. |
| US PBK model | Oral dose was calculated from EDI times bioavailability ratios between protein foods and water. Used the same parameters provided by Fabrega et al. for oral exposure. The R model takes absolute PFOA and PFOS intake in ng/person/day from the historical exposure stage. |

The current CO₂ card aggregates archived Figure 4a rates. The shared diet rule applies when calculating new CO₂ rates from the pathway inputs listed under Pathway Diets and Greenhouse Gas Emissions.

## Setup and workflow

| File or group | What it contains or does |
| --- | --- |
| `Setup Environment.cmd`<br>`research/bootstrap.py` | Set up the dedicated Miniforge environment. The Windows locks are environment-win64-explicit.txt and requirements-lock-win64.txt. certificate_trust.py and check_R_CA.R verify certificate handling. |
| `Start Pipeline.cmd and Stop Pipeline.cmd`<br>`research/launch.py` | Start and stop the local pipeline service. research/app.py schedules dependent stages and research/window.html displays the controls and results. |
| `research/worker.py`<br>`research/calculations.py and research/health.py` | Run the scientific stages and write their status and results. The default run folder is research/workspace/runs/. |
| `research/SIMULATION_DEFAULT.json`<br>`research/common.py` | Specify simulation counts, seeds and body weight settings, and define the reference doses used for the hazard index. |
| `research/ASSET_MANIFEST.json`<br>`research/SOURCE_PROVENANCE.json`<br>`research/RELEASE_MANIFEST.json` | List bundled inputs, record their source paths and checksums, and identify the files included in the portable release. |

## Dietary PFAS Exposure and Hazard Index

### United States from 2003 to 2016

The US historical EDI stage calls us_stage in research/calculations.py. Its inputs and scripts are under research/assets/us/.

| File or group | What it contains or does |
| --- | --- |
| `code/run_us_exposure.py`<br>`code/exposure_model.py` | Run the annual Monte Carlo exposure simulation. The exposure model applies compound-specific pooling windows and time trend factors for aquatic foods. |
| `inputs/diets/FAOSTAT_YYYY.csv`<br>`inputs/trades/consump_trade matrix YYYY.xlsx` | Provide country food quantities and trade sourcing for each year from 2003 through 2016. |
| `inputs/concentration_cases/baseline/`<br>`inputs/aquatic_time_trends.xlsx`<br>`settings.json` | Supply food PFAS measurements, sampling-site and country mappings, concentration basis fractions, aquatic time trend parameters, and run settings. |
| `inputs/reference.json`<br>`inputs/figure1_serum_reference.csv`<br>`inputs/geometric_mean_edi_cv_2020.csv` | Provide the archived EDI comparison, measured serum composition reference, and 2020 US variability reference used in the plots. |

The stage writes US_EDI.csv, US_Sum7.csv, difference_from_historical_by_year.csv, and annual/YYYY/baseline_r1.npz. The first-repeat arrays are the PBK intake input.

### Global exposure in 2020 and 2050

The global_stage function runs the 2020 Trade and No trade cases and the six 2050 pathway and trade-mode cases. The files below are under research/assets/global/.

| File or group | What it contains or does |
| --- | --- |
| `program/base_runner.py`<br>`program/simulation_single_trade.py`<br>`program/weighted_median_fast.py` | Generate Monte Carlo intakes, sample supply origins using trade or domestic supply, and compute weighted exposure statistics. |
| `input_file/PFAS in food data.csv`<br>`input_file/most significant periods.xlsx` | Supply the concentration records and time trend parameters. SampleSite-Waters.csv, SampleSite-Terri.csv, aq and lip fraction.csv, and Map_Country_Code_OECD.csv support site mapping and concentration preparation. |
| `input_file/consump_trade matrix.xlsx`<br>`input_file/consump_trade matrix 2050.xlsx` | Provide the standard Trade supply shares and the distinct 2050 Metatrade shares. The standard matrix serves 2020 and 2050 Trade. |
| `input_file/reference_geography.csv` | Provides country groups and the 2020 or 2050 populations used in regional and world summaries. |

The stage writes statistics.csv and individual intake arrays indexed by individual_manifest.json. The hazard index sums compound-specific EDI-to-reference-dose ratios for each country before population weighting.

## Pathway Diets and Greenhouse Gas Emissions

### Shared diet inputs

Use the matching table below for each 2050 pathway in both dietary exposure and a new emissions calculation. Rows identify countries and foods and give annual food quantities per person before adjustment for edible yield.

| File or group | What it contains or does |
| --- | --- |
| `research/assets/global/input_file/diet/`<br>`LR diet.csv` | Low Road food quantities. The balanced exposure diet adjusts mutton and goat meat, pork, and poultry proportionally to match the BAU total for animal-sourced food. |
| `research/assets/global/input_file/diet/`<br>`BAU diet.csv` | Business as Usual food quantities and the total used to balance the Low Road diet. |
| `research/assets/global/input_file/diet/`<br>`HR diet.csv` | High Road food quantities. |
| `research/assets/global/input_file/diet/`<br>`2020 diet.csv` | Baseline food quantities used by the EDI and diet pathway stages. |
| `research/calculations.py`<br>`research/diet_map_views.py` | The diet_stage function summarizes population-weighted aquatic and terrestrial consumption. The map view shows domestic and imported supply shares for the selected country. |

### Emissions calculation and archived reproduction

For a calculation with the shared diets, convert kg/person/year to edible g/person/day using food-specific yields. Multiply each food quantity by its emission factor, apply the country-specific terrestrial factor where relevant, and sum across foods. Compute regional and world intensity as total emissions divided by total edible food, using the matching year’s population weights.

| File or group | What it contains or does |
| --- | --- |
| `research/assets/co2/`<br>`GHG emission intensity (2020).xlsx`<br>`GHG emission intensity.xlsx`<br>`terri GHG intensity by country.xlsx` | Provide emission intensities and country factors for calculation from food quantities. source_estimate_GHG.py preserves the earlier emissions script. |
| `research/assets/co2/`<br>`Figure 4a country rates.csv` | Stores archived annual per-person emissions and edible food rates for 47 countries in each of the four scenarios. The current card uses these saved rates. |
| `research/calculations.py`<br>`co2_stage` | Applies 2020 or 2050 population weights to the archived rates. It writes country_emissions_and_intensity.csv, population_weighted_emissions.csv, and the world emissions and intensity chart. |

The four diet copies in research/assets/co2/ are retained with the archived inputs. The LR and HR copies differ from the active EDI diets. Reproducing the shared diet calculation requires regenerating country emission and edible food rates from the pathway inputs above.

## Serum Concentrations and Health Outcomes

### United States PBK model

| File or group | What it contains or does |
| --- | --- |
| `research/calculations.py`<br>`research/r_runner.R` | The pbk_stage function exports the first historical repeat’s PFOA and PFOS total, aquatic, and terrestrial intake draws. The R runner compares four exposure scenarios after the 2003–2004 calibration. |
| `research/assets/r/code/`<br>`PFAS_PBK_US_2003_2016_Fabrega_2015.R`<br>`ode_fast.R` | Implement the adapted compartment model, source-specific food bioavailability, and accelerated ODE solver. |
| `research/assets/r/original_source/`<br>`Fabrega_2015_data.xlsx`<br>`PFAS_PBK_validation_Fabrega_2015.R` | Preserve the source parameters and validation code. research/assets/r/nhanes_pfas_total_population.csv supplies measured US concentrations for comparison. |

Key PBK outputs include PFOA_PFOS_period_results.csv, the US_PBK_R plot, and the US_PBK_serum_sources plot.

### Serum and health in 2020 and 2050

| File or group | What it contains or does |
| --- | --- |
| `research/assets/health/source/`<br>`serum_mapping.py`<br>`research/calculations.py` | Map absolute dietary intake to modeled serum concentrations in ng/mL for the 2020 and 2050 cases. The fitted curves retain their own internal divisor. avalible chems by country.xlsx under research/assets/global/input_file/ records compound coverage. |
| `research/assets/health/data/`<br>`Measured_serum.xlsx`<br>`research/serum_comparison.py` | Supply measured serum values and construct the 2020 predicted-versus-measured comparison. |
| `research/assets/health/published_data/`<br>`data_outcome indicators derived local.xlsx`<br>`data_outcome diseases.xlsx`<br>`tag indicators.csv and tag diseases.csv` | Supply the cleaned NHANES indicator and disease datasets and the variable tags used by the health models. data_outcome indicators.xlsx preserves the original indicator workbook. |
| `research/health.py`<br>`research/assets/health/health_outcomes.json`<br>`research/assets/health/published/` | Fit and apply models for 34 continuous and two binary outcomes. The published folder has DMLOrthoForest (reg).py, the BPQ020 and MCQ160A variants, and their neural tree checkpoints. |

The serum stage writes country_serum_concentrations.csv and regional_world_serum.csv. The health stage writes country_health_outcomes.csv and regional_world_health_outcomes.csv. The 2050 health summary compares the projected outcomes against 2020 Trade.
