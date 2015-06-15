#!/usr/local/anaconda/bin/python

# This script plots different routed flow results together

import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import sys
import pandas as pd
import argparse
import my_functions

parser = argparse.ArgumentParser()
parser.add_argument("--USGS_code", type=str,  help="USGS code")
parser.add_argument("--USGS_name", type=str,  help="USGS name")
parser.add_argument("--hist_route_path", type=str, help="Historical route output path")
parser.add_argument("--future_route_paths", nargs='+', type=str, help="eg. 'path1' 'path2'")
parser.add_argument("--future_route_names", nargs='+', type=str, help="eg. 'Scenario1' 'Scenario2'")
args = parser.parse_args()

#========================================================
# Parameter setting
#========================================================
usgs_site_code = args.USGS_code # '03571850'
usgs_site_name = args.USGS_name # 'Tennessee River at Lower Pittsburgh'

hist_route_path = args.hist_route_path # historical run. Lohmann routing output. year; month; day; flow(cfs)
future_route_paths = args.future_route_paths # future run. Lohmann routing output. year; month; day; flow(cfs); ['path1', 'path2']
future_route_names = args.future_route_names # future run. year; month; day; flow(cfs); ['Scenario1', 'Scenario2']

output_plot_basename = '../output/Tennessee_' + usgs_site_code # output plot path basename (suffix will be added to different plots)

#-------------------------------------------------

plot_hist_start_date = dt.datetime(1969, 10, 1)  # start date shown on the plot for historical run (should be complete water years)
plot_hist_end_date = dt.datetime(1999, 9, 30)  # end date shown on the plot for historical run

plot_future_start_date = dt.datetime(1939, 10, 1)  # start date shown on the plot for future run (should be complete water years)
plot_future_end_date = dt.datetime(2069, 9, 30)  # end date shown on the plot for future run

time_locator = ('year', 20)  # time locator on the plot; 'year' for year; 'month' for month. e.g., ('month', 3) for plot one tick every 3 months

#-------------------------------------------------

nfuture = len(future_route_paths)  # number of future scenarios

list_future_control_labels = []
list_future_labels = []
for i in range(nfuture):
	list_future_control_labels.append(future_route_names[i]+', WY%d-%d' %(plot_hist_start_date.year+1, plot_hist_end_date.year))
	list_future_labels.append(future_route_names[i]+', WY%d-%d' %(plot_future_start_date.year+1, plot_future_end_date.year))

hist_style = 'k-'
style_options = ['b--', 'r--', 'g--', 'm--', 'y--']
list_style_future = []  # a list of plotting styles of future scenarios
list_style_future_control = []  # a list of plotting styles of future scenarios in control period
for i in range(nfuture):
	list_style_future_control.append('b-')
#	list_style_future.append(style_options[i])
	list_style_future.append('r--')

#-------------------------------------------------

model_info = 'VIC runoff, historical -  1/8 deg, Maurer forcing, Andy Wood setup\n          VIC runoff, climate change scenarios - 1/8 deg, Reclamation archive (GCM forcing)\n          Route: Lohmann, Wu flowdir, Andy Wood setup'

#========================================================
# Load data
#========================================================
s_hist = my_functions.read_Lohmann_route_daily_output(hist_route_path)
list_s_future = []  # a list contains pd.Series of data of each futre scenario
for i in range(nfuture):
	s_future = my_functions.read_Lohmann_route_daily_output(future_route_paths[i])
	list_s_future.append(s_future)

#========================================================
# Select data to be plotted
#========================================================
s_hist_to_plot = my_functions.select_time_range(s_hist, plot_hist_start_date, plot_hist_end_date)

list_s_future_to_plot = []
for i in range(nfuture):
	s_future_to_plot = my_functions.select_time_range(list_s_future[i], plot_future_start_date, plot_future_end_date)
	list_s_future_to_plot.append(s_future_to_plot)

list_s_future_control_to_plot = []  # control period of future run
for i in range(nfuture):
	s_future_control_to_plot = my_functions.select_time_range(list_s_future[i], plot_hist_start_date, plot_hist_end_date)
	list_s_future_control_to_plot.append(s_future_control_to_plot)

#========================================================
# plot
#========================================================

