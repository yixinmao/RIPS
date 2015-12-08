#!/usr/local/anaconda/bin/python

# This script plots control and future stream temperature results together

import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import sys
import pandas as pd
import os
import my_functions

# Read in cfg file
cfg = my_functions.read_config(sys.argv[1])

dpi = 200 # figure dpi

#=======================================================#
# Preprocess
#=======================================================#
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
print 'Loading data...'
s_rcp45 = my_functions.read_Lohmann_route_daily_output(\
                            cfg['GCM_AVG']['path'].replace('<RCP>', 'rcp45'))
s_rcp85 = my_functions.read_Lohmann_route_daily_output(\
                            cfg['GCM_AVG']['path'].replace('<RCP>', 'rcp85'))

#========================================================
# Select data to be plotted
#========================================================
# Select control period
control_s_to_plot = s_rcp45.truncate(before=control_plot_start_date, \
                                     after=control_plot_end_date)
# Select future periods
list_future_s_to_plot_rcp45 = []
list_future_s_to_plot_rcp85 = []
for i in range(nfuture):
    # rcp45
    future_s_to_plot_rcp45 = s_rcp45.truncate(before=list_future_plot_start_date[i], \
                                               after=list_future_plot_end_date[i])
    list_future_s_to_plot_rcp45.append(future_s_to_plot_rcp45)
    # rcp85
    future_s_to_plot_rcp85 = s_rcp85.truncate(before=list_future_plot_start_date[i], \
                                               after=list_future_plot_end_date[i])
    list_future_s_to_plot_rcp85.append(future_s_to_plot_rcp85)

#========================================================
# plot
#========================================================
print 'plotting...'
#============== plot seasonality data ===============#
# plot rcp45
fig = my_functions.plot_seasonality_data(list_s_data=[control_s_to_plot]+list_future_s_to_plot_rcp45, \
        list_style=[control_style]+list_future_style, \
        list_label=[control_label]+list_future_label, \
        plot_start=1, plot_end=12, \
        ylabel='Stream temperature ($^oC$)', \
        title='Monthly climatology, {}, RCP4.5'.format(cfg['PLOT']['title']), 
        fontsize=16, legend_loc='upper left', \
        xtick_location=range(1,13), \
        xtick_labels=['Jan','Feb','Mar','Apr','May','Jun',\
                      'Jul','Aug','Sep','Oct','Nov','Dec'], \
        add_info_text=True, model_info=cfg['PLOT']['model_info'], \
        stats='Monthly mean; historical - WY{}-{}; future projection - 1980s: WY1970-1999; \n          2020s: WY2010-2039; 2050s: WY2040-2069; 2080s: WY2070-2099'.format(hist_plot_start_date.year+1, hist_plot_end_date.year)) \

fig = plt.savefig('{}.rcp45.future.Tstream.seas.png'\
                        .format(cfg['OUTPUT']['output_plot_basepath']), \
                  format='png', dpi=dpi)

# plot rcp85
fig = my_functions.plot_seasonality_data(list_s_data=[control_s_to_plot]+list_future_s_to_plot_rcp85, \
        list_style=[control_style]+list_future_style, \
        list_label=[control_label]+list_future_label, \
        plot_start=1, plot_end=12, \
        ylabel='Stream temperature ($^oC$)', \
        title='Monthly climatology, {}, RCP8.5'.format(cfg['PLOT']['title']), 
        fontsize=16, legend_loc='upper left', \
        xtick_location=range(1,13), \
        xtick_labels=['Jan','Feb','Mar','Apr','May','Jun',\
                      'Jul','Aug','Sep','Oct','Nov','Dec'], \
        add_info_text=True, model_info=cfg['PLOT']['model_info'], \
        stats='Monthly mean; historical - WY{}-{}; future projection - 1980s: WY1970-1999; \n          2020s: WY2010-2039; 2050s: WY2040-2069; 2080s: WY2070-2099'.format(hist_plot_start_date.year+1, hist_plot_end_date.year)) \

fig = plt.savefig('{}.rcp85.future.Tstream.seas.png'\
                        .format(cfg['OUTPUT']['output_plot_basepath']), \
                  format='png', dpi=dpi)

