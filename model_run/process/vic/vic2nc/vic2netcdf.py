#!/usr/bin/env python
"""
Python implementation of vic2nc

This module facilitates the conversion of ascii VIC output files into 3 or 4
dimenstional netcdf files.

References:
 - VIC: http://www.hydro.washington.edu/Lettenmaier/Models/VIC/index.shtml
 - netCDF: http://www.unidata.ucar.edu/software/netcdf/
 - Python netCDF4: https://code.google.com/p/netcdf4-python/
 - NetCDF Climate and Forecast (CF) Metadata Convention: http://cf-pcmdi.llnl.gov/
 - Pandas: http://pandas.pydata.org/
"""
# Imports
from os import path
from glob import glob
from re import findall
from collections import OrderedDict, deque
from bisect import bisect_left
from argparse import ArgumentParser
from getpass import getuser
from datetime import datetime, timedelta
from pandas import read_table, DataFrame, Series, date_range
from netCDF4 import Dataset, date2num, num2date, default_fillvals
from ConfigParser import SafeConfigParser
from scipy.spatial import cKDTree
import socket
import subprocess
import dateutil.relativedelta as relativedelta
import os
import sys
import numpy as np
import time as tm

SECSPERDAY = 86400.0

REFERENCE_STRING = '0001-1-1 0:0:0'
TIMEUNITS = 'days since {0}'.format(REFERENCE_STRING)  # (MUST BE DAYS)!
TIMESTAMPFORM = '%Y-%m-%d-%H'

# Precision
NC_DOUBLE = 'f8'
NC_FLOAT = 'f4'
NC_INT = 'i4'

# Default configuration
default_config = {'OPTIONS': {'out_file_format': 'NETCDF3_64BIT',
                              'precision': 'single',
                              'calendar': 'standard',
                              'time_segment': 'month',
                              'snow_bands': False,
                              'veg_tiles': False,
                              'soil_layers': False},
                  'DOMAIN': {'longitude_var': 'longitude',
                             'latitude_var': 'latitude',
                             'y_x_dims': ['y', 'x']}}


class Point(object):
    '''Creates a point class for intellegently
    storing coordinate information'''

    def __init__(self, lat='', lon='', x='', y='', filename=''):
        '''Defines x and y variables'''
        self.lat = lat
        self.lon = lon
        self.x = x
        self.y = y
        self.filename = filename

    def _open_binary(self):
        print('opening binary file: {0}'.format(self.filename))
        self.f = open(self.filename, 'rb')

    def _open_ascii(self):
        print('opening ascii file: {0}'.format(self.filename))
        # return an iterator
        self._reader = read_table(self.filename,
                                  sep=self.delimeter,
                                  header=None,
                                  iterator=True,
                                  usecols=self.usecols,
                                  names=self.names)

    def _open_netcdf(self):
        print('opening ascii file: {0}'.format(self.filename))
        self.f = Dataset(self.filename, 'r')

    def _read_ascii(self, count=None):
        self.df = self._reader.get_chunk(count)

        return

    def _read_binary(self, count=-1):

        d = np.fromfile(self.f, dtype=self.dt, count=count)

        data = {}
        for i, name in enumerate(self.names):
            data[name] = np.array(d[name], dtype=self.dtypes[i],
                                  copy=True) / float(self.bin_mults[i])

        self.df = DataFrame(data)
        return

    def _read_netcdf(self):

        data = {}
        for key in self.names:
            print key
            if key[0:-1] in ['SoilMoist']:
                print key
                layer = key[-1]
                key = key[0:-1]
                print key
                print layer
                data[key+str(layer)] = np.squeeze(self.f.variables[key][:][:,layer])
            else:
                data[key] = np.squeeze(self.f.variables[key][:])
#             data[key] = np.squeeze(self.f.variables[key][:])
        self.df = DataFrame(data)
       
        return

    def close(self):
        print('closing file: {0}'.format(self.filename))
        try:
            self.f.close()
        except:
            pass

    def __str__(self):
        return "Point({0},{1},{2},{3})".format(self.lat, self.lon,
                                               self.y, self.x)

    def __repr__(self):
        return "Point(lat={0}, lon={1}, \
                      y={2}, x={3}, \
                      filename={4})".format(self.lat,
                                            self.lon,
                                            self.y,
                                            self.x,
                                            self.filename)

# -------------------------------------------------------------------- #


