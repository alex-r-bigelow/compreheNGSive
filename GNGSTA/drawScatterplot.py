#!/usr/bin/env python

import sys
import operator
from resources.structures import TwoTree,FourTree
from widgets.scatterplot import ScatterPlot
from widgets.parallelCoordinates import ParallelCoordinates
from PySide.QtCore import *
from PySide.QtGui import *

class MainWindow(QWidget):
    def __init__(self, parent = None, data = None, width = 1200, height = 600):
        QWidget.__init__(self, parent)
        
        self.setWindowTitle(self.tr("Single Variant"))
        
        self.data = data
        
        self.selected = set()
        self.highlighted = set()
        self.deselected = set()
        
        self.scatter = ScatterPlot(self, data)
        self.scatter.move(50,50)
        
        self.pc = ParallelCoordinates(self, data)
        self.pc.move(600,25)
    
    def sizeHint(self):
        return QSize(1200,600)
    
    def highlight(self, rsNumbers):
        self.highlighted = rsNumbers
    
    def select(self, rsNumbers):
        self.selected.update(rsNumbers)
        
class variantData:
    reservedAttributes = set(["rsNumber","Position","Chromosome","Genome Position"])
    chrStarts = {"1":249250621,
                    "2":492449994,
                    "3":690472424,
                    "4":881626700,
                    "5":1062541960,
                    "6":1233657027,
                    "7":1392795690,
                    "8":1539159712,
                    "9":1680373143,
                    "10":1815907890,
                    "11":1950914406,
                    "12":2084766301,
                    "13":2199936179,
                    "14":2307285719,
                    "15":2409817111,
                    "16":2500171864,
                    "17":2581367074,
                    "18":2659444322,
                    "19":2718573305,
                    "20":2781598825,
                    "21":2829728720,
                    "22":2881033286,
                    "X":3036303846,
                    "Y":3095677412,
                    "M":3155050978,   # TODO: find out the real length of this one...
                    }
    
    def __init__(self):
        self.data = {}
        self.transposedData = {}
        self.attributes = list(variantData.reservedAttributes)  # clone
        for a in self.attributes:
            self.transposedData[a] = {}
        
        self.axes = None
        self.scatter = None
        self.isFrozen = False
        
    def loadCSV(self,filePath,delimiter=','):
        if self.isFrozen:
            self.thaw()
        
        headerMap = {}
        rsIndex = 0
        posIndex = 0
        chrIndex = 0
        
        def processDefaults(columns, newRow):
            # Find the chromosome
            chr = columns[chrIndex]
            
            if chr.startswith("chr"):
                chr = chr[3:]
            
            if not variantData.chrStarts.has_key(chr):
                print "ERROR: Unknown chromosome: %s" % chr
                sys.exit(1)
            
            chrPos = variantData.chrStarts[chr]
            
            if chr == "X":
                chr = 23
            elif chr == "Y":
                chr = 24
            elif chr =="M":
                chr = 25
            else:
                chr = int(chr)
            
            # Find the position
            pos = columns[posIndex]
            try:
                pos = int(pos)
            except ValueError:
                print "ERROR: non-int position: %s" % pos
            
            rs = columns[rsIndex]
            
            genPos = chrPos + pos
            
            newRow[0] = None    # TODO: make int proxies for strings
            self.transposedData["rsNumber"][rs] = None
            newRow[1] = pos
            self.transposedData["Position"][rs] = pos
            newRow[2] = None    # TODO: make int proxies for strings
            self.transposedData["Chromosome"][rs] = None
            newRow[3] = genPos
            self.transposedData["Genome Position"][rs] = genPos
            
            return (rs,chr,pos,genPos)
        
        isFirstLine = True
        inFile = open(filePath,'r')
        for line in inFile:
            if len(line) <= 1:
                continue
            columns = line[:-1].split(delimiter)
            if isFirstLine:
                if "Position" not in columns or "Chromosome" not in columns or "rsNumber" not in columns:
                    print "ERROR: \"rsNumber\" and \"Chromosome\" and \"Position\" column headers are required."
                    sys.exit(1)
                rsIndex = columns.index("rsNumber")
                posIndex = columns.index("Position")
                chrIndex = columns.index("Chromosome")
                
                for i,h in enumerate(columns):
                    if h in self.attributes:
                        if h not in variantData.reservedAttributes:
                            print "WARNING: Duplicate attribute: %s\nLoaded data may be replaced." % h
                        index = self.attributes.index(h)
                    else:
                        index = len(self.attributes)
                        self.attributes.append(h)
                        self.transposedData[h] = {}
                    headerMap[i] = index
                isFirstLine = False
            else:
                newRow = [None for i in xrange(len(self.attributes))]
                
                currentRsNumber,chr,pos,genPos = processDefaults(columns, newRow)
                
                for i,c in enumerate(columns):
                    attributeIndex = headerMap[i]
                    h = self.attributes[attributeIndex]
                    if h in variantData.reservedAttributes:
                        continue
                    elif c == "":
                        pass # leave it None
                    else:
                        try:
                            temp = int(c)
                            newRow[attributeIndex] = temp
                            self.transposedData[h][currentRsNumber] = temp
                        except ValueError:
                            try:
                                temp = float(c)
                                newRow[attributeIndex] = temp
                                self.transposedData[h][currentRsNumber] = temp
                            except ValueError:
                                # TODO... add categorical stuff? Maybe just alphabetize the strings?
                                print "WARNING: non-numeric values are currently unsupported!"
                self.data[currentRsNumber] = newRow
        inFile.close()
    
    def freeze(self):
        '''
        Builds query structures; prevents from loading more data.
        '''
        if self.isFrozen:
            return
        self.isFrozen = True
        
        self.axes = {}
        
        for att,dat in self.transposedData.iteritems():
            sorted_dat = sorted(dat.iteritems(), key=operator.itemgetter(1))
            self.axes[att] = TwoTree(sorted_dat)
    
    def thaw(self):
        '''
        Throws out all query structures; allows us to load more data
        '''
        self.axes = None
        self.scatter = None
        self.isFrozen = False
    
    def setScatterAxes(self, attribute1, attribute2):
        '''
        Builds a FourTree for drawing the scatterplot - maybe could be sped up by some kind of sorting...
        '''
        if not self.isFrozen:
            self.freeze()
        
        if attribute1 not in self.attributes:
            raise ValueError("Attempted to set non-existent axis to scatterplot: %s" % attribute1)
        
        if attribute2 not in self.attributes:
            raise ValueError("Attempted to set non-existent axis to scatterplot: %s" % attribute2)
        
        self.scatter = FourTree()
        
        index1 = self.attributes.index(attribute1)
        index2 = self.attributes.index(attribute2)
        
        for rsNumber,row in self.data.iteritems():
            if index1 > len(row):
                x = None
            else:
                x = row[index1]
            
            if index2 > len(row):
                y = None
            else:
                y = row[index2]
            self.scatter.add(rsNumber,x,y)
    
    def getData(self, rsNumber, a):
        index = self.attributes.index(a)
        return self.data[rsNumber][index]
    
    def getXYRange(self):
        return (self.scatter.root.lowX,self.scatter.lowY,self.scatter.highX,self.scatter.highY)

def runProgram():
    myData = variantData()
    print 'Retrieving Data...'
    myData.loadCSV('/Users/Home/Desktop/data/100000.csv',delimiter='\t')
    print 'Building TwoTrees...'
    myData.freeze()
    print 'Building FourTree...'
    myData.setScatterAxes('CASES Allele Frequency', 'CONTROLS Allele Frequency')
    
    #print len(myData.query1d('CASES Allele Frequency',0.0,0.5,includeNull=False,includeMasked=False))
    #print len(myData.query2d(0.0,0.0,0.5,1.0,includeNullX=False,includeNullY=True,includeMaskedX=False,includeMaskedY=False))
    print 'Drawing...'
    app = QApplication(sys.argv)
    window = MainWindow(data = myData)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    runProgram()
    #import cProfile
    
    #cProfile.run('runProgram()')