##============== plot daily data ===============#
#fig = my_functions.plot_time_series(plot_date=True, \
#		list_s_data=[s_hist_to_plot]+list_s_future_to_plot, \
#		list_style=[hist_style]+list_style_future, \
#		list_label=['historical']+future_route_names, \
#		plot_start=plot_hist_start_date, plot_end=plot_future_end_date, \
#		ylabel='Flow (cfs)', title='%s, %s' %(usgs_site_name, usgs_site_code), 
#		fontsize=16, legend_loc='upper left', \
#		time_locator=time_locator,\
#		add_info_text=True, model_info=model_info, stats='daily, no stats')
#
#fig.savefig('%s.future.flow.daily.png' %output_plot_basename, format='png')
#
##============== plot monthly data ===============#
#fig = my_functions.plot_monthly_data(list_s_data=[s_hist_to_plot]+list_s_future_to_plot, \
#		list_style=[hist_style]+list_style_future, \
#		list_label=['historical']+future_route_names, \
#		plot_start=plot_hist_start_date, plot_end=plot_future_end_date, \
#		ylabel='Flow (cfs)', title='Monthly mean, %s, %s' %(usgs_site_name, usgs_site_code), 
#		fontsize=16, legend_loc='upper left', \
#		time_locator=time_locator,\
#		add_info_text=True, model_info=model_info, stats='Monthly mean')
#
#fig.savefig('%s.future.flow.monthly.png' %output_plot_basename, format='png')

#============== plot seasonality data ===============#
fig = my_functions.plot_seasonality_data(list_s_data=[s_hist_to_plot]+list_s_future_control_to_plot+list_s_future_to_plot, \
		list_style=[hist_style]+list_style_future_control+list_style_future, \
		list_label=['historical, WY%d-%d' %(plot_hist_start_date.year+1, plot_hist_end_date.year)]+list_future_control_labels+list_future_labels, \
		plot_start=1, plot_end=12, \
		ylabel='Flow (cfs)', \
		title='Monthly mean seasinality, %s, %s' %(usgs_site_name, usgs_site_code), 
		fontsize=16, legend_loc=None, \
		xtick_location=range(1,13), \
		xtick_labels=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Nov','Oct','Nov','Dec'], \
		add_info_text=True, model_info=model_info, stats='Monthly mean; historical - WY%d-%d; cfuture projection - WY%d-%d' %(plot_hist_start_date.year+1, plot_hist_end_date.year, plot_future_start_date.year+1, plot_future_end_date.year))

fig = plt.savefig('%s.future.flow.seas.png' %output_plot_basename, format='png')

##============== plot annual mean flow ===============#
#fig = my_functions.plot_WY_mean_data(list_s_data=[s_hist_to_plot]+list_s_future_to_plot, \
#		list_style=[hist_style]+list_style_future, \
#		list_label=['historical']+future_route_names, \
#		plot_start=plot_hist_start_date.year, plot_end=plot_future_end_date.year, \
#		ylabel='Flow (cfs)', title='Annual mean (WY), %s, %s' %(usgs_site_name, usgs_site_code), 
#		fontsize=16, legend_loc='upper left', \
#		add_info_text=True, model_info=model_info, stats='Annual mean (WY)')
#
#fig.savefig('%s.future.flow.WY.png' %output_plot_basename, format='png')

#============== plot period-average annual mean flow ===============#
# calculate annual mean flow data (WY)
list_s_WY_mean = my_functions.calc_WY_mean(list_s_data=[s_hist_to_plot]+list_s_future_control_to_plot+list_s_future_to_plot)
# plot
fig = my_functions.plot_boxplot(list_data=list_s_WY_mean, \
			list_xlabels=['historical, WY%d-%d' %(plot_hist_start_date.year+1, plot_hist_end_date.year)]+list_future_control_labels+list_future_labels, \
			ylabel='Flow (cfs)', \
			title='Average annual mean flow, %s, %s' %(usgs_site_name, usgs_site_code), \
			fontsize=16, add_info_text=True, model_info=model_info, \
			stats='Period average of annual mean flow (WY); \n          historical and control - average over WY%d-%d; \n          future projection - WY%d-%d' %(plot_hist_start_date.year+1, plot_hist_end_date.year, plot_future_start_date.year+1, plot_future_end_date.year))

fig = plt.savefig('%s.future.flow.WY_mean_boxplot.png' %output_plot_basename, format='png')