class Plist(deque):
    '''List subclass that has a few helper methods for adding and
    obtaining coordinates'''

    def get_lons(self):
        return np.array([p.lon for p in self])

    def get_lats(self):
        return np.array([p.lat for p in self])

    def add_xs(self, xinds):
        for i in xrange(len(self)):
            self[i].x = xinds[i]
        return

    def add_ys(self, yinds):
        for i in xrange(len(self)):
            self[i].y = yinds[i]
        return

    def get_ys(self):
        return np.array([p.y for p in self])

    def get_xs(self):
        return np.array([p.x for p in self])

    def get_data(self, name, data_slice):
        return np.array([p.df[name].values[data_slice] for p in self])

    def set_fileformat(self, fileformat):
        """sets and assigns fileformat specific attributes and methods"""

        if fileformat == 'ascii':
            delimeter = r'\t'  # VIC ascii files are tab seperated
        else:
            delimeter = r','  # true csv

        for p in self:
            p.fileformat = fileformat
            if fileformat in ['ascii', 'csv']:
                p.open = p._open_ascii
                p.delimeter = delimeter
                p.read = p._read_ascii
            elif fileformat == 'binary':
                p.open = p._open_binary
                p.read = p._read_binary
                p.dt = np.dtype(zip(p.names, p.bin_dtypes))
            elif fileformat == 'netcdf':
                p.open = p._open_netcdf
                p.read = p._read_netcdf
            else:
                raise ValueError('Unknown file format: {0}'.format(fileformat))
        return

    def set_names(self, names):
        for p in self:
            p.names = names
        return

    def set_usecols(self, usecols):
        for p in self:
            p.usecols = usecols
        return

    def set_dtypes(self, dtypes):
        for p in self:
            p.dtypes = dtypes
        return

    def set_bin_dtypes(self, bin_dtypes):
        for p in self:
            p.bin_dtypes = bin_dtypes
        return

    def set_bin_mults(self, bin_mults):
        for p in self:
            p.bin_mults = bin_mults
        return
# -------------------------------------------------------------------- #


