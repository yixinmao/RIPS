#!/usr/local/anaconda/bin/python

# This script plots control and future stream temperature results together

import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import sys
import pandas as pd
import os
import xray
import my_functions

# Read in cfg file
cfg = my_functions.read_config(sys.argv[1])

dpi = 200 # figure dpi

#=======================================================#
# Preprocess
#=======================================================#
#-------------------------------------------------
# Load in GCM list
f = open(cfg['INPUT']['GCM_list_path'])
list_GCM = []
while 1:
    line = f.readline().rstrip("\n")
    if line=="":
        break
    list_GCM.append(line)
f.close()
nGCM = len(list_GCM)

#-------------------------------------------------

# list of start date shown on the plot for each time series to plot (should be complete water years)
hist_plot_start_date = dt.datetime(cfg['PLOT']['hist_plot_start_date'][0],
                                   cfg['PLOT']['hist_plot_start_date'][1],
                                   cfg['PLOT']['hist_plot_start_date'][2])  # historical
control_plot_start_date = dt.datetime(cfg['PLOT']['control_plot_start_date'][0],
                                      cfg['PLOT']['control_plot_start_date'][1],
                                      cfg['PLOT']['control_plot_start_date'][2])  # control
list_future_plot_start_date = [dt.datetime(cfg['PLOT']['future_plot_start_date_1'][0],
                                           cfg['PLOT']['future_plot_start_date_1'][1],
                                           cfg['PLOT']['future_plot_start_date_1'][2]),  # future 1, 2020s
                               dt.datetime(cfg['PLOT']['future_plot_start_date_2'][0],
                                           cfg['PLOT']['future_plot_start_date_2'][1],
                                           cfg['PLOT']['future_plot_start_date_2'][2]),  # future 2, 2050s
                               dt.datetime(cfg['PLOT']['future_plot_start_date_3'][0],
                                           cfg['PLOT']['future_plot_start_date_3'][1],
                                           cfg['PLOT']['future_plot_start_date_3'][2])]  # future 3, 2080s # list of end date shown on the plot for each time series to plot (should be complete water years)
hist_plot_end_date = dt.datetime(cfg['PLOT']['hist_plot_end_date'][0],
                                 cfg['PLOT']['hist_plot_end_date'][1],
                                 cfg['PLOT']['hist_plot_end_date'][2])  # historical
control_plot_end_date = dt.datetime(cfg['PLOT']['control_plot_end_date'][0],
                                    cfg['PLOT']['control_plot_end_date'][1],
                                    cfg['PLOT']['control_plot_end_date'][2])  # control
list_future_plot_end_date = [dt.datetime(cfg['PLOT']['future_plot_end_date_1'][0],
                                         cfg['PLOT']['future_plot_end_date_1'][1],
                                         cfg['PLOT']['future_plot_end_date_1'][2]),  # future 1, 2020s
                               dt.datetime(cfg['PLOT']['future_plot_end_date_2'][0],
                                           cfg['PLOT']['future_plot_end_date_2'][1],
                                           cfg['PLOT']['future_plot_end_date_2'][2]),  # future 2, 2050s
                               dt.datetime(cfg['PLOT']['future_plot_end_date_3'][0],
                                           cfg['PLOT']['future_plot_end_date_3'][1],
                                           cfg['PLOT']['future_plot_end_date_3'][2])]  # future 3, 2080s

#-------------------------------------------------

hist_label = cfg['PLOT']['hist_label'] # 'Historical, 1980s'
control_label = cfg['PLOT']['control_label'] # 'Control, 1980s, 5 GCM avg.'
list_future_label = cfg['PLOT']['list_future_label']  # ['2020s', '2050s', '2080s']

hist_style = cfg['PLOT']['hist_style']  # 'k-'
control_style = cfg['PLOT']['control_style']  #  'b-'
list_future_style = cfg['PLOT']['list_future_style']   # ['y--', 'g--', 'r--']
hist_color = cfg['PLOT']['hist_color']  # 'k'
control_color = cfg['PLOT']['control_color']  # 'b'
list_future_color = cfg['PLOT']['list_future_color']  # ['y', 'g', 'r'] 

nfuture = cfg['PLOT']['nfuture']
#-------------------------------------------------

model_info = cfg['PLOT']['model_info']
model_info = model_info.replace("\\n", "\n")

#========================================================
# Load data
#========================================================
print 'Loading historical data...'
# Load historical data
ds_hist = xray.open_dataset(cfg['INPUT']['hist_flow_path'])
if cfg['INPUT']['flow_type']=='RVIC':  # if RVIC output, delete last junk time step
    ds_hist = ds_hist.isel(time=slice(0,-1))
    # select out the grid cell
    hist_s_data = ds_hist.sel(lat=cfg['INPUT']['lat'])\
                        .sel(lon=cfg['INPUT']['lon'])['streamflow'].to_series()
