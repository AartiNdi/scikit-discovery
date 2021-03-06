# The MIT License (MIT)
# Copyright (c) 2017 Massachusetts Institute of Technology
#
# Authors: Victor Pankratius, Justin Li, Cody Rude
# This software is part of the NSF DIBBS Project "An Infrastructure for
# Computer Aided Discovery in Geoscience" (PI: V. Pankratius) and 
# NASA AIST Project "Computer-Aided Discovery of Earth Surface 
# Deformation Phenomena" (PI: V. Pankratius)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


class PipelineItem:
    '''
    The general class used to create pipeline items.
    '''

    def __init__(self, str_description, ap_paramList=[]):
        '''
        Initialize an object

        @param str_description: String description of filter
        @param ap_paramList: List of AutoParam parameters.
        '''
        self.str_description = str_description
        self.ap_paramList = ap_paramList
        self.ap_paramNames = []

    def perturbParams(self):
        '''choose other random value for all parameters'''
        for param in self.ap_paramList:
            param.perturb()
            
    def resetParams(self):
        '''set all parameters to initial value'''
        for param in self.ap_paramList:
            param.reset()
            
    def process(self, obj_data):
        '''
        The actual filter processing. Empty in this generic filter. 

        @param obj_data: Data wrapper that will be processed
        '''
        pass
 
    def __str__(self):
        ''' 
        String represntation of object.

        @return String listing all currenter parameters
        '''
        return str([str(p) for p in self.ap_paramList])
        
    def getMetadata(self):
        ''' 
        Retrieve metadata about filter
        
        @return String containing the item description and current parameters for filter.
        '''
        return self.str_description + str([str(p) for p in self.ap_paramList])