#============== plot period-average annual mean flow ===============#
# calculate annual mean flow data (WY)
control_s_WY_mean = my_functions.calc_WY_mean(control_s_to_plot)  # only plot one control result
list_future_s_WY_mean = []  # each element of the list is a sublist: [rcp45, rcp85]
for i in range(nfuture):
    s_WY_mean_rcp45 = my_functions.calc_WY_mean(list_future_s_to_plot_rcp45[i])
    s_WY_mean_rcp85 = my_functions.calc_WY_mean(list_future_s_to_plot_rcp85[i])
    list_future_s_WY_mean.append([s_WY_mean_rcp45, s_WY_mean_rcp85])  # only plot one control result

# determine data to plot (control; future periods (each period has rcp45 and rcp85))
list_data = []
list_data.append([control_s_WY_mean])
for i in range(nfuture):
    list_data.append(list_future_s_WY_mean[i])
# determine color to plot
color_list = []
color_list.append([control_color])
for i in range(nfuture):
    color_list.append(['y', 'm'])  # these two colors correspond to rcp45 and rcp85
# plot
fig = my_functions.plot_boxplot(list_data = list_data, \
            list_xlabels = ['Control, 1980s\n5 GCM avg.']+list_future_label, \
            color_list = color_list, \
            rotation = 0, ylabel = 'Stream temperature ($^oC$)', \
            title='Average annual mean stream T\n{}'.format(cfg['PLOT']['title']), \
            fontsize=20, \
            legend_text_list=['RCP4.5', 'RCP8.5'], legend_color_list=['y', 'm'], \
            legend_loc='upper left', \
            add_info_text=True, model_info=model_info, \
            stats='Period average of annual mean stream T (WY); \n          historical - WY%d-%d; future projection - 1980s: WY1970-1999; \n          2020s: WY2010-2039; 2050s: WY2040-2069; 2080s: WY2070-2099' %(hist_plot_start_date.year+1, hist_plot_end_date.year), \
            bottom=0.4, text_location=-0.2)

ax = plt.gca()
for tick in ax.xaxis.get_major_ticks():
    tick.label.set_fontsize(18)
for tick in ax.yaxis.get_major_ticks():
    tick.label.set_fontsize(18)

fig = plt.savefig('{}.future.Tstream.WY_mean_boxplot.png'\
                        .format(cfg['OUTPUT']['output_plot_basepath']), \
                  format='png', dpi=dpi)

#============== plot duration curve ===============#
# RCP4.5
fig = my_functions.plot_duration_curve(\
        list_s_data=[control_s_to_plot]+list_future_s_to_plot_rcp45, \
        list_style=[control_style]+list_future_style, \
        list_label=[control_label]+list_future_label, \
        figsize=(10,10), ylog=True, xlim=None, ylim=None, \
        xlabel='Exceedence', ylabel='Stream temperature ($^oC$)', \
        title='{}, RCP4.5'.format(cfg['PLOT']['title']), fontsize=16, \
        legend_loc='upper right', add_info_text=True, model_info=model_info, \
        stats='Stream T duration curve based on daily data', show=False)

fig = plt.savefig('{}.future.Tstream_duration.rcp45.png'\
                        .format(cfg['OUTPUT']['output_plot_basepath']), \
                  format='png', dpi=dpi)

# RCP8.5
fig = my_functions.plot_duration_curve(\
        list_s_data=[control_s_to_plot]+list_future_s_to_plot_rcp85, \
        list_style=[control_style]+list_future_style, \
        list_label=[control_label]+list_future_label, \
        figsize=(10,10), ylog=True, xlim=None, ylim=None, \
        xlabel='Exceedence', ylabel='Stream temperature ($^oC$)', \
        title='{}, RCP8.5'.format(cfg['PLOT']['title']), fontsize=16, \
        legend_loc='upper right', add_info_text=True, model_info=model_info, \
        stats='Stream T duration curve based on daily data', show=False)

fig = plt.savefig('{}.future.Tstream_duration.rcp85.png'\
                        .format(cfg['OUTPUT']['output_plot_basepath']), \
                  format='png', dpi=dpi)


