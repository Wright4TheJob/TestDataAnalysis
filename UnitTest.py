import unittest
import sys
import time
import math
import TestDataAnalysis as test

class KnownValues(unittest.TestCase):

    def test_slope_intercept(self):
        '''Simple data points should return known slopes and intercepts'''
        # of the form [[x,y],[x,y],[slope,intercept]]
        test_line_points = [[[0,0],[1,1],[1,0]],[[1,1],[3,2],[0.5,0.5]]]
        settings = test.Settings()
        this_test = test.Test('Name',settings,load_data=False)
        for test_line in test_line_points:
            point1 = test_line[0]
            point2 = test_line[1]
            (slope,intercept) = test_line[2]

            (slope_result,intercept_result) = this_test.slope_intercept(point1,point2)
            self.assertEqual(slope,slope_result)
            self.assertEqual(intercept,intercept_result)

    def test_line_intersection(self):
        '''Simple intersecting lines should have predictable intersections'''
        # of the form [[[x,y],[x,y]],[[x,y],[x,y]],[intersection x,y]]
        test_lines = [[[[0,0],[1,0]],[[0,-1],[1,1]],[0.5,0]]]
        settings = test.Settings()
        this_test = test.Test('Name',settings,load_data=False)
        for test_set in test_lines:
            point1 = test_set[0]
            point2 = test_set[1]
            intersection = test_set[2]

            intesection_test = this_test.intersection_of_lines(point1,point2)
            self.assertEqual(intersection,intesection_test)

    #def test_parabola_results(self):
    #	'''parabola should return known results'''
    #	result = MainProgram.valueOfParabola([0,0,0],1)
    #	self.assertEqual(0,result)

if __name__ == '__main__':
    unittest.main()