class Segment(object):
    def __init__(self, num, i0, i1, nc_format, filename,
                 memory_mode='original'):
        '''Class used for holding segment information '''
        self.num = num
        self.i0 = i0
        self.i1 = i1
        self.filename = filename
        self.fields = {}
        self.memory_mode = memory_mode

        self.nc_write(nc_format)

        # Set slice
        if memory_mode == 'original':
            self.slice = slice(None)
        else:
            self.slice = slice(i0, i1)

    def nc_globals(self,
                   title='VIC netCDF file',
                   history='Created: {0} by {1}'.format(tm.ctime(tm.time()),
                                                        getuser()),
                   institution='University of Washington',
                   source=sys.argv[0],
                   references='Primary Historical Reference for VIC: Liang, \
                        X., D. P. Lettenmaier, E. F. Wood, and S. J. Burges, \
                        1994: A Simple hydrologically Based Model of Land \
                        Surface Water and Energy Fluxes for GSMs, J. Geophys. \
                        Res., 99(D7), 14,415-14,428.',
                   comment='Output from the Variable Infiltration Capacity \
                        (VIC) Macroscale Hydrologic Model',
                   Conventions='CF-1.6',
                   target_grid_file='unknown',
                   username=None,
                   hostname=None,
                   version=None,
                   **kwargs):

        self.f.title = title
        self.f.history = history
        self.f.institution = institution
        self.f.source = source
        self.f.references = references
        self.f.comment = comment
        self.f.Conventions = Conventions
        if hostname:
            self.f.hostname = hostname
        else:
            self.f.hostname = socket.gethostname()
        if username:
            self.f.username = username
        else:
            self.f.username = getuser()
        if version:
            self.f.version = version
        else:
            try:
                self.f.version = subprocess.check_output(["git",
                                                         "describe"]).rstrip()
            except:
                self.f.version = 'unknown'

        for attribute, value in kwargs.iteritems():
            if hasattr(self.f, attribute):
                print('WARNING: Attribute {0} already \
                      exists'.format(attribute))
                print('Renaming to g_{0} to ovoid \
                      overwriting.'.format(attribute))
                attribute = 'g_{0}'.format(attribute)
            setattr(self.f, attribute, value)
        return

    def __str__(self):
        return "Segment Object({0})".format(self.filename)

    def __repr__(self):
        return """
-------------------------- Segment {0} --------------------------
Filename: {1}
Start Index: {2}
End Index: {3}
Start Date: {4}
End Date: {5}
------------------------------------------------------------------
""".format(self.num, self.filename, self.i0, self.i1, self.startdate,
           self.enddate)

    def nc_time(self, t0, t1, times, calendar):
        """ define time dimension (and write data) """
        time = self.f.createDimension('time', len(times[self.i0:self.i1]))
        time = self.f.createVariable('time', 'f8', ('time', ))
        time[:] = times[self.i0:self.i1]
        time.units = TIMEUNITS
        time.calendar = calendar
        self.count = len(time)
        self.startdate = t0
        self.enddate = t1

    def nc_domain(self, domain):
        """ define the coordinate dimension (and write data) """
        # Setup dimensions
        dimensions = []
        for name, ncvar in domain.iteritems():
            # Setup dimensions
            for dim in ncvar.dimensions:
                if dim not in dimensions:
                    dimensions.append(dim)
                    d = self.f.createDimension(dim, getattr(ncvar, dim))
            # Create variable
            if "_FillValue" in ncvar.attributes.keys():
                fill_val = ncvar.attributes['_FillValue']
                del ncvar.attributes['_FillValue']
            else:
                fill_val = None
            self.fields[name] = self.f.createVariable(name, NC_DOUBLE,
                                                      ncvar.dimensions,
                                                      fill_value=fill_val)
            # Apply the data
            self.fields[name][:] = ncvar
            # Add the attributes
            for key, val in ncvar.attributes.iteritems():
                setattr(self.fields[name], key, val)

        return

    def nc_dimensions(self, snow_bands=False, veg_tiles=False,
                      soil_layers=False):
        """ Define 4th dimensions """
        if snow_bands:
            d = self.f.createDimension('snow_bands', snow_bands)
        if veg_tiles:
            d = self.f.createDimension('veg_tiles', veg_tiles)
        if soil_layers:
            d = self.f.createDimension('soil_layers', soil_layers)
        return

    def nc_fields(self, fields, y_x_dims, precision):
        """ define each field """
        coords = ('time',)+tuple(y_x_dims)

        if precision == 'single':
            prec_global = NC_FLOAT
        elif precision == 'double':
            prec_global = NC_DOUBLE
        else:
            raise ValueError('Unkown value for OPTIONS[precision] \
                             field: {0}'.format(precision))

        self.three_dim_vars = []
        self.four_dim_vars = []

        for name, field in fields.iteritems():
            write_out_var = True
            if 'write_out_var' in field:
                if not field['write_out_var']:
                    write_out_var = False

            if write_out_var:
                if 'dim4' in field.keys():
                    if len(field['column']) == len(self.f.dimensions[field['dim4']]):
                        # 4d var
                        coords = ('time',) + tuple([field['dim4']]) \
                            + tuple(y_x_dims)
                        self.four_dim_vars.append(name)
                    elif len(field['column']) != len(self.f.dimensions[field['dim4']]):
                        raise ValueError('Number of columns for variable {0} \
                                         does not match the length ({1}) of the \
                                         {2} dimension'.format(name,
                                                               len(self.f.dimensions[field['dim4']]),
                                                               field['dim4']))
                else:
                    # standard 3d var
                    coords = ('time',)+tuple(y_x_dims)
                    self.three_dim_vars.append(name)

                if 'type' in field.keys():
                    prec = field['type']
                else:
                    prec = prec_global
                fill_val = default_fillvals[prec]

                self.fields[name] = self.f.createVariable(name, prec, coords,
                                                          fill_value=fill_val,
                                                          zlib=False)

                if 'units' in field.keys():
                    self.fields[name].long_name = name
                    self.fields[name].coordinates = 'lon lat'
                    for key, val in field.iteritems():
                        setattr(self.fields[name], key, val)
                else:
                    raise ValueError('Field {0} missing units \
                                     attribute'.format(name))
        return

    def allocate(self):
        self.data = {}
        for name, field in self.fields.iteritems():
            if hasattr(field, '_FillValue'):
                self.data[name] = np.zeros_like(field) + field._FillValue
            else:
                self.data[name] = np.zeros_like(field)

    def nc_add_data_to_array(self, point):
        for name in self.three_dim_vars:
            self.data[name][:, point.y, point.x] = point.df[name].values[self.slice]
        for name in self.four_dim_vars:
            varshape = self.f.variables[name].shape[1]
            for i in xrange(varshape):
                subname = name + str(i)
                self.data[name][:, i, point.y, point.x] = point.df[subname].values[self.slice]

    def nc_add_data_standard(self, points):
        ys = points.get_ys()
        xs = points.get_xs()
        for point in points:
            for name in self.three_dim_vars:
                data = points.get_data(name, self.slice)
                self.f.variables[name][:, ys, xs] = data
            for name in self.four_dim_vars:
                varshape = self.f.variables[name].shape[1]
                for i in xrange(varshape):
                    subname = name + str(i)
                    self.f.variables[name][:, i, ys, xs] = point.df[subname].values[self.slice]

    def nc_write_data_from_array(self):
        """ write completed data arrays to disk """
        for name in self.three_dim_vars:
            self.f.variables[name][:, :, :] = self.data[name]
        for name in self.four_dim_vars:
                self.f.variables[name][:, :, :, :] = self.data[name]

    def nc_write(self, nc_format):
        self.f = Dataset(self.filename, mode="w", clobber=True,
                         format=nc_format)
        self.f.set_fill_on()

    def nc_close(self):
        self.f.close()
        print('Closed: {0}'.format(self.filename))
# -------------------------------------------------------------------- #


# -------------------------------------------------------------------- #
class NcVar(np.ndarray):
    """ Subclass of numpy array to cary netcdf attributes"""
    def __new__(cls, f, varname):
        obj = np.asarray(f.variables[varname][:]).view(cls)
        # add the new attribute to the created instance
        obj.dimensions = f.variables[varname].dimensions
        obj.attributes = f.variables[varname].__dict__
        for dim in obj.dimensions:
            setattr(obj, dim, len(f.dimensions[dim]))
        # Finally, we must return the newly created object:
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
# -------------------------------------------------------------------- #


