#!/usr/local/anaconda/bin/python

# This script plots routed flow together with USGS observed streamflow

import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import pandas as pd
import argparse
import my_functions

parser = argparse.ArgumentParser()
parser.add_argument("--cfg", type=str,  help="config file for this script")
args = parser.parse_args()
cfg = my_functions.read_config(args.cfg)

#========================================================
# Load data
#========================================================
list_s = []  # list of Series to be plotted
list_plot_style = []  # list of plot style for each time series
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

    else:
        print 'Error: unsupported routed flow format!'
        exit()

    # Append this time series data to list
    list_s.append(s)
    list_plot_style.append(cfg[input_section]['plot_style'])
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
list_s_to_plot = []
for i in range(cfg['INPUT_CONTROL']['n_ts']):  # Loop over each time series
    s_to_plot = my_functions.select_time_range(list_s[i], plot_start_date, plot_end_date)    
    list_s_to_plot.append(s_to_plot)

#========================================================
# Calculate weekly average (TVA weekly data week definition)
#========================================================
list_s_to_plot_weekly = []
for i, s_to_plot in enumerate(list_s_to_plot):
    s_to_plot_week = my_functions.calc_ts_stats_by_group(s_to_plot, by='TVA_week', stat='mean')
    list_s_to_plot_weekly.append(s_to_plot_week)

#========================================================
# Calculate annual streamflow bias (water year) and KGE
#========================================================
# Calculate annual bias
df_to_plot = pd.concat(list_s_to_plot, axis=1, ignore_index=True)
df_to_plot.columns = ['obs_TVA', 'sim_before_cali', 'sim_after_cali']
df_WY_mean = my_functions.calc_ts_stats_by_group(df_to_plot, 'year', 'mean')
avg_WY_mean = df_WY_mean.mean()
bias_before_cali = (avg_WY_mean['sim_before_cali'] - avg_WY_mean['obs_TVA'])/avg_WY_mean['obs_TVA']
bias_after_cali = (avg_WY_mean['sim_after_cali'] - avg_WY_mean['obs_TVA'])/avg_WY_mean['obs_TVA']
# Calculate KGE
kge_before_cali = my_functions.kge(list_s_to_plot_weekly[1], list_s_to_plot_weekly[0])
kge_after_cali = my_functions.kge(list_s_to_plot_weekly[2], list_s_to_plot_weekly[0])

#========================================================
# plot
#========================================================
#============ Process "\n" in "model_info" ==================#
model_info = cfg['PLOT_OPTIONS']['model_info'].replace("\\n", "\n")

#============== plot original data (daily, weekly) ===============#
fig = my_functions.plot_time_series(plot_date=True, \
            list_s_data=list_s_to_plot_weekly, \
            list_style=list_plot_style, \
            list_label=list_plot_label, \
            plot_start=plot_start_date, plot_end=plot_end_date, \
            xlabel=None, ylabel='Flow (thousand cfs)', \
            title=cfg['PLOT_OPTIONS']['plot_title'], \
            fontsize=16, legend_loc='upper right', \
#            time_locator=time_locator, time_format='%Y/%m', \
            xtick_location=None, xtick_labels=None, \
            add_info_text=True, model_info=model_info, \
            stats='Weekly (TVA week definition)', show=False)
plt.savefig('%s.flow.weekly.png' %cfg['OUTPUT']['output_plot_basename'], format='png')

#============== plot monthly data ===============#
fig = my_functions.plot_monthly_data(\
            list_s_data=list_s_to_plot, \
            list_style=list_plot_style, \
            list_label=list_plot_label, \
            plot_start=plot_start_date, plot_end=plot_end_date, \
            xlabel=None, ylabel='Flow (thousand cfs)', \
            title='Monthly, {}'.format(cfg['PLOT_OPTIONS']['plot_title']), \
            fontsize=16, legend_loc='upper right', \
#            time_locator=time_locator, time_format='%Y/%m', \
            add_info_text=True, model_info=model_info, \
            stats='Monthly mean', show=False)
fig = plt.savefig('%s.flow.monthly.png' %cfg['OUTPUT']['output_plot_basename'], format='png')

#============== plot seasonal data ===============#
list_plot_label_new = []
list_plot_label_new.append('{}\n(Annual flow={:.1f}cfs)'.\
                      format(list_plot_label[0], avg_WY_mean['obs_TVA']))  # TVA obs
