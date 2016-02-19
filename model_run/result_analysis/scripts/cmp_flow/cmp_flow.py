#!/usr/local/anaconda/bin/python

# This script plots routed flow together with USGS observed streamflow

import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import argparse
from scipy import stats
import sys
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
    data_avai_start_date, data_avai_end_date = my_functions.\
                        find_data_common_range(list_s)
    if (data_avai_start_date-data_avai_end_date).days>=0: # if no common time range
        print "No common range data available!"
        exit()
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
df = pd.concat(list_s, axis=1, \
               keys=['obs_TVA', 'sim_before_cali', 'sim_after_cali'])
df_to_plot = df.truncate(before=plot_start_date, after=plot_end_date)

# No NAN version
df_to_plot_noNAN = df_to_plot.dropna()

#========================================================
# Calculate weekly average (TVA weekly data week definition)
#========================================================
list_s_to_plot_weekly = []
for i, key in enumerate(df_to_plot.columns):
    s_to_plot_week = my_functions.calc_ts_stats_by_group(\
                        df_to_plot[key], by='TVA_week', stat='mean')
    list_s_to_plot_weekly.append(s_to_plot_week)
df_to_plot_weekly = pd.concat(list_s_to_plot_weekly, axis=1, \
                         keys=['obs_TVA', 'sim_before_cali', 'sim_after_cali'])
df_to_plot_weekly_noNAN = df_to_plot_weekly.dropna()

#========================================================
# Calculate annual streamflow bias (water year) and KGE
#========================================================
# Calculate annual bias
df_WY_mean = my_functions.calc_ts_stats_by_group(df_to_plot, 'WY', 'mean')
avg_WY_mean = df_WY_mean.mean()
bias_before_cali = (avg_WY_mean['sim_before_cali'] - avg_WY_mean['obs_TVA'])/avg_WY_mean['obs_TVA']
bias_after_cali = (avg_WY_mean['sim_after_cali'] - avg_WY_mean['obs_TVA'])/avg_WY_mean['obs_TVA']
# Calculate KGE
kge_before_cali = my_functions.kge(df_to_plot_weekly['sim_before_cali'], \
                                   df_to_plot_weekly['obs_TVA'])
kge_after_cali = my_functions.kge(df_to_plot_weekly['sim_after_cali'], \
                                  df_to_plot_weekly['obs_TVA'])

#========================================================
# plot
#========================================================
#============ Process "\n" in "model_info" ==================#
model_info = cfg['PLOT_OPTIONS']['model_info'].replace("\\n", "\n")

#=============== Add drainage area info to title =====================#
area = cfg['PLOT_OPTIONS']['drainage_area']
area_grid = cfg['PLOT_OPTIONS']['drainage_area_grid_cell']
if (type(area) is float) or (type(area) is int):  # If valid drainage area
    area_bias = (area_grid - area) / area
    title_new_line = 'Drainage area={:.1f} km2, grid cell area={:.1f} km2, area bias={:.1f}%'\
                               .format(area, area_grid, area_bias*100)
else:  # If no valid drainage area
    title_new_line = 'Upstream grid cell area={:.1f} km2' \
                    .format(area_grid)

