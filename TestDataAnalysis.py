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
    folder = '/Users/davidwright/Dropbox/Cob/Data/MatrixExperiment/MatrixRatios/'
    base_name = '100-'
    suffix = '.Dat'

    ######## Read settings
    files_to_read = 1
    start_index = 1
    index_digits = 3

    x_axis = 'Displacement'
    #x_axis = 'Strain'
    y_axis = 'Load'
    #y_axis = 'Stress'
    # Compliance constants:
    compliance = 0 # tensile testing
    # compliance = 0.00005917356 # Three-point bending [mm/N]
    # compliance = 0.00001037912 # Flat Plate compression [mm/N]
    modulus_lower_bound = 0.4
    modulus_upper_bound = 0.75

    ######## Yield stress calculation
    yield_offset = 0.2

    ######## Input File Parameters
    delimiter = ',' # CSV file
    #delimiter = '\t' # tab separated file
    header_lines = 4
    time_column = None
    load_column = 0
    disp_column = 1
    stress_column = 2
    strain_column = 5

    ######## Plotting Settings
    plot_modulus_points = True
    plot_modulus_line = True
    plot_yield_point = True
    plot_peak = True
    show_figures = False

class Analyst:
    '''Class for running analysis on individual tests'''
    def __init__(self):
        self.names = []
        self.settings = Settings()
        self.names = self.generate_filename_list()
        self.data_sets = []
        self.peaks = []
        self.yields = []
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
            self.data_sets.append(Test(filename))
        return

