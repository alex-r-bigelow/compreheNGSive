import math
from PySide.QtCore import *
from PySide.QtGui import *

class Axis:
    def __init__(self, name, queryObject):
        self.ranges = []    # list of tuples
        self.name = name
        self.hidden = False
        self.queryObject = queryObject

class ParallelCoordinates(QWidget):
    def __init__(self, parent = None, data = None, width = 500, height = 500, lineWidth = 1, lineSpacing = 100, selectionSize = 10):
        QWidget.__init__(self, parent)
        
        self.setWindowTitle(self.tr("parallelCoordinates.py"))
        
        self.setMouseTracking(True)
        
        self.axes = []  # will be drawn in this order
        for name,axis in data.axes.iteritems():
            self.axes.append(Axis(name,axis))
        
        self.scrollOffset = 0
        self.visibleIndices = []
        
        self.pcWidth = width
        self.pcHeight = height
        
        self.lineSpacing = lineSpacing
        self.lineWidth = lineWidth
        self.selectionSize = selectionSize
        
        self.selectionRadius = selectionSize/(2.0*max(self.pcWidth,self.pcHeight))
        
        self.loadingImage = QPixmap(self.pcWidth,self.pcHeight)
        self.image = QPixmap(self.pcWidth,self.pcHeight)
        self.selectionOverlay = QPixmap(self.pcWidth,self.pcHeight)
        
        self.highlightColor = QColor.fromRgbF(1.0,0.0,0.0,0.5)
        self.selectedColor = QColor.fromRgbF(0.0,0.0,1.0,0.5)
        
        self.selectionRect = QRect(-selectionSize/2,-selectionSize/2,selectionSize,selectionSize)
        
        self.mousex = 0
        self.mousey = 0
        
        self.setCursor(Qt.BlankCursor)
        
        self.dirty = True
        
        self.drawPC()
        
        #self.drawingTimer = QTimer()
        #self.drawingTimer.setSingleShot(True)
        #self.connect(self.drawingTimer, SIGNAL("timeout()"), self.drawPC)
        #self.drawingTimer.start(1000)
        
        self.animationTimer = QTimer()
        self.animationTimer.setSingleShot(False)
        self.connect(self.animationTimer, SIGNAL("timeout()"), self.animate)
        self.animationTimer.start(25)
    
    def sizeHint(self):
        return QSize(self.pcWidth, self.pcHeight)
    
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
        if self.width() != self.pcWidth or self.height() != self.pcHeight:
            # might still be resizing... try again a second later
            self.drawingTimer.stop()
            self.pcHeight = self.height()
            self.pcWidth = self.width()
            
            self.selectionRadius = self.selectionSize/(2.0*max(self.pcWidth,self.pcHeight))
            
            self.drawingTimer.start(1000)
            return False
        else:
            return True'''
    
    def drawPC(self):
        if True:#if self.checkSizes():
            #self.image = QPixmap(self.pcWidth,self.pcHeight)
            #self.selectionOverlay = QPixmap(self.pcWidth,self.pcHeight)
            self.image.fill(Qt.white)
            
            painter = QPainter()
            painter.begin(self.image)
            
            painter.setRenderHint(QPainter.Antialiasing)
            
            visIndex = self.scrollOffset
            axisIndex = self.scrollOffset
            self.visibleIndices = []
            while axisIndex < len(self.axes) and visIndex*self.lineSpacing <= self.pcWidth:
                if self.axes[axisIndex].hidden:
                    axisIndex += 1
                else:
                    painter.drawLine(visIndex*self.lineSpacing,0,visIndex*self.lineSpacing,self.pcHeight)
                    self.visibleIndices.append(axisIndex)
                    axisIndex += 1
                    visIndex += 1
            
            painter.end()
            self.dirty = False
    
    def animate(self):
        if self.dirty:
            self.loadingImage.fill(Qt.white)
            
            painter = QPainter()
            painter.begin(self.loadingImage)
            
            painter.drawText(0,0,self.width(),self.height(),Qt.AlignCenter | Qt.AlignHCenter,"Loading...")
            
            painter.end()
        else:
            self.selectionOverlay.fill(Qt.transparent)
            
            painter = QPainter()
            painter.begin(self.selectionOverlay)
            
            painter.setPen(self.selectedColor)
            for rsNumber in self.parent().selected:
                lastY = None
                for visIndex,axisIndex in enumerate(self.visibleIndices):
                    x = visIndex*self.lineSpacing
                    y = self.parent().data.getData(rsNumber,self.axes[axisIndex].name)
                    if y == None or math.isinf(y) or math.isnan(y):
                        y = 0
                    y = self.transformDataCoordinates(y)
                    if lastY != None:
                        painter.save()
                        painter.drawLine((visIndex-1)*self.lineSpacing,lastY,x,y)
                        painter.restore()
                    lastY = y
            
            painter.setPen(self.highlightColor)
            for rsNumber in self.parent().highlighted:
                lastY = None
                for visIndex,axisIndex in enumerate(self.visibleIndices):
                    x = visIndex*self.lineSpacing
                    y = self.parent().data.getData(rsNumber,self.axes[axisIndex].name)
                    if y == None or math.isinf(y) or math.isnan(y):
                        y = 0
                    y = self.transformDataCoordinates(y)
                    if lastY != None:
                        painter.save()
                        painter.drawLine((visIndex-1)*self.lineSpacing,lastY,x,y)
                        painter.restore()
                    lastY = y
            
            if self.underMouse():
                painter.save()
                painter.setPen(self.highlightColor)
                painter.translate(self.mousex,self.mousey)
                painter.drawRect(self.selectionRect)
                painter.restore()
            
            painter.end()
        self.update()
    
    def mouseMoveEvent(self, event):
        self.mousex = event.x()
        self.mousey = event.y()
        
        axis = self.findAxis(self.mousex)
        if axis != None:
            y = self.transformScreenCoordinates(self.mousey)
            temp = axis.queryObject.select(y-self.selectionRadius,y+self.selectionRadius)
            temp.intersection_update(self.parent().selected)
            self.parent().highlight(temp)
            
            #if event.buttons() & Qt.LeftButton:
                #self.parent().select(temp)
    
    def transformScreenCoordinates(self, y):
        y = y/float(self.pcHeight)
        
        return y
    
    def findAxis(self, x):
        if len(self.visibleIndices) > 0:
            i = x/float(self.pcWidth)
            i = int(math.floor(i*len(self.visibleIndices)))
            if abs(x-i*self.lineSpacing) <= self.selectionSize:
                return self.axes[i]
        return None
            
    
    def transformDataCoordinates(self, y):
        if y > 1.0 or y < 0.0:
            y = 0.5
        y = math.ceil(y*self.pcHeight)
        
        return y