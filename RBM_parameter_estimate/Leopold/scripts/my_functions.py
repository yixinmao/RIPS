#!/usr/local/anaconda/bin/python

# -------------------------------------------------------------------- #
def read_config(config_file, default_config=None):
    """
    This function is from tonic (author: Joe Hamman)
    Return a dictionary with subdictionaries of all configFile options/values
    """

    from netCDF4 import Dataset
    try:
        from cyordereddict import OrderedDict
    except:
        from collections import OrderedDict
    try:
        from configparser import SafeConfigParser
    except:
        from ConfigParser import SafeConfigParser
    import configobj

    config = SafeConfigParser()
    config.optionxform = str
    config.read(config_file)
    sections = config.sections()
    dict1 = OrderedDict()
    for section in sections:
        options = config.options(section)
        dict2 = OrderedDict()
        for option in options:
            dict2[option] = config_type(config.get(section, option))
        dict1[section] = dict2

    if default_config is not None:
        for name, section in dict1.items():
            if name in default_config.keys():
                for option, key in default_config[name].items():
                    if option not in section.keys():
                        dict1[name][option] = key

    return dict1
# -------------------------------------------------------------------- #

# -------------------------------------------------------------------- #
def config_type(value):
    """
    This function is originally from tonic (author: Joe Hamman); modified so that '\' is considered as an escapor. For example, '\,' can be used for strings with ','. e.g., Historical\, 1980s  will be recognized as one complete string
    Parse the type of the configuration file option.
    First see the value is a bool, then try float, finally return a string.
    """

    import cStringIO
    import csv

    val_list = [x.strip() for x in csv.reader(cStringIO.StringIO(value), delimiter=',', escapechar='\\').next()]
    if len(val_list) == 1:
        value = val_list[0]
        if value in ['true', 'True', 'TRUE', 'T']:
            return True
        elif value in ['false', 'False', 'FALSE', 'F']:
            return False
        elif value in ['none', 'None', 'NONE', '']:
            return None
        else:
            try:
                return int(value)
            except:
                pass
            try:
                return float(value)
            except:
                return value
    else:
        try:
            return list(map(int, val_list))
        except:
            pass
        try:
            return list(map(float, val_list))
        except:
            return val_list
# -------------------------------------------------------------------- #

#==============================================================
#==============================================================

