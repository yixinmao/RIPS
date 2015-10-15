#!/usr/local/anaconda/bin/python

# This script plots different routed flow results together

import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import sys
import pandas as pd
import argparse
import os
import my_functions

parser = argparse.ArgumentParser()
parser.add_argument("--cfg", type=str,  help="config file for this script")
parser.add_argument("--USGS_code", type=str,  help="USGS code")
parser.add_argument("--USGS_name", type=str,  help="USGS name")
parser.add_argument("--hist_route_path", type=str, help="Historical route output path")
parser.add_argument("--future_route_paths_rcp45", type=str, help="eg. 'path_rcp45'")
parser.add_argument("--future_route_paths_rcp85", type=str, help="eg. 'path_rcp85'")
parser.add_argument("--future_route_names", type=str, help="eg. 'GCM'")
args = parser.parse_args()

# Read in cfg file
cfg = my_functions.read_config(args.cfg)

dpi = 200  # figure dpi

#-------------- The following is temporal --------------#
individual_model_list = cfg['INPUT']['GCM_list_path']  # '/raid2/ymao/VIC_RBM_east/VIC_RBM/model_run/result_analysis/data/list_5GCM_route_path'
future_scenario_basedir = cfg['INPUT']['future_scenario_basedir']  # '/raid2/ymao/VIC_RBM_east/VIC_RBM/model_run/output/Lohmann_route/reclamation_CMIP5/Tennessee_1950_2099'  # Lohmann route output files of a certain scenario will be: future_scenario_basedir/GCM/

#========================================================
# Parameter setting
#========================================================
usgs_site_code = args.USGS_code # '03571850'
usgs_site_name = args.USGS_name # 'Tennessee River at Lower Pittsburgh'

hist_route_path = args.hist_route_path # historical run. Lohmann routing output. year; month; day; flow(cfs)
future_route_paths_rcp45 = args.future_route_paths_rcp45 # future run. Lohmann routing output. year; month; day; flow(cfs); ['path1', 'path2']
future_route_paths_rcp85 = args.future_route_paths_rcp85 # future run. Lohmann routing output. year; month; day; flow(cfs); ['path1', 'path2']
future_route_names = args.future_route_names # future run. year; month; day; flow(cfs); ['GCM1', 'GCM2']

output_plot_basename = cfg['OUTPUT']['output_plot_basepath'] + '.' + usgs_site_code + '.' + future_route_names  # output plot path basename (suffix will be added to different plots)

#-------------------------------------------------
# list of Lohmann daily output data paths
hist_route_path = hist_route_path
control_route_path = future_route_paths_rcp45
list_future_route_path_rcp45 = [future_route_paths_rcp45, future_route_paths_rcp45, future_route_paths_rcp45]
list_future_route_path_rcp85 = [future_route_paths_rcp85, future_route_paths_rcp85, future_route_paths_rcp85]

nfuture = len(list_future_route_path_rcp45)

# list of start date shown on the plot for each time series to plot (should be complete water years)
#hist_plot_start_date = dt.datetime(1969,10,1)  # historical
#control_plot_start_date = dt.datetime(1969,10,1)  # control
#list_future_plot_start_date = [dt.datetime(2009,10,1),  # future 1, 2020s
#                          dt.datetime(2039,10,1),  # future 2, 2050s
#                          dt.datetime(2069,10,1)]   # future 3, 2080s
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
#hist_plot_end_date = dt.datetime(1999,9,30)  # historical
#control_plot_end_date = dt.datetime(1999,9,30)  # control
#list_future_plot_end_date = [dt.datetime(2039,9,30),   # future 1, 2020s
#                      dt.datetime(2069,9,30),   # future 2, 2050s 
#                      dt.datetime(2099,9,30)]   # future 3, 2080s
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

#-------------------------------------------------

#model_info = 'VIC runoff, historical -  1/8 deg, Maurer forcing, Andy Wood setup\n          VIC runoff, climate change scenarios - 1/8 deg, Reclamation archive (GCM forcing)\n          Route: Lohmann, Wu flowdir, Andy Wood setup'
#model_info = 'VIC runoff, historical -  1/8 deg, Maurer forcing, Andy Wood setup\n          VIC runoff, climate change scenarios - 1/8 deg, Reclamation archive (GCM forcing)\n          5 model avg.: average the routing results of: access1-0; bcc-csm1-1-m; canesm2; \n          ccsm4; cesm1-bgc\n          Route: Lohmann, Wu flowdir, Andy Wood setup'
model_info = cfg['PLOT']['model_info']
model_info = model_info.replace("\\n", "\n")

