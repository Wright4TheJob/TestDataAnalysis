#!/bin/env/python
# David Wright
# Written for Python 3.7

"""
Gets the peak load from a standard tensile test file for a list of filenames
"""

import csv
import os
import sys

class Test:
    '''Class containing test data and results'''

    def __init__(self,name):
        self.name = name
        self.data = []
        self.input_suffix = None

        self.peak = None
        self.modulus = None

        self.x_axis = 'Stress'
        self.y_axis = 'Strain'
        self.x_data = None
        self.y_data = None
        self.lower_thresh=0.25
        self.upper_thresh=0.75

    def useful_data(self):
        if self.y_axis == 'Stress':
            self.y_data = [point.stress for point in data]
        elif self.y_axis == 'Load':
            self.y_data = [point.load for point in data]
        else:
            print('Unknown y axis parameter encountered in calculate_peak: '
                + self.y_axis)

        if self.x_axis == 'Strain':
            self.x_data = [point.strain for point in data]
        elif self.x_axis == 'Displacement':
            self.x_data = [point.displacement for point in data]
        else:
            print('Unknown x axis parameter encountered in calculate_peak: '
                + self.x_axis)
        return
        
    def add_data_point(self,point):
        self.data.append(point)

    def peak(self):
        # if self.peak != nil, return value, otherwise calculate value
        if self.peak == None:
            self.peak = self.calculate_peak()
        return self.peak

    def calculate_peak(self):
        '''Calculates the peak of a given column from data'''
        peak = max(self.y_data)
        return peak

    def modulus(self):
        if self.modulus == None:
            self.modulus = self.calculate_modulus()
        return self.modulus

    def calculate_modulus(self):

        lower = get_modulus_point(self.lower_thresh)
        upper = get_modulus_point(self.upper_thresh)
        # get slope at d_load/d_disp
        slope = (upper[0] - lower[0])/(upper[1]-lower[1])

        return slope

    def get_modulus_point(self,thresh):
        max = self.peak()
        y_target = thresh*max
        index = get_nearest_index(y_target,self.y_data)
        y = self.y_data[index]
        x = self.x_data[index]
        return [y,x]

    def get_nearest_index(self,value,list):
        index = -1
        for i in range(0,len(list)):

            if list[i] == value:
                index = i
                break
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
                    break
        if index == -1:
            print('Value %f not found in list'%(value))
            return

        return index

class DataPoint:
    '''Single test data point (row) read from file'''
    def __init__(self):
        self.time = None
        self.load = None
        self.displacement = None
        self.stress = None
        self.strain = None

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
        print('Unknown kind of test selected in readtensiledata: ' + kind)
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

def get_max_point(data):
    max_load = get_max_load(data)
    max_load_disp = data[1][get_nearest_index(max_load,data[0])]
    return [max_load,max_load_disp]

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

    lower = get_modulus_point(data,lower_thresh)
    upper = get_modulus_point(data,upper_thresh)
    # get slope at d_load/d_disp
    slope = (upper[0] - lower[0])/(upper[1]-lower[1])

    return slope

def get_modulus_point(data,thresh):
    load_max = get_max_load(data)
    load_target = thresh*load_max
    index = get_nearest_index(load_target,data[0])
    load_actual = data[0][index]
    disp = data[1][index]
    return [load_actual,disp]

def get_nearest_index(value,list):
    index = -1
    for i in range(0,len(list)):

        if list[i] == value:
            index = i
            break
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
                break
    if index == -1:
        print('Value %f not found in list'%(value))
        return

    return index

##################################################
# Plotting functions
def plot_data_sets(data_sets,
    names,
    kind = 'stress-strain',
    load_units='',
    disp_units='',
    analysis=True,
    shouldShow=False,
    mod_lower=0.25,
    mod_upper=0.75):

    import matplotlib.pyplot as plt

    x_label = ''
    y_label = ''
    if kind == 'load-displacement':
        x_label += 'Displacement'
        y_label += 'Load'
    elif kind == 'stress-strain':
        x_label += 'Strain'
        y_label += 'Stress'
    else:
        print('Unknown kind of test selected in plot_data_sets: ' + kind)
        return []

    x_label += disp_units
    y_label += load_units

    for i in range(0,len(data_sets)):
        plot_data(
            data_sets[i],
            names[i],
            analysis=analysis,
            xLabel=x_label,
            yLabel=y_label,
            shouldShow=shouldShow,
            mod_lower = mod_lower,
            mod_upper = mod_upper)

def plot_data(data,name,analysis=True,xLabel='x',yLabel='y',shouldShow=False,mod_lower=0.25,mod_upper=0.75):
    import matplotlib.pyplot as plt
    name = name[:-4] + '.png'
    xs = data[1]
    ys = data[0]
    fig = plt.figure()
    plt.plot(xs,ys)
    if analysis == True:
        peak_point = get_max_point(data)
        lower_modulus_point = get_modulus_point(data,mod_lower)
        upper_modulus_point = get_modulus_point(data,mod_upper)
    plt.plot(peak_point[1],peak_point[0],'rx')
    plt.plot(lower_modulus_point[1],lower_modulus_point[0],'rx')
    plt.plot(upper_modulus_point[1],upper_modulus_point[0],'rx')
    fig.set_size_inches(6,4)
    plt.xlabel(xLabel)
    plt.ylabel(yLabel)
    plt.savefig(name, dpi=120)
    if shouldShow == True:
        plt.show()
    plt.close()


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
# Compliance constants:
compliance = 0 # tensile testing
# compliance = 0.00005917356 # Three-point bending [mm/N]
compliance = 0.00001037912 # Flat Plate compression [mm/N]
modulus_lower_bound = 0.4
modulus_upper_bound = 0.75
# Excecute analysis
filenames = generate_filename_list(
    base_name,
    suffix,
    files_to_read,
    digits=index_digits,
    start_index = start_index)

data_sets = read_files(
    folder,
    filenames,
    delimiter = delimiter,
    kind = test_kind)

if data_sets is None:
    sys.exit('No data sets read. Exiting.')

max_loads = get_max_loads(data_sets)
moduli = get_moduli(data_sets,
    compliance_rate=compliance,
    upper_thresh = modulus_upper_bound,
    lower_thresh=modulus_lower_bound)
plot_data_sets(data_sets,filenames,
    kind=test_kind,
    mod_upper = modulus_upper_bound,
    mod_lower=modulus_lower_bound)

# print results
print('Max Loads:')
[print(x) for x in max_loads]
print('Slopes:')
[print(x) for x in moduli]
