#!/usr/local/anaconda/bin/python

# This script calculates multi-model-average daily streamflow from Lohmann routing model

import glob
import pandas as pd
import os
import sys
import my_functions

#=============================================
# Parameter setting
#=============================================
#=== input ===#
future_scenario_list = '/raid2/ymao/VIC_RBM_east/VIC_RBM/model_run/result_analysis/data/scenario_list_temp'  # list of future scenarios to be plotted; e.g.: ccsm4. For each scenario, there are rcp45 and rcp85 runs; the final name of scenario files are like: 'ccsm4_rcp85_r1i1p1'
future_scenario_basedir = '/raid2/ymao/VIC_RBM_east/VIC_RBM/model_run/output/Lohmann_route/reclamation_CMIP5/Tennessee_1950_2099'  # Lohmann route output files of a certain scenario will be: future_scenario_basedir/scenario_name/
daily_basename = sys.argv[1]  # Lohmann routing model daily output file basename (e.g., 923  .day)
rcp = 'rcp85'

#=== output ===#
multi_model_avg_output_dir = '/raid2/ymao/VIC_RBM_east/VIC_RBM/model_run/output/Lohmann_route/reclamation_CMIP5/Tennessee_1950_2099/5modelAvg_{}_r1i1p1'.format(rcp)  # directory for multi-model-average daily streamflow

#=============================================
# Processing
#=============================================
#=== Get GCM list ===#
GCM_list = []
f = open(future_scenario_list, 'r')
while 1:
	GCM = f.readline().rstrip("\n")
	if GCM=="":
		break
	GCM_list.append(GCM)
#=== Calculate multi-model average ===#
# Read in data for all GCMs 
for i in range(len(GCM_list)):  # for each GCM
	GCM = GCM_list[i]
	s = my_functions.read_Lohmann_route_daily_output("{}/{}_{}_r1i1p1/{}".format(future_scenario_basedir, GCM, rcp, daily_basename))  # read in one daily file
	if i==0:  # if reading in the first GCM, create pd.DataFrame
		df = pd.DataFrame(s, columns=[GCM])
	else:  # if not the first GCM, add column to the DataFrame
		df[GCM] = s
# Calculate mean
df_multi_model_avg = df.mean(axis=1)
# Save results to file
f = open("{}/{}".format(multi_model_avg_output_dir, daily_basename), 'w')
for i in range(len(df_multi_model_avg)):
	f.write("{:d} {:d} {:d} {:f}\n".format(df_multi_model_avg.index[i].year, df_multi_model_avg.index[i].month, df_multi_model_avg.index[i].day, df_multi_model_avg.iloc[i]))




