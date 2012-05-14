#!/usr/bin/env python

"""PySide port of the opengl/hellogl example from Qt v4.x"""

import sys
import math, random
from PySide.QtCore import *
from PySide.QtGui import *
from resources.structures import RangeTree

class ScatterPlot(QWidget):
    def __init__(self, parent = None, trees = None):
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


if __name__ == '__main__':
    myTrees = {}
    myHeaders = []
        
    isFirstLine = True
    currentRsNumber = None
    inFile = open('/Users/Home/Desktop/data/1000.csv','r')
    for line in inFile:
        if len(line) <= 1:
            continue
        if isFirstLine:
            columns = line[:-1].split("\t")
            for h in columns:
                myHeaders.append(h)
                myTrees[h] = RangeTree()
            isFirstLine = False
        else:
            columns = line[:-1].split("\t")
            for i,c in enumerate(columns):
                h = myHeaders[i]
                if h == "rsNumber":
                    currentRsNumber = c
                elif h == "Chromosome":
                    pass
                elif h == "Position":
                    pass
                else:
                    if c == "":
                        myTrees[h].add(currentRsNumber,None)
                    else:
                        try:
                            myTrees[h].add(currentRsNumber,float(c))
                        except ValueError:
                            print c
                            print "...%s..." % h
                            print "Tried to add a non-numerical value"
                            sys.exit(1)
    inFile.close()
    
    print myTrees['CASES Allele Frequency'].estimatePopulation(-0.1,1.1)
    #for i in myTrees['CASES Allele Frequency'].select(0.0,0.5):
    #    print i
    
    #app = QApplication(sys.argv)
    #window = ScatterPlot(trees = myTrees)
    #window.show()
    #sys.exit(app.exec_())
