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

plot_hist_start_date = dt.datetime(1951, 10, 1)  # start date shown on the plot for historical run (should be complete water years)
plot_hist_end_date = dt.datetime(2010, 9, 30)  # end date shown on the plot for historical run

plot_future_start_date = dt.datetime(1951, 10, 1)  # start date shown on the plot for future run (should be complete water years)
plot_future_end_date = dt.datetime(2099, 9, 30)  # end date shown on the plot for future run

time_locator = ('year', 20)  # time locator on the plot; 'year' for year; 'month' for month. e.g., ('month', 3) for plot one tick every 3 months

#-------------------------------------------------

nfuture = len(future_route_paths)  # number of future scenarios

hist_style = 'k-'
style_options = ['b--', 'r--', 'g--', 'm--', 'y--']
list_style_future = []  # a list of plotting styles of future scenarios
for i in range(nfuture):
	list_style_future.append(style_options[i])

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

#========================================================
# plot
#========================================================
model_info = 'VIC runoff, historical -  1/8 deg, Maurer forcing, Andy Wood setup\n          VIC runoff, climate change scenarios - 1/8 deg, Reclamation archive (GCM forcing)\n          Route: Lohmann, Wu flowdir, Andy Wood setup'

#============== plot daily data ===============#
fig = my_functions.plot_time_series(plot_date=True, \
		list_s_data=[s_hist_to_plot]+list_s_future_to_plot, \
		list_style=[hist_style]+list_style_future, \
		list_label=['historical']+future_route_names, \
		plot_start=plot_hist_start_date, plot_end=plot_future_end_date, \
		ylabel='Flow (cfs)', title='%s, %s' %(usgs_site_name, usgs_site_code), 
		fontsize=16, legend_loc='upper left', \
		time_locator=time_locator,\
		add_info_text=True, model_info=model_info, stats='daily, no stats')

fig.savefig('%s.future.flow.daily.png' %output_plot_basename, format='png')

#============== plot monthly data ===============#
fig = my_functions.plot_monthly_data(list_s_data=[s_hist_to_plot]+list_s_future_to_plot, \
		list_style=[hist_style]+list_style_future, \
		list_label=['historical']+future_route_names, \
		plot_start=plot_hist_start_date, plot_end=plot_future_end_date, \
		ylabel='Flow (cfs)', title='Monthly mean, %s, %s' %(usgs_site_name, usgs_site_code), 
		fontsize=16, legend_loc='upper left', \
		time_locator=time_locator,\
		add_info_text=True, model_info=model_info, stats='Monthly mean')

fig.savefig('%s.future.flow.monthly.png' %output_plot_basename, format='png')

#============== plot seasonality data ===============#
fig = my_functions.plot_seasonality_data(list_s_data=[s_hist_to_plot]+list_s_future_to_plot, \
		list_style=[hist_style]+list_style_future, \
		list_label=['historical']+future_route_names, \
		plot_start=1, plot_end=12, \
		ylabel='Flow (cfs)', \
		title='Monthly mean seasinality, %s, %s' %(usgs_site_name, usgs_site_code), 
		fontsize=16, legend_loc=None, \
		xtick_location=range(1,13), \
		xtick_labels=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Nov','Oct','Nov','Dec'], \
		add_info_text=True, model_info=model_info, stats='Monthly mean; historical - WY%d-%d; climate change scenario - WY%d-%d' %(plot_hist_start_date.year+1, plot_hist_end_date.year, plot_future_start_date.year+1, plot_future_end_date.year))

fig = plt.savefig('%s.future.flow.seas.png' %output_plot_basename, format='png')

exit()

#============== plot annual cumulative flow ===============#
# calculate
time, usgs_cum = my_functions.calc_annual_cumsum_water_year(s_usgs_to_plot.index, s_usgs_to_plot)
s_usgs_cum = pd.Series(usgs_cum, index=time)
time, rbm_cum = my_functions.calc_annual_cumsum_water_year(s_rbm_to_plot.index, s_rbm_to_plot)
s_rbm_cum = pd.Series(rbm_cum, index=time)
# plot
fig = plt.figure()
ax = plt.axes()
plt.plot_date(s_usgs_cum.index, s_usgs_cum, 'b-', label='USGS gauge')
plt.plot_date(s_rbm_cum.index, s_rbm_cum, 'r--', label='Lohmann route')
plt.ylabel('Flow (cfs)', fontsize=16)
plt.title('%s, %s\nAnnual cumulated' %(usgs_site_name, usgs_site_code), fontsize=16)
plt.legend()
my_functions.plot_date_format(ax, time_range=(plot_start_date, plot_end_date), locator=time_locator, time_format='%Y/%m')

fig = plt.savefig('%s.flow.cumsum.png' %output_plot_basename, format='png')


