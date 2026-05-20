# Support-Blue-Transformation-Dilemma-in-Dietary-PFAS-exposure
data and algorithm employed in research "Blue Transformation Dilemma in Dietary PFAS exposure". Project Includes data analysis for food PFAS concentrations, economic driven food consumption projection, serum vs estimated daily intake, and health outcome prediction.

1) concentration analysis t/
   file contains programs to expore time trend of terrestrial food and aquatic food PFAS concentrations (data in "PFAS in food (1113).csv", "PFAS in food (1113 EA).csv" for Asia, "PFAS in food (1113 NA EU).csv" for North America & Europe), employing Monte Carlo statistics (functions in MC stats.py). Program "find most significant period.py" finds for the period with lowest p_value in person correlation test for each pair of PFAS-food type. Monte Carlo statistics for global PFAS level in aquatic food weighted by market values (2020 and 2030 export and production.xlsx) was conducted in "global PFAS level.py". 
2) consumption t/
   file contains programs and raw data for both projected values of animal-sourced food consumption in 47 countries, and the FAO estimated consumption in the United States. In program file, "read_file" is a module to be loaded in "estimated food in 2050". The later predict consumptions in 2021-2050, using data in file "consumption raw data".

Note: ./ refer to the same dictionary path to the position of script; ../ refer to the dictionary path one level up to the script (parent dictionary)
