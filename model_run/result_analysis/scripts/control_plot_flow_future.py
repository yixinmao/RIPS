#!/usr/local/anaconda/bin/python

# This script is a wrap for running 'plot_flow_future.py'; historical and climate scenario flows are all from Lohmann routing runs

import csv
import subprocess
import os
import numpy as np
import sys

# Read in config file
cfg = sys.argv[1]

#=======================================================
# Parameter setting
#=======================================================
gauge_info_path = '../data/USGS_data/USGS_gauge_info/Tennessee_location_intested.csv'  # gauge info csv
route_station_file = '/raid2/ymao/VIC_RBM_east_RIPS/RIPS/model_run/param/Lohmann_route/Wu_8th/Tennessee/Tennessee.Rout.Cells'  # Lohmann routing station file (this is for determining station name of a grid cell)
route_hist_output_dir = '/raid2/ymao/VIC_RBM_east_RIPS/RIPS/model_run/output/Lohmann_route/reclamation_CMIP5/Tennessee_1949_2010_historical_for_comparison'  # directory of Lohmann route output - historical run
GCM_list = '/raid2/ymao/VIC_RBM_east_RIPS/RIPS/model_run/result_analysis/data/scenario_list_temp'  # list of future GCMs to be plotted; e.g.: ccsm4. For each GCM, there are rcp45 and rcp85 runs; the final name of scenario files are like: 'ccsm4_rcp85_r1i1p1'
future_scenario_basedir = '/raid2/ymao/VIC_RBM_east_RIPS/RIPS/model_run/output/Lohmann_route/reclamation_CMIP5/Tennessee_1950_2099'  # Lohmann route output files of a certain scenario will be: future_scenario_basedir/scenario_name/

#=======================================================
# Process
#=======================================================
#with open(gauge_info_path, 'r') as f:
f = open(gauge_info_path, 'r')
csvreader = csv.reader(f)
next(csvreader)
for line in csvreader:  # for each stream gauge
    #=== Get gauge info ===#
    usgs_code = line[3]
    usgs_name = line[2]
    usgs_flow_col = line[10]
    grid_lat = line[6]
    grid_lon = line[7]
    #=== Determine Lohmann routing output file name of the grid cell ===#
    p = subprocess.Popen("grep %s_%s %s | head -n 1 | awk '{print $2}'" %(grid_lat, grid_lon, route_station_file), stdout=subprocess.PIPE, shell=True)
    station_num = int(p.communicate()[0].rstrip("\n"))  # get station number of the grid cell and convert to integer
    route_outfile_name = "{:<5d}.day".format(station_num)
    #=== Determine historical route output path ===#
    hist_route_path = os.path.join(route_hist_output_dir, route_outfile_name)

    #=== Loop over each scenario ===#
    f_GCM = open(GCM_list, 'r')
    while 1:
        GCM = f_GCM.readline().rstrip("\n")
        if GCM=="":
            break
        # Determine Lohmann route output paths of this GCM (rcp45 and rcp85)
        future_route_path_rcp45 = os.path.join(future_scenario_basedir, '{}_rcp45_r1i1p1'.format(GCM), route_outfile_name)
        future_route_path_rcp85 = os.path.join(future_scenario_basedir, '{}_rcp85_r1i1p1'.format(GCM), route_outfile_name)
        # Run plotting script
        print 'Plotting site {} {}, GCM {}...'.format(usgs_code, usgs_name, GCM)
        subprocess.call(["./plot_flow_future.py", "--cfg", cfg, \
            "--USGS_code", usgs_code, \
            "--USGS_name", usgs_name, "--hist_route_path", hist_route_path, \
            "--future_route_paths_rcp45", future_route_path_rcp45, \
            "--future_route_paths_rcp85", future_route_path_rcp85, \
            "--future_route_names", "{}".format(GCM)])
    f_GCM.close()

f.close()

