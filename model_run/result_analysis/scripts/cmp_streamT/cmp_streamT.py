#!/usr/local/anaconda/bin/python

# This script plots routed flow, simulated regulated flow, together with USGS observed streamflow and TVA pass-through flow, if data available

import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import sys
from scipy import stats
import xray
import my_functions

cfg = my_functions.read_config(sys.argv[1])

dpi = 200 # This needs to be put into config file

#========================================================
# Load data
#========================================================
list_s = []  # list of Series to be plotted
list_plot_style = []  # list of plot style for each time series
list_plot_color = []  # list of plot style for each time series
list_plot_lw = []  # list of plot style for each time series
list_plot_label = []  # list of plot legend label for each time series
for i in range(cfg['INPUT_CONTROL']['n_ts']):  # Load all time series data
    input_section = 'INPUT_{}'.format(i+1)

    # If from formatted RBM output
    if cfg[input_section]['ts_format']=='RBM_formatted':
        s = my_functions.read_RMB_formatted_output(cfg[input_section]['ts_path'], \
                                             var='Tstream')

    # If from Lohmann output format (year month day data)
    elif cfg[input_section]['ts_format']=='Lohmann':
        s = my_functions.read_Lohmann_route_daily_output(cfg[input_section]['ts_path'])

    # If USGS data
    elif cfg[input_section]['ts_format']=='USGS':
        if type(cfg[input_section]['usgs_col']) is int:  # if only one needed data column
            df_usgs = my_functions.read_USGS_data(cfg[input_section]['ts_path'], \
                                               columns=[cfg[input_section]['usgs_col']], \
                                               names=['streamT'])
            s= df_usgs.ix[:,0]  # convert df to Series

        else:  # if more than one data column needed, take average
            usgs_flow_col_split = cfg[input_section]['usgs_col'].split('&')
            names=[]
            for i in range(len(usgs_flow_col_split)):
                usgs_flow_col_split[i] = int(usgs_flow_col_split[i])
                names.append('streamT%d' %i)
            df_usgs = my_functions.read_USGS_data(cfg[input_section]['ts_path'], \
                                          columns=usgs_flow_col_split, \
                                          names=names)
            s = df_usgs.mean(axis=1, skipna=False) # if either column is missing,
                                                        # return NaN
    else:
        print 'Error: unsupported routed flow format!'
        exit()

    # Append this time series data to list
    list_s.append(s)
    list_plot_style.append(cfg[input_section]['plot_style'])
    list_plot_color.append(cfg[input_section]['plot_color'])
    list_plot_lw.append(cfg[input_section]['plot_lw'])
    list_plot_label.append(cfg[input_section]['plot_label'])

#========================================================
# Determine plot starting and ending date
#========================================================
if cfg['PLOT_OPTIONS']['plot_date_range']:  # if user-defined plotting date range
    plot_start_date = dt.datetime(cfg['PLOT_OPTIONS']['plot_start_date'][0], \
                                  cfg['PLOT_OPTIONS']['plot_start_date'][1], \
                                  cfg['PLOT_OPTIONS']['plot_start_date'][2])
    plot_end_date = dt.datetime(cfg['PLOT_OPTIONS']['plot_end_date'][0], \
                                cfg['PLOT_OPTIONS']['plot_end_date'][1], \
                                cfg['PLOT_OPTIONS']['plot_end_date'][2])

else:   # if plotting date range not defined, calculate full water year when all datasets are available
    # determine the common range of available data of both data sets
    df = pd.concat(list_s, axis=1)
    df_common_range = df.dropna()
    if len(df_common_range) == 0:  # if no common time range
        print "No common range data available!"
        exit()
    data_avai_start_date = df_common_range.index[0]
    data_avai_end_date = df_common_range.index[-1]

    # find the full water years with available data for both data sets
    plot_start_date, plot_end_date = my_functions.\
        find_full_water_years_within_a_range(data_avai_start_date, data_avai_end_date)

#--- determine time locator ---#
if plot_end_date.year-plot_start_date.year < 5:  # if less than 5 years
    time_locator = ('year', 1)  # time locator on the plot; 'year' for year; 'month' for month. e.g., ('month', 3) for plot one tick every 3 months
else:  # if at least 5 years
    time_locator = ('year', (plot_end_date.year-plot_start_date.year)/5)  # time locator on the plot; 'year' for year; 'month' for month. e.g., ('month', 3) for plot one tick every 3 months

#========================================================
# Select data to be plotted
#========================================================
df = pd.concat(list_s, axis=1)
df_to_plot = df.truncate(before=plot_start_date, after=plot_end_date)

# No NAN version
df_to_plot_noNAN = df_to_plot.dropna()

#========================================================
# plot
#========================================================
#============ Process "\n" in "model_info" ==================#
model_info = cfg['PLOT_OPTIONS']['model_info'].replace("\\n", "\n")

