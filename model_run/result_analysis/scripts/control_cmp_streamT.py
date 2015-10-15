#!/usr/local/anaconda/bin/python

import csv
import subprocess
import os
import numpy as np

#=======================================================
# Parameter setting
#=======================================================
gauge_info_path = '../data/USGS_data/USGS_gauge_info/Tennessee_location_intested.csv'  # gauge info csv
rbm_output_basedir = '/raid2/ymao/VIC_RBM_east_RIPS/RIPS/model_run/output/RBM/Maurer_8th/Tennessee/hist_1949_2010.from_RVIC.calibrated_1961_1970/Tennessee'  # RBM formatted output file would be: rbm_output_basedir/lat_lon/lat_lon_reach<reach#>_seg<1OR2>

#=======================================================
# Process
#=======================================================
#with open(gauge_info_path, 'r') as f:
f = open(gauge_info_path, 'r')
csvreader = csv.reader(f)
next(csvreader)
for line in csvreader:  # for each stream gauge
	# get gauge info
	usgs_code = line[3]
	usgs_name = line[2]
	usgs_streamT_col = line[11]
	if usgs_streamT_col=='0':  # if no stream T observation data, skip this location
		continue
	grid_lat = line[6]
	grid_lon = line[7]
	# determine RBM formatted output file (for a given grid cell, we choose the biggest stream (i.e., the sum of all tributaries), seg2)
	rbm_file_names = os.listdir('%s/%s_%s' %(rbm_output_basedir, grid_lat, grid_lon))
	reach = []
	for i in rbm_file_names:
		reach_id = int(i.split('_')[2][5:])
		reach.append(reach_id)
	reach_sorted =  np.sort(reach)
	reach_biggest = reach_sorted[-1]  # obtain the biggest reach ID
	rbm_output_formatted_path = '%s/%s_%s/%s_%s_reach%d_seg2' %(rbm_output_basedir, grid_lat, grid_lon, grid_lat, grid_lon, reach_biggest)
	# Run plotting script
	print 'Plotting site %s %s...' %(usgs_code, usgs_name)
	subprocess.call(['./cmp_streamT_Thead_Tair.py', rbm_output_formatted_path, usgs_code, usgs_name, usgs_streamT_col])
f.close()

