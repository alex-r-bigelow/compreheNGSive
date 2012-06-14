from svgHelpers import SvgWrapper
from PySide.QtCore import *
from PySide.QtGui import *

class layer:
    def __init__(self, size, dynamic):
        self.image = QPixmap(size)
        self.dynamic = dynamic
        self.dirtyLayer = True
    
    def drawLayer(self):
        self.image.fill(QColor.fromRgbF(0.0,0.0,0.0,0.0))
        painter = QPainter()
        painter.begin(self.image)
        
        self.draw(painter)
        
        painter.end()
        self.dirtyLayer = False
    
    def setDirty(self):
        self.dirtyLayer = True
    
    # Override this
    def resize(self, size):
        self.image = QPixmap(size)
        self.dirtyLayer = True
    
    # Override this
    def handleFrame(self, event):
        return None
    
    # Override this
    def draw(self, painter):
        return None

class mutableSvgLayer(layer):
    def __init__(self, mutableSvg, size=None, dynamic=True):
        self.svg = mutableSvg
        
        if size == None:
            temp = self.svg.getBoundaries()
            size = temp.size().toSize()
        
        layer.__init__(self, size, dynamic)
        #self.setFixedSize(self.bounds.width(),self.bounds.height())
    
    def handleFrame(self, event):
        result = self.svg.handleFrame(event)
        if not self.svg.isFrozen:
            self.setDirty()
        return result
    
    def draw(self,painter,queryString=None):
        self.svg.render(painter,queryString)

class eventPacket:
    def __init__(self):
        self.x = -1
        self.y = -1
        self.deltaX = 0
        self.deltaY = 0
        self.buttons = set()
        self.keys = set()
    
    def moveMouse(self, x, y):
        if self.x != -1:    # and self.y != -1... but they'll always go together
            self.deltaX += x-self.x
            self.deltaY += y-self.y
        self.x = x
        self.y = y

class layeredWidget(QWidget):
    '''
    This abstracts away much of the Qt drawing and userState
    components; subclasses should call addLayer and pass
    in their own instances that are subclasses of layer.
    Layers will be drawn in the order that they are
    created. A layer can be dynamic or static; a dynamic
    layer will be continually redrawn, while a static
    layer will only be redrawn if it is resized or its
    setDirty() function is called. Layers that can be
    drawn quickly should be dynamic, but if it takes
    longer than approximately a second to draw, the layer
    should be static (and a "loading" screen will be
    drawn while it is updating).
    If desired, a
    controller object should be supplied to accept
    an abstract userState array. The userState array will
    contain an object for every existing layer (in the
    same order from bottom to top) that represents the
    results of the events on that layer (subclasses of
    layer should generate these objects).
    '''
    
    def __init__(self, title = "Abstract Layered Widget", parent = None, controller = None):
        QWidget.__init__(self, parent)
        self.setWindowTitle(self.tr(title))
        
        self.loadingImage = QPixmap(self.size())
        self.layers = []
        
        self.controller = controller
        
        self.userState = eventPacket()
        self.setMouseTracking(True)
        
        self.drawingTimer = QTimer()
        self.drawingTimer.setSingleShot(True)
        self.connect(self.drawingTimer, SIGNAL("timeout()"), self.drawStatic)
        
        self.animationTimer = QTimer()
        self.animationTimer.setSingleShot(False)
        self.connect(self.animationTimer, SIGNAL("timeout()"), self.animate)
        self.animationTimer.start(25)
        
        self.progress = 0
        self.progressTimer = QTimer()
        self.progressTimer.setSingleShot(False)
        self.connect(self.progressTimer, SIGNAL("timeout()"), self.incrementProgress)
        self.progressTimer.setInterval(10000000)
        self.progressTimer.start(25)
        
        self.setDirty()
    
    def sizeHint(self):
        return self.bounds.size().toSize()
    
    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.isDirty:
            painter.drawPixmap(0,0,self.loadingImage)
        else:
            for l in self.layers:
                painter.drawPixmap(0,0,l.image)
        painter.end()
    
    def resizeEvent(self, event):
        self.loadingImage = QPixmap(self.size())
        for l in self.layers:
            l.resize(self.size())
    
    def setDirty(self):
        self.isDirty = True
        self.drawingTimer.start(25)
        self.progressTimer.start(50)
    
    def animate(self):
        if self.isDirty or len(self.layers) == 0:
            painter = QPainter()
            
            self.loadingImage.fill(QColor.fromRgbF(0.0,0.0,0.0,0.5))
            painter.begin(self.loadingImage)
            
            if len(self.layers) == 0:
                outText = "Nothing to draw."
            else:
                outText = "Loading"
                for i in xrange(self.progress):
                    outText += "."
            
            painter.setPen(QColor.fromRgbF(1.0,1.0,1.0,1.0))
            painter.drawText(0,0,self.width(),self.height(),Qt.AlignCenter | Qt.AlignHCenter,outText)
            
            painter.end()
        else:
            eventResults = []
            for l in self.layers:
                eventResults.append(l.handleFrame(self.userState))
                if l.dynamic:
                    l.drawLayer()
                elif l.dirtyLayer:
                    self.setDirty()
            self.userState.deltaX = 0
            self.userState.deltaY = 0
            if self.controller != None:
                self.controller.handleEvents(eventResults)
        self.update()
    
    def incrementProgress(self):
        self.progress += 1
        if self.progress > 10:
            self.progress = 0
    
    def drawStatic(self):
        for layer in self.layers:
            if not layer.dynamic and layer.dirtyLayer:
                layer.drawLayer()
        self.isDirty = False
        self.progressTimer.stop()
    
    def addLayer(self, newLayer, index=None):
        if index == None:
            self.layers.append(newLayer)
        else:
            self.layers.insert(index, newLayer)
        
    def mouseMoveEvent(self, event):
        self.userState.moveMouse(event.x(),event.y())
    
    def mousePressEvent(self, event):
        #self.userState.moveMouse(event.x(),event.y())
        self.userState.buttons.add(event.button().name)
    
    def mouseReleaseEvent(self, event):
        #self.userState.moveMouse(event.x(),event.y())
        self.userState.buttons.discard(event.button().name)
    
    def keyPressEvent(self,event):
        # TODO: store string representations of keys, not just their numbers!
        self.userState.keys.add(event.key())
    
    def keyReleaseEvent(self,event):
        self.userState.keys.discard(event.key())
