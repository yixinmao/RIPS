#!/usr/local/anaconda/bin/python

# This script estimates Leopold parameters for each individual site based on USGS flow velocity/width data
# Output file format:
#   each row: D_a D_b v_a v_b w_a w_b (for ft and sec)
#   where Depth=aQ^b; velocity=aQ^b; width=aQ^b

import sys
import numpy as np
import my_functions

#===========================================================#
# Load in config parameters
#===========================================================#
cfg = my_functions.read_config(sys.argv[1])

# [INPUT]
# Path for original USGS field measurement data for all sites
usgs_fld_path = cfg['INPUT']['usgs_fld_path']

# [OPTIONS]
# Mode for coefficients calculation.
# Options:
#   INDIV: calculate coefficients and write results for individual sites
#   ALL: combine data of all sites, and calculate one set of coefficients for the given sites
coef_calc_mode = cfg['OPTIONS']['coef_calc_mode']

# [OUTPUT]
# Output parameter path
output_path = cfg['OUTPUT']['output_path']

#===========================================================#
# Read field measurement data for all sites
#===========================================================#
print 'Loading data...'
# Load data (all data in ft and sec units)
df_fld = my_functions.read_USGS_fld_meas(usgs_fld_path, time_column=4, 
                                data_columns=[24,25,26,27], 
                                data_names=['discharge','width','area','velocity'],
                                code_column=2, code_name='USGS_code')
# If coef_calc_mode==INDIV, separate data for each site to separate smaller dataframes
# (into dictionary with site code as keys)
if coef_calc_mode=='ALL':
    pass
elif coef_calc_mode=='INDIV':
    dict_df_fld = my_functions.separate_df_basedOnColumn(df_fld, 'USGS_code')
else:
    print 'Error: input coef_calc_mode {} is not supported!'.format(coef_calc_mode)
    exit()

#===========================================================#
# Process flow velocity and calculate depth
#===========================================================#
print 'Processing data...'
if coef_calc_mode=='ALL':
    df_fld_processed = my_functions.process_flow_velocity_depth(df_fld, 'discharge', 
                                                'width', 'area', 'velocity',
                                                'depth')
elif coef_calc_mode=='INDIV':
    dict_df_fld_processed = {}
    for key in dict_df_fld.keys():
        dict_df_fld_processed[key] = my_functions.process_flow_velocity_depth(dict_df_fld[key], 'discharge', 'width', 'area', 'velocity', 'depth')

#===========================================================#
# Fit Leopold coefficients
#===========================================================#
print 'Fitting Leopold parameters...'
if coef_calc_mode=='ALL':
    leop_fit_vel_coef = my_functions.fit_Leopold_velocity(df_fld_processed, 'discharge', 'velocity') # Fitted Leopold ceofficients for velocity (a, b)
    leop_fit_depth_coef = my_functions.fit_Leopold_depth(df_fld_processed, 'discharge', 'depth') # Fitted Leopold ceofficients for depth (a, b)
    leop_fit_width_coef = my_functions.fit_Leopold_width(df_fld_processed, 'discharge', 'width') # Fitted Leopold ceofficients for width (a, b)
elif coef_calc_mode=='INDIV':
    dict_leop_fit_vel_coef = {}
    dict_leop_fit_depth_coef = {}
    dict_leop_fit_width_coef = {}
    for key in dict_df_fld.keys():
        dict_leop_fit_vel_coef[key] = my_functions.fit_Leopold_velocity(dict_df_fld_processed[key], 'discharge', 'velocity') # Fitted Leopold ceofficients for velocity (a, b)
        dict_leop_fit_depth_coef[key] = my_functions.fit_Leopold_depth(df_fld_processed[key], 'discharge', 'depth') # Fitted Leopold ceofficients for depth (a, b)
        dict_leop_fit_width_coef[key] = my_functions.fit_Leopold_width(df_fld_processed[key], 'discharge', 'width') # Fitted Leopold ceofficients for width (a, b)

#===========================================================#
# Write results to file
#===========================================================#
print 'Writing results...'
f = open(output_path, 'w')
f.write('type D_a D_b v_a v_b w_a w_b (for ft and sec)\n')
if coef_calc_mode=='ALL':
    f.write('ALL {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f}\n'\
            .format(leop_fit_depth_coef[0], leop_fit_depth_coef[1], \
                    leop_fit_vel_coef[0], leop_fit_vel_coef[1], \
                    leop_fit_width_coef[0], leop_fit_width_coef[1]))
elif coef_calc_mode=='INDIV':
    for key in dict_df_fld.keys():
        f.write('{} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f}\n'\
            .format(key, dict_leop_fit_depth_coef[key][0], dict_leop_fit_depth_coef[key][1], \
                    dict_leop_fit_vel_coef[key][0], dict_leop_fit_vel_coef[key][1], \
                    dict_leop_fit_width_coef[key][0], dict_leop_fit_width_coef[key][1]))
f.close()







