#!/usr/local/anaconda/bin/python

# This script plots routed flow together with USGS observed streamflow

import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import argparse
from scipy import stats
import my_functions

parser = argparse.ArgumentParser()
parser.add_argument("--cfg", type=str,  help="config file for this script")
args = parser.parse_args()
cfg = my_functions.read_config(args.cfg)

#========================================================
# Load dam grid cell info
#========================================================
dam_grid_cell_info = pd.read_csv(cfg['INPUT_CONTROL']['dam_grid_cell_info_path'])

#========================================================
# Load data
#========================================================
#=== Load TVA obs ===#
df_TVA = pd.DataFrame()
for i in range(len(dam_grid_cell_info)):
    print 'Loading TVA data for location {}...'.format(i+1)
    lat = dam_grid_cell_info.iloc[i]['grid_lat_corr'] # extract grid cell lat
    lon = dam_grid_cell_info.iloc[i]['grid_lon_corr'] # extract grid cell lon
    s = my_functions.read_Lohmann_route_daily_output(\
            '{}/{}_{}.daily.1903_2013'.format(cfg['TVA_obs']['ts_dir'], lat, lon))\
                                                     / 1000 # convert to thousand cfs
    df_TVA['{}_{}'.format(lat,lon)] = s

#=== Load before calibration ===#
print 'Loading routed flow before calibration...'
if cfg['BEFORE_CALI']['ts_format']=='RVIC_array':
    df, dict_outlet = my_functions.read_RVIC_output(cfg['BEFORE_CALI']['ts_path'], \
                                  output_format='array', \
                                  outlet_ind=-1)
    df = df / 1000  # convert to thousand cfs
for i in range(np.shape(df)[1]):  # Rename columns lat_lon
    dam_name = df.columns[i]
    df = df.rename(columns={dam_name:'{}_{}'.format(dict_outlet[dam_name][0], \
                                                    dict_outlet[dam_name][1])})
df_before_cali = df

#=== Load after calibration ===#
print 'Loading routed flow after calibration...'
if cfg['AFTER_CALI']['ts_format']=='RVIC_array':
    df, dict_lat_lon = my_functions.read_RVIC_output(cfg['AFTER_CALI']['ts_path'], \
                                  output_format='array', \
                                  outlet_ind=-1)
    df = df / 1000  # convert to thousand cfs
for i in range(np.shape(df)[1]):  # Rename columns lat_lon
    dam_name = df.columns[i]
    df = df.rename(columns={dam_name:'{}_{}'.format(dict_lat_lon[dam_name][0], \
                                                    dict_lat_lon[dam_name][1])})
df_after_cali = df

#=== Put all df together ===#
list_df = [df_TVA, df_before_cali, df_after_cali]

#========================================================
# Select calibration period and validation period to be plotted
#========================================================
cali_start_date = dt.datetime(cfg['TIME_RANGE']['cali_start_date'][0], \
                              cfg['TIME_RANGE']['cali_start_date'][1], \
                              cfg['TIME_RANGE']['cali_start_date'][2])
cali_end_date = dt.datetime(cfg['TIME_RANGE']['cali_end_date'][0], \
                              cfg['TIME_RANGE']['cali_end_date'][1], \
                              cfg['TIME_RANGE']['cali_end_date'][2])
vali_start_date = dt.datetime(cfg['TIME_RANGE']['vali_start_date'][0], \
                              cfg['TIME_RANGE']['vali_start_date'][1], \
                              cfg['TIME_RANGE']['vali_start_date'][2])
vali_end_date = dt.datetime(cfg['TIME_RANGE']['vali_end_date'][0], \
                              cfg['TIME_RANGE']['vali_end_date'][1], \
                              cfg['TIME_RANGE']['vali_end_date'][2])

list_df_caliPeriod = []
list_df_valiPeriod = []
for i in range(len(list_df)):
    df_caliPeriod = my_functions.select_time_range(list_df[i], cali_start_date, cali_end_date)
    df_valiPeriod = my_functions.select_time_range(list_df[i], vali_start_date, vali_end_date)
    list_df_caliPeriod.append(df_caliPeriod)
    list_df_valiPeriod.append(df_valiPeriod)
    
