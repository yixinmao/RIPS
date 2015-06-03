#!/usr/local/anaconda/bin/python

# This script plots routed flow together with USGS observed streamflow

import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import sys
import my_functions

#========================================================
# Parameter setting
#========================================================
rbm_output_formatted_path = sys.argv[1] # '/raid2/ymao/VIC_RBM_east/VIC_RBM/model_run/output/RBM/Maurer_8th/Tennessee/Tennessee_1949_2010/35.0625_-85.6875_reach299_seg2'  # year; month; day; flow(cfs); T_stream(deg); 1 header line

usgs_site_code = sys.argv[2] # '03571850'
usgs_site_name = sys.argv[3] # 'Tennessee River at Lower Pittsburgh'
usgs_data_path = '../data/USGS_data/Tennessee/' + usgs_site_code + '.txt'
usgs_streamT_col = sys.argv[4] # format: 1 or 1&2
# check how many data columns there are
ave_flag = 0  # 0 for only one data column; >0 for more than one column, # columns, need to average
if len(usgs_streamT_col.split('&'))>1:  # if more than one column, need to average these columns
	ave_flag = len(usgs_streamT_col.split('&'))
else:
	usgs_streamT_col = int(usgs_streamT_col)

output_plot_basename = '../output/Tennessee_' + usgs_site_code # output plot path basename (suffix will be added to different plots)

#-------------------------------------------------

#plot_start_date = dt.datetime(1950, 10, 1)  # start date shown on the plot (should be complete water years)
#plot_end_date = dt.datetime(1987, 9, 30)  # end date shown on the plot

#time_locator = ('year', 5)  # time locator on the plot; 'year' for year; 'month' for month. e.g., ('month', 3) for plot one tick every 3 months

#-------------------------------------------------

#========================================================
# Load data
#========================================================
# RBM output
rbm_data = np.loadtxt(rbm_output_formatted_path, skiprows=1)  # year; month; day; flow(cfs); T_stream(degC)
rbm_date = my_functions.convert_YYYYMMDD_to_datetime(rbm_data[:,0], rbm_data[:,1], rbm_data[:,2])
df_rbm = my_functions.convert_time_series_to_df(rbm_date, rbm_data[:,4], ['streamT'])  # convert to pd.DataFrame
s_rbm = df_rbm.ix[:,0]  # convert df to Series

# USGS stream T
if ave_flag==0:  # if only one needed data column
	df_usgs = my_functions.read_USGS_data(usgs_data_path, columns=[usgs_streamT_col], names=['streamT'])  # [degC]
	s_usgs= df_usgs.ix[:,0]  # convert df to Series
else:  # if more than one data column needed, take average
	usgs_streamT_col_split = usgs_streamT_col.split('&')
	names=[]
	for i in range(len(usgs_streamT_col_split)):
		usgs_streamT_col_split[i] = int(usgs_streamT_col_split[i])
		names.append('streamT%d' %i)
	df_usgs = my_functions.read_USGS_data(usgs_data_path, columns=usgs_streamT_col_split, names=names)  # read in data
	s_usgs = df_usgs.mean(axis=1, skipna=False) # if either column is missing, return NaN

# check if both datasets are not all missing values
if s_rbm.notnull().sum()==0:  # if all missing
	print 'All RBM output values are missing!'
	exit()
if s_usgs.notnull().sum()==0:  # if all missing
	print 'All USGS data are missing!'
	exit()

#========================================================
# Determine plot starting and ending date (always plot full water years)
#========================================================
# determine the common range of available data of both data sets
data_avai_start_date, data_avai_end_date = my_functions.find_data_common_range(s_rbm, s_usgs)
if (data_avai_start_date-data_avai_end_date).days>=0: # if no common time range
	print "No common range data available!"
	exit()
# find the full water years with available data for both data sets
plot_start_date, plot_end_date = my_functions.find_full_water_years_within_a_range(data_avai_start_date, data_avai_end_date)
# determine time locator
if plot_end_date.year-plot_start_date.year < 5:  # if less than 5 years
	time_locator = ('year', 1)  # time locator on the plot; 'year' for year; 'month' for month. e.g., ('month', 3) for plot one tick every 3 months
else:  # if at least 5 years
	time_locator = ('year', (plot_end_date.year-plot_start_date.year)/5)  # time locator on the plot; 'year' for year; 'month' for month. e.g., ('month', 3) for plot one tick every 3 months

#========================================================
# Select data to be plotted
#========================================================
s_rbm_to_plot = my_functions.select_time_range(s_rbm, plot_start_date, plot_end_date)
s_usgs_to_plot = my_functions.select_time_range(s_usgs, plot_start_date, plot_end_date)

#========================================================
# plot
#========================================================
#============== plot daily data ===============#
fig = plt.figure()
ax = plt.axes()
plt.plot_date(s_usgs_to_plot.index, s_usgs_to_plot, 'b-', label='USGS gauge')
plt.plot_date(s_rbm_to_plot.index, s_rbm_to_plot, 'r--', label='Lohmann route')
plt.ylabel('Stream T (degC)', fontsize=16)
plt.title('%s, %s' %(usgs_site_name, usgs_site_code), fontsize=16)
plt.legend()
my_functions.plot_date_format(ax, time_range=(plot_start_date, plot_end_date), locator=time_locator, time_format='%Y/%m')

fig = plt.savefig('%s.streamT.daily.png' %output_plot_basename, format='png')

#============== plot monthly data ===============#
# calculate
s_usgs_mon = my_functions.calc_monthly_data(s_usgs_to_plot)
s_rbm_mon = my_functions.calc_monthly_data(s_rbm_to_plot)
# plot
fig = plt.figure()
ax = plt.axes()
plt.plot_date(s_usgs_mon.index, s_usgs_mon, 'b-', label='USGS gauge')
plt.plot_date(s_rbm_mon.index, s_rbm_mon, 'r--', label='Lohmann route')
plt.ylabel('Stream T (degC)', fontsize=16)
plt.title('Monthly, %s, %s' %(usgs_site_name, usgs_site_code), fontsize=16)
plt.legend()
my_functions.plot_date_format(ax, time_range=(plot_start_date, plot_end_date), locator=time_locator, time_format='%Y/%m')

fig = plt.savefig('%s.streamT.monthly.png' %output_plot_basename, format='png')

#============== plot seasonal data ===============#
# calculate
s_usgs_seas = my_functions.calc_ts_stats_by_group(s_usgs_to_plot, 'month', 'mean') # index is 1-12 (month)
s_rbm_seas = my_functions.calc_ts_stats_by_group(s_rbm_to_plot, 'month', 'mean') # index is 1-12 (month)
# plot
fig = plt.figure()
ax = plt.axes()
plt.plot_date(s_usgs_seas.index, s_usgs_seas, 'b-', label='USGS gauge')
plt.plot_date(s_rbm_seas.index, s_rbm_seas, 'r--', label='Lohmann route')
plt.ylabel('Stream T (degC)', fontsize=16)
plt.title('%s, %s\nMonthly mean seasonality, water years %d - %d' %(usgs_site_name, usgs_site_code, plot_start_date.year+1, plot_end_date.year), fontsize=16)
plt.legend()
# formatting
plt.xlim([1, 12])
tick_labels = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Nov','Oct','Nov','Dec']
my_functions.plot_format(ax, xtick_location=range(1,13), xtick_labels=tick_labels)

fig = plt.savefig('%s.streamT.season.png' %output_plot_basename, format='png')





