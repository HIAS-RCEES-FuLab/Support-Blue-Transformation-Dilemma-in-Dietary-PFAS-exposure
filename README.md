# Support-Blue-Transformation-Dilemma-in-Dietary-PFAS-exposure
data and algorithm employed in research "Blue Transformation Dilemma in Dietary PFAS exposure". Project Includes data analysis for food PFAS concentrations, economic driven food consumption projection, serum vs estimated daily intake, and health outcome prediction.

1) "concentration analysis"
* file contains programs to expore time trend of terrestrial food and aquatic food PFAS concentrations (data in "PFAS in food (1113).csv", "PFAS in food (1113 EA).csv" for Asia, "PFAS in food (1113 NA EU).csv" for North America & Europe), employing Monte Carlo statistics (functions in "MC stats.py").
* Program "find most significant period.py" finds for the period with lowest p_value in person correlation test for each pair of PFAS-food type.
* Monte Carlo statistics for global PFAS level in aquatic food weighted by market values (2020 and 2030 export and production.xlsx) was conducted in "global PFAS level.py".
* the "most_signigicant_periods" were later used in estimation of daily intake.
2) "consumption"
* file contains programs and results of projected values of animal-sourced food consumption in 47 countries, in addition to the FAO estimated consumption in the United States. In "program" file, "read_file.py" is a module to be loaded in "estimated food in 2050.py". The later predict consumptions in 2021-2050, using data in file "consumption raw data".
3) "estimate daily intake"
* file contains programs and summaized results that estimate daily intake PFAS amount in the United States (2003-2016), and in 47 countries (2020, 6 scenarios in 2050), in addition to that in 47 countries when top 5% contaminated aquatic food from 5 countries were baned (High road pathway & Metatrade mode in 2050).

Note: ./ refer to the same dictionary path to the position of script; ../ refer to the dictionary path one level up to the script (parent dictionary)
