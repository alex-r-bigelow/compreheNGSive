import math
from PySide.QtCore import *
from PySide.QtGui import *

class ScatterPlot(QWidget):
    def __init__(self, parent = None, data = None, width = 500, height = 500, pointSize = 5, lighnessSteps = 5, selectionSize = 10):
        QWidget.__init__(self, parent)
        
        self.setWindowTitle(self.tr("scatterplot.py"))
        
        self.setMouseTracking(True)
        
        self.data = data
        
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
                
        self.drawingTimer = QTimer()
        self.drawingTimer.setSingleShot(True)
        self.connect(self.drawingTimer, SIGNAL("timeout()"), self.drawScatter)
        self.drawingTimer.start(100)
        
        self.animationTimer = QTimer()
        self.animationTimer.setSingleShot(False)
        self.connect(self.animationTimer, SIGNAL("timeout()"), self.animate)
        self.animationTimer.start(25)
    
    def sizeHint(self):
        return QSize(self.scatterWidth, self.scatterHeight)
    
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
    
    '''def resizeEvent(self, event):
        self.drawingTimer.stop()
        self.dirty = True
        self.drawingTimer.start(1000)
        
    def checkSizes(self):
        if self.width() != self.scatterWidth or self.height() != self.scatterHeight:
            # might still be resizing... try again a second later
            self.drawingTimer.stop()
            self.scatterHeight = self.height()
            self.scatterWidth = self.width()
            
            self.pointRadius = self.pointSize/(2.0*max(self.scatterWidth,self.scatterHeight))
            self.selectionRadius = self.selectionSize/(2.0*max(self.scatterWidth,self.scatterHeight))
            
            self.drawingTimer.start(1000)
            return False
        else:
            return True'''
    
    def drawScatter(self):
        #if self.checkSizes():
        #self.image = QPixmap(self.scatterWidth,self.scatterHeight)
        #self.selectionOverlay = QPixmap(self.scatterWidth,self.scatterHeight)
        self.image.fill(Qt.white)
        
        painter = QPainter()
        painter.begin(self.image)
        
        #painter.setRenderHint(QPainter.Antialiasing)
        
        for y in xrange(self.scatterWidth):
            for x in xrange(self.scatterHeight):
                xVal,yVal = self.transformScreenCoordinates(x,y)
                painter.setPen(self.getColor(xVal-self.pointRadius,yVal-self.pointRadius,xVal+self.pointRadius,yVal+self.pointRadius))
                painter.drawPoint(x,y)
        
        painter.end()
        
        # that probably took a while... if by chance they resized again while we weren't looking, we'll have to do this again
        #if self.checkSizes():
        self.dirty = False
    
    def animate(self):
        painter = QPainter()
        if self.dirty:
            self.loadingImage.fill(Qt.white)
            painter.begin(self.loadingImage)
            
            painter.drawText(0,0,self.width(),self.height(),Qt.AlignCenter | Qt.AlignHCenter,"Loading...")
            
            painter.end()
        else:
            self.selectionOverlay.fill(Qt.transparent)
            painter.begin(self.selectionOverlay)
            
            for rsNumber in self.parent().selected:
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
            
            for rsNumber in self.parent().highlighted:
                painter.save()
                x,y = self.transformDataCoordinates(self.data.getData(rsNumber,"CASES Allele Frequency"),self.data.getData(rsNumber,"CONTROLS Allele Frequency"))
                painter.translate(x,y)
                painter.fillRect(self.dot,self.highlightColor)
                painter.restore()
            
            painter.end()
        self.update()
    
    def getColor(self, x, y, x2, y2):
        population = self.data.scatter.countPopulation(x,y,x2,y2)
        
        if population > self.lightnessSteps:
            return QColor.fromRgbF(0.0,0.0,0.0,1.0)
        else:
            alphaValue = population/self.lightnessSteps
            return QColor.fromRgbF(0.0,0.0,0.0,alphaValue)
    
    def mouseMoveEvent(self, event):
        self.mousex = event.x()
        self.mousey = event.y()
        
        x,y = self.transformScreenCoordinates(self.mousex, self.mousey)
        temp = self.data.scatter.select(x-self.selectionRadius,y-self.selectionRadius,x+self.selectionRadius,y+self.selectionRadius)
        self.parent().highlight(temp)
        
        if event.buttons() & Qt.LeftButton:
            self.parent().select(temp)
    
    def transformScreenCoordinates(self, x, y):
        x = x/float(self.scatterWidth)
        y = y/float(self.scatterHeight)
        
        return (x,y)
    
    def transformDataCoordinates(self, x, y):
        if x < 0.0 or x > 1.0:
            x = 0.5
        if y < 0.0 or y > 1.0:
            y = 0.5
        x = math.ceil(x*self.scatterWidth)
        y = math.ceil(y*self.scatterHeight)
        
        return (x,y)