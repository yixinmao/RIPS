#!/usr/local/anaconda/bin/python

import pandas as pd
import subprocess
import os
import numpy as np

#=======================================================
# Parameter setting
#=======================================================
cfg_template = './calibrated_1961_1970.Mohs_v1.Leop_v1.natural/plot_streamT_future.template.cfg' # template for cmp_streamT.cfg
new_cfg_basename = './calibrated_1961_1970.Mohs_v1.Leop_v1.natural/Tennessee' # '.usgs<code>.cfg' will be attached

gauge_info_path = '/raid2/ymao/VIC_RBM_east_RIPS/data/USGS/streamT/Tennessee_location_intested.csv'  # gauge info csv
rbm_output_basedir = '/raid2/ymao/VIC_RBM_east_RIPS/RIPS/model_run/output/RBM/Maurer_8th/Tennessee/hist_1949_2010.from_RVIC.calibrated_1961_1970/Mohs_v1.Leop_v1/Tennessee'  # RBM formatted output file would be: rbm_output_basedir/lat_lon/lat_lon_reach<reach#>_seg<1OR2>  (this is just for the purpose of determining file name (reach and segment)!!!)

#=======================================================
# Process
#=======================================================
#=== Load gauge info ===#
df_gauges = pd.read_csv(gauge_info_path, dtype={'USGS_code':str})

for i in range(len(df_gauges)):  # for each stream gauge
    #=== get gauge info ===#
    usgs_code = df_gauges.ix[i]['USGS_code']
    usgs_name = df_gauges.ix[i]['name']
    usgs_streamT_col = df_gauges.ix[i]['T_col']
    if usgs_streamT_col=='0':  # if no stream T observation data, skip this location
        continue
    grid_lat = df_gauges.ix[i]['grid_lat_corr']
    grid_lon = df_gauges.ix[i]['grid_lon_corr']

    #=== determine RBM formatted output file name (for a given grid cell, we choose the biggest stream (i.e., the sum of all tributaries), seg2) ===#
    rbm_file_names = os.listdir(os.path.join(rbm_output_basedir, \
                                             '{}_{}'.format(grid_lat, grid_lon)))
    reach = []
    for i in rbm_file_names:
        reach_id = int(i.split('_')[2][5:])
        reach.append(reach_id)
    reach_sorted =  np.sort(reach)
    reach_biggest = reach_sorted[-1]  # obtain the biggest reach ID
    filename = '{}_{}_reach{:d}_seg2'.format(grid_lat, grid_lon, reach_biggest)

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
        line = line.replace('<RBM_FILENAME>', filename)
        # write to new cfg file
        f2.write('{}'.format(line))
    f1.close()
    f2.close()

    