list_plot_label_new.append('{}\n(Weekly KGE={:.2f}\nAnnual flow={:.1f}cfs\nAnnual bias={:.1f}%)'\
                      .format(list_plot_label[1], kge_before_cali, \
                              avg_WY_mean['sim_before_cali'], bias_before_cali*100))  # Before calibration
list_plot_label_new.append('{}\n(Weekly KGE={:.2f}\nAnnual flow={:.1f}cfs\nAnnual bias={:.1f}%)'\
                      .format(list_plot_label[2], kge_after_cali, \
                              avg_WY_mean['sim_after_cali'], bias_after_cali*100))  # After calibration

fig = my_functions.plot_seasonality_data(\
            list_s_data=list_s_to_plot, \
            list_style=list_plot_style, \
            list_label=list_plot_label_new, \
            plot_start=1, plot_end=12, \
            xlabel=None, ylabel='Flow (thousand cfs)', \
            title='Seasonality, {}, WY {}-{}'.format(cfg['PLOT_OPTIONS']['plot_title'], \
                                                     plot_start_date.year+1, \
                                                     plot_end_date.year), \
            fontsize=16, legend_loc='upper right', \
            xtick_location=range(1,13), \
            xtick_labels=['Jan','Feb','Mar','Apr','May','Jun', \
                          'Jul','Aug','Nov','Oct','Nov','Dec'], \
            add_info_text=True, model_info=model_info, \
            stats='Seasonality for each month', show=False)

#plt.text(0.65, 0.4, \
#        'Annual flow cfs:\nObs TVA: {:.1f}\nBefore_cali: {:.1f}\nafter_cali: {:.1f}\n\nAnnual bias: \nBefore calibration: {:.1f}%\nAfter calibration: {:.1f}%\n(WY {}-{})'\
#                    .format(avg_WY_mean['obs_TVA'], avg_WY_mean['sim_before_cali'], \
#                            avg_WY_mean['sim_after_cali'], \
#                            bias_before_cali*100, bias_after_cali*100, \
#                            plot_start_date.year+1, plot_end_date.year), 
#        transform=plt.gca().transAxes, fontsize=12)

fig = plt.savefig('%s.flow.season.png' %cfg['OUTPUT']['output_plot_basename'], format='png')

#============== plot flow duration curve (based on weekly data) ===============#
fig = my_functions.plot_duration_curve(\
            list_s_data=list_s_to_plot_weekly, \
            list_style=list_plot_style, \
            list_label=list_plot_label, \
            figsize=(10,10), xlog=False, ylog=True, \
            xlim=None, ylim=None, \
            xlabel='Exceedence', ylabel='Flow (thousand cfs)', \
            title='{}, WY {}-{}'.format(cfg['PLOT_OPTIONS']['plot_title'], \
                                        plot_start_date.year+1, \
                                        plot_end_date.year), \
            fontsize=16, legend_loc='upper right', \
            add_info_text=True, model_info=model_info, \
            stats='Flow duration curve based on weekly data', show=False)

fig = plt.savefig('%s.flow_duration_weekly.png' %cfg['OUTPUT']['output_plot_basename'], format='png')

#============== plot sim vs. obs on scatter plot (based on weekly data) ===============#






##============== plot annual cumulative flow ===============#
## calculate
#time, usgs_cum = my_functions.calc_annual_cumsum_water_year(s_usgs_to_plot.index, s_usgs_to_plot)
#s_usgs_cum = pd.Series(usgs_cum, index=time)
#time, route_cum = my_functions.calc_annual_cumsum_water_year(s_route_to_plot.index, s_route_to_plot)
#s_route_cum = pd.Series(route_cum, index=time)
## plot
#fig = plt.figure()
#ax = plt.axes()
#plt.plot_date(s_usgs_cum.index, s_usgs_cum, 'b-', label='USGS gauge')
#plt.plot_date(s_route_cum.index, s_route_cum, 'r--', label='Lohmann route')
#plt.ylabel('Flow (cfs)', fontsize=16)
#plt.title('%s, %s\nAnnual cumulative' %(cfg['INPUT_USGS']['usgs_site_name'], cfg['INPUT_USGS']['usgs_site_code']), fontsize=16)
#plt.legend()
#my_functions.plot_date_format(ax, time_range=(plot_start_date, plot_end_date), locator=time_locator, time_format='%Y/%m')
#
#fig = plt.savefig('%s.flow.cumsum.png' %cfg['OUTPUT']['output_plot_basename'], format='png')
#
#
#
#
