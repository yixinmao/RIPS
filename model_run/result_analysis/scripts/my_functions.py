#!/usr/local/anaconda/bin/python

#==============================================================
#==============================================================

def read_USGS_data(file, columns, names):
	'''This function reads USGS streamflow from the directly downloaded format (date and data are in the 3rd and 4th columns, respectively; data in cfs)

	Input: 
		file: directly downloaded streamflow file path [str]
		columns: a list of data colomn numbers, starting from 1. E.g., if the USGS original data has three variables: max_flow, min_flow, mean_flow, and the desired variable is mean_flow, then columns = [3]
		names: a list of data column names. E.g., ['mean_flow']; must the same length as columns

	Return:
		a pd.DataFrame object with time as index and data columns (NaN for missing data points)

	Note: returned data and flow might not be continuous if there is missing data!!!

	'''

	import numpy as np
	import datetime as dt
	import pandas as pd

	ndata = len(columns)
	if ndata != len(names):  # check input validity
		print "Error: input arguments 'columns' and 'names' must have same length!"
		exit()

	f = open(file, 'r')
	date_array = []
	data = []
	for i in range(ndata):
		data.append([])
	while 1:
		line = f.readline().rstrip("\n")  # read in one line
		if line=="":
			break
		line_split = line.split('\t')
		if line_split[0]=='USGS':  # if data line
			date_string = line_split[2]  # read in date string
			date = dt.datetime.strptime(date_string, "%Y-%m-%d")  # convert date to dt object
			date_array.append(date)

			for i in range(ndata):  # for each desired data variable
				col = columns[i]
				if line_split[3+(col-1)*2] == '':  # if data is missing
					value = np.nan
				elif line_split[3+(col-1)*2] == 'Ice':  # if data is 'Ice'
					value = np.nan
				else:  # if data is not missing
					value = float(line_split[3+(col-1)*2])
				data[i].append(value)

	data = np.asarray(data).transpose()
	df = pd.DataFrame(data, index=date_array, columns=names)
	return df

#==============================================================
#==============================================================

def convert_YYYYMMDD_to_datetime(year, month, day):
	''' Convert arrays of year, month, day to datetime objects
	Input:
		year: an array of years
		month: an array of months
		day: an array of days
		(The three arrays must be the same length)
	Return:
		A list of datetime objects
'''

	import numpy as np
	import datetime as dt

	# Check if the input arrays are the same length
	if len(year)!=len(month) or len(year)!=len(day) or len(month)!=len(day):
		print "Error: the length of input date arrays not the same length!"
		exit()

	n = len(year)
	date = []
	for i in range(n):
		date.append(dt.datetime(year=np.int(np.round(year[i])), month=np.int(np.round(month[i])), day=np.int(np.round(day[i]))))

	return date

#==============================================================
#==============================================================

def convert_time_series_to_df(time, data, columns):
	'''This function converts datetime objects and data array to pandas dataframe object

	Input:
		time: a list of datetime objects, e.g. [dt.datetime(2011,1,1), dt.datetime(2011,1,3)]
		data: a 1-D or 2D array of corresponding data; if 2-D, should have the same number of rows as 'time' length
		columns: a list of column names, the same length as the number of columns of 'data', e.g. ['A', 'B', 'C']

	Return: a dataframe object
	'''

	import pandas as pd
	df = pd.DataFrame(data, index=time, columns=columns)
	return df

#==============================================================
#==============================================================

def select_time_range(data, start_datetime, end_datetime):
	''' This function selects out the part of data within a time range

	Input:
		data: [dataframe/Series] data with index of datetime
		start_datetime: [dt.datetime] start time
		end_datetime: [dt.datetime] end time

	Return:
		Selected data (same object type as input)
	'''

	import datetime as dt

	start = data.index.searchsorted(start_datetime)
	end = data.index.searchsorted(end_datetime)

	data_selected = data.ix[start:end+1]

	return data_selected

#==============================================================
#==============================================================

def plot_date_format(ax, time_range=None, locator=None, time_format=None):
	''' This function formatting plots by plt.plot_date
	Input:
		ax: plotting axis
		time range: a tuple of two datetime objects indicating xlim. e.g., (dt.date(1991,1,1), dt.date(1992,12,31))

	'''

	import matplotlib.pyplot as plt
	import datetime as dt
	from matplotlib.dates import YearLocator, MonthLocator, DateFormatter

	# Plot time range
	if time_range!=None:
		plt.xlim(time_range[0], time_range[1])

	# Set time locator (interval)
	if locator!=None:
		if locator[0]=='year':
			ax.xaxis.set_major_locator(YearLocator(locator[1]))
		elif locator[0]=='month':
			ax.xaxis.set_major_locator(MonthLocator(interval=locator[1]))

	# Set time ticks format
	if time_format!=None:
		ax.xaxis.set_major_formatter(DateFormatter(time_format))

	return ax

#==============================================================
#==============================================================

def find_first_and_last_nonNaN_index(s):
	''' This function finds the first and last index with valid column values
	Input:
		df: Series object
		column: data column name to be investigated [str]
	'''

	import pandas as pd

	first_index = s[s.notnull()].index[0]
	last_index = s[s.notnull()].index[-1]
	return first_index, last_index

