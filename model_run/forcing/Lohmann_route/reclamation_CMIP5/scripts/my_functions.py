#!/usr/local/anaconda/bin/python

#========================================================================
#========================================================================

def read_nc(infile, varname, dimension=-1, is_time=0):
	'''Read a variable from a netCDF file

	Input:
		input file path
		variable name
		dimension: if < 0, read in all dimensions of the variable; if >= 0, only read in the [dimension]th of the variable (index starts from 0). For example, if the first dimension of the variable is time, and if dimension=2, then only reads in the 3rd time step.
		is_time: if the desired variable is time (1 for time; 0 for not time). If it is time, return an array of datetime object

	Return:
		var: a numpy array of
	''' 
	from netCDF4 import Dataset
	from netCDF4 import num2date

	nc = Dataset(infile, 'r')
	if is_time==0:  # if not time variable
		if dimension<0:
			var = nc.variables[varname][:]
		else:
			var = nc.variables[varname][dimension]
	if is_time==1:  # if time variable
		time = nc.variables[varname]
		if hasattr(time, 'calendar'):  # if time variable has 'calendar' attribute
			if dimension<0:
				var = num2date(time[:], time.units, time.calendar)
			else:
				var = num2date(time[dimension], time.units, time.calendar)
		else:  # if time variable does not have 'calendar' attribute
			if dimension<0:
				var = num2date(time[:], time.units)
			else:
				var = num2date(time[dimension], time.units)
	nc.close()
	return var

#========================================================================
#========================================================================

def find_value_index(value_array, value):
	'''Find the index of a value in an array (index starts from 0)
	Return:
		The first index of the value
	'''

	import numpy as np

	index = np.where(value_array==value)
	return index[0][0]



