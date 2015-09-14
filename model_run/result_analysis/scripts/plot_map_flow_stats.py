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
# Extract calibration period and validation period
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

# loop over each location
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
        # Put results in bias dictionary
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
    dict_kge[lat_lon] = dict_kge_cell

#================================================================================#
#--------------------------------------------------------------------------------#
# Process grid cell data (calibration period only)
#--------------------------------------------------------------------------------#
#================================================================================#

#========================================================
# Load grid cell runoff data
#========================================================
list_df_caliPeriod = []  # a list of df (TVA, before_cali, after_cali)
list_df_caliPeriod_weekly = []

for f, infile in enumerate([cfg['INVERSE_ROUTE']['vic_path'], \
                            cfg['BEFORE_CALI']['vic_path'], \
                            cfg['AFTER_CALI']['vic_path']]):       
    print 'Extracting VIC output netCDF file {}...'.format(f+1)

    #=== Load data ===#
    time = my_functions.read_nc(infile, 'time', dimension=-1, is_time=1)
    lat_all = my_functions.read_nc(infile, 'lat', dimension=-1, is_time=0)
    lon_all = my_functions.read_nc(infile, 'lon', dimension=-1, is_time=0)
    runoff = my_functions.read_nc(infile, 'Runoff', dimension=-1, is_time=0)
    baseflow = my_functions.read_nc(infile, 'Baseflow', dimension=-1, is_time=0)
    mask = my_functions.read_nc(infile, 'mask', dimension=-1, is_time=0)
    total_runoff = runoff + baseflow

    #=== Extract data for each grid cell ===#
    print 'Extracting data for each grid cell..'
    df = pd.DataFrame()  # columns: lat_lon
    for i, lat in enumerate(lat_all):
        for j, lon in enumerate(lon_all):
            if mask[i,j]:  # If this grid cell not masked
                
                lat_lon = '{}_{}'.format(lat, lon)
                #=== Extract data for this grid cell ===#
                s = pd.Series(total_runoff[:,i,j], index=time)
                df[lat_lon] = s

    #=== Extract calibration period ===#
    print 'Extracting calibration period..'
    df_caliPeriod = my_functions.select_time_range(df, cali_start_date, cali_end_date)
    
    #=== Calculate weekly average (TVA weekly data week definition) ===#
    print 'Calculaing weekly average...'
    df_caliPeriod_weekly = my_functions.calc_ts_stats_by_group(df_caliPeriod, 
                                                               by='TVA_week', stat='mean')
    
    #=== Append to list ===#
    list_df_caliPeriod.append(df_caliPeriod)
    list_df_caliPeriod_weekly.append(df_caliPeriod_weekly)

#========================================================
# Calculate stats for each active grid cell
#========================================================
list_bias = []  # Each element: a grid cell; each column is a list: [lat, lon, stats_beforeCali, stats_afterCali]
list_kge = []
for lat_lon in list_df_caliPeriod[0].columns:
    print 'Calculating stats for grid cell {}...'.format(lat_lon)
    lat = float(lat_lon.split('_')[0])
    lon = float(lat_lon.split('_')[1])

    #=== Calculate annual bias ===#
    list_s = [list_df_caliPeriod[0][lat_lon], list_df_caliPeriod[1][lat_lon], list_df_caliPeriod[2][lat_lon]]
    df_concat = pd.concat(list_s, axis=1, ignore_index=True)
    df_concat.columns = ['obs_TVA', 'sim_before_cali', 'sim_after_cali']
    df_WY_mean = my_functions.calc_ts_stats_by_group(df_concat, 'WY', 'mean')
    avg_WY_mean = df_WY_mean.mean()
    bias_before_cali = (avg_WY_mean['sim_before_cali'] - avg_WY_mean['obs_TVA'])\
                        /avg_WY_mean['obs_TVA']
    bias_after_cali = (avg_WY_mean['sim_after_cali'] - avg_WY_mean['obs_TVA'])\
                        /avg_WY_mean['obs_TVA']

    #=== Calculate KGE ===#
    list_s_weekly = [list_df_caliPeriod_weekly[0][lat_lon], \
                     list_df_caliPeriod_weekly[1][lat_lon], \
                     list_df_caliPeriod_weekly[2][lat_lon]] # list of Series (weekly) at this grid cell
    kge_before_cali = my_functions.kge(list_s_weekly[1], list_s_weekly[0])
    kge_after_cali = my_functions.kge(list_s_weekly[2], list_s_weekly[0])    
    
    #=== Put results into list ===#
    list_bias.append([lat, lon, bias_before_cali, bias_after_cali])
    list_kge.append([lat, lon, kge_before_cali, kge_after_cali])