class FakeNcVar(np.ndarray):
    """ Subclass of numpy array to carry netcdf attributes"""
    def __new__(cls, data, dimensions, attributes):
        obj = np.asarray(data).view(cls)
        # add the new attribute to the created instance
        obj.dimensions = dimensions
        obj.attributes = attributes
        shape = data.shape
        for i, dim in enumerate(obj.dimensions):
            setattr(obj, dim, shape[i])
        # Finally, we must return the newly created object:
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
# -------------------------------------------------------------------- #


def main():
    """Top level driver"""

    # ---------------------------------------------------------------- #
    # Read command Line
    config_file, create_batch, batch_dir = process_command_line()
    # ---------------------------------------------------------------- #

    if create_batch:
        # ------------------------------------------------------------ #
        # Create batch files and exit
        batch(config_file, create_batch, batch_dir)
        # ------------------------------------------------------------ #
    else:
        # ------------------------------------------------------------ #
        # Read Configuration files
        config_dict = read_config(config_file)
        options = config_dict.pop('OPTIONS')
        global_atts = config_dict.pop('GLOBAL_ATTRIBUTES')
        if not options['regular_grid']:
            domain_dict = config_dict.pop('DOMAIN')
        else:
            domain_dict = None

        # set aside fields dict (sort by column)
        #fields = OrderedDict(sorted(config_dict.iteritems(),
        #                     key=lambda x: x[1]['column']))
        
        fields = config_dict

        vic2nc(options, global_atts, domain_dict, fields)
        # ------------------------------------------------------------ #
    return
# -------------------------------------------------------------------- #


