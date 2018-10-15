#!/bin/env/python
# David Wright
# Written for Python 3.7

"""
Gets the peak load from a standard tensile test file for a list of filenames
"""

import csv
import os
import sys

class Settings:
    '''Program settings'''
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

    x_axis = 'displacement'
    #x_axis = 'strain'
    y_axis = 'load'
    #y_axis = 'stress'
    # Compliance constants:
    compliance = 0 # tensile testing
    # compliance = 0.00005917356 # Three-point bending [mm/N]
    compliance = 0.00001037912 # Flat Plate compression [mm/N]
    modulus_lower_bound = 0.4
    modulus_upper_bound = 0.75

    ######## Input File Parameters
    delimiter = ',' # CSV file
    #delimiter = '\t' # tab separated file
    header_lines = 4
    time_column = None
    load_column = 0
    disp_column = 1
    stress_column = 2
    strain_column = 5

class Analyst:
    '''Class for running analysis on individual tests'''
    def __init__(self,settings):
        self.names = []
        self.settings = settings
        self.names = self.generate_filename_list()
        self.data_sets = []
        self.peaks = []
        self.moduli = []
        self.create_data_sets()

    def generate_filename_list(self):
        n = self.settings.files_to_read
        filenames = [0]*n
        for i in range(self.settings.start_index,n+self.settings.start_index):
            number = str(i).zfill(self.settings.index_digits)

            filename = self.settings.base_name + number
            filenames[i-1] = filename
        return filenames

    def set_dir(self):
        folder = self.settings.folder
        exists = False
        is_folder = False
        if os.path.exists(folder):
            exists = True
        else:
            print('Filepath specified does not exist: ' + folder)
            return
        if os.path.isdir(folder):
            is_folder = True
        else:
            print('Filepath specified is not a directory: ' + folder)
            return
        if exists and is_folder:
            os.chdir(folder)
        return

    def create_data_sets(self):
        self.set_dir()
        for filename in self.names:
            self.data_sets.append(Test(filename,self.settings))
        return

class Test:
    '''Class containing test data and results'''

    def __init__(self,name,settings):
        self.settings = settings
        self.name = name
        self.data = []
        self.input_suffix = None

        self.peak = None
        self.modulus = None

        self.x_axis = self.settings.x_axis
        self.y_axis = self.settings.y_axis
        self.x_data = None
        self.y_data = None
        self.lower_thresh=0.25
        self.upper_thresh=0.75

        self.read_data()
        self.useful_data()
        self.calculate_peak()
        self.calculate_modulus()

    def useful_data(self):
        if self.y_axis == 'stress':
            self.y_data = [point.stress for point in self.data]
        elif self.y_axis == 'load':
            self.y_data = [point.load for point in self.data]
        else:
            print('Unknown y axis parameter encountered in calculate_peak: '
                + self.y_axis)

        if self.x_axis == 'strain':
            self.x_data = [point.strain for point in self.data]
        elif self.x_axis == 'displacement':
            self.x_data = [point.displacement for point in self.data]
        else:
            print('Unknown x axis parameter encountered in calculate_peak: '
                + self.x_axis)
        return

    def add_data_point(self,point):
        self.data.append(point)

    def calculate_peak(self):
        '''Calculates the peak of a given column from data'''
        peak = max(self.y_data)
        return peak

    def calculate_modulus(self):
        lower = self.get_modulus_point(self.lower_thresh)
        upper = self.get_modulus_point(self.upper_thresh)
        # get slope at d_load/d_disp
        slope = (upper[0] - lower[0])/(upper[1]-lower[1])
        return slope

    def get_modulus_point(self,thresh):
        max = self.peak
        y_target = thresh*max
        index = get_nearest_index(y_target,self.y_data)
        y = self.y_data[index]
        x = self.x_data[index]
        return [y,x]

    def get_nearest_index(self,value,list):
        '''Gets the index of the first item from list closest to target value'''
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

    def input_filename(self):
        input_filename = self.name + self.settings.suffix
        return input_filename

    def read_float(self,index,to_read):
        if index is None:
            return None
        else:
            try:
                return float(to_read[index])
            except:
                print('Float conversion error')

    def read_data(self):
        filename = self.input_filename()
        delimiter = self.settings.delimiter
        with open(filename, 'r') as fin:
            for i in range(0,self.settings.header_lines):
                next(fin)  # skip headings
            if delimiter == ',':
                reader = csv.reader(fin)
            else:
                reader = csv.reader(fin, delimiter=delimiter)

            for line in reader:
                this_point = DataPoint()
                this_point.load = self.read_float(self.settings.load_column,line)
                this_point.displacement = self.read_float(self.settings.disp_column,line)
                this_point.stress = self.read_float(self.settings.stress_column,line)
                this_point.strain = self.read_float(self.settings.strain_column,line)
                this_point.time = self.read_float(self.settings.time_column,line)
                self.add_data_point(this_point)
        return

class DataPoint:
    '''Single test data point (row) read from file'''
    def __init__(self):
        self.time = None
        self.load = None
        self.displacement = None
        self.stress = None
        self.strain = None

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
my_settings = Settings()
analyst = Analyst(my_settings)
print(analyst.names)

if analyst.data_sets is None:
    sys.exit('No data sets read. Exiting.')

#plot_data_sets(data_sets,filenames,
#    kind=test_kind,
#    mod_upper = modulus_upper_bound,
#    mod_lower=modulus_lower_bound)

# print results
analyst.calculate_peaks()

print('Max Loads:')
for x in analyst.data_sets:
    print(x.peak)
#[print(x) for x in analyst.data_sets]
#print('Slopes:')
#[print(x) for x in moduli]