#============ Determine 5-year time range to plot for daily, weekly and/or monthly time series ===#
if (plot_end_date-plot_start_date).days / 365 > 5:  # if time series is long, only plot the last 5 years
    plot_start_date_ts = pd.datetime(plot_end_date.year-5, plot_start_date.month, plot_start_date.day)
    plot_end_date_ts = plot_end_date
else:  # if time series is short
    plot_start_date_ts = plot_start_date
    plot_end_date_ts = plot_end_date

#============== plot original data (daily) ===============#
fig = plt.figure(figsize=(12,8))
ax = plt.subplot()
fig, ax = my_functions.plot_time_series(fig, ax, plot_date=True, \
            df_data=df_to_plot, \
            list_style=list_plot_style, \
            list_color=list_plot_color, \
            list_lw=list_plot_lw, \
            list_label=list_plot_label, \
            plot_start=plot_start_date_ts, \
            plot_end=plot_end_date_ts, \
            xlabel=None, ylabel='Stream temperature ($^oC$)', \
            title='{}\n'.format(cfg['PLOT_OPTIONS']['plot_title']), \
            fontsize=24, legend_loc='upper center', \
            time_locator=time_locator, time_format='%b%Y', \
            xtick_location=None, xtick_labels=None, \
            add_info_text=True, model_info=model_info, \
            stats='Daily, no stats', show=False)

for tick in ax.xaxis.get_major_ticks():
    tick.label.set_fontsize(24)
for tick in ax.yaxis.get_major_ticks():
    tick.label.set_fontsize(24)

plt.savefig('%s.streamT.daily.png' %cfg['OUTPUT']['output_plot_basename'], format='png', dpi=dpi)

##============== plot monthly data (need update with new my_functions!) ===============#
#fig = my_functions.plot_monthly_data(\
#            list_s_data=list_s_to_plot, \
#            list_style=list_plot_style, \
#            list_label=list_plot_label, \
#            plot_start=plot_start_date_ts,
#            plot_end=plot_end_date_ts, \
#            xlabel=None, ylabel='Stream temperature ($^o$C)', \
#            title='Monthly, {}\n'.format(cfg['PLOT_OPTIONS']['plot_title']), \
#            fontsize=18, legend_loc='upper right', \
##            time_locator=time_locator, time_format='%Y/%m', \
#            add_info_text=True, model_info=model_info, \
#            stats='Monthly mean', show=False)
#fig = plt.savefig('%s.streamT.monthly.png' %cfg['OUTPUT']['output_plot_basename'], format='png', dpi=dpi)
#
##============== plot seasonal data (need update with new my_functions!) ===============#
#fig = my_functions.plot_seasonality_data(\
#            list_s_data=list_s_to_plot_noNAN, \
#            list_style=list_plot_style, \
#            list_label=list_plot_label, \
#            plot_start=1, plot_end=12, \
#            xlabel=None, ylabel='Stream temperature ($^o$C)', \
#            title='Seasonality, {}, WY{}-{}\n'\
#                  .format(cfg['PLOT_OPTIONS']['plot_title'],
#                          plot_start_date.year+1, plot_end_date.year), \
#            fontsize=18, legend_loc='upper right', \
#            xtick_location=range(1,13), \
#            xtick_labels=['Jan','Feb','Mar','Apr','May','Jun', \
#                          'Jul','Aug','Sep','Oct','Nov','Dec'], \
#            add_info_text=True, model_info=model_info, \
#            stats='Monthly clamatology', show=False)
#
#ax = plt.gca()
#for tick in ax.xaxis.get_major_ticks():
#    tick.label.set_fontsize(16)
#for tick in ax.yaxis.get_major_ticks():
#    tick.label.set_fontsize(16)
#
#fig = plt.savefig('%s.streamT.season.png' %cfg['OUTPUT']['output_plot_basename'], format='png', dpi=dpi)
#
##============== plot flow duration curve (based on daily data) (need update with new my_functions!) ===============#
#fig = my_functions.plot_duration_curve(\
#            list_s_data=list_s_to_plot_noNAN, \
#            list_style=list_plot_style, \
#            list_label=list_plot_label, \
#            figsize=(10,10), xlog=False, ylog=True, \
#            xlim=None, ylim=None, \
#            xlabel='Exceedence', ylabel='Stream temperature ($^o$C)', \
#            title='{}, WY {}-{}\n'.format(cfg['PLOT_OPTIONS']['plot_title'], \
#                                        plot_start_date.year+1, \
#                                        plot_end_date.year), \
#            fontsize=18, legend_loc='upper right', \
#            add_info_text=True, model_info=model_info, \
#            stats='Flow duration curve based on daily data', show=False)
#
#ax = plt.gca()
#for tick in ax.xaxis.get_major_ticks():
#    tick.label.set_fontsize(16)
#for tick in ax.yaxis.get_major_ticks():
#    tick.label.set_fontsize(16)
#
#fig = plt.savefig('%s.flow_duration_daily.png' %cfg['OUTPUT']['output_plot_basename'], format='png', dpi=dpi)
#
#
#
