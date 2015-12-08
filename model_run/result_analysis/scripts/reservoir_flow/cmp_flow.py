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
col_keys = []  # column names for df
for i in range(cfg['INPUT_CONTROL']['n_ts']):  # Load all time series data
    input_section = 'INPUT_{}'.format(i+1)

    # If from formatted RBM output
    if cfg[input_section]['ts_format']=='RBM_formatted':
        s = my_functions.read_RMB_formatted_output(cfg[input_section]['ts_path'], \
                                             var='flow') / 1000 # convert to thousand cfs

    # If from formatted RBM output
    elif cfg[input_section]['ts_format']=='Lohmann':
        s = my_functions.read_Lohmann_route_daily_output(cfg[input_section]['ts_path'])\
                                                         / 1000 # convert to thousand cfs

    # If USGS data
    elif cfg[input_section]['ts_format']=='USGS':
        if type(cfg[input_section]['usgs_col']) is int:  # if only one needed data column
            df_usgs = my_functions.read_USGS_data(cfg[input_section]['ts_path'], \
                                               columns=[cfg[input_section]['usgs_col']], \
                                               names=['flow']) / 1000 # convert to thousand cfs
            s= df_usgs.ix[:,0]  # convert df to Series

        else:  # if more than one data column needed, take average
            usgs_flow_col_split = cfg[input_section]['usgs_col'].split('&')
            names=[]
            for i in range(len(usgs_flow_col_split)):
                usgs_flow_col_split[i] = int(usgs_flow_col_split[i])
                names.append('flow%d' %i)
            df_usgs = my_functions.read_USGS_data(cfg[input_section]['ts_path'], \
                                          columns=usgs_flow_col_split, \
                                          names=names) / 1000  # convert to thousand cfs
            s = df_usgs.mean(axis=1, skipna=False) # if either column is missing,
                                                        # return NaN
    # If TVA pass-through flow data
    elif cfg[input_section]['ts_format']=='TVA':
        s = my_functions.read_TVA_pass_through_flow(cfg[input_section]['ts_path'], \
                                        dam_num=cfg[input_section]['dam_num']) \
                                        / 1000  # convert to thousand cfs

    # If RVIC output array format
    elif cfg[input_section]['ts_format']=='RVIC_array':
        df, dict_outlet = my_functions.read_RVIC_output(cfg[input_section]['ts_path'], \
                                      output_format='array', \
                                      outlet_ind=cfg[input_section]['outlet_ind'])
        df = df / 1000  # convert to thousand cfs
        s = df.ix[:,0]
        s.index -= dt.timedelta(hours=12)

    # If RVIC output grid format
    elif cfg[input_section]['ts_format']=='RVIC_grid':
        s = my_functions.read_RVIC_output(cfg[input_section]['ts_path'], \
                                      output_format='grid', \
                                      outlet_ind=(cfg[input_section]['outlet_lat'], \
                                                  cfg[input_section]['outlet_lon']))
        s = s / 1000  # convert to thousand cfs
        s.index -= dt.timedelta(hours=12)

    # If reservoir simulation output format
    elif cfg[input_section]['ts_format']=='reservoir_output':
        ds = xray.open_dataset(cfg[input_section]['ts_path'])
        s = ds['streamflow'].loc[:,cfg[input_section]['outlet_lat'],\
                                 cfg[input_section]['outlet_lon']]\
                .to_series() / 1000  # convert to thousand cfs
        s.index -= dt.timedelta(hours=12)

    else:
        print 'Error: unsupported routed flow format!'
        exit()

    # Append this time series data to list
    list_s.append(s)
    list_plot_style.append(cfg[input_section]['plot_style'])
    list_plot_color.append(cfg[input_section]['plot_color'])
    list_plot_lw.append(cfg[input_section]['plot_lw'])
    list_plot_label.append(cfg[input_section]['plot_label'])
    col_keys.append(str(i+1))

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
df = pd.concat(list_s, axis=1, keys=col_keys)
df_to_plot = df.truncate(before=plot_start_date, after=plot_end_date)

# No NAN version
df_to_plot_noNAN = df_to_plot.dropna()

#========================================================
# Calculate weekly average (TVA weekly data week definition)
#========================================================
# Has NAN version
list_s_to_plot_weekly = []
for i, key in enumerate(df_to_plot.columns):
    s_to_plot_week = my_functions.calc_ts_stats_by_group(\
                            df_to_plot[key], by='TVA_week', stat='mean')
    list_s_to_plot_weekly.append(s_to_plot_week)
df_to_plot_weekly = pd.concat(list_s_to_plot_weekly, axis=1)

# No NAN version
df_to_plot_weekly_noNAN = df_to_plot_weekly.dropna()

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

