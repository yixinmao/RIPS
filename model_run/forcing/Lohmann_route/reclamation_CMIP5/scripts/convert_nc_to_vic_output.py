#!/usr/local/anaconda/bin/python

#================================================#
#================================================#

import numpy as np
import sys
import my_functions

scenario = sys.argv[1]


#=================================================#
# Parameter setting
#=================================================#
#=== input ===#
input_nc_basepath = '/raid2/ymao/VIC_RBM_east/VIC_RBM/model_run/forcing/Lohmann_route/reclamation_CMIP5/%s/nc/conus_c5.%s.daily.total_runoff' %(scenario, scenario)  # input netCDF file containing VIC output runoff (surface runoff and baseflow data); Each file is one year; ".$year.nc" will be appended to this basepath
start_year = 1950  # process start year
end_year = 2099  # process end year
lat_name = 'latitude'  # variable name of lat in the nc file
lon_name = 'longitude'  # variable name of lon in the nc file
time_name = 'time'  # variable name of time in the nc file
runoff_name = 'total runoff'  # variable name of surface runoff in the nc file; None for no surface runoff
baseflow_name = None  # variable name of baseflow in the nc file; None for no baseflow
# NOTE: surface runoff and baseflow will be summed in the routing model to arrive at total channel inflow
basin_latlon_list_path = '/raid2/ymao/VIC_RBM_east/VIC_RBM/preprocess/find_basin_grid_cells/output/global_Wu_8th/Tennessee/Tennessee.latlon_list'  # [lat]; [lon]. A latlon list of desired basin; only these latlon grid cells will be converted to VIC output ascii format

#=== output ===#
output_dir = '/raid2/ymao/VIC_RBM_east/VIC_RBM/model_run/forcing/Lohmann_route/reclamation_CMIP5/%s/asc/Tennessee' %scenario  # outpud directory to put traditional VIC output files in
latlon_digit = 4  # number of digits in the output file names

#=================================================#
# Load netCDF file for the first year
#=================================================#
lat_nc = my_functions.read_nc('%s.%d.nc' %(input_nc_basepath, start_year), lat_name, dimension=-1, is_time=0)
lon_nc = my_functions.read_nc('%s.%d.nc' %(input_nc_basepath, start_year), lon_name, dimension=-1, is_time=0)

#=================================================#
# Load latlon list
#=================================================#
latlon_list = np.loadtxt(basin_latlon_list_path)

#=================================================#
# Write traditional VIC output files
# <YYYY> <MM> <DD> <-999> <-999> <runoff (mm/d)> <baseflow (mm/day)>
# If either of surface runoff and baseflow is None, 0 value will be assined
#=================================================#
# open files for each grid cell for writing
f = []  # a list of file objects
for i in range(len(latlon_list)):
	filename = '%s/flow_%.*f_%.*f' %(output_dir, latlon_digit, latlon_list[i,0], latlon_digit, latlon_list[i,1])
	f.append(open(filename, 'w'))

# load and write data for each year
for year in range(start_year, end_year+1):
	print 'Write data for year %d...' %year
	#=== load nc file for this year ===#
	time_nc = my_functions.read_nc('%s.%d.nc' %(input_nc_basepath, year), time_name, dimension=-1, is_time=1)
	if runoff_name!=None:
		runoff_nc = my_functions.read_nc('%s.%d.nc' %(input_nc_basepath, year), runoff_name, dimension=-1, is_time=0)
	if baseflow_name!=None:
		baseflow_nc = my_functions.read_nc('%s.%d.nc' %(input_nc_basepath, year), baseflow_name, dimension=-1, is_time=0)

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
			if runoff_name!=None:
				runoff = runoff_nc[t, lat_ind, lon_ind]
			else:
				runoff = 0
			if baseflow_name!=None:
				baseflow = baseflow_nc[t, lat_ind, lon_ind]
			else:
				baseflow = 0
			f[i].write('%4d %02d %02d -999 -999 %f %f\n' %(year, month, day, runoff, baseflow))

# close files
for i in range(len(latlon_list)):
	f[i].close()







