#!/bin/env/python
# David Wright
# Written for Python 3.7

"""
Gets the peak load from a standard tensile test file for a list of filenames
"""

import csv
import os
import sys

def readtensiledata(filename,delimiter = ','):
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

    return columns

def generate_filename_list(basename,suffix,n,digits,start_index=1):
    filenames = [0]*n
    for i in range(start_index,n+start_index):
        number = str(i).zfill(digits)

        filename = basename + number + suffix
        filenames[i-1] = filename
    return filenames

def read_files(folder,filenames,delimiter=','):
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
        data = readtensiledata(filename,delimiter=delimiter)
        data_sets.append(data)

    for i in range(0,len(data_sets)):
        for j in range(0,len(data_sets[i])-1):
            for k in range(0,len(data_sets[i][j])):
                try:
                    data_sets[i][j][k] = float(data_sets[i][j][k])
                except Exception as ex:
                    logging.exception('Caught an error')

    return data_sets

def get_max_loads(data_sets,kind='stress-strain'):
    column = 0
    if kind == 'load-displacement':
        column=0
    elif kind == 'stress-strain':
        column=2
    else:
        print('Unknown kind of test selected in get_max_loads: ' + kind)
        return []

    max_loads = []
    for data in data_sets:
        load_data = data[0]
        max_load = max(load_data)
        max_loads.append(max_load)
        #print('Max Load for ' + filename + ' is:\t' +  repr(maxload))
    return max_loads

def get_moduli(data_sets,kind='stress-strain'):
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

    max_loads = get_max_loads(data_sets,kind=kind)
    lower_loads = [x*0.25 for x in max_loads]
    upper_loads = [x*0.75 for x in max_loads]
    slopes = []

    for i in range(0,len(data_sets)):
        data = data_sets[i]
        max_load = max_loads[i]
        upper_load = upper_loads[i]
        lower_load = lower_loads[i]
        upper_index = get_nearest_index(upper_load,data[load_column])
        lower_index = get_nearest_index(lower_load,data[load_column])
        upper_actual_load = data[load_column][upper_index]
        lower_actual_load = data[load_column][lower_index]
        upper_disp = data[disp_column][upper_index]
        lower_disp = data[disp_column][lower_index]
        # get slope at d_load/d_disp
        slope = (upper_actual_load - lower_actual_load)/(upper_disp-lower_disp)
        slopes.append(slope)

    return slopes

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
files_to_read = 5
start_index = 1
index_digits = 3
delimiter = ',' # CSV file
#delimiter = '\t' # tab separated file

test_kind = 'load-displacement'
#test_kind = 'stress-strain'

# Excecute analysis
data_sets = read_files(
    folder,
    generate_filename_list(
        base_name,
        suffix,
        files_to_read,
        digits=index_digits,
        start_index = start_index),
    delimiter = delimiter)

if data_sets is None:
    sys.exit('No data sets read. Exiting.')

max_loads = get_max_loads(data_sets,kind=test_kind)
moduli = get_moduli(data_sets,kind=test_kind)

# print results
print('Max Loads:')
[print(x) for x in max_loads]
print('Slopes:')
[print(x) for x in moduli]
