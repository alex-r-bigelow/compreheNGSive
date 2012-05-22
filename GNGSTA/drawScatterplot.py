#!/usr/bin/env python

import sys
from resources.structures import TwoTree,FourTree
from PySide.QtCore import *
from PySide.QtGui import *

class ScatterPlot(QWidget):
    def __init__(self, parent = None, data = None):
        QWidget.__init__(self, parent)
        
        self.setWindowTitle(self.tr("drawScatterplot.py"))
        
        self.setMouseTracking(True)
        
        self.data = data
        
        self.highlighted = set()
        self.selected = set()
        
        self.scatterWidth = 500
        self.scatterHeight = 500
        self.scatterOffsetX = 10
        self.scatterOffsetY = 10
        
        self.image = QPixmap(self.scatterWidth,self.scatterHeight)
        self.selectionOverlay = QPixmap(self.scatterWidth,self.scatterHeight)
        
        self.highlightColor = QColor.fromRgbF(1.0,0.0,0.0,0.5)
        self.selectedColor = QColor.fromRgbF(0.0,0.0,1.0,0.5)
        
        pointSize = 2
        selectionSize = 6
        
        self.pointRadius = pointSize/(2.0*min(self.scatterWidth,self.scatterHeight))
        self.selectionRadius = selectionSize/(2.0*min(self.scatterWidth,self.scatterHeight))
        
        self.dot = QRect(0,0,1,1)
        self.selectionRect = QRect(-selectionSize/2,-selectionSize/2,selectionSize,selectionSize)
        self.selectedDot = QRect(-pointSize/2,-pointSize/2,pointSize,pointSize)
        
        self.drawScatter(self.scatterWidth,self.scatterHeight)
        
        self.mousex = 0
        self.mousey = 0
        
        self.animationTimer = QTimer()
        self.animationTimer.setSingleShot(False)
        self.connect(self.animationTimer, SIGNAL("timeout()"), self.animate)
        self.animationTimer.start(25)
        
    def getColor(self, x, y, x2, y2):
        population = self.data.scatter.countPopulation(x,y,x2,y2)
        
        if population > 10:
            return QColor.fromRgbF(0.0,0.0,0.0,1.0)
        else:
            alphaValue = population * 0.1
            return QColor.fromRgbF(0.0,0.0,0.0,alphaValue)
    
    def drawScatter(self, width, height):
        self.image.fill(Qt.white)
        
        painter = QPainter()
        painter.begin(self.image)
        
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.NonCosmeticDefaultPen)
        
        xRange,yRange = self.transformScreenCoordinates(width, height)
        
        for y in xrange(width):
            for x in xrange(height):
                painter.translate(1, 0)
                xVal,yVal = self.transformScreenCoordinates(x,y)
                painter.fillRect(self.dot,self.getColor(xVal-self.pointRadius,yVal-self.pointRadius,xVal+self.pointRadius,yVal+self.pointRadius))
            painter.translate(-width,1)
        
        painter.end()
    
    def mouseMoveEvent(self, event):
        self.mousex = event.x()
        self.mousey = event.y()
        
        x,y = self.transformScreenCoordinates(self.mousex-self.scatterOffsetX, self.mousey-self.scatterOffsetY)
        self.highlighted = self.data.scatter.select(x-self.selectionRadius,y-self.selectionRadius,x+self.selectionRadius,y+self.selectionRadius)
        
        if event.buttons() & Qt.LeftButton:
            self.selected.update(self.highlighted)
    
    def transformScreenCoordinates(self, x, y):
        x = x/float(self.scatterWidth)
        y = y/float(self.scatterHeight)
        
        return (x,y)
    
    def transformDataCoordinates(self, x, y):
        x = int(x*self.scatterWidth)
        y = int(y*self.scatterHeight)
        
        return (x,y)
    
    def animate(self):
        self.selectionOverlay.fill(Qt.transparent)
        
        painter = QPainter()
        painter.begin(self.selectionOverlay)
        
        painter.setPen(self.highlightColor)
        painter.save()
        painter.translate(self.mousex-self.scatterOffsetX,self.mousey-self.scatterOffsetY)
        painter.drawRect(self.selectionRect)
        painter.restore()
        
        for rsNumber in self.selected:
            painter.save()
            x,y = self.transformDataCoordinates(self.data.getData(rsNumber,"CASES Allele Frequency"),self.data.getData(rsNumber,"CONTROLS Allele Frequency"))
            painter.translate(x,y)
            painter.fillRect(self.selectedDot,self.selectedColor)
            painter.restore()
        
        for rsNumber in self.highlighted:
            painter.save()
            x,y = self.transformDataCoordinates(self.data.getData(rsNumber,"CASES Allele Frequency"),self.data.getData(rsNumber,"CONTROLS Allele Frequency"))
            painter.translate(x,y)
            painter.fillRect(self.selectedDot,self.highlightColor)
            painter.restore()
        
        painter.end()
        self.update()
        
    
    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPixmap(self.scatterOffsetX,self.scatterOffsetY,self.image)
        painter.drawPixmap(self.scatterOffsetX,self.scatterOffsetY,self.selectionOverlay)
        painter.end()
    
    def sizeHint(self):
        return QSize(self.scatterWidth+2*self.scatterOffsetX, self.scatterHeight+2*self.scatterOffsetY)
        
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
        self.data = {}
        self.attributes = []
        
        self.axes = None
        self.scatter = None
        self.isFrozen = False
        
        self.attributes.append("genomePosition")
        
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
                if "Position" not in columns or "Chromosome" not in columns:
                    print "ERROR: \"Chromosome\" and \"Position\" column headers are required."
                    sys.exit(1)
                for i,h in enumerate(columns):
                    if h in self.attributes:
                        if h not in variantData.reservedAttributes:
                            print "WARNING: Duplicate attribute: %s\nLoaded data may be replaced." % h
                            index = self.attributes.index(h)
                        else:
                            index = None
                    else:
                        index = len(self.attributes)
                        self.attributes.append(h)
                    headerMap[i] = index
                isFirstLine = False
            else:
                newRow = [None for i in xrange(len(self.attributes))]
                
                currentRsNumber = None
                currentPosition = 0
                
                for i,c in enumerate(columns):
                    attributeIndex = headerMap[i]
                    h = self.attributes[attributeIndex]
                    if h in variantData.reservedAttributes:
                        if h == "rsNumber":
                            currentRsNumber = c
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
                        pass # leave it None
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
                self.data[currentRsNumber] = newRow
        inFile.close()
    
    def freeze(self):
        '''
        Builds query structures; prevents from loading more data. This is the long haul - do this as little as possible!
        '''
        if self.isFrozen:
            return
        self.isFrozen = True
        
        self.axes = {}
        
        for c,a in enumerate(self.attributes):
            self.axes[a] = TwoTree()
        
        # add data to trees, fill in any empty spots with None
        
        # TODO: I might be able to speed this (and queries) up a little by sorting the columns before I add them...
        for rsNumber,row in self.data.iteritems():
            for c,a in enumerate(self.attributes):
                if c >= len(row):
                    row.append(None)
                self.axes[a].add(rsNumber,row[c])
    
    def thaw(self):
        '''
        Throws out all query structures; allows us to load more data
        '''
        self.axes = None
        self.scatter = None
        self.isFrozen = False
    
    def setScatterAxes(self, attribute1, attribute2):
        '''
        Builds a FourTree for drawing the scatterplot... this is designed to be reset relatively quickly
        '''
        if attribute1 not in self.attributes:
            raise ValueError("Attempted to set non-existent axis to scatterplot: %s" % attribute1)
        
        if attribute2 not in self.attributes:
            raise ValueError("Attempted to set non-existent axis to scatterplot: %s" % attribute2)
        
        #if not self.isFrozen:
        #    self.freeze()
        
        self.scatter = FourTree()
        
        index1 = self.attributes.index(attribute1)
        index2 = self.attributes.index(attribute2)
        
        for rsNumber,row in self.data.iteritems():
            x = row[index1]
            y = row[index2]
            self.scatter.add(rsNumber,x,y)
    
    def getData(self, rsNumber, a):
        index = self.attributes.index(a)
        return self.data[rsNumber][index]

def runProgram():
    myData = variantData()
    print 'Retrieving Data...'
    myData.loadCSV('/Users/Home/Desktop/data/100000.csv',delimiter='\t')
    #print 'Building TwoTrees...'
    #myData.freeze()
    print 'Building FourTree...'
    myData.setScatterAxes('CASES Allele Frequency', 'CONTROLS Allele Frequency')
    
    #print len(myData.query1d('CASES Allele Frequency',0.0,0.5,includeNull=False,includeMasked=False))
    #print len(myData.query2d(0.0,0.0,0.5,1.0,includeNullX=False,includeNullY=True,includeMaskedX=False,includeMaskedY=False))
    print 'Drawing...'
    app = QApplication(sys.argv)
    window = ScatterPlot(data = myData)
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    runProgram()
    #import cProfile
    
    #cProfile.run('runProgram()')