class Test:
    '''Class containing test data and results'''
    def __init__(self,name,load_data=True):
        self.settings = Settings()
        self.name = name
        self.data = []
        self.input_suffix = None

        self._peak_stress = None
        self._peak_strain = None
        self._modulus = None
        self._modulus_x_intercept = None
        self.modulus_upper_point = None
        self.modulus_lower_point = None
        self._yield_stress = None
        self._yield_strain = None
        self.x_axis = self.settings.x_axis
        self.y_axis = self.settings.y_axis
        self.x_data = None
        self.y_data = None
        self.lower_thresh=self.settings.modulus_lower_bound
        self.upper_thresh=self.settings.modulus_upper_bound
        if load_data == True:
            self.read_data()
            self.useful_data()

    def useful_data(self):
        if self.y_axis == 'Stress':
            self.y_data = [point.stress for point in self.data]
        elif self.y_axis == 'Load':
            self.y_data = [point.load for point in self.data]
        else:
            print('Unknown y axis parameter encountered in calculate_peak: '
                + self.y_axis)

        if self.x_axis == 'Strain':
            self.x_data = [point.strain for point in self.data]
        elif self.x_axis == 'Displacement':
            self.x_data = [point.displacement for point in self.data]
        else:
            print('Unknown x axis parameter encountered in calculate_peak: '
                + self.x_axis)
        return

    def add_data_point(self,point):
        self.data.append(point)

    @property
    def peak(self):
        if self._peak_stress is None:
            self._peak_stress = self.calculate_peak()
        return self._peak_stress

    def calculate_peak(self):
        '''Calculates the peak of a given column from data'''
        if self.y_data is not None:
            return max(self.y_data)
        else:
            print('No data loaded, canceling data analysis')

    @property
    def peak_strain(self):
        if self._peak_strain is None:
            self._peak_strain = self.calculate_peak_strain()
        return self._peak_strain

    def calculate_peak_strain(self):
        peak_stress = self.peak
        index = self.get_nearest_index(peak_stress,self.y_data)
        return self.x_data[index]

    @property
    def modulus(self):
        if self._modulus is None:
            self._modulus = self.calculate_modulus()
        return self._modulus

    def calculate_modulus(self):
        self.modulus_lower_point = self.get_modulus_point(self.lower_thresh)
        self.modulus_upper_point = self.get_modulus_point(self.upper_thresh)
        # get slope at d_load/d_disp
        (slope,intercept) = self.slope_intercept(self.modulus_upper_point,self.modulus_lower_point)
        self._modulus_x_intercept = -intercept/slope
        return slope

    def get_modulus_point(self,thresh):
        max = self.peak
        y_target = thresh*max
        index = self.get_nearest_index(y_target,self.y_data)
        y = self.y_data[index]
        x = self.x_data[index]
        return [x,y]

    @property
    def yield_stress(self):
        if self._yield_stress is None:
             point = self.calculate_yield()
             self._yield_stress = point[1]
        return self._yield_stress

    def calculate_yield(self):
        '''Calculates a yield stress/load from offset modulus'''
        if self._modulus_x_intercept is None or self._modulus is None:
            self._modulus = self.calculate_modulus()
        self._yield_x_intercept = self._modulus_x_intercept + self.settings.yield_offset
        found_yield = False
        for i in range(0,len(self.y_data)-1):
            x = self.x_data[i]
            y = self.y_data[i]
            yield_i = self.yield_line_value(x)
            x_next = self.x_data[i+1]
            y_next = self.y_data[i+1]
            yield_next = self.yield_line_value(x_next)
            if y > yield_i and y_next < yield_next:
                yield_line = [[x,yield_i], [x_next,yield_next]]
                data_line = [[x,y],[x_next,y_next]]
                intersection = self.intersection_of_lines(yield_line,data_line)
                #print(intersection)
                found_yield = True
                return intersection
            elif y == yield_i:
                found_yield = True
                return y
        if found_yield == False:
            print('Unable to calculate yield stress')

    @property
    def yield_strain(self):
        if self._yield_strain is None:
             point = self.calculate_yield()
             self._yield_strain = point[0]
        return self._yield_strain

    def yield_line_value(self,x):
        stress = self.modulus*(x-self._yield_x_intercept)
        #print('%2.4f, %2.4f'%(x,stress))
        return stress

    def intersection_of_lines(self,first_pair,second_pair):
        '''Takes in two pairs of points and returns intection point'''
        (m1,b1) = self.slope_intercept(first_pair[0],first_pair[1])
        (m2,b2) = self.slope_intercept(second_pair[0],second_pair[1])
        x = (b2-b1)/(m1-m2)
        y = m2*x+b2
        return [x,y]

    def slope_intercept(self,point1,point2):
        '''The slope and intercept form of a line from two points'''
        x1 = point1[0]
        y1 = point1[1]
        x2 = point2[0]
        y2 = point2[1]
        if x1 == x2 and y1 != y2:
            print('Line is vertical, slope is infinite')
            return (999999,x1)
        slope = (y2 - y1)/(x2 - x1)
        intercept = y1-slope*x1
        return (slope,intercept)

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
def plot_test(test):
    import matplotlib.pyplot as plt
    settings = Settings()
    set_dir(settings)
    name = test.name + '.png'
    xs = test.x_data
    ys = test.y_data
    fig = plt.figure()
    plt.plot(xs,ys,'.',markersize=1.5,label='Data')
    # Modulus line plotting
    if settings.plot_modulus_line == True:
        slope = test.modulus
        intercept = test._modulus_x_intercept
        mod_line_lower = [intercept,0]
        mod_line_upper = [test.peak/slope + intercept,test.peak]
        plt.plot(
            [mod_line_lower[0],mod_line_upper[0]],
            [mod_line_lower[1],mod_line_upper[1]],
            'k',
            linewidth=1,
            label='Modulus')
    # Modulus secant point plotting
    if settings.plot_modulus_points == True:
        if test.modulus_upper_point is None or test.modulus_lower_point is None:
            modulus = test.modulus
        mod_lower = test.modulus_lower_point
        mod_upper = test.modulus_upper_point
        plt.plot(
            [mod_lower[0],mod_upper[0]],
            [mod_lower[1],mod_upper[1]],
            'rx',
            label='Modulus Secant Points')
    # Peak value point plotting
    if settings.plot_peak == True:
        peak_y = test.peak
        peak_x = test.peak_strain
        plt.plot(peak_x,peak_y,'rx','Peak')
    # Yield point plotting
    if settings.plot_yield_point == True:
        plt.plot(test.yield_strain,test.yield_stress,'r*',markersize=4,label='Yield')

    fig.set_size_inches(6,4)
    plt.xlabel(test.x_axis)
    plt.ylabel(test.y_axis)
    plt.legend(loc=4)
    plt.savefig(name, dpi=120)
    if settings.show_figures == True:
        plt.show()
    plt.close()

def set_dir(settings):
    folder = settings.folder
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


#########################
##### Begin script ######
#########################
my_settings = Settings()
analyst = Analyst()
#print(analyst.names)

if analyst.data_sets is None:
    sys.exit('No data sets read. Exiting.')

#plot_data_sets(data_sets,filenames,
#    kind=test_kind,
#    mod_upper = modulus_upper_bound,
#    mod_lower=modulus_lower_bound)

print('Max Loads:')
[print(x.peak) for x in analyst.data_sets]

print('Yield Loads:')
[print(x.yield_stress) for x in analyst.data_sets]

print('Slopes:')
[print(x.modulus) for x in analyst.data_sets]

print('Plotting Figures...')
[plot_test(x) for x in analyst.data_sets]

print('Done')