##============== plot original data (daily, weekly) (need to be updated with new plot functions!) ===============#
#fig = my_functions.plot_time_series(plot_date=True, \
#            list_s_data=list_s_to_plot_weekly, \
#            list_style=list_plot_style, \
#            list_label=list_plot_label, \
#            plot_start=plot_start_date_ts, \
#            plot_end=plot_end_date_ts, \
#            xlabel=None, ylabel='Flow (thousand cfs)', \
#            title='{}\n'.format(cfg['PLOT_OPTIONS']['plot_title']), \
#            fontsize=18, legend_loc='upper right', \
##            time_locator=time_locator, time_format='%Y/%m', \
#            xtick_location=None, xtick_labels=None, \
#            add_info_text=True, model_info=model_info, \
#            stats='Weekly (TVA week definition)', show=False)
#ax = plt.gca()
#for tick in ax.yaxis.get_major_ticks():
#    tick.label.set_fontsize(16)
#
#plt.savefig('%s.flow.weekly.png' %cfg['OUTPUT']['output_plot_basename'], format='png', dpi=dpi)
#
##============== plot monthly data (need to be updated with new plot functions!) ===============#
#fig = my_functions.plot_monthly_data(\
#            list_s_data=list_s_to_plot, \
#            list_style=list_plot_style, \
#            list_label=list_plot_label, \
#            plot_start=plot_start_date_ts,
#            plot_end=plot_end_date_ts, \
#            xlabel=None, ylabel='Flow (thousand cfs)', \
#            title='Monthly, {}\n'.format(cfg['PLOT_OPTIONS']['plot_title']), \
#            fontsize=18, legend_loc='upper right', \
##            time_locator=time_locator, time_format='%Y/%m', \
#            add_info_text=True, model_info=model_info, \
#            stats='Monthly mean', show=False)
#fig = plt.savefig('%s.flow.monthly.png' %cfg['OUTPUT']['output_plot_basename'], format='png', dpi=dpi)

#============== plot seasonal data ===============#
# Calculate seasonality
df_season_to_plot = my_functions.calc_ts_stats_by_group(\
                        df_to_plot_noNAN, 'month', 'mean') # index is 1-12 (month)

# Plot

fig = plt.figure(figsize=(16,6))
ax = plt.subplot()
fig, ax = my_functions.plot_time_series(fig, ax, plot_date=False, \
            df_data=df_season_to_plot, \
            list_style=list_plot_style, \
            list_color=list_plot_color, \
            list_lw=list_plot_lw, \
            list_label=list_plot_label, \
            plot_start=1, plot_end=12, \
            xlabel=None, ylabel='Flow (thousand cfs)', \
            title='Monthly climatology, {}, WY{}-{}\n'\
                  .format(cfg['PLOT_OPTIONS']['plot_title'],
                          plot_start_date.year+1, plot_end_date.year), \
            fontsize=24, legend_loc='upper right', \
            xtick_location=range(1,13), \
            xtick_labels=['Jan','Feb','Mar','Apr','May','Jun', \
                          'Jul','Aug','Sep','Oct','Nov','Dec'], \
            add_info_text=True, model_info=model_info, \
            stats='Monthly climatology for each month', show=False)

ax = plt.gca()
for tick in ax.xaxis.get_major_ticks():
    tick.label.set_fontsize(24)
for tick in ax.yaxis.get_major_ticks():
    tick.label.set_fontsize(24)

fig = plt.savefig('%s.flow.season.png' %cfg['OUTPUT']['output_plot_basename'], format='png', dpi=dpi)

##============== plot seasonal reservoir impact (regulated - unregulated) (need to be updated with new plot functions!!!) ===============#
#if len(list_s_to_plot_noNAN)==4:  # if has full data
#    fig = my_functions.plot_seasonality_data(\
#            list_s_data=[list_s_to_plot_noNAN[1]-list_s_to_plot_noNAN[0], \
#                         list_s_to_plot_noNAN[3]-list_s_to_plot_noNAN[2]], \
#            list_style=['k-', 'm'], \
#            list_label=['Regulated - unregulated, obs.', 'Regulated - unregulated, simulated'], \
#            plot_start=1, plot_end=12, \
#            xlabel=None, ylabel='Flow (thousand cfs)', \
#            title='Rugulation impact seasonality, {}, WY{}-{}\n'\
#                  .format(cfg['PLOT_OPTIONS']['plot_title'],
#                          plot_start_date.year+1, plot_end_date.year), \
#            fontsize=18, legend_loc='upper left', \
#            xtick_location=range(1,13), \
#            xtick_labels=['Jan','Feb','Mar','Apr','May','Jun', \
#                          'Jul','Aug','Sep','Oct','Nov','Dec'], \
#            add_info_text=True, model_info=model_info, \
#            stats='Seasonality for each month', show=False)
#    plt.plot(range(1,13), np.zeros(12), 'k--')
#
#    ax = plt.gca()
#    for tick in ax.xaxis.get_major_ticks():
#        tick.label.set_fontsize(16)
#    for tick in ax.yaxis.get_major_ticks():
#        tick.label.set_fontsize(16)
#
#    fig = plt.savefig('%s.flow.season_regulation_impact.png' %cfg['OUTPUT']['output_plot_basename'], format='png', dpi=dpi)

#============== plot flow duration curve (based on weekly data) ===============#
fig = plt.figure(figsize=(10,10))
ax = plt.subplot()

fig, ax = my_functions.plot_duration_curve(fig, ax, \
            df_data=df_to_plot_weekly_noNAN, \
            list_style=list_plot_style, \
            list_color=list_plot_color, \
            list_lw=list_plot_lw, \
            list_label=list_plot_label, \
            xlog=False, ylog=True, \
            xlim=None, ylim=None, \
            xlabel='Exceedence', ylabel='Flow (thousand cfs)', \
            title='{}, WY {}-{}\n'.format(cfg['PLOT_OPTIONS']['plot_title'], \
                                        plot_start_date.year+1, \
                                        plot_end_date.year), \
            fontsize=24, legend_loc='lower left', \
            add_info_text=True, model_info=model_info, \
            stats='Flow duration curve based on weekly data', show=False)

ax = plt.gca()
for tick in ax.xaxis.get_major_ticks():
    tick.label.set_fontsize(24)
for tick in ax.yaxis.get_major_ticks():
    tick.label.set_fontsize(24)

fig = plt.savefig('%s.flow_duration_weekly.png' %cfg['OUTPUT']['output_plot_basename'], format='png', dpi=dpi)



