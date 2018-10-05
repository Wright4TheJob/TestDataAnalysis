#!/bin/env/python
# David Wright
# Written for Python 3.7

"""
Gets the peak load from a standard tensile test file for a list of filenames
"""

import csv
import os
import sys

def generate_filename_list(basename,suffix,n,digits,start_index=1):
    filenames = [0]*n
    for i in range(start_index,n+start_index):
        number = str(i).zfill(digits)

        filename = basename + number + suffix
        filenames[i-1] = filename
    return filenames

def read_files(folder,filenames,delimiter=',',kind = 'stress-strain'):
    exists = False
    is_folder = False
    if os.path.exists(folder):
        exists = True
    else:
        print('Filepath specified does not exist: ' + folder)
        return
    if os.path.isdir(folder):
        is_folder = True
    if exists and is_folder:
        os.chdir(folder)

    data_sets = []
    for filename in filenames:
        data = readtensiledata(filename,delimiter=delimiter,kind=kind)
        data_sets.append(data)

    for i in range(0,len(data_sets)):
        for j in range(0,len(data_sets[i])):
            for k in range(0,len(data_sets[i][j])):
                try:
                    data_sets[i][j][k] = float(data_sets[i][j][k])
                except Exception as ex:
                    logging.exception('Caught an error')

    return data_sets

def readtensiledata(filename,delimiter = ',',kind = 'stress-strain'):

    load_column = 0
    disp_column = 0
    if kind == 'load-displacement':
        load_column = 0
        disp_column = 1
    elif kind == 'stress-strain':
        load_column = 2
        disp_column = 5
    else:
        print('Unknown kind of test selected in get_max_loads: ' + kind)
        return []

    ########## Data Importing ############################################
    Load= []
    Disp = []
    Stress = []
    Time = []
    Temp = []
    Axial = []
    Transverse = []
    RawLoad = []
    Empty = []
    columns = [Load, Disp,Stress,Time,Temp,Axial,Transverse,RawLoad,Empty]

    with open(filename, 'r') as fin:
        for i in range(0,4):
            next(fin)  # skip headings
        if delimiter == ',':
            reader = csv.reader(fin)
        else:
            reader = csv.reader(fin, delimiter=delimiter)

        for line in reader:
            if len(line) != len(columns):
                print('Error: Line has %i elements and %i columns specified'%(len(line),len(columns)))
                return
            for element, targetlist in zip(line,columns):
                targetlist.append(element)
    data_set = [columns[load_column],columns[disp_column]]
    return data_set

def get_max_loads(data_sets):
    max_loads = []
    for data in data_sets:
        max_loads.append(get_max_load(data))
    return max_loads

def get_max_load(data):

    load_data = data[0]
    max_load = max(load_data)

    return max_load

def compliance_correction(data,rate):
    loads = data[0]
    disps = data[1]
    if len(loads) != len(disps):
        print('Length of load and displacement data not matched')

    for i in range(0,len(loads)):
        load = loads[i]
        disp = disps[i]
        disp_corrected = disp - load*rate
        disps[i] = disp_corrected

    return [loads,disps]

def get_moduli(data_sets,lower_thresh=0.25,upper_thresh=0.75,compliance_rate=0):
    slopes = []
    for data in data_sets:
        if compliance_rate != 0:
            data = compliance_correction(data,compliance_rate)
        slopes.append(get_modulus(
                data,
                lower_thresh=lower_thresh,
                upper_thresh=upper_thresh)
            )

    return slopes

def get_modulus(data,lower_thresh=0.25,upper_thresh=0.75):

    max_load = get_max_load(data)
    lower_load = lower_thresh*max_load
    upper_load = upper_thresh*max_load

    upper_index = get_nearest_index(upper_load,data[0])
    lower_index = get_nearest_index(lower_load,data[0])
    upper_actual_load = data[0][upper_index]
    lower_actual_load = data[0][lower_index]
    upper_disp = data[1][upper_index]
    lower_disp = data[1][lower_index]
    # get slope at d_load/d_disp
    slope = (upper_actual_load - lower_actual_load)/(upper_disp-lower_disp)

    return slope

def get_nearest_index(value,list):
    index = -1
    for i in range(0,len(list)):

        if list[i] == value:
            index = i
        if i > 0:
            if list[i] > value and list[i-1] < value:
                lower_val = list[i-1]
                lower_error = lower_val - value
                upper_val = list[i]
                upper_error = upper_val - value
                if abs(lower_error) < abs(upper_error):
                    index = i-1
                else:
                    index = i
    if index == -1:
        print('Value %f not found in list'%(value))
        return

    return index

#########################
##### Begin script ######
#########################

# File path and filename settings
#folder = '/Users/your_username/your_folder/' # MacOS
#folder = 'C:\\Users\\your_home_folder\\your_folder' # Windows
folder = '/Users/davidwright/Dropbox/Cob/Data/MixRatioExperiment/MatrixRatios/'
base_name = '100-'
suffix = '.Dat'

# Read settings
files_to_read = 1
start_index = 1
index_digits = 3
delimiter = ',' # CSV file
#delimiter = '\t' # tab separated file

test_kind = 'load-displacement'
#test_kind = 'stress-strain'
# Compliance constants:
# compliance = 0 # tensile testing
# compliance = 0.00005917356 # Three-point bending [mm/N]
# compliance = 0.00001037912 # Flat Plate compression [mm/N]

# Excecute analysis
data_sets = read_files(
    folder,
    generate_filename_list(
        base_name,
        suffix,
        files_to_read,
        digits=index_digits,
        start_index = start_index),
    delimiter = delimiter,
    kind = test_kind)

if data_sets is None:
    sys.exit('No data sets read. Exiting.')

max_loads = get_max_loads(data_sets)
moduli = get_moduli(data_sets,compliance_rate=0.0001)

# print results
print('Max Loads:')
[print(x) for x in max_loads]
print('Slopes:')
[print(x) for x in moduli]