#========================================================
# Calculate weekly average (TVA weekly data week definition)
#========================================================
list_df_caliPeriod_weekly = []
for i, df in enumerate(list_df_caliPeriod):
    df_week = my_functions.calc_ts_stats_by_group(list_df_caliPeriod[i], \
                                                  by='TVA_week', stat='mean')
    list_df_caliPeriod_weekly.append(df_week)

list_df_valiPeriod_weekly = []
for i, df in enumerate(list_df_valiPeriod):
    df_week = my_functions.calc_ts_stats_by_group(list_df_valiPeriod[i], \
                                                  by='TVA_week', stat='mean')
    list_df_valiPeriod_weekly.append(df_week)

#========================================================
# Calculate annual streamflow bias (water year) and KGE for each location
#========================================================
dict_bias = {}  # key level 1: lat_lon
                # key level 2: <cali/vali>Period
                # key level 3: <before/after>Cali
dict_kge = {}  # same structure
# Loop over each location
for key in dict_outlet.keys():
    lat = dict_outlet[key][0]
    lon = dict_outlet[key][1]
    lat_lon = '{}_{}'.format(lat, lon)

    #=== Select out column data for this location ===#
    dict_s = {}  # key: caliPeriod; valiPeriod; content: list of Series(TVA, before cali, after cali)
    dict_s['caliPeriod'] = []
    dict_s['valiPeriod'] = []
    for i, df in enumerate(list_df_caliPeriod):
        dict_s['caliPeriod'].append(df[lat_lon])
    for i, df in enumerate(list_df_valiPeriod):
        dict_s['valiPeriod'].append(df[lat_lon])

    dict_s_weekly = {}  # key: caliPeriod; valiPeriod; content: list of Series(TVA, before cali, after cali)
    dict_s_weekly['caliPeriod'] = []
    dict_s_weekly['valiPeriod'] = []
    for i, df in enumerate(list_df_caliPeriod_weekly):
        dict_s_weekly['caliPeriod'].append(df[lat_lon])
    for i, df in enumerate(list_df_valiPeriod):
        dict_s_weekly['valiPeriod'].append(df[lat_lon])

    #=== Calculate annual bias ===#
    dict_bias_cell = {}
    for key in dict_s.keys():  # for caliPeriod or valiPeriod
        list_s = dict_s[key]  # list of Series at this location
        df_concat = pd.concat(list_s, axis=1, ignore_index=True)
        df_concat.columns = ['obs_TVA', 'sim_before_cali', 'sim_after_cali']
        df_WY_mean = my_functions.calc_ts_stats_by_group(df_concat, 'WY', 'mean')
        avg_WY_mean = df_WY_mean.mean()
        bias_before_cali = (avg_WY_mean['sim_before_cali'] - avg_WY_mean['obs_TVA'])\
                          /avg_WY_mean['obs_TVA']
        bias_after_cali = (avg_WY_mean['sim_after_cali'] - avg_WY_mean['obs_TVA'])\
                          /avg_WY_mean['obs_TVA']
        # Put results in for this period
        dict_period = {}
        dict_period['beforeCali'] = bias_before_cali
        dict_period['afterCali'] = bias_after_cali
        # Put results in bias dictionary for this grid cell
        dict_bias_cell[key] = dict_period
    # Put results in final bias dictionary
    dict_bias[lat_lon] = dict_bias_cell

    #=== Calculate KGE ===#
    dict_kge_cell = {}
    for key in dict_s_weekly.keys():  # for caliPeriod or valiPeriod
        list_s_weekly = dict_s_weekly[key]  # list of Series (weekly) at this location
        kge_before_cali = my_functions.kge(list_s_weekly[1], list_s_weekly[0])
        kge_after_cali = my_functions.kge(list_s_weekly[2], list_s_weekly[0])
        # Put results in for this period
        dict_period = {}
        dict_period['beforeCali'] = kge_before_cali
        dict_period['afterCali'] = kge_after_cali
        # Put results in bias dictionary for this grid cell
        dict_kge_cell[key] = dict_period
    # Put results in final bias dictionary
    dict_kge[lat_lon] = dict_bias_cell


#========================================================
# plot
#========================================================
