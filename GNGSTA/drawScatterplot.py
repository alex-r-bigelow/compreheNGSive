#!/usr/bin/env python

import sys
import numpy as np
import resources.scipyPatches
from scipy import spatial
from PySide.QtCore import *
from PySide.QtGui import *

class ScatterPlot(QWidget):
    def __init__(self, parent = None, data = None):
        QWidget.__init__(self, parent)
        
        self.trees = trees
        self.loadedAmount = 0.0
        
        self.pen = QtGui.QPen()
        self.pen.width = 1
        
        self.dot = QtCore.QRect(0,0,1,1)
        
        self.setWindowTitle(self.tr("drawScatterplot.py"))
    
    def getColor(self, x, y):
        # TODO: find the population in this area
        
        if population > 5:
            return QtGui.QColor.black
        else:
            alphaValue = population * 0.2
            return QtGui.QColor.fromRgbF(1.0,1.0,1.0,alphaValue)
    
    def sizeHint(self):
        return QSize(500, 500)
    
    def paintEvent(self, event):
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.save()
        
        width = 1.0*self.width()
        height = 1.0*self.height()
        
        for y in xrange(self.height()):
            for x in xrange(self.width()):
                painter.translate(1, 0)
                painter.setPen(getColor(x/width,y/height))
                painter.drawRect(self.dot)
            painter.translate(-self.width(),1)
        
        painter.restore()
        painter.end()
    
    def updateLoaded(self, amount):
        self.loadedAmount = amount

