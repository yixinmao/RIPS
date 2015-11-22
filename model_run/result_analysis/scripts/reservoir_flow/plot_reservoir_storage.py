#!/usr/local/anaconda/bin/python

''' This script plots simulated reservoir storages at each dam '''

import pandas as pd
import sys
import glob
import datetime as dt
import matplotlib.pyplot as plt
import my_functions

cfg = my_functions.read_config(sys.argv[1])

parse = lambda x: dt.datetime.strptime(x, '%Y %m %d')

#============ Process "\n" in "model_info" ==================#
model_info = cfg['PLOT_OPTIONS']['model_info'].replace("\\n", "\n")

#=== Loop over each dam ===#
for filename in glob.glob('{}.dam*.txt'.format(cfg['INPUT']['storage_basepath'])):
    dam = filename.split('.')[-2]  # a string: 'dam#'
    print 'Plotting {}...'.format(dam)
    #=== Load data ===#
    df = pd.read_csv(filename, delim_whitespace=True, parse_dates=[[0,1,2]], \
                     index_col=0, date_parser=parse)

    #=== Plot - time series ===#
    fig = my_functions.plot_time_series(plot_date=True, \
                list_s_data=[df['rule_curve_acre_ft'], df['storage_acre_ft']], \
                list_style=['k-', 'g--'], \
                list_label=['Rule curve', 'Simulated storage'], \
                plot_start=dt.datetime(df.index[-1].year-5, 10, 1), \
                plot_end=dt.datetime(df.index[-1].year, 9, 30), \
                xlabel=None, ylabel='Rule curve or storage (acre-feet)', \
                title='Daily, {}'.format(dam), fontsize=16, \
                legend_loc='upper right', \
                time_locator=None, time_format='%Y/%m', \
                xtick_location=None, xtick_labels=None, \
                add_info_text=True, model_info=model_info, \
                stats=None, show=False)
    fig.savefig('{}.storage.daily.{}.png'.format(cfg['OUTPUT']['plots_basepath'], dam), \
                format='png')

    #=== Plot - average daily storage ===#
    # Calculate average daily storage
    df_day = my_functions.calc_ts_stats_by_group(df, by='day_of_year', stat='mean')
    fig = my_functions.plot_time_series(plot_date=False, \
                list_s_data=[df_day['rule_curve_acre_ft'], df_day['storage_acre_ft']], \
                list_style=['k-', 'g--'], \
                list_label=['Rule curve', 'Simulated storage'], \
                plot_start=1, \
                plot_end=365, \
                xlabel=None, ylabel='Rule curve or storage (acre-feet)', \
                title='Average daily storage, {}'.format(dam), fontsize=16, \
                legend_loc='upper right', \
                xtick_location=range(1,366,31), \
                xtick_labels=['Jan','Feb','Mar','Apr','May','Jun', \
                              'Jul','Aug','Sep','Oct','Nov','Dec'], \
                add_info_text=True, model_info=model_info, \
                stats='Average daily in year', show=False)
    fig.savefig('{}.storage.dailyAvg.{}.png'.format(cfg['OUTPUT']['plots_basepath'], dam), \
                format='png')