#========================================================
# Convert stats to 2-D data to be plot
#========================================================
# Convert data list to array
bias_xyz_array = np.asarray(list_bias)
kge_xyz_array = np.asarray(list_kge)
# Mesh stats data
dlatlon = cfg['INPUT_CONTROL']['grid_cell_size']  # grid cell size
lat_mesh, lon_mesh, bias_mesh_beforeCali = my_functions.mesh_xyz(bias_xyz_array[:,0], bias_xyz_array[:,1], \
                                                            bias_xyz_array[:,2], dlatlon, dlatlon)
lat_mesh, lon_mesh, bias_mesh_afterCali = my_functions.mesh_xyz(bias_xyz_array[:,0], bias_xyz_array[:,1], \
                                                            bias_xyz_array[:,3], dlatlon, dlatlon)
lat_mesh, lon_mesh, kge_mesh_beforeCali = my_functions.mesh_xyz(kge_xyz_array[:,0], kge_xyz_array[:,1], \
                                                            kge_xyz_array[:,2], dlatlon, dlatlon)
lat_mesh, lon_mesh, kge_mesh_afterCali = my_functions.mesh_xyz(kge_xyz_array[:,0], kge_xyz_array[:,1], \
                                                            kge_xyz_array[:,3], dlatlon, dlatlon)
# Put before/after cali into dict 
dict_bias_gridmesh = {}  # key: <before/after>Cali
dict_bias_gridmesh['beforeCali'] = bias_mesh_beforeCali
dict_bias_gridmesh['afterCali'] = bias_mesh_afterCali
dict_kge_gridmesh = {}
dict_kge_gridmesh['beforeCali'] = kge_mesh_beforeCali
dict_kge_gridmesh['afterCali'] = kge_mesh_afterCali



#========================================================
# plot
#========================================================
#============ Process "\n" in "model_info" ==================#
model_info = cfg['PLOT_OPTIONS']['model_info'].replace("\\n", "\n")