#========================================================
# Load data
#========================================================
hist_s_data = my_functions.read_Lohmann_route_daily_output(hist_route_path)/1000  # convert to 1000 cfs
control_s_data = my_functions.read_Lohmann_route_daily_output(control_route_path)/1000  # convert to 1000 cfs
list_future_s_data_rcp45 = []  # a list contains pd.Series of data of each time series to plot
list_future_s_data_rcp85 = []  # a list contains pd.Series of data of each time series to plot
for i in range(nfuture):
	future_s_data_rcp45 = my_functions.read_Lohmann_route_daily_output(list_future_route_path_rcp45[i])/1000  # convert to 1000 cfs
	list_future_s_data_rcp45.append(future_s_data_rcp45)
	future_s_data_rcp85 = my_functions.read_Lohmann_route_daily_output(list_future_route_path_rcp85[i])/1000  # convert to 1000 cfs
	list_future_s_data_rcp85.append(future_s_data_rcp85)

#========================================================
# Select data to be plotted
#========================================================
hist_s_to_plot = my_functions.select_time_range(hist_s_data, hist_plot_start_date, hist_plot_end_date)
control_s_to_plot = my_functions.select_time_range(control_s_data, control_plot_start_date, control_plot_end_date)
list_future_s_to_plot_rcp45 = []
list_future_s_to_plot_rcp85 = []
for i in range(nfuture):
	future_s_to_plot_rcp45 = my_functions.select_time_range(list_future_s_data_rcp45[i], list_future_plot_start_date[i], list_future_plot_end_date[i])
	list_future_s_to_plot_rcp45.append(future_s_to_plot_rcp45)
	future_s_to_plot_rcp85 = my_functions.select_time_range(list_future_s_data_rcp85[i], list_future_plot_start_date[i], list_future_plot_end_date[i])
	list_future_s_to_plot_rcp85.append(future_s_to_plot_rcp85)

#========================================================
# plot
#========================================================