##============== plot original data (daily, weekly) (need to be updated with new plot functions!!!) ===============#
#fig = my_functions.plot_time_series(plot_date=True, \
#            list_s_data=list_s_to_plot_weekly, \
#            list_style=list_plot_style, \
#            list_label=list_plot_label, \
#            plot_start=dt.datetime(1988,10,1),  # plot_start_date, \
#            plot_end=dt.datetime(1989,9,30),  # plot_end_date, \
#            xlabel=None, ylabel='Flow (thousand cfs)', \
#            title='{}\n{}'.format(cfg['PLOT_OPTIONS']['plot_title'], title_new_line), \
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
##============== plot monthly data ===============#
#fig = my_functions.plot_monthly_data(\
#            list_s_data=list_s_to_plot, \
#            list_style=list_plot_style, \
#            list_label=list_plot_label, \
#            plot_start=dt.datetime(1991,10,1), # plot_start_date, 
#            plot_end=dt.datetime(1996,9,30), # plot_end_date, \
#            xlabel=None, ylabel='Flow (thousand cfs)', \
#            title='Monthly, {}\n{}'.format(cfg['PLOT_OPTIONS']['plot_title'], \
#                                           title_new_line), \
#            fontsize=18, legend_loc='upper right', \
##            time_locator=time_locator, time_format='%Y/%m', \
#            add_info_text=True, model_info=model_info, \
#            stats='Monthly mean', show=False)
#fig = plt.savefig('%s.flow.monthly.png' %cfg['OUTPUT']['output_plot_basename'], format='png', dpi=dpi)

#============== plot seasonal data ===============#
# Add stats to label
list_plot_label_new = []
list_plot_label_new.append('{}\n(Annual flow={:.1f}cfs)'.\
                      format(list_plot_label[0], avg_WY_mean['obs_TVA']))  # TVA obs
list_plot_label_new\
        .append('{}\n(Weekly KGE={:.2f}\nAnnual flow={:.1f}cfs\nAnnual bias={:.1f}%)'\
                      .format(list_plot_label[1], kge_before_cali, \
                              avg_WY_mean['sim_before_cali'], \
                              bias_before_cali*100))  # Before calibration
list_plot_label_new\
        .append('{}\n(Weekly KGE={:.2f}\nAnnual flow={:.1f}cfs\nAnnual bias={:.1f}%)'\
                      .format(list_plot_label[2], kge_after_cali, \
                              avg_WY_mean['sim_after_cali'], \
                              bias_after_cali*100))  # After calibration

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
            list_label=list_plot_label_new, \
            plot_start=1, plot_end=12, \
            xlabel=None, ylabel='Flow (thousand cfs)', \
            title='Mean monthly flow, {}, WY{}-{}\n{}'\
                  .format(cfg['PLOT_OPTIONS']['plot_title'], 
                          plot_start_date.year+1, plot_end_date.year, \
                          title_new_line), \
            fontsize=24, legend_loc=(0.5,0.25), \
            xtick_location=range(1,13), \
            xtick_labels=['Jan','Feb','Mar','Apr','May','Jun', \
                          'Jul','Aug','Sep','Oct','Nov','Dec'], \
            add_info_text=True, model_info=model_info, \
            stats='Climatology for each month', show=False)

ax = plt.gca()
for tick in ax.xaxis.get_major_ticks():
    tick.label.set_fontsize(24)
for tick in ax.yaxis.get_major_ticks():
    tick.label.set_fontsize(24)

fig = plt.savefig('%s.flow.season.png' %cfg['OUTPUT']['output_plot_basename'], format='png', dpi=dpi)

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
            title='{}, WY {}-{}\n{}'.format(cfg['PLOT_OPTIONS']['plot_title'], \
                                        plot_start_date.year+1, \
                                        plot_end_date.year, \
                                        title_new_line), \
            fontsize=24, legend_loc='lower left', \
            add_info_text=True, model_info=model_info, \
            stats='Flow duration curve based on weekly data', show=False)

ax = plt.gca()
for tick in ax.xaxis.get_major_ticks():
    tick.label.set_fontsize(16)
for tick in ax.yaxis.get_major_ticks():
    tick.label.set_fontsize(16)

fig = plt.savefig('%s.flow_duration_weekly.png' %cfg['OUTPUT']['output_plot_basename'], format='png', dpi=dpi)