# Load projection data
list_future_s_data_rcp45 = []  # a list contains pd.Series of data of each RCP4.5 GCM
list_future_s_data_rcp85 = []  # a list contains pd.Series of data of each RCP8.5 GCM
for i, GCM in enumerate(list_GCM):
    print 'Loading data for {}...'.format(GCM)
    ds_rcp45 = xray.open_dataset(\
                cfg['INPUT']['future_flow_path'].replace('<GCM>', GCM)\
                                               .replace('<RCP>', 'rcp45'))
    ds_rcp45 = ds_rcp45.isel(time=slice(0,-1))
    future_s_data_rcp45 = ds_rcp45.sel(lat=cfg['INPUT']['lat'])\
                        .sel(lon=cfg['INPUT']['lon'])['streamflow'].to_series()
    ds_rcp85 = xray.open_dataset(\
                cfg['INPUT']['future_flow_path'].replace('<GCM>', GCM)\
                                               .replace('<RCP>', 'rcp85'))
    ds_rcp85 = ds_rcp85.isel(time=slice(0,-1))
    future_s_data_rcp85 = ds_rcp85.sel(lat=cfg['INPUT']['lat'])\
                        .sel(lon=cfg['INPUT']['lon'])['streamflow'].to_series()
    list_future_s_data_rcp45.append(future_s_data_rcp45)
    list_future_s_data_rcp85.append(future_s_data_rcp85)
    
# Put all projection data into df
df_rcp45 = pd.concat(list_future_s_data_rcp45, axis=1, keys=list_GCM)
df_rcp85 = pd.concat(list_future_s_data_rcp85, axis=1, keys=list_GCM)

#========================================================
# Select data to be plotted, and calculate GCM avg.
#========================================================
# Select historical data to be plotted
hist_s_to_plot = hist_s_data.truncate(before=hist_plot_start_date, \
                                      after=hist_plot_end_date)
# Select control period, for each GCM
control_df_to_plot = df_rcp45.truncate(before=control_plot_start_date, \
                                       after=control_plot_end_date)
# Calculate GCM avg. for control
control_s_avg = control_df_to_plot.mean(axis=1)

#========================================================
# Calculate GCM avg. and write to file
#========================================================
# Calculate GCM avg. for complete time series, and write to file
# rcp45
s_avg_rcp45 = df_rcp45.mean(axis=1)
df = pd.DataFrame()
df['year'] = s_avg_rcp45.index.year
df['month'] = s_avg_rcp45.index.month
df['day'] = s_avg_rcp45.index.day
df['data'] = s_avg_rcp45.values
df[['year', 'month', 'day', 'data']].\
    to_csv(cfg['GCM_AVG']['path'].replace('<RCP>', 'rcp45'), \
           sep='\t', header=None, index=False)
# rcp85
s_avg_rcp85 = df_rcp85.mean(axis=1)
df = pd.DataFrame()
df['year'] = s_avg_rcp85.index.year
df['month'] = s_avg_rcp85.index.month
df['day'] = s_avg_rcp85.index.day
df['data'] = s_avg_rcp85.values
df[['year', 'month', 'day', 'data']].\
    to_csv(cfg['GCM_AVG']['path'].replace('<RCP>', 'rcp85'), \
           sep='\t', header=None, index=False)

#========================================================
# plot
#========================================================
#============== plot period-average annual mean flow ===============#
# calculate annual mean flow data (WY)
hist_s_WY_mean = my_functions.calc_WY_mean(hist_s_to_plot)  # only plot one control result
control_df_WY_mean = my_functions.calc_WY_mean(control_df_to_plot)  # only plot one control result
control_s_avg_WY_mean = my_functions.calc_WY_mean(control_s_avg)

list_s_control_WY_mean = [[control_df_WY_mean.iloc[:,i]] \
                          for i in range(len(control_df_WY_mean.columns))]
                         # convert df to list of s

#------- plot historical vs. control (control is for individual models) -------#
fig = my_functions.plot_boxplot(list_data = [[hist_s_WY_mean/1000]]+\
                                            [[control_s_avg_WY_mean/1000]]+\
                                            [i/1000 for i in list_s_control_WY_mean], \
            list_xlabels = ['Historical\n1980s', \
                            'Control, 1980s\n {:d}GCM avg.'.format(nGCM)] \
                           + list_GCM, \
            color_list = ['k', 'b'] + ['m']*nGCM, \
            rotation = 0, ylabel = 'Streamflow (thousand cfs)', \
            title='Average annual mean streamflow \n{}'\
                    .format(cfg['PLOT']['title']), \
            fontsize=16, add_info_text=True, model_info=cfg['PLOT']['model_info'], \
            stats = 'Period average of annual mean streamflow (WY); \n          historical & control - WY1970-1999', \
            bottom=0.4, text_location=-0.2)

fig = plt.savefig('{}.future.flow.WY_mean_boxplot.hist_control.png'\
                    .format(cfg['OUTPUT']['output_plot_basepath']), \
                  format='png', dpi=dpi)
