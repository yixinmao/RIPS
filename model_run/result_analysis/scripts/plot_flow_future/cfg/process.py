#!/usr/local/anaconda/bin/python

import pandas as pd
import subprocess
import os
import numpy as np

#=======================================================
# Parameter setting
#=======================================================
cfg_template = './calibrated_1961_1970.Mohs_v1.Leop_v1.natural/plot_flow_future.template.cfg' # template for plot_flow_future.cfg
new_cfg_basename = './calibrated_1961_1970.Mohs_v1.Leop_v1.natural/Tennessee' # '.usgs<code>.cfg' will be attached

gauge_info_path = '/raid2/ymao/VIC_RBM_east_RIPS/data/USGS/streamT/Tennessee_location_intested.csv'  # gauge info csv

#=======================================================
# Process
#=======================================================
#=== Load gauge info ===#
df_gauges = pd.read_csv(gauge_info_path, dtype={'USGS_code':str})

for i in range(len(df_gauges)):  # for each stream gauge
    #=== get gauge info ===#
    usgs_code = df_gauges.ix[i]['USGS_code']
    usgs_name = df_gauges.ix[i]['name']
    usgs_flow_col = df_gauges.ix[i]['flow_col']
    if usgs_flow_col=='0':  # if no stream T observation data, skip this location
        continue
    grid_lat = df_gauges.ix[i]['grid_lat_corr']
    grid_lon = df_gauges.ix[i]['grid_lon_corr']

    #=== Copy and substitute cfg file for plotting ===#
    cfg_new = '{}.usgs{}.cfg'.format(new_cfg_basename, usgs_code)
    f1 = open(cfg_template, 'r')
    f2 = open(cfg_new, 'w')
    for line in f1:
        # substitue variables
        line = line.replace('<USGS_CODE>', usgs_code)
        line = line.replace('<USGS_NAME>', usgs_name.replace(',', '\,'))
        line = line.replace('<LAT>', str(grid_lat))
        line = line.replace('<LON>', str(grid_lon))
        # write to new cfg file
        f2.write('{}'.format(line))
    f1.close()
    f2.close()

    

