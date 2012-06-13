import math
from axes import scatterAxes
from PySide.QtCore import *
from PySide.QtGui import *

class scatterPlot(QWidget):
    def __init__(self, controller, svg, parent = None, width = 500, height = 500, pointSize = 5, lighnessSteps = 5, selectionSize = 10):
        QWidget.__init__(self, parent)
        
        self.setWindowTitle(self.tr("scatterplot.py"))
        
        self.setMouseTracking(True)
        
        self.controller = controller.scatterPlot
        self.scatterAxes = scatterAxes()
        
        self.scatterWidth = width
        self.scatterHeight = height
        
        self.pointSize = pointSize
        self.lightnessSteps = float(lighnessSteps)
        self.selectionSize = selectionSize
        
        self.pointRadius = pointSize/(2.0*max(self.scatterWidth,self.scatterHeight))
        self.selectionRadius = selectionSize/(2.0*max(self.scatterWidth,self.scatterHeight))
        
        self.loadingImage = QPixmap(self.scatterWidth,self.scatterHeight)
        self.image = QPixmap(self.scatterWidth,self.scatterHeight)
        self.selectionOverlay = QPixmap(self.scatterWidth,self.scatterHeight)
        
        self.highlightColor = QColor.fromRgbF(1.0,0.0,0.0,0.5)
        self.selectedColor = QColor.fromRgbF(0.0,0.0,1.0,0.5)
        
        self.selectionRect = QRect(-selectionSize/2,-selectionSize/2,selectionSize,selectionSize)
        self.dot = QRect(-pointSize/2,-pointSize/2,pointSize,pointSize)
        
        self.mousex = 0
        self.mousey = 0
        
        self.setCursor(Qt.BlankCursor)
        
        self.dirty = True
        self.progress = 0
        self.currentXaxis = None
        self.currentYaxis = None
                
        self.drawingTimer = QTimer()
        self.drawingTimer.setSingleShot(True)
        self.connect(self.drawingTimer, SIGNAL("timeout()"), self.drawScatter)
        
        self.animationTimer = QTimer()
        self.animationTimer.setSingleShot(False)
        self.connect(self.animationTimer, SIGNAL("timeout()"), self.animate)
        self.animationTimer.start(25)
    
    def sizeHint(self):
        return QSize(self.scatterWidth, self.scatterHeight)
    
    def checkAxes(self):
        if self.currentXaxis != self.controller.currentXaxis or self.currentYaxis != self.controller.currentYaxis:
            self.currentXaxis = self.controller.currentXaxis
            self.currentYaxis = self.controller.currentYaxis
            self.dirty = True
            self.drawingTimer.start(50)
    
    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.dirty:
            painter.drawPixmap(0,0,self.loadingImage)
        else:
            painter.drawPixmap(0,0,self.image)
            painter.drawPixmap(0,0,self.selectionOverlay)
        painter.end()
    
    def animate(self):
        self.checkAxes()
        
        painter = QPainter()
        
        if self.dirty:
            self.loadingImage.fill(Qt.white)
            painter.begin(self.loadingImage)
            
            outText = "Loading"
            if self.progress >= 10:
                self.progress = 0
            for i in xrange(self.progress):
                outText += "."
            
            painter.drawText(0,0,self.width(),self.height(),Qt.AlignCenter | Qt.AlignHCenter,outText)
            
            painter.end()
        else:
            self.selectionOverlay.fill(Qt.transparent)
            painter.begin(self.selectionOverlay)
            
            for rsNumber in self.data.currentSelection.current:
                painter.save()
                x,y = self.transformDataCoordinates(self.data.getData(rsNumber,"CASES Allele Frequency"),self.data.getData(rsNumber,"CONTROLS Allele Frequency"))
                painter.translate(x,y)
                painter.fillRect(self.dot,self.selectedColor)
                painter.restore()
            
            painter.setPen(self.highlightColor)
            if self.underMouse():
                painter.save()
                painter.translate(self.mousex,self.mousey)
                painter.drawRect(self.selectionRect)
                painter.restore()
            
            for rsNumber in self.data.highlighted:
                painter.save()
                x,y = self.transformDataCoordinates(self.data.getData(rsNumber,"CASES Allele Frequency"),self.data.getData(rsNumber,"CONTROLS Allele Frequency"))
                painter.translate(x,y)
                painter.fillRect(self.dot,self.highlightColor)
                painter.restore()
            
            painter.end()
        self.update()
    
    def drawScatter(self):
        self.image.fill(Qt.white)
        
        painter = QPainter()
        painter.begin(self.image)
        
        #painter.setRenderHint(QPainter.Antialiasing)
        
        for y in xrange(self.scatterWidth):
            for x in xrange(self.scatterHeight):
                xVal,yVal = self.controller.transformScreenCoordinates(x,y)
                painter.setPen(self.getColor(xVal-self.pointRadius,yVal-self.pointRadius,xVal+self.pointRadius,yVal+self.pointRadius))
                painter.drawPoint(x,y)
        
        painter.end()
        
        self.dirty = False
    
    def getColor(self, x, y, x2, y2):
        population = self.controller.countPopulation(x,y,x2,y2)
        
        if population > self.lightnessSteps:
            return QColor.fromRgbF(0.0,0.0,0.0,1.0)
        else:
            alphaValue = population/self.lightnessSteps
            return QColor.fromRgbF(0.0,0.0,0.0,alphaValue)
    
    def mouseMoveEvent(self, event):
        self.mousex = event.x()
        self.mousey = event.y()
        
        '''self.handleEvent(event)
        
        if event.buttons() & Qt.LeftButton:
            self.data.currentSelection.add(temp)'''