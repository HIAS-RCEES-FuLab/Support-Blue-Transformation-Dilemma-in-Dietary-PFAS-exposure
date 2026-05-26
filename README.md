# Support-Blue-Transformation-Dilemma-in-Dietary-PFAS-exposure
data and algorithm employed in research "Blue Transformation Dilemma in Dietary PFAS exposure". Project Includes data analysis for food PFAS concentrations, economic driven food consumption projection, national food GHG emissions, serum vs estimated daily intake, and health outcome prediction (double machine learning).

1) "concentration analysis"
* file contains programs to expore time trend of terrestrial food and aquatic food PFAS concentrations (data in "PFAS in food (1113).csv", "PFAS in food (1113 EA).csv" for Asia, "PFAS in food (1113 NA EU).csv" for North America & Europe), employing Monte Carlo statistics (functions in "MC stats.py").
* Program "find most significant period.py" finds for the period with lowest p_value in person correlation test for each pair of PFAS-food type.
* Monte Carlo statistics for global PFAS level in aquatic food weighted by market values (2020 and 2030 export and production.xlsx) was conducted in "global PFAS level.py".
* the "most_signigicant_periods" were later used in estimation of daily intake.
2) "consumption"
* file contains programs and results of projected values of animal-sourced food consumption in 47 countries, in addition to the FAO estimated consumption in the United States. In "program" file, "read_file.py" is a module to be loaded in "estimated food in 2050.py". The later predict consumptions in 2021-2050, using data in file "consumption raw data".
3) "estimate daily intake"
* file contains programs and summaized results that estimate daily intake PFAS amount (before devided by body weight) in the United States (2003-2016), and in 47 countries (2020, 6 scenarios in 2050), in addition to that in 47 countries when top 5% contaminated aquatic food from 5 countries were baned (High road pathway & Metatrade mode in 2050). Note that, intake amounts were used in serum level prediction: those of US 2003-2016 were used for curve_fit, and those of 2020 and 2050 6 scenarios were used to predict serum concentrations in correspoding time.
4) "national_food_GHG_intake"
* file contains program, input_file, results, and summary of national total GHG emissions and food emission intensity (GHG emission by unit amount of edible weight). the GHG emissions by each type of terrestrial foods are assumed in normal distribution (statisitics in "CO2 emission.xlsx"), and those by aquatic foods are randomly drawed from pool in "CO2 emission.xlsx". Food consumptions in edible weights were computed by "compute edible weights.py".
5) "EDIs vs NHANES serum concentrations"
* file contains input_file, program, and results (results data is in Releases due to large file size). The serum concnetration were predicted for individuals corresponding to the relative percentile: a person with serum concentration at 25% in 2016 would still have his/her serum concentration at 25% in 2050, but the geometric mean value of population serum concnetrations will shift based on the fitted curve.
6) "double machine learning"
* file contrins input_file, program, and sensitivity_results. The specific results are in "effects" file in "BPQ020", "MCQ160A", and "continuous" file in releases. Summary is in "Data 5_Health outcomes predicted by double machine learning in 2020 and 2050 by region".

  6.1) "test_NN_clssification_F_BPQ020.py" and "test_NN_clssification_F_MCQ160A.py" builds the "NRFRegressionTreeNode" models for BPQ020 and MCQ160A; the trained models are NNTree_BPQ020.pth and NNTree_MCQ160A.pth, respectively.
  
  6.2)"DMLOrthoForest (BPQ020 NN-causalforest).py" and "DMLOrthoForest (MCQ160A NN-causalforest).py" built double machine learning models using pretrained "NRFRegressionTreeNode" models as Y-model, to predict PFAS attributable disease health outcomes (individual treatment effects). "DMLOrthoForest (reg).py" built double machine learning models using xgboost as Y-model, to predict indivator health outcomes.
  
  6.3) Those programs also compared the results with xgboost buy correlation test as a method cross validation. The sensitivity were also tested, including: coverites-permutation test, treatment-permutation test, coverites-robustness test, and treatment-robustness test.

Data 1~4 are directively linked to the article. So is data 5, which is in Releases.

Note: ./ refer to the same dictionary path to the position of script; ../ refer to the dictionary path one level up to the script (parent dictionary)
