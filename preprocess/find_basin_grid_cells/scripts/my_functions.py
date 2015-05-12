#!/usr/local/anaconda/bin/python

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

def get_nc_spatial(infile, varname, lonname, latname):
	''' This function reads in a spatial variable from netCDF file

	Input:
		infile: input nc file path [str]
		varname: variable name [str]
		lonname, latname: lon and lat variable names [str] (lat and lon can be 1-D or 2-D variables)

	Return:
		var, lon_mesh, lat_mesh: all are 2-D numpy arrays [np.array]

	Require:
		read_nc
		count_dimension
	'''

	import numpy as np

	var = read_nc(infile, varname)
	lat = read_nc(infile, latname)
	lon = read_nc(infile, lonname)

	lat_dim = count_dimension(lat)  # lat variable dimension
	lon_dim = count_dimension(lon)  # lon variable dimension

	if lat_dim==lon_dim and lat_dim==1:  # if lat and lon are 1-D
		lon_mesh, lat_mesh = np.meshgrid(lon, lat)
	elif lat_dim==lon_dim and lat_dim==2:
		lon_mesh = lon
		lat_mesh = lat
	else:
		print "Dimension of lat or lon is incorrect!"
		exit()

	return var, lon_mesh, lat_mesh

#========================================================================
#========================================================================

def count_dimension(x):
	''' This function returns the number of dimension of an np array

	Input: a numpy array

	Return: number of dimension of the array [int]
	'''

	import numpy as np

	return np.shape(np.shape(x))[0]






