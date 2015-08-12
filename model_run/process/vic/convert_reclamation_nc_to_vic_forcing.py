#!/usr/local/anaconda/bin/python

# This script is for preprocessing Reclamation VIC forcing netCDF data
# This script converts Reclamation VIC forcing netCDF data to VIC input ascii format

import numpy as np
import sys
import my_functions

scenario = sys.argv[1]

#=================================================#
# Parameter setting
#=================================================#
#=== input ===#
input_nc_basepath = '/raid2/ymao/VIC_RBM_east/VIC_RBM/model_run/forcing/vic/reclamation_CMIP5/{}/nc/conus_c5.{}.daily'.format(scenario, scenario)  # input netCDF file containing VIC forcing data); Each file is one year; "pr/tasmas/tasmin/wind.$year.nc" will be appended to this basepath
start_year = 1950  # process start year
end_year = 2099  # process end year
lat_name = 'latitude'  # variable name of lat in the nc file
lon_name = 'longitude'  # variable name of lon in the nc file
time_name = 'time'  # variable name of time in the nc file
pr_name = 'pr'  # variable name of precipitation in the nc file
tasmax_name = 'tasmax'  # variable name of Tmax in the nc file
tasmin_name = 'tasmin'  # variable name of Tmin in the nc file
wind_name = 'wind'  # variable name of wind in the nc file

basin_latlon_list_path = '/raid2/ymao/VIC_RBM_east/VIC_RBM/preprocess/find_basin_grid_cells/output/global_Wu_8th/Tennessee/Tennessee.latlon_list'  # [lat]; [lon]. A latlon list of desired basin; only these latlon grid cells will be converted to VIC output ascii format

#=== output ===#
output_dir = '/raid2/ymao/VIC_RBM_east/VIC_RBM/model_run/forcing/vic/reclamation_CMIP5/{}/asc'.format(scenario)  # outpud directory to put VIC ascii forcing files in
latlon_digit = 4  # number of digits in the output file names

#=================================================#
# Get lat lon info from nc file
#=================================================#
lat_nc = my_functions.read_nc('{:s}.pr.{:4d}.nc'.format(input_nc_basepath, start_year), lat_name, dimension=-1, is_time=0)
lon_nc = my_functions.read_nc('{:s}.pr.{:4d}.nc'.format(input_nc_basepath, start_year), lon_name, dimension=-1, is_time=0)

#=================================================#
# Load latlon list
#=================================================#
latlon_list = np.loadtxt(basin_latlon_list_path)

#=================================================#
# Write traditional VIC output files
# <YYYY> <MM> <DD> <pr (mm/day)> <tasmax (degC)> <tasmin (degC)> <wind (m/s)>
#=================================================#
# open files for each grid cell for writing
f = []  # a list of file objects
for i in range(len(latlon_list)):
	filename = '%s/data_%.*f_%.*f' %(output_dir, latlon_digit, latlon_list[i,0], latlon_digit, latlon_list[i,1])
	f.append(open(filename, 'w'))

# load and write data for each year
for year in range(start_year, end_year+1):
	print 'Write data for year %d...' %year
	#=== load nc file for this year ===#
	time_nc = my_functions.read_nc('{:s}.pr.{:4d}.nc'.format(input_nc_basepath, year), time_name, dimension=-1, is_time=1)
	pr_nc = my_functions.read_nc('{:s}.pr.{:4d}.nc'.format(input_nc_basepath, year), pr_name, dimension=-1, is_time=0)
	tasmax_nc = my_functions.read_nc('{:s}.tasmax.{:4d}.nc'.format(input_nc_basepath, year), tasmax_name, dimension=-1, is_time=0)
	tasmin_nc = my_functions.read_nc('{:s}.tasmin.{:4d}.nc'.format(input_nc_basepath, year), tasmin_name, dimension=-1, is_time=0)
	wind_nc = my_functions.read_nc('{:s}.wind.{:4d}.nc'.format(input_nc_basepath, year), wind_name, dimension=-1, is_time=0)

	for i in range(len(latlon_list)):  # for each grid cell in the latlon list
		#=== Calculate lat and lon index in the nc file ===#
		lat = latlon_list[i,0]
		lon = latlon_list[i,1]
		lat_ind = my_functions.find_value_index(lat_nc, lat)
		lon_ind = my_functions.find_value_index(lon_nc, lon)
		#=== Write for each grid cell ===#
		for t in range(len(time_nc)):  # for each day in this year
			time = time_nc[t]
			year = time.year
			month = time.month
			day = time.day
			pr = pr_nc[t, lat_ind, lon_ind]
			tasmax = tasmax_nc[t, lat_ind, lon_ind]
			tasmin = tasmin_nc[t, lat_ind, lon_ind]
			wind = wind_nc[t, lat_ind, lon_ind]
			f[i].write('{:4d} {:2d} {:2d} {:f} {:.2f} {:.2f} {:.2f}\n'.format(year, month, day, pr, tasmax, tasmin, wind))

# close files
for i in range(len(latlon_list)):
	f[i].close()