def vic2nc(options, global_atts, domain_dict, fields):
    """ Convert ascii VIC files to netCDF format"""

    # determine run mode
    if (options['memory_mode'] == 'standard') \
            and (options['chunksize'] in ['all', 'All', 'ALL', 0]):
        memory_mode = 'big_memory'
    else:
        memory_mode = options['memory_mode']

    print("\n-------------------------------")
    print("Configuration File Options")
    print("-------------OPTIONS-------------")
    for pair in options.iteritems():
        print("{0}: {1}".format(*pair))
    print('Fields: {0}'.format(", ".join(fields.keys())))
    if domain_dict:
        print("-------------DOMAIN--------------")
        for pair in domain_dict.iteritems():
            print("{0}: {1}".format(*pair))
    print("--------GLOBAL_ATTRIBUTES--------")
    for pair in global_atts.iteritems():
        print("{0}: {1}".format(*pair))
    print("--------RUN MODE--------")
    print('Memory Mode: {0}'.format(memory_mode))
    if memory_mode == 'standard':
        print('Chunksize={0}'.format(options['chunksize']))
    print("---------------------------------\n")
    # ---------------------------------------------------------------- #

    # ---------------------------------------------------------------- #
    # Make output directory
    if not os.path.exists(options['out_directory']):
        os.makedirs(options['out_directory'])
    # ---------------------------------------------------------------- #

    # ---------------------------------------------------------------- #
    # Make pairs (i.e. find inds)
    files = glob(options['input_files'])
    points = get_file_coords(files)
    # ---------------------------------------------------------------- #

    # ---------------------------------------------------------------- #
    # Get target grid information
    if domain_dict:
        domain = read_domain(domain_dict)
        target_grid_file = path.split(domain_dict['filename'])[1]
        global_atts['target_grid_file'] = target_grid_file
    else:
        # must be a regular grid, build from file names
        domain = calc_grid(points.get_lats(), points.get_lons())
        target_grid_file = None
        domain_dict = {'y_x_dims': ['lat', 'lon']}
    # ---------------------------------------------------------------- #

    # ---------------------------------------------------------------- #
    # Get grid index locations
    points = get_grid_inds(domain, points)
    # ---------------------------------------------------------------- #

    # ---------------------------------------------------------------- #
    # Get timestamps
    if options['input_file_format'].lower() == 'ascii':
        vic_datelist = get_dates(files[0])
        vic_ordtime = date2num(vic_datelist, TIMEUNITS,
                               calendar=options['calendar'])

    elif options['input_file_format'].lower() in ['binary', 'netcdf']:
        vic_datelist, vic_ordtime = make_dates(options['bin_start_date'],
                                               options['bin_end_date'],
                                               options['bin_dt_sec'],
                                               calendar=options['calendar'])

    else:
        raise ValueError('Unknown input file format: {}. Valid options are \
                         ascii or binary'.format(options['input_file_format']))
    # ---------------------------------------------------------------- #

    # ---------------------------------------------------------------- #
    # Determine time segmentation
    if options['start_date']:
        start_date = datetime.strptime(options['start_date'], TIMESTAMPFORM)
        if start_date < vic_datelist[0]:
            print("WARNING: Start date in configuration file is before \
                  first date in file.")
            start_date = vic_datelist[0]
            print('WARNING: New start date is {0}'.format(start_date))
    else:
        start_date = vic_datelist[0]

    if options['end_date']:
        end_date = datetime.strptime(options['end_date'], TIMESTAMPFORM)
        if end_date > vic_datelist[-1]:
            print("WARNING: End date in configuration file is after \
                  last date in file.")
            end_date = vic_datelist[-1]
            print('WARNING: New end date is {0}'.format(end_date))
    else:
        end_date = vic_datelist[-1]


    # Ordinal Time
    start_ord = date2num(start_date, TIMEUNITS, calendar=options['calendar'])
    end_ord = date2num(end_date, TIMEUNITS, calendar=options['calendar'])

    print("netCDF Start Date: {0}".format(start_date))
    print("netCDF End Date: {0}".format(end_date))

    segment_dates = []
    if options['time_segment'] == 'day':
        # calendar insensitive
        num_segments = np.ceil(end_ord - start_ord)
        if start_date.hour == 0:
            segment_dates = num2date(np.arange(start_ord, end_ord+1, 1),
                                     TIMEUNITS, calendar=options['calendar'])
        else:
            # allow start at time other than 0
            temp = [start_ord].append(np.arange(np.ceil(start_ord),
                                      end_ord+1, 1))
            segment_dates = num2date(temp, TIMEUNITS,
                                     calendar=options['calendar'])
    elif options['time_segment'] == 'month':
        num_segments = (end_date.year - start_date.year)*12 \
            + end_date.month - start_date.month + 1
        month = start_date.month
        year = start_date.year
        for i in xrange(num_segments+1):
            segment_dates.append(datetime(year, month, 1))
            month += 1
            if month == 13:
                month = 1
                year += 1
    elif options['time_segment'] == 'year':
        num_segments = end_date.year - start_date.year + 1
        year = start_date.year
        for i in xrange(num_segments+1):
            segment_dates.append(datetime(year, 1, 1))
            year += 1
    elif options['time_segment'] == 'decade':
        num_segments = (end_date.year - start_date.year)/10 + 1
        year = start_date.year
        for i in xrange(num_segments+1):
            segment_dates.append(datetime(year, 1, 1))
            year += 10
    elif options['time_segment'] == 'all':
        num_segments = 1
        segment_dates = [start_date, end_date]
    else:
        raise ValueError('Unknown timesegment options \
                         {0}'.format(options['time_segment']))
    print("Number of files: {0}".format(len(segment_dates)-1))
    assert len(segment_dates) == num_segments+1

    # Make sure the first and last dates are start/end_date
    segment_dates[0] = start_date
    segment_dates[-1] = end_date + timedelta(minutes=1)
    # ---------------------------------------------------------------- #

    # ---------------------------------------------------------------- #
    # Setup Segments
    segments = deque()

    for num in xrange(num_segments):
        # Segment time bounds
        t0 = segment_dates[num]
        t1 = segment_dates[num+1]

        # Get segment inds
        i0 = bisect_left(vic_datelist, t0)
        i1 = bisect_left(vic_datelist, t1)

        # Make segment filename (with path)
        if options['time_segment'] == 'day':
            filename = "{0}.{1}.nc".format(options['out_file_prefix'],
                                           t0.strftime('%Y-%m-%d'))
        elif options['time_segment'] == 'month':
            filename = "{0}.{1}.nc".format(options['out_file_prefix'],
                                           t0.strftime('%Y-%m'))
        elif options['time_segment'] == 'year':
            filename = "{0}.{1}.nc".format(options['out_file_prefix'],
                                           t0.strftime('%Y'))
        elif options['time_segment'] == 'all':
            filename = "{0}.{1}-{2}.nc".format(options['out_file_prefix'],
                                               t0.strftime('%Y%m%d'),
                                               t1.strftime('%Y%m%d'))

        filename = path.join(options['out_directory'], filename)

        # Setup segment and initialize netcdf
        segment = Segment(num, i0, i1, options['out_file_format'],
                          filename, memory_mode=memory_mode)
        segment.nc_globals(**global_atts)
        segment.nc_time(t0, t1, vic_ordtime, options['calendar'])
        segment.nc_dimensions(snow_bands=options['snow_bands'],
                              veg_tiles=options['veg_tiles'],
                              soil_layers=options['soil_layers'])

        segment.nc_domain(domain)
        segment.nc_fields(fields,
                          domain_dict['y_x_dims'], options['precision'])

        print(repr(segment))
        segments.append(segment)
    # ---------------------------------------------------------------- #

    # ---------------------------------------------------------------- #
    # Get column numbers and names (will help speed up reading)
    names = []
    usecols = []
    dtypes = []
    bin_dtypes = []
    bin_mults = []

    if options['precision'] == 'double':
        prec = NC_DOUBLE
    else:
        prec = NC_FLOAT

    for name, field in fields.iteritems():

        if type(field['column']) == list:
            # multiple levels
            for i, col in enumerate(field['column']):
                names.append(name+str(i))
                usecols.append(col)
            if 'type' in field:
                if type(field['type']) == list:
                    dtypes.extend(field['type'])
                else:
                    dtypes.extend([field['type']] * len(field['column']))
            else:
                dtypes.append([prec] * len(field['column']))
            print names
            print usecols
            print name
            if options['input_file_format'].lower() == 'binary':
                if 'bin_dtype' in field:
                    if type(field['bin_dtype']) == list:
                        bin_dtypes.extend(field['bin_dtype'])
                    else:
                        bin_dtypes.extend([field['bin_dtype']] * len(field['column']))
                else:
                    raise ValueError('bin_dtype not in field: {}'.format(name))

                if 'bin_mult' in field:
                    if type(field['bin_mult']) == list:
                        bin_mults.extend(field['bin_mult'])
                    else:
                        bin_mults.extend([field['bin_mult']] * len(field['column']))
                else:
                    bin_mults.extend([1.0] * len(field['column']))
        else:
            # no levels
            names.append(name)
            usecols.append(field['column'])

            if 'type' in field:
                dtypes.append(field['type'])
            else:
                dtypes.append(prec)

            if options['input_file_format'].lower() == 'binary':
                if 'bin_dtype' in field:
                    bin_dtypes.append(field['bin_dtype'])
                else:
                    raise ValueError('bin_dtype not in field: {}'.format(name))

                if 'bin_mult' in field:
                    bin_mults.append(field['bin_mult'])
                else:
                    bin_mults.append(1.0)

    print('setting point attributes (fileformat, names, usecols, and dtypes)')
    points.set_names(names)
    points.set_usecols(usecols)
    points.set_dtypes(dtypes)
    # set binary attributes
    if options['input_file_format'].lower() == 'binary':
        points.set_bin_dtypes(bin_dtypes)
        points.set_bin_mults(bin_mults)
    points.set_fileformat(options['input_file_format'])
    print('done')
    # ---------------------------------------------------------------- #

    # ---------------------------------------------------------------- #
    if memory_mode == 'big_memory':
        # ------------------------------------------------------------ #
        # run in big memory mode
        for i, segment in enumerate(segments):
            segments[i].allocate()

        while points:
            point = points.popleft()
            point.open()
            point.read()
            point.close()

            for segment in segments:
                segment.nc_add_data_to_array(point)

        for segment in segments:
            segment.nc_write_data_from_array()
            segment.nc_close()
        # ------------------------------------------------------------ #

    elif memory_mode == 'standard':
        # ------------------------------------------------------------ #
        # Open VIC files and put data into netcdfs

        chunk = Plist()
        while points:
            point = points.popleft()
            point.open()
            point.read()
            point.close()
            chunk.append(point)
            if len(chunk) > int(options['chunksize']) or len(points) == 0:
                for segment in segments:
                    segment.nc_add_data_standard(chunk)
                chunk = Plist()
            del point
        # ------------------------------------------------------------ #

        # ------------------------------------------------------------ #
        # Close the netcdf files
        for segment in segments:
            segment.nc_close()
        # ------------------------------------------------------------ #
    elif memory_mode == 'original':
        # ------------------------------------------------------------ #
        # Run in original memory mode (a.k.a. vic2nc.c mode)
        # Open all files
        for point in points:
            point.open()

        while segments:
            segment = segments.popleft()
            segment.allocate()
            count = segment.count

            for point in points:
                point.read(count)
                segment.nc_add_data_to_array(point)

            segment.nc_write_data_from_array()
            segment.nc_close()

        for point in points:
            point.close()
        # ------------------------------------------------------------ #

    return