##============== plot sim vs. obs on scatter plot (based on weekly data) () ===============#
## list_x: TVA_obs;
## list_y: before_cali, after_cali
#max_flow = max([max(s) for s in list_s_to_plot_weekly])
#
##-------- non-log, with fitting line ---#
#fig = my_functions.plot_scatter(\
#            list_x=[list_s_to_plot_weekly[0], list_s_to_plot_weekly[0]], \
#            list_y=[list_s_to_plot_weekly[1], list_s_to_plot_weekly[2]], \
#            list_s=[10,10], list_c=['r','b'], list_marker=['o','o'], \
#            list_label=[list_plot_label[1], list_plot_label[2]], \
#            figsize=(12,8), linewidths=0, alpha=0.5, \
#            xlog=False, ylog=False, \
#            xlim=None, ylim=None, \
#            xlabel='TVA naturalized flow, weekly (thousand cfs)', \
#            ylabel='Simulated flow, weekly (thousand cfs)', \
#            title='{}, weekly avg., WY{}-{}\n{}'\
#                .format(cfg['PLOT_OPTIONS']['plot_title'], \
#                        plot_start_date.year+1, plot_end_date.year, \
#                        title_new_line), \
#            fontsize=18, legend_loc='upper left', \
#            add_info_text=True, model_info=model_info, \
#            stats='Simulated vs. TVA naturalized flow, before and after calibration, \
#                   \n          all avg. to weekly', show=False)
## Set x axis and y axis equal
#plt.axis('scaled')
#plt.xlim([0, max_flow])
#plt.ylim([0, max_flow])
## Add 1:1 line
#plt.plot([0,max_flow], [0,max_flow], 'k--', lw=2)
## Add fitted lines
#slope_before_cali, interc_before_cali, r_before_cali, p_before_cali, std_err_before_cali = \
#            stats.linregress(list_s_to_plot_weekly[0], list_s_to_plot_weekly[1])
#slope_after_cali, interc_after_cali, r_after_cali, p_after_cali, std_err_after_cali = \
#            stats.linregress(list_s_to_plot_weekly[0], list_s_to_plot_weekly[2])
#plt.plot([0,max_flow], [interc_before_cali,interc_before_cali+slope_before_cali*max_flow], \
#         'r-', lw=2)
#plt.plot([0,max_flow], [interc_after_cali,interc_after_cali+slope_after_cali*max_flow], \
#         'b-', lw=2)
#
#fig = plt.savefig('%s.flow_weekly_scatter.png' %cfg['OUTPUT']['output_plot_basename'], format='png', dpi=dpi)
#
#
##-------- log, no fitting line ---#
#fig = my_functions.plot_scatter(\
#            list_x=[list_s_to_plot_weekly[0], list_s_to_plot_weekly[0]], \
#            list_y=[list_s_to_plot_weekly[1], list_s_to_plot_weekly[2]], \
#            list_s=[10,10], list_c=['r','b'], list_marker=['o','o'], \
#            list_label=[list_plot_label[1], list_plot_label[2]], \
#            figsize=(12,8), linewidths=0, alpha=0.5, \
#            xlog=True, ylog=True, \
#            xlim=None, ylim=None, \
#            xlabel='TVA naturalized flow, weekly (thousand cfs)', \
#            ylabel='Simulated flow, weekly (thousand cfs)', \
#            title='{}, weekly avg., WY{}-{}\n{}'\
#                .format(cfg['PLOT_OPTIONS']['plot_title'], \
#                        plot_start_date.year+1, plot_end_date.year, \
#                        title_new_line), \
#            fontsize=18, legend_loc='upper left', \
#            add_info_text=True, model_info=model_info, \
#            stats='Simulated vs. TVA naturalized flow, before and after calibration, \
#                   \n          all avg. to weekly', show=False)
## Set x axis and y axis equal
#plt.axis('scaled')
#plt.xlim([0.1, max_flow])
#plt.ylim([0.1, max_flow])
## Add 1:1 line
#plt.plot([0,max_flow], [0,max_flow], 'k--', lw=2)
#
#fig = plt.savefig('%s.flow_weekly_scatter_log.png' %cfg['OUTPUT']['output_plot_basename'], format='png', dpi=dpi)