#============== plot seasonality data ===============#
# plot rcp45
fig = my_functions.plot_seasonality_data(list_s_data=[control_s_to_plot]+list_future_s_to_plot_rcp45, \
		list_style=[control_style]+list_future_style, \
		list_label=[control_label]+list_future_label, \
		plot_start=1, plot_end=12, \
		ylabel='Flow (thousand cfs)', \
		title='Monthly mean seasonality, {:s}, {:s}\nRCP4.5'.format(usgs_site_name, usgs_site_code), 
		fontsize=20, legend_loc=None, \
		xtick_location=range(1,13), \
		xtick_labels=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Nov','Oct','Nov','Dec'], \
		add_info_text=True, model_info=model_info, stats='Monthly mean; historical - WY%d-%d; future projection - 1980s: WY1970-1999; \n          2020s: WY2010-2039; 2050s: WY2040-2069; 2080s: WY2070-2099' %(hist_plot_start_date.year+1, hist_plot_end_date.year)) \

ax = plt.gca()
for tick in ax.xaxis.get_major_ticks():
    tick.label.set_fontsize(18)
for tick in ax.yaxis.get_major_ticks():
    tick.label.set_fontsize(18)

fig = plt.savefig('%s.rcp45.future.flow.seas.png' %output_plot_basename, format='png', dpi=dpi)

# plot rcp85
fig = my_functions.plot_seasonality_data(list_s_data=[control_s_to_plot]+list_future_s_to_plot_rcp85, \
		list_style=[control_style]+list_future_style, \
		list_label=[control_label]+list_future_label, \
		plot_start=1, plot_end=12, \
		ylabel='Flow (thousand cfs)', \
		title='Monthly mean seasonality, {:s}, {:s}\nRCP8.5'.format(usgs_site_name, usgs_site_code), 
		fontsize=20, legend_loc=None, \
		xtick_location=range(1,13), \
		xtick_labels=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Nov','Oct','Nov','Dec'], \
		add_info_text=True, model_info=model_info, stats='Monthly mean; historical - WY%d-%d; future projection - 1980s: WY1970-1999; \n          2020s: WY2010-2039; 2050s: WY2040-2069; 2080s: WY2070-2099' %(hist_plot_start_date.year+1, hist_plot_end_date.year)) \

ax = plt.gca()
for tick in ax.xaxis.get_major_ticks():
    tick.label.set_fontsize(18)
for tick in ax.yaxis.get_major_ticks():
    tick.label.set_fontsize(18)

fig = plt.savefig('%s.rcp85.future.flow.seas.png' %output_plot_basename, format='png', dpi=dpi)

#============== plot period-average annual mean flow ===============#
# calculate annual mean flow data (WY)
hist_s_WY_mean = my_functions.calc_WY_mean(hist_s_to_plot)  # only plot one control result
control_s_WY_mean = my_functions.calc_WY_mean(control_s_to_plot)  # only plot one control result
list_future_s_WY_mean = []  # each element of the list is a sublist: [rcp45, rcp85]
for i in range(nfuture):
	s_WY_mean_rcp45 = my_functions.calc_WY_mean(list_future_s_to_plot_rcp45[i])
	s_WY_mean_rcp85 = my_functions.calc_WY_mean(list_future_s_to_plot_rcp85[i])
	list_future_s_WY_mean.append([s_WY_mean_rcp45, s_WY_mean_rcp85])  # only plot one control result

##------- plot historical vs. control (control is for individual models) -------#
## This part is not general and has some hard-coded parts!!!
## Read in individual GCM results
#list_individual_GCM = []
#f = open(individual_model_list, 'r')
#while 1:
#	line = f.readline().rstrip("\n")
#	if line=="":
#		break
#	list_individual_GCM.append(line)
#f.close()
## Load data and select control period for each GCM
#list_s_control_GCMs_WY_mean = [[hist_s_WY_mean]]
#list_xlabels = ['Historical\n1980s']
#color_list = [[hist_color]]
#list_s_control_GCMs_WY_mean.append([control_s_WY_mean])
#list_xlabels.append('Control, 1980s\n5 GCM avg.')
#color_list.append([control_color])
#for i in range(len(list_individual_GCM)):
#	s_GCM_45 = my_functions.read_Lohmann_route_daily_output('{}/{}_rcp45_r1i1p1/{}'.format(future_scenario_basedir, list_individual_GCM[i], os.path.basename(hist_route_path)))/1000  # convert to 1000 cfs
#	s_GCM_control = my_functions.select_time_range(s_GCM_45, control_plot_start_date, control_plot_end_date)
#	s_GCM_control_WY_mean = my_functions.calc_WY_mean(s_GCM_control)
#	list_s_control_GCMs_WY_mean.append([s_GCM_control_WY_mean])
#	list_xlabels.append(list_individual_GCM[i])
#	color_list.append(['m'])
#
#fig = my_functions.plot_boxplot(list_data = list_s_control_GCMs_WY_mean, \
#			list_xlabels = list_xlabels, \
#			color_list = color_list, \
#			rotation = 0, ylabel = 'Flow (thousand cfs)', \
#			title='Average annual mean flow, {}, {}'.format(usgs_site_name, usgs_site_code), \
#			fontsize=16, add_info_text=True, model_info=model_info, \
#			stats = 'Period average of annual mean flow (WY); \n          historical & control - WY1970-1999', \
#			bottom=0.4, text_location=-0.2)
#
#fig = plt.savefig('%s.future.flow.WY_mean_boxplot.hist_control.png' %output_plot_basename, format='png', dpi=dpi)

#--------- plot future periods ----------#
# determine data to plot (control; future periods (each period has rcp45 and rcp85))
list_data = []
list_data.append([control_s_WY_mean])
for i in range(nfuture):
	list_data.append(list_future_s_WY_mean[i])
# determine color to plot
color_list = []
color_list.append([control_color])
for i in range(nfuture):
	color_list.append(['y', 'r'])  # these two colors correspond to rcp45 and rcp85
# plot
fig = my_functions.plot_boxplot(list_data = list_data, \
			list_xlabels = ['Control, 1980s\n5 GCM avg.']+list_future_label, \
			color_list = color_list, \
			rotation = 0, ylabel = 'Flow (thousand cfs)', \
			title='Average annual mean flow\n{}, {}'.format(usgs_site_name, usgs_site_code), \
			fontsize=20, \
			legend_text_list=['RCP4.5', 'RCP8.5'], legend_color_list=['y', 'r'], \
			legend_loc='upper left', \
			add_info_text=True, model_info=model_info, \
			stats='Period average of annual mean flow (WY); \n          historical - WY%d-%d; future projection - 1980s: WY1970-1999; \n          2020s: WY2010-2039; 2050s: WY2040-2069; 2080s: WY2070-2099' %(hist_plot_start_date.year+1, hist_plot_end_date.year), \
			bottom=0.4, text_location=-0.2)

ax = plt.gca()
for tick in ax.xaxis.get_major_ticks():
    tick.label.set_fontsize(18)
for tick in ax.yaxis.get_major_ticks():
    tick.label.set_fontsize(18)

fig = plt.savefig('%s.future.flow.WY_mean_boxplot.png' %output_plot_basename, format='png', dpi=dpi)

##============== plot flow duration curve ===============#
#fig = my_functions.plot_duration_curve(list_s_data=[control_s_to_plot]+list_future_s_to_plot_rcp45, \
#		list_style=[control_style]+list_future_style, \
#		list_label=[control_label]+list_future_label, \
#		figsize=(10,10), ylog=True, xlim=None, ylim=None, \
#		xlabel='Exceedence', ylabel='Flow (thousand cfs)', \
#		title='{:s}, {:s}, RCP4.5'.format(usgs_site_name, usgs_site_code), fontsize=16, \
#		legend_loc='upper right', add_info_text=True, model_info=model_info, \
#		stats='Flow duration curve based on daily data', show=False)
#
#fig = plt.savefig('%s.future.flow_duration.png' %output_plot_basename, format='png', dpi=dpi)