#==============================================================
#==============================================================

def find_data_common_range(s1, s2):
	''' This function determines the common range of valid data of two datasets (missing data in the middle also count as 'valid')

	Input: pd.Series objects

	Return: first and last datetimes of common range (Note: if one or both data have missing data at the beginning or end, those missing periods will be omitted; however, if there is missing data in the middle, those missing points will still be considered as valid)

	Requred:
		find_first_and_last_nonNaN_index
	'''

	s1_first_date, s1_last_date =  find_first_and_last_nonNaN_index(s1)
	s2_first_date, s2_last_date =  find_first_and_last_nonNaN_index(s2)
	data_avai_start_date = sorted([s1_first_date, s2_first_date])[-1]
	data_avai_end_date = sorted([s1_last_date, s2_last_date])[0]

	return data_avai_start_date, data_avai_end_date 

#==============================================================
#==============================================================

def find_full_water_years_within_a_range(dt1, dt2):
	''' This function determines the start and end date of full water years within a time range

	Input:
		dt1: time range starting time [dt.datetime]
		dt2: time range ending time [dt.datetime]

	Return:
		start and end date of full water years
	'''

	import datetime as dt

	if dt1.month <= 9:  # if dt1 is before Oct, start from Oct 1 this year
		start_date_WY = dt.datetime(dt1.year, 10, 1)
	elif dt1.month==10 and dt1.day==1:  # if dt1 is on Oct 1, start from this date
		start_date_WY = dt.datetime(dt1.year, 10, 1)
	else:  # if dt1 is after Oct 1, start from Oct 1 next year
		start_date_WY = dt.datetime(dt1.year+1, 10, 1)

	if dt2.month >=10:  # if dt2 is Oct or after, end at Sep 30 this year
		end_date_WY = dt.datetime(dt2.year, 9, 30)
	elif dt2.month==9 and dt2.day==30:  # if dt2 is on Sep 30, end at this date
		end_date_WY = dt.datetime(dt2.year, 9, 30)
	else:  # if dt2 is before Sep 30, end at Sep 30 last year
		end_date_WY = dt.datetime(dt2.year-1, 9, 30)

	if (end_date_WY-start_date_WY).days > 0:  # if at least one full water year
		return start_date_WY, end_date_WY
	else: # else, return -1 
		return -1

#==============================================================
#==============================================================

def calc_monthly_data(data):
	'''This function calculates monthly mean values

	Input: [DataFrame/Series] with index of time
	Return: a [DataFrame/Series] object, with monthly mean values (the same units as input data)
	'''

	import pandas as pd
	data_mon = data.resample("M", how='mean')
	return data_mon

#==============================================================
#==============================================================

def calc_ts_stats_by_group(data, by, stat):
	'''This function calculates statistics of time series data grouped by year, month, etc

	Input:
		df: a [pd.DataFrame/Series] object, with index of time
		by: string of group by, (select from 'year' or 'month')
		stat: statistics to be calculated, (select from 'mean')
		(e.g., if want to calculate monthly mean seasonality (12 values), by='month' and stat='mean')

	Return:
		A [dateframe/Series] object, with group as index (e.g. 1-12 for 'month')
	'''

	import pandas as pd

	if by=='year':
		if stat=='mean':
			data_result = data.groupby(lambda x:x.year).mean()
	elif by=='month':
		if stat=='mean':
			data_result = data.groupby(lambda x:x.month).mean()

	return data_result

#==============================================================
#==============================================================

def plot_format(ax, xtick_location=None, xtick_labels=None):
	'''This function formats plots by plt.plot

	Input:
		xtick_location: e.g. [1, 2, 3]
		xtick_labels: e.g. ['one', 'two', 'three']
	'''

	import matplotlib.pyplot as plt

	ax.set_xticks(xtick_location)
	ax.set_xticklabels(xtick_labels)

	return ax

#==============================================================
#==============================================================

def calc_annual_cumsum_water_year(time, data):
	'''This function calculates cumulative sum of data in each water year

	Input:
		time: corresponding datetime objects
		data: an array of data

	Return:
		time: the same as input
		data_cumsum: an array of annual (water year based) cumsum data; if there is missing data at a point, data_cumsum is np.nan after this point in this water year
	'''

	import numpy as np

	# Check if data and time is of the same length
	if len(data)!=len(time):
		print 'Error: data and time are not of the same length!'
		exit()

	data_cumsum = np.empty(len(data))
	for i in range(len(data)):
		if i==0:  # if the first day of record
			data_cumsum[0] = data[0]
		elif time[i].month!=10 or time[i].day!=1:  # if not Oct 1st, the same water year
			if (time[i]-time[i-1]).days>1:  # if the current day is not the next day of the previous day, i.e., if there is missing data here
				print 'Warning: missing data exists!'
				data_cumsum[i] = np.nan
			else:  # if no missing data at this time step, calculate cumsum
					data_cumsum[i] = data_cumsum[i-1] + data[i]
		else:  # if the current day is Oct 1st, and i!=0, the next water year
			data_cumsum[i] = data[i]

	return time, data_cumsum
 