# -------------------------------------------------------------------- #


def read_config(config_file):
    """
    Return a dictionary with subdictionaries of all configFile options/values
    """
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

    for name, section in dict1.iteritems():
        if name in default_config.keys():
            for option, key in default_config[name].iteritems():
                if option not in section.keys():
                    dict1[name][option] = key

    return dict1


def config_type(value):
    """
    Parse the type of the configuration file option.
    First see the value is a bool, then try float, finally return a string.
    """
    val_list = [x.strip() for x in value.split(',')]
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
            return map(int, val_list)
        except:
            pass
        try:
            return map(float, val_list)
        except:
            return val_list
# -------------------------------------------------------------------- #


def get_file_coords(files):
    """
    Get list of Point objects
    """

    points = Plist()

    for i, filename in enumerate(files):
        # fname = path.split(f)[1][-16:] # just look at last 16 characters
        f = filename[-30:]  # just look at last 16 characters
        lat, lon = map(float, findall(r"[-+]?\d*\.\d+|\d+", f))[-2:]
        points.append(Point(lat=lat, lon=lon, filename=filename))

    return points
# -------------------------------------------------------------------- #


def get_dates(file):
    """
    Read the first file in the input directory and create a ordinal based
    timeseries.
    Also find the indicies to split the time series into months and years
    """
    hours = (0, 1, 2, 3)
    days = (0, 1, 2)
    try:
        data = np.loadtxt(file, usecols=hours, dtype=int)
        datelist = [datetime(*d) for d in data]
    except (ValueError, TypeError):
        data = np.loadtxt(file, usecols=days, dtype=int)
        datelist = [datetime(*d) for d in data]

    # check to make sure we haven't used used daily by mistake
    # (creating a bunch of duplicate times)
    newlist = []
    for i in datelist:
        if i not in newlist:
            newlist.append(i)
        else:
            raise ValueError('Found duplicate datetimes in datelist')

    print('VIC startdate: {0}'.format(datelist[0]))
    print('VIC enddate: {0}'.format(datelist[-1]))

    return datelist
