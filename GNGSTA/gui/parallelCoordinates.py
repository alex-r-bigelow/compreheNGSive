from axes import pcAxis
from PySide.QtCore import *
from PySide.QtGui import *

class parallelCoordinates(QWidget):
    def __init__(self, controller, svg, parent = None, width = 500, height = 500, lineWidth = 1, lineSpacing = 50, selectionSize = 10):
        QWidget.__init__(self, parent)
        
        self.setWindowTitle(self.tr("parallelCoordinates.py"))
        
        self.setMouseTracking(True)
        
        self.controller = controller
        self.svg = svg
        
        self.scrollOffset = 0
        self.visibleIndices = []
        # TODO set these up
        
        self.pcWidth = width
        self.pcHeight = height
        
        self.lineSpacing = lineSpacing
        self.lineWidth = lineWidth
        self.selectionSize = selectionSize
        
        self.selectionRadius = selectionSize/(2.0*max(self.pcWidth,self.pcHeight))
        
        self.loadingImage = QPixmap(self.pcWidth,self.pcHeight)
        self.selectionImage = QPixmap(self.pcWidth,self.pcHeight)
        
        self.highlightColor = QColor.fromRgbF(1.0,0.0,0.0,0.5)
        self.selectedColor = QColor.fromRgbF(0.0,0.0,1.0,0.5)
        
        self.selectionRect = QRect(-selectionSize/2,-selectionSize/2,selectionSize,selectionSize)
        
        self.mousex = 0
        self.mousey = 0
        
        self.setCursor(Qt.BlankCursor)
        
        self.dirty = False
        
        self.animationTimer = QTimer()
        self.animationTimer.setSingleShot(False)
        self.connect(self.animationTimer, SIGNAL("timeout()"), self.animate)
        self.animationTimer.start(25)
    
    def getNumberClone(self, xOffset=None, yOffset=None):
        return self.svg("axis").clone(xOffset, yOffset)
    
    def sizeHint(self):
        return QSize(self.pcWidth, self.pcHeight)
    
    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.dirty:
            painter.drawPixmap(0,0,self.loadingImage)
        else:
            painter.drawPixmap(0,0,self.selectionImage)
        painter.end()
    
    def animate(self):
        if self.dirty:
            self.loadingImage.fill(Qt.white)
            
            painter = QPainter()
            painter.begin(self.loadingImage)
            
            painter.drawText(0,0,self.width(),self.height(),Qt.AlignCenter | Qt.AlignHCenter,"Loading...")
            
            painter.end()
        else:
            self.selectionImage.fill(Qt.transparent)
            
            painter = QPainter()
            painter.begin(self.selectionImage)
            
            painter.setRenderHint(QPainter.Antialiasing)
            
            painter.setPen(self.selectedColor)
            selected = self.controller.getSelected()
            lastYs = None
            lastX = None
            
            for visIndex,axisIndex in enumerate(self.visibleIndices):
                x = visIndex*self.lineSpacing
                lastYs = self.axes[axisIndex].draw(painter,selected,lastX,x,lastYs)
                lastX = x
            
            painter.setPen(self.highlightColor)
            highlighted = self.controller.getHighlighted()
            lastYs = None
            lastX = None
            
            for visIndex,axisIndex in enumerate(self.visibleIndices):
                x = visIndex*self.lineSpacing
                lastYs = self.axes[axisIndex].draw(painter,highlighted,lastX,x,lastYs)
                lastX = x
            
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
            action = axis.handleEvent(event)
            # TODO: highlight moused-over items, etc
    
    def findAxis(self, x):
        if len(self.visibleIndices) > 0:
            i = x/float(self.pcWidth)
            i = int(math.floor(i*len(self.visibleIndices)))
            if abs(x-i*self.lineSpacing) <= self.controller.axes[i].pixelWidth/2:
                return self.controller.axes[i]
        return None