for period in ['caliPeriod', 'valiPeriod']:
    for cali in ['beforeCali', 'afterCali']:

        #============================ Plot KGE ===========================#
        fig = plt.figure(figsize=(16, 8))
        ax = plt.axes()
        m = my_functions.define_map_projection(projection='gall', llcrnrlat=34, urcrnrlat=38, \
                                               llcrnrlon=-91, urcrnrlon=-80, resolution='l', \
                                               land_color='grey', ocean_color='lightblue', lakes=True) 
        # Project VIC meshed grid cells
        xx, yy = m(lon_mesh, lat_mesh)
        
        # If calibration period, plot grid-cell data also
        if period=='caliPeriod':
            cs = m.pcolormesh(xx, yy, dict_kge_gridmesh[cali], cmap=plt.cm.jet_r, vmin=-0.6, vmax=1.0)
        
        # Plot station data
        for lat_lon in dict_kge.keys():
            lat = float(lat_lon.split('_')[0])
            lon = float(lat_lon.split('_')[1])
            x, y = m(lon, lat)
            m.scatter(x, y, s=90, c=dict_kge[lat_lon][period][cali], cmap=plt.cm.jet_r, \
                      edgecolors='white', vmin=-0.6, vmax=1.0)
        cbar=m.colorbar(extend='min')
        cbar.ax.tick_params(labelsize=16)
        cbar.set_label('KGE', fontsize=20)
        plt.title('{}, {}'.format(period, cali), size=20)
        my_functions.add_info_text_to_plot(fig, ax, model_info=model_info, \
                                           stats='KGE based on weekly avg. data', \
                                           fontsize=14, bottom=0.3, text_location=-0.1)        
        fig.savefig('{}.KGE.{}.{}.png'.format(cfg['OUTPUT']['output_plot_basename'], \
                                             period, cali), format='png')
        
        #============================== Plot bias ============================#
        fig = plt.figure(figsize=(16, 8))
        ax = plt.axes()
        m = my_functions.define_map_projection(projection='gall', llcrnrlat=34, urcrnrlat=38, \
                                               llcrnrlon=-91, urcrnrlon=-80, resolution='l', \
                                               land_color='grey', ocean_color='lightblue', lakes=True)
        # Project VIC meshed grid cells
        xx, yy = m(lon_mesh, lat_mesh)
        
        # If calibration period, plot grid-cell data also
        if period=='caliPeriod':
            cs = m.pcolormesh(xx, yy, dict_bias_gridmesh[cali]*100, cmap=plt.cm.RdBu, vmin=-30, vmax=30)
        
        # Plot station data
        for lat_lon in dict_kge.keys():
            lat = float(lat_lon.split('_')[0])
            lon = float(lat_lon.split('_')[1])
            x, y = m(lon, lat)
            m.scatter(x, y, s=90, c=dict_bias[lat_lon][period][cali]*100, cmap=plt.cm.RdBu, \
                      edgecolors='black', vmin=-30, vmax=30)
        cbar=m.colorbar(extend='both')
        cbar.ax.tick_params(labelsize=16)
        cbar.set_label('Bias [%]', fontsize=20)
        plt.title('{}, {}'.format(period, cali), size=20)
        my_functions.add_info_text_to_plot(fig, ax, model_info=model_info, \
                                           stats='Bias based on annual WY avg. data', \
                                           fontsize=14, bottom=0.3, text_location=-0.1)        
        fig.savefig('{}.bias.{}.{}.png'.format(cfg['OUTPUT']['output_plot_basename'], \
                                             period, cali), format='png')
    

    #============================ Plot KGE difference before and after cali ===========================#
    fig = plt.figure(figsize=(16, 8))
    ax = plt.axes()
    m = my_functions.define_map_projection(projection='gall', llcrnrlat=34, urcrnrlat=38, \
                                           llcrnrlon=-91, urcrnrlon=-80, resolution='l', \
                                           land_color='grey', ocean_color='lightblue', lakes=True) 
    # Project VIC meshed grid cells
    xx, yy = m(lon_mesh, lat_mesh)
    
    # If calibration period, plot grid-cell data also
    if period=='caliPeriod':
        cs = m.pcolormesh(xx, yy, dict_kge_gridmesh['afterCali'] - dict_kge_gridmesh['beforeCali'], \
                          cmap=plt.cm.PuOr, vmin=-0.5, vmax=0.5)
    
    # Plot station data
    for lat_lon in dict_kge.keys():
        lat = float(lat_lon.split('_')[0])
        lon = float(lat_lon.split('_')[1])
        x, y = m(lon, lat)
        m.scatter(x, y, s=90, \
                  c=dict_kge[lat_lon][period]['afterCali']-dict_kge[lat_lon][period]['beforeCali'], \
                  cmap=plt.cm.PuOr, \
                  edgecolors='black', vmin=-0.5, vmax=0.5)
    cbar=m.colorbar(extend='both')
    cbar.ax.tick_params(labelsize=16)
    cbar.set_label('KGE difference', fontsize=20)
    plt.title('KGE difference (afterCali - beforeCali), {}'.format(period), size=20)
    my_functions.add_info_text_to_plot(fig, ax, model_info=model_info, \
                                       stats='KGE based on weekly avg. data, afterCali-beforeCali', \
                                       fontsize=14, bottom=0.3, text_location=-0.1)        
    fig.savefig('{}.KGE_diff.{}.{}.png'.format(cfg['OUTPUT']['output_plot_basename'], \
                                         period, cali), format='png')
    