# -------------------------------------------------------------------- #


def make_dates(start, end, dt, calendar='standard'):
    """
    Return a list of datetime object from inputs of

    start - python date string (i.e. 1989-01-01-00)
    end - python date string (i.e. 1989-01-01-23)
    dt - int or float timestep in seconds
    """

    start = map(int, start.split('-'))
    end = map(int, end.split('-'))

    start_ord = date2num(datetime(*start), TIMEUNITS, calendar=calendar)
    end_ord = date2num(datetime(*end), TIMEUNITS, calendar=calendar)
    step = float(dt)/SECSPERDAY

    ordlist = np.arange(start_ord, end_ord+step, step)

    datelist = num2date(ordlist, TIMEUNITS, calendar=calendar)

    return datelist, ordlist
# -------------------------------------------------------------------- #


def read_domain(domain_dict):

    print('reading domain file: {0}'.format(domain_dict['filename']))
    f = Dataset(domain_dict['filename'])

    domain = {'lon': NcVar(f, domain_dict['longitude_var']),
              'lat': NcVar(f, domain_dict['latitude_var'])}

    if domain_dict['copy_vars']:
        for varname in domain_dict['copy_vars']:
            domain[varname] = NcVar(f, varname)

    f.close()

    return domain
# -------------------------------------------------------------------- #


def get_grid_inds(domain, points):
    """
    Find location of lat/lon points in 2d target grid.
    Uses cKdtree nearest neighbor mapping.
    """
    lons = points.get_lons()
    lats = points.get_lats()

    if (lons.min() < 0) and (domain['lon'].min() >= 0):
        posinds = np.nonzero(lons < 0)
        lons[posinds] += 360
        print('adjusted VIC lon minimum (+360 for negative lons)')

    # Make sure the longitude / latitude vars are 2d
    if domain['lat'].ndim == 1 or domain['lon'].ndim == 1:
        dlons, dlats = np.meshgrid(domain['lon'], domain['lat'])

    combined = np.dstack(([dlats.ravel(), dlons.ravel()]))[0]
    point_list = list(np.vstack((lats, lons)).transpose())

    mytree = cKDTree(combined)
    dist, indexes = mytree.query(point_list, k=1)

    yinds, xinds = np.unravel_index(indexes, dlons.shape)

    points.add_xs(xinds)
    points.add_ys(yinds)

    return points
# -------------------------------------------------------------------- #


