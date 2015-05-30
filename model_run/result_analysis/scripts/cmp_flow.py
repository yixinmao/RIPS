#!/usr/local/anaconda/bin/python

import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import my_functions

#========================================================
# Parameter setting
#========================================================
rbm_output_formatted_path = '/raid2/ymao/VIC_RBM_east/VIC_RBM/model_run/output/RBM/Maurer_8th/Tennessee/Tennessee_1949_2010/35.0625_-85.6875_reach299_seg2'  # year; month; day; flow(cfs); T_stream(deg); 1 header line

usgs_site_code = '03571850'
usgs_site_name = 'Tennessee River at Lower Pittsburgh'
usgs_data_path = '../data/USGS_data/streamflow_' + usgs_site_code + '.txt'
usgs_data_col = 1

output_plot_basename = '../output/Tennessee_flow_' + usgs_site_code # output plot path basename (suffix will be added to different plots)

#-------------------------------------------------

plot_start_date = dt.datetime(1950, 10, 1)  # start date shown on the plot (should be complete water years)
plot_end_date = dt.datetime(1987, 9, 30)  # end date shown on the plot

time_locator = ('year', 5)  # time locator on the plot; 'year' for year; 'month' for month. e.g., ('month', 3) for plot one tick every 3 months

#-------------------------------------------------

#========================================================
# Load data
#========================================================
# RBM output
rbm_data = np.loadtxt(rbm_output_formatted_path, skiprows=1)  # year; month; day; flow(cfs); T_stream(deg)
rbm_date = my_functions.convert_YYYYMMDD_to_datetime(rbm_data[:,0], rbm_data[:,1], rbm_data[:,2])
df_rbm = my_functions.convert_time_series_to_df(rbm_date, rbm_data[:,3], ['flow'])  # convert to pd.DataFrame

# USGS flow
df_usgs = my_functions.read_USGS_data(usgs_data_path, columns=[1], names=['flow'])  # [cfs]

#========================================================
# Select data to be plotted
#========================================================
df_rbm_to_plot = my_functions.select_time_range(df_rbm, plot_start_date, plot_end_date)
df_usgs_to_plot = my_functions.select_time_range(df_usgs, plot_start_date, plot_end_date)

#========================================================
# plot
#========================================================
#============== plot daily data ===============#
fig = plt.figure()
ax = plt.axes()
plt.plot_date(df_usgs_to_plot.index, df_usgs_to_plot.flow, 'b-', label='USGS gauge')
plt.plot_date(df_rbm_to_plot.index, df_rbm_to_plot.flow, 'r--', label='Lohmann route')
plt.ylabel('Flow (cfs)', fontsize=16)
plt.title('%s, %s' %(usgs_site_name, usgs_site_code), fontsize=16)
plt.legend()
my_functions.plot_date_format(ax, time_range=(plot_start_date, plot_end_date), locator=time_locator, time_format='%Y/%m')

fig = plt.savefig('%s.daily.png' %output_plot_basename, format='png')

plt.show()