class variantData:
    reservedAttributes = set(["rsNumber","Position","Chromosome"])
    chrLengths = {"1":249250621,
                    "2":243199373,
                    "3":198022430,
                    "4":191154276,
                    "5":180915260,
                    "6":171115067,
                    "7":159138663,
                    "8":146364022,
                    "9":141213431,
                    "10":135534747,
                    "11":135006516,
                    "12":133851895,
                    "13":115169878,
                    "14":107349540,
                    "15":102531392,
                    "16":90354753,
                    "17":81195210,
                    "18":78077248,
                    "19":59128983,
                    "20":63025520,
                    "21":48129895,
                    "22":51304566,
                    "X":155270560,
                    "Y":59373566
                    }
    
    def __init__(self):
        self.data = []
        self.attributes = []
        self.rsDin = {} # for looking up data indices by rs number
        
        self.attModeRangeQin = None   # for storing query tuples that yield query indices
        self.attQinRs = None  # for converting query indices back into rs numbers
        self.npData = None
        self.isFrozen = False
        
        self.scatModeRangeQin = None
        self.scatModeQinRs = None
        
        self.attributes.append("genomePosition")
        for h in variantData.reservedAttributes:
            if h == "rsNumber":
                continue
            self.attributes.append(h)
        
    def loadCSV(self,filePath,delimiter=','):
        if self.isFrozen:
            self.thaw()
        
        headerMap = {}
        
        isFirstLine = True
        inFile = open(filePath,'r')
        for line in inFile:
            if len(line) <= 1:
                continue
            columns = line[:-1].split(delimiter)
            if isFirstLine:
                for i,h in enumerate(columns):
                    if h in self.attributes:
                        if h not in variantData.reservedAttributes:
                            print "WARNING: duplicate attribute!"
                        index = self.attributes.index(h)
                    else:
                        index = len(self.attributes)
                        self.attributes.append(h)
                    headerMap[i] = index
                isFirstLine = False
            else:
                newRow = [np.nan for i in xrange(len(self.attributes))]
                rowIndex = len(self.data)
                
                currentRsNumber = None
                currentPosition = 0
                
                for i,c in enumerate(columns):
                    attributeIndex = headerMap[i]
                    h = self.attributes[attributeIndex]
                    if h in variantData.reservedAttributes:
                        if h == "rsNumber":
                            currentRsNumber = c
                            if self.rsDin.has_key(c):
                                rowIndex = self.rsDin[c]
                                newRow = self.data[rowIndex]
                            else:
                                self.rsDin[c] = rowIndex
                        elif h == "Chromosome":
                            continue # TODO - delete this
                            if c.startswith("chr"):
                                c = c[3:]
                            if not variantData.chrLengths.has_key(c):
                                print "ERROR: Unknown chromosome: %s" % c
                                sys.exit(1)
                            
                            currentPosition += variantData.chrLengths[c]
                            
                            if c == "X":
                                c = 23
                            if c == "Y":
                                c = 24
                            else:
                                c = int(c)
                            
                            newRow[attributeIndex] = c
                        elif h == "Position":
                            continue # TODO - delete this
                            try:
                                pos = int(c)
                            except ValueError:
                                print "ERROR: non-int position: %s" % c
                            
                            self.attributes[0] = currentPosition + pos
                            currentPosition = 0
                            
                            newRow[attributeIndex] = pos
                    elif c == "":
                        pass # leave it NaN
                    else:
                        try:
                            temp = int(c)
                            newRow[attributeIndex] = temp
                        except ValueError:
                            try:
                                temp = float(c)
                                newRow[attributeIndex] = temp
                            except ValueError:
                                # TODO... add categorical stuff? Maybe just alphabetize the strings?
                                print "WARNING: non-numeric values are currently unsupported!"
                self.data.append(newRow)
        inFile.close()
    
    @staticmethod
    def buildKDTree(values):
        if len(values) > 0:
            return spatial.KDTree(values)
        else:
            return None
    
    def freeze(self):
        '''
        Builds query structures; prevents from loading more data. This is the long haul - do this as little as possible!
        '''
        if self.isFrozen:
            return
        self.isFrozen = True
                
        # fill in any empty rows with NaN
        for row in self.data:
            while len(row) < len(self.attributes):
                row.append(np.nan)
        
        # convert to sliceable numpy array
        self.npData = np.array(self.data, copy=False)
        
        # We need to build two of the lookups:
        self.attQinRs = {}
        self.attModeRangeQin = {}
        
        values = {}
        nulls = {}
        masked = {}
        for c,a in enumerate(self.attributes):
            self.attQinRs[a] = []
            values[c] = []
            nulls[c] = set()
            masked[c] = set()
        
        print "Prepping Data",
        i = 0
        nextTick = len(self.data)/10
        for r,i in self.rsDin.iteritems():
            for c,a in enumerate(self.attributes):
                if np.isnan(self.data[i][c]):
                    nulls[c].add(r)
                elif np.isinf(self.data[i][c]):
                    masked[c].add(r)
                else:
                    self.attQinRs[a].append(r)
                    values[c].append([self.data[i][c]])
            if i >= nextTick:
                print ".",
                nextTick += len(self.data)/10
        print ""
        
        print "Building KDTrees",
        for c,a in enumerate(self.attributes):
            print ".",
            if len(values[c]) == 0:
                values[c] = [[np.nan]]
            self.attModeRangeQin[a] = {'values':variantData.buildKDTree(values[c]),'null':nulls[c],'mask':masked[c]}
        print ""
            
    def thaw(self):
        '''
        Throws out all query structures; allows us to load more data
        '''
        self.npData = None
        self.attQinRs = None
        self.attModeRangeQin = None
        self.isFrozen = False
        
        self.scatModeQinRs = None
        self.scatModeRangeQin = None
    
    def setScatterAxes(self, attribute1, attribute2):
        '''
        Builds a 2D KDTree for drawing the scatterplot... this is designed to be reset relatively quickly
        '''
        if attribute1 not in self.attributes:
            raise ValueError("Attempted to set non-existent axis to scatterplot: %s" % attribute1)
        
        if attribute2 not in self.attributes:
            raise ValueError("Attempted to set non-existent axis to scatterplot: %s" % attribute2)
        
        if not self.isFrozen:
            self.freeze()
        
        # np.inf indicates that a variant has been masked because of how the minor allele was defined
        # np.nan indicates values that are undefined or missing
        
        # there are 16 configurations of null1, null2, mask1, and mask2; 7 are impossible (where the
        # same attribute is null AND masked), and here are the others:
        
        values = []             # points that are defined & unmasked in both dimensions
        
        nulls1 = []             # points that are undefined for attribute1 (but have values for attribute2)
        masked1 = []            # points that are masked for attribute1 (but have values for attribute2)
        masked1null2 = set()    # points that are masked for attribute1 and undefined for attribute2
        
        nulls2 = []             # points that are undefined for attribute2 (but have values for attribute1)
        masked2 = []            # points that are masked for attribute2 (but have values for attribute1)
        masked2null1 = set()    # points that are masked for attribute2 and undefined for attribute1
        
        bothNulls = set()       # points that are undefined in both dimensions
        bothMasked = set()      # points that are masked for both dimensions
        
        self.scatModeQinRs = {'values':[],'nullX':[],'maskX':[],'nullY':[],'maskY':[]}
        
        column1 = self.attributes.index(attribute1)
        column2 = self.attributes.index(attribute2)
        
        # Prep the data...
        for r,i in self.rsDin.iteritems():
            x = self.data[i][column1]
            y = self.data[i][column2]
            
            null1 = np.isnan(x)
            mask1 = np.isinf(x)
            null2 = np.isnan(y)
            mask2 = np.isinf(y)
            
            if not null1:
                if not null2:
                    if not mask1:
                        if not mask2:
                            values.append([x,y])
                            self.scatModeQinRs['values'].append(r)
                        else:
                            masked2.append([x])
                            self.scatModeQinRs['maskY'].append(r)
                    else:
                        if not mask2:
                            masked1.append([y])
                            self.scatModeQinRs['maskX'].append(r)
                        else:
                            bothMasked.add(r)
                else:
                    if not mask1:
                        # if not mask2:    ... impossible; we already know Y is null
                        nulls2.append([x])
                        self.scatModeQinRs['nullY'].append(r)
                    else:
                        masked1null2.add(r)
            else:
                if not null2:
                    # if not mask1:    ... impossible; we already know X is null
                    if not mask2:
                        nulls1.append([y])
                        self.scatModeQinRs['nullX'].append(r)
                    else:
                        masked2null1.add(r)
                else:
                    # if not mask1:    ... impossible; we already know X is null
                    # if not mask2:    ... impossible; we already know Y is null
                    bothNulls.add(r)
        
        # Build the trees...
        self.scatModeRangeQin = {}
        self.scatModeRangeQin['values'] = variantData.buildKDTree(values)
        self.scatModeRangeQin['nullX'] = variantData.buildKDTree(nulls1)
        self.scatModeRangeQin['maskX'] = variantData.buildKDTree(masked1)
        self.scatModeRangeQin['maskXnullY'] = masked1null2
        self.scatModeRangeQin['nullY'] = variantData.buildKDTree(nulls2)
        self.scatModeRangeQin['maskY'] = variantData.buildKDTree(masked2)
        self.scatModeRangeQin['maskYnullX'] = masked2null1
        self.scatModeRangeQin['nullBoth'] = bothNulls
        self.scatModeRangeQin['maskBoth'] = bothMasked
        
    
    def query1d(self, attribute, point1, point2, includeNull=False, includeMasked=False):
        '''
        Returns a set of the rs numbers in the queried range
        '''
        if not self.isFrozen:
            self.freeze()
        print "1D"
        results = set()
        if self.attModeRangeQin[attribute]['values'] != None:
            qins = self.attModeRangeQin[attribute]['values'].query_rectangle([point1],[point2])
            for i in qins:
                results.add(self.attQinRs[attribute][i])
        print len(results)
        if includeNull:
            results = results.union(self.attModeRangeQin[attribute]['null'])
        print len(results)
        if includeMasked:
            results = results.union(self.attModeRangeQin[attribute]['mask'])
        print len(results)
        return results
    
    def query2d(self, x1, y1, x2, y2, includeNullX=False, includeNullY=False, includeMaskedX=False, includeMaskedY=False):
        '''
        Returns a set of the rs numbers in the queried range
        '''
        if not self.isFrozen or self.scatModeQinRs == None or self.scatModeRangeQin == None:
            print "WARNING: attempted 2D query without first freezing or selecting axes. Ignoring..."
            return []
        print "2D"
        results = set()
        if self.scatModeRangeQin['values'] != None:
            qins = self.scatModeRangeQin['values'].query_rectangle([x1,y1],[x2,y2])
            for i in qins:
                results.add(self.scatModeQinRs['values'][i])
        print len(results)
        if includeNullX:
            if self.scatModeRangeQin['nullX'] != None:
                qins = self.scatModeRangeQin['nullX'].query_rectangle([y1],[y2])
                for i in qins:
                    results.add(self.scatModeQinRs['nullX'][i])
            print len(results)
            if includeNullY:
                results.update(self.scatModeRangeQin['nullBoth'])
            print len(results)
            if includeMaskedY:
                results.update(self.scatModeRangeQin['maskXnullY'])
        print len(results)
        if includeNullY:
            if self.scatModeRangeQin['nullY'] != None:
                qins = self.scatModeRangeQin['nullY'].query_rectangle([x1],[x2])
                for i in qins:
                    results.add(self.scatModeQinRs['nullY'][i])
            print len(results)
            if includeMaskedX:
                results.update(self.scatModeRangeQin['maskYnullX'])
        print len(results)
        if includeMaskedX:
            if self.scatModeRangeQin['maskX'] != None:
                qins = self.scatModeRangeQin['maskX'].query_rectangle([y1],[y2])
                for i in qins:
                    results.add(self.scatModeQinRs['maskX'][i])
            print len(results)
            if includeMaskedY:
                results.update(self.scatModeRangeQin['maskBoth'])
        print len(results)
        if includeMaskedY:
            if self.scatModeRangeQin['maskY'] != None:
                qins = self.scatModeRangeQin['maskY'].query_rectangle([x1],[x2])
                for i in qins:
                    results.add(self.scatModeQinRs['maskY'][i])
        print len(results)
        return results
        

if __name__ == '__main__':
    myData = variantData()
    print "Retrieving Data..."
    myData.loadCSV("/Users/Home/Desktop/data/1000000.csv",delimiter="\t")
    
    myData.freeze()
    myData.setScatterAxes("CASES Allele Frequency", "CONTROLS Allele Frequency")
    
    print len(myData.query1d("CASES Allele Frequency",0.0,0.5,includeNull=False,includeMasked=False))
    print len(myData.query2d(0.0,0.0,0.5,1.0,includeNullX=False,includeNullY=True,includeMaskedX=False,includeMaskedY=False))
        
    '''app = QApplication(sys.argv)
    window = ScatterPlot(data = myData)
    window.show()
    sys.exit(app.exec_())'''