def batch(config_file, create_batch, batch_dir):
    """Create a set of batch configuration files"""

    # Read Configuration files
    config_dict = read_config(config_file)
    options = config_dict.pop('OPTIONS')
    global_atts = config_dict.pop('GLOBAL_ATTRIBUTES')
    domain_dict = config_dict.pop('DOMAIN', None)
    fields = config_dict

    config = SafeConfigParser()
    config.optionxform = str

    # Figure out what to call the new files
    nameprefix = os.path.splitext(os.path.split(config_file)[1])[0]

    if create_batch == 'variables':
        # batch by variables
        # options section
        config.add_section('OPTIONS')
        for option, value in options.iteritems():
            if type(value) == list:
                try:
                    value = ", ".join(value)
                except TypeError:
                    value = ", ".join(repr(e) for e in value)
            elif type(value) != str:
                value = str(value)
            config.set('OPTIONS', option, str(value))

        # global_atts section
        config.add_section('GLOBAL_ATTRIBUTES')
        for option, value in global_atts.iteritems():
            if type(value) == list:
                try:
                    value = ", ".join(value)
                except TypeError:
                    value = ", ".join(repr(e) for e in value)
            elif type(value) != str:
                value = str(value)
            config.set('GLOBAL_ATTRIBUTES', option, str(value))

        # domain dict section
        if domain_dict:
            config.add_section('DOMAIN')
            for option, value in domain_dict.iteritems():
                if type(value) == list:
                    try:
                        value = ", ".join(value)
                    except TypeError:
                        value = ", ".join(repr(e) for e in value)
                elif type(value) != str:
                    value = str(value)

                config.set('DOMAIN', option, value.strip("'"))

        for var, field in fields.iteritems():
            suffix = "_{0}.cfg".format(var)
            new_cfg_file = os.path.join(batch_dir, nameprefix+suffix)

            # this var
            config.add_section(var)
            for option, value in field.iteritems():
                if type(value) == list:
                    try:
                        value = ", ".join(value)
                    except TypeError:
                        value = ", ".join(repr(e) for e in value)
                elif type(value) != str:
                    value = str(value)
                config.set(var, option, str(value))

            # write that config
            with open(new_cfg_file, 'wb') as cf:
                config.write(cf)

            # clear the var section
            config.remove_section(var)

    else:
        # start with existing config
        config.read(config_file)

        # by time
        start_date = datetime.strptime(options['start_date'], TIMESTAMPFORM)
        end_date = datetime.strptime(options['end_date'], TIMESTAMPFORM)

        t0 = start_date

        if create_batch == 'years':
            td = relativedelta.relativedelta(years=1)
            t1 = datetime(t0.year, 12, 31, end_date.hour)
        elif create_batch == 'months':
            td = relativedelta.relativedelta(months=1)
        elif create_batch == 'days':
            # days option is only valid for gregorian calendar
            td = relativedelta.relativedelta(days=1)

        hour = relativedelta.relativedelta(hours=-1)

        i = 0
        while t0 < end_date:
            i += 1
            t1 = t0 + td
            if t1 > end_date:
                t1 = end_date
            else:
                t1 += hour

            # suffix = "_{0}-{1}.cfg".format(t0.strftime("%Y%m%d%H"),
            #                                t1.strftime("%Y%m%d%H"))
            suffix = '_{0}'.format(i)
            new_cfg_file = os.path.join(batch_dir, nameprefix+suffix)

            # Write config replacing start and end dates
            config.set('OPTIONS', 'start_date', t0.strftime(TIMESTAMPFORM))
            config.set('OPTIONS', 'end_date', t1.strftime(TIMESTAMPFORM))

            with open(new_cfg_file, 'wb') as cf:
                config.write(cf)

            t0 += td
    return
# -------------------------------------------------------------------- #


def latlon2yx(plats, plons, glats, glons):
    """find y x coordinates """

    if glons.ndim == 1 or glats.ndim == 1:
        glons, glats = np.meshgrid(glons, glats)

    combined = np.dstack(([glats.ravel(), glons.ravel()]))[0]
    points = list(np.vstack((np.array(plats), np.array(plons))).transpose())

    mytree = cKDTree(combined)
    dist, indexes = mytree.query(points, k=1)
    y, x = np.unravel_index(np.array(indexes), glons.shape)
    return y, x
# -------------------------------------------------------------------- #


def calc_grid(lats, lons, decimals=4):
    """ determine shape of regular grid from lons and lats"""

    print('Calculating grid size now...')

    target_grid = {}

    # get unique lats and lons
    lon = np.sort(np.unique(lons.round(decimals=decimals)))
    print('found {0} unique lons'.format(len(lon)))

    lat = np.sort(np.unique(lats.round(decimals=decimals)))
    print('found {0} unique lats'.format(len(lat)))

    y, x = latlon2yx(lats, lons, lat, lon)

    mask = np.zeros((len(lat), len(lon)), dtype=int)

    mask[y, x] = 1

    # Create fake NcVar Types
    target_grid['lon'] = FakeNcVar(lon, ('lon', ),
                                   {'long_name': 'longitude coordinate',
                                    'units': 'degrees_east'})
    target_grid['lat'] = FakeNcVar(lat, ('lat', ),
                                   {'long_name': 'latitude coordinate',
                                    'units': 'degrees_north'})
    target_grid['mask'] = FakeNcVar(mask, ('lat', 'lon', ),
                                    {'long_name': 'domain mask',
                                     'comment': '0 indicates grid cell is not \
                                     active'})

    print('Created a target grid based on the lats and lons in the '
          'input file names')
    print('Grid Size: {}'.format(mask.shape))

    return target_grid
# -------------------------------------------------------------------- #


def process_command_line():
    """
    Get the path to the config_file
    """
    # Parse arguments
    parser = ArgumentParser(description='convert VIC ascii output to \
                            netCDF format')
    parser.add_argument("config_file", type=str,
                        help="Input configuration file")
    parser.add_argument("--create_batch", type=str,
                        choices=['days', 'months', 'years', 'variables'],
                        default=False, help="Create a batch of config files")
    parser.add_argument("--batch_dir", type=str, default="./",
                        help="Location to put batch config files")
    args = parser.parse_args()

    if not os.path.isfile(args.config_file):
        raise IOError('Configuration File: {0} is not a valid \
                      file'.format(args.config_file))

    if not os.path.isdir(args.batch_dir) and args.create_batch:
        raise IOError('Configuration File: {0} is not a valid \
                      file'.format(args.config_file))

    return args.config_file, args.create_batch, args.batch_dir
# -------------------------------------------------------------------- #

# -------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
# -------------------------------------------------------------------- #