def read_USGS_fld_meas(file, time_column, data_columns, data_names, code_column, code_name):
    '''This function reads USGS field measurement data from the directly downloaded format

    Input:
        file: directly downloaded streamflow file path [str]
        time_column: date column number, starting from 1
        data_columns: a list of data column numbers, starting from 1. If only want one column of data, e.g., [5]
        data_names: a list of data column names. E.g., ['mean_flow']; must the same length as columns
        code_column, code_name: column number and name for USGS code 

    Return:
        a pd.DataFrame object with time as index and data columns (NaN for missing data points)

    '''

    import numpy as np
    import datetime as dt
    import pandas as pd

    ndata = len(data_columns)
    if ndata != len(data_names):  # check input validity
        print "Error: input arguments 'data_columns' and 'data_names' must have same length!"
        exit()

    f = open(file, 'r')
    time_list = []
    data_list = []
    while 1:
        line = f.readline().rstrip("\n")  # read in one line
        if line=="":
            break
        line_split = line.split('\t')
        if line_split[0]=='USGS':  # if data line
            # Read in time column
            time_string = line_split[time_column-1]
            try:
                time = dt.datetime.strptime(time_string, "%Y-%m-%d")  # convert time to dt object
            except ValueError:
                try:
                    time = dt.datetime.strptime(time_string, "%m/%d/%Y")
                except ValueError:
                    try:
                        time = dt.datetime.strptime(time_string, "%m/%d/%Y %H:%M")
                    except ValueError:
                        try:
                            time = dt.datetime.strptime(time_string, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            print 'Error: Time format not supported!'
                            raise
            time_list.append(time)
            
            # Read in USGS code column
            data_list.append([])
            data_list[-1].append(line_split[code_column-1]) 
           
            # Read in data values 
            for i in range(ndata):  # for each desired data variable
                col = data_columns[i]
                if line_split[col-1] == '':  # if data is missing
                    value = np.nan
                else:  # if data is not missing
                    value = float(line_split[col-1])
                data_list[-1].append(value)

    df = pd.DataFrame(data_list, index=time_list, columns=[code_name]+data_names)
    return df

#==============================================================
#==============================================================

def separate_df_basedOnColumn(df, column_name):
    ''' This function separates a pd.DataFrame into several smaller dataframes according to one column

    Input:
        df: original pd.DataFrame
        column_name: name of the column as separating base [str]
    Return:
        
    '''

    import pandas as pd

    unique_names = df[column_name].unique()
    dict_df = {elem: pd.DataFrame for elem in unique_names}
    for key in dict_df.keys():
        dict_df[key] = df[:][df[column_name]==key]

    return dict_df

#==============================================================
#==============================================================

def process_flow_velocity_depth(df, discharge_name, width_name, area_name, velocity_name, depth_name):
    ''' This function fills in velocity and flow depth (if missing and if other data can be used to infer it), and calculate flow depth if other data available

    '''

    import numpy as np

    # Pre-process data
    for row_index, row in df.iterrows():  # iterate through each row
        if row[discharge_name]<=0 or row[width_name]<=0 or row[area_name]<=0 \
                or row[velocity_name]<=0:
            df.loc[row_index, discharge_name] = np.nan
            df.loc[row_index, width_name] = np.nan
            df.loc[row_index, area_name] = np.nan
            df.loc[row_index, velocity_name] = np.nan


    # Fill in missing velocity if possible
    for row_index, row in df.iterrows():  # iterate through each row
        if np.isnan(row[velocity_name]):  # if velocity is missing
            if np.isnan(row[discharge_name])==False and \
                    np.isnan(row[area_name])==False:  # if there is discharge and area values
                df.loc[row_index, velocity_name] = row[discharge_name] / row[area_name]
                
    # Calculate depth
    df[depth_name] = df[area_name] / df[width_name]  # D = A/w
        # D = Q/(vw)
    for row_index, row in df.iterrows():  # iterate through each row
        if np.isnan(row[depth_name]):  # if depth is missing
            if np.isnan(row[discharge_name])==False and \
                    np.isnan(row[velocity_name])==False and \
                    np.isnan(row[width_name])==False:  # if there is discharge, velocity and width
                try:
                    df.loc[row_index, depth_name] = row[discharge_name] / row[velocity_name] / row[width_name]
                except ZeroDivisionError:
                    pass    
    return df
        
#==============================================================
#==============================================================

def fit_Leopold_velocity(df, discharge_name, velocity_name):
    ''' This function fits Leopold coefficients for velocity
        vel = aQ^b

    Input:
        df: pd.DataFrame containing velocity and discharge data

    Return:
        An array of fitted parameters (here, an array with two elements - a and b)
    '''

    import numpy as np
    from scipy.optimize import curve_fit
    import matplotlib.pyplot as plt

    # Define function vel = aQ^b
    def func(x, a, b):
        return a*np.power(x, b)

    # Delete missing values
    df_temp = df[np.isnan(df[velocity_name])==False]
    df_perfect = df_temp[np.isnan(df_temp[discharge_name])==False]

    # Fit parameters
    popt, pcov = curve_fit(func, df_perfect[discharge_name].values, 
                            df_perfect[velocity_name].values, p0=(1.0, 0.5))

    return popt

#==============================================================
#==============================================================

def fit_Leopold_depth(df, discharge_name, depth_name):
    ''' This function fits Leopold coefficients for depth
        depth = aQ^b

    Input:
        df: pd.DataFrame containing depth and discharge data

    Return:
        An array of fitted parameters (here, an array with two elements - a and b)
    '''

    import numpy as np
    from scipy.optimize import curve_fit
    import matplotlib.pyplot as plt

    # Define function depth = aQ^b
    def func(x, a, b):
        return a*np.power(x, b)

    # Delete missing values
    df_temp = df[np.isnan(df[depth_name])==False]
    df_perfect = df_temp[np.isnan(df_temp[discharge_name])==False]

    popt, pcov = curve_fit(func, df_perfect[discharge_name].values, 
                            df_perfect[depth_name].values, p0=(1.0, 0.5))

    return popt

#==============================================================
#==============================================================

def fit_Leopold_width(df, discharge_name, width_name):
    ''' This function fits Leopold coefficients for width
        width = aQ^b

    Input:
        df: pd.DataFrame containing width and discharge data

    Return:
        An array of fitted parameters (here, an array with two elements - a and b)
    '''

    import numpy as np
    from scipy.optimize import curve_fit
    import matplotlib.pyplot as plt

    # Define function width = aQ^b
    def func(x, a, b):
        return a*np.power(x, b)

    # Delete missing values
    df_temp = df[np.isnan(df[width_name])==False]
    df_perfect = df_temp[np.isnan(df_temp[discharge_name])==False]

    popt, pcov = curve_fit(func, df_perfect[discharge_name].values, 
                            df_perfect[width_name].values, p0=(1.0, 0.5))

    return popt

