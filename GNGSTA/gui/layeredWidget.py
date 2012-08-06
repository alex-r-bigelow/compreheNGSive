from gui.mutableSvg import mutableSvgRenderer
from PySide.QtCore import *
from PySide.QtGui import *
import time

class SvgLayerException(Exception):
    def __init__(self, value):
        self.value = "\n" + value
    def __str__(self):
        return self.value

class layer:
    def __init__(self, size, dynamic):
        self.size = size
        self.image = QPixmap(size)
        self.dynamic = dynamic
        self.dirtyLayer = True
        self.resized = False
    
    def drawLayer(self):
        self.image.fill(QColor.fromRgbF(0.0,0.0,0.0,0.0))
        painter = QPainter()
        painter.begin(self.image)
        
        self.draw(painter)
        
        painter.end()
        self.dirtyLayer = False
    
    def setDirty(self):
        self.dirtyLayer = True
    
    def resize(self, size):
        self.size = size
        self.image = QPixmap(size)
        self.dirtyLayer = True
        self.resized = True
    
    # Optionally override this
    def resizeEvent(self):
        pass
    
    # Override this
    def handleFrame(self, event, signals):
        raise NotImplementedError("You should never directly instantiate a layer, and all subclasses must implement the handleFrame(event,signals) method.")
    
    # Override this
    def draw(self, painter):
        raise NotImplementedError("You should never directly instantiate a layer, and all subclasses must implement the draw(painter) method.")

class mutableSvgLayer(layer):
    def __init__(self, path, controller, size=None, dynamic=True):
        self.svg = mutableSvgRenderer(path, controller)
        
        if size == None:
            temp = self.svg.getBoundaries()
            size = temp.size().toSize()
        
        layer.__init__(self, size, dynamic)
    
    def resize(self, size):
        self.svg.forceFreeze()
        layer.resize(self, size)
    
    def handleFrame(self, event, signals):
        result = self.svg.handleFrame(event, results=signals)
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
        self.deltaWheel = 0
        self.buttons = set()
        self.lastButtons = set()
        self.keys = set()
        self.lastKeys = set()
        self.contextRequested = False
        self.retainWheelFocus = False
    
    def moveMouse(self, x, y):
        if self.x != -1:    # and self.y != -1... but they'll always go together
            self.deltaX += x-self.x
            self.deltaY += y-self.y
        self.x = x
        self.y = y
    
    def prepForNextFrame(self):
        self.deltaX = 0
        self.deltaY = 0
        self.deltaWheel = 0
        self.lastButtons = set(self.buttons)    # copy each set
        self.lastKeys = set(self.keys)
        self.contextRequested = False

class layeredWidget(QWidget):
    '''
    This abstracts away much of the Qt drawing and event
    components; subclasses should call addLayer and pass
    in their own instances that are subclasses of layer.
    Layers will be drawn in the order that they are
    created. A layer can be dynamic or static; a dynamic
    layer will be continually redrawn, while a static
    layer will only be redrawn if it is resized or its
    setDirty() function is called. Layers that can be
    drawn quickly should be dynamic, but if it takes
    longer than approximately a second to draw, the layer
    should be static.
    '''
    
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.loadingImage = QPixmap(QSize(1,1))
        self.loadingImage.fill(QColor.fromRgbF(0.0,0.0,0.0,0.0))
        self.loadingMode = False
        self.layers = []
                
        self.userState = eventPacket()
        self.setMouseTracking(True)
        
        self.drawingTimer = QTimer()
        self.drawingTimer.setSingleShot(True)
        
        self.animationTimer = QTimer()
        self.animationTimer.setSingleShot(False)
        
        # an ugly way to force this to work (sometimes connecting fails... sometimes even with a runtime error)
        
        failureCount = 0
        success = False
        #while not success:
        #    try:
        success = self.drawingTimer.timeout.connect(self.drawStatic)
        #    except RuntimeError:
        #        success = False
        #    if not success:
        #        failureCount += 1
        #        if failureCount > 100:
        #            raise RuntimeError("Sorry, a rendering error occurred, and I couldn't recover... this is a known bug that should be fixed soon.\n"+
        #                               "You should be able to just run the program again.")
        
        failureCount = 0
        success = False
        #while not success:
        #    try:
        success = self.animationTimer.timeout.connect(self.animate)
        #    except RuntimeError:
        #        success = False
        #    if not success:
        #        failureCount += 1
        #        if failureCount > 100:
        #            raise RuntimeError("Sorry, a rendering error occurred, and I couldn't recover... this is a known bug that should be fixed soon.\n"+
        #                               "You should be able to just run the program again.")
        
        self.animationTimer.start(100)
        
        self.setDirty()
    
    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        #if self.isDirty:
        #    painter.drawPixmap(0,0,self.loadingImage)
        #else:
        for l in self.layers:
            painter.drawPixmap(0,0,l.image)
        painter.end()
    
    def setDirty(self):
        self.isDirty = True
        self.drawingTimer.start(100)
    
    def animate(self):
        if self.isDirty or len(self.layers) == 0:
            # TODO: keep flattened version of everything in self.loadingImage to get rid of the blink
            '''painter = QPainter()
            
            if self.parentWidget() != 0:
                self.loadingImage = QPixmap(self.parentWidget().size())
            else:
                self.loadingImage = QPixmap(self.size())
            
            self.loadingImage.fill(QColor.fromRgbF(0.0,0.0,0.0,1.0))
            painter.begin(self.loadingImage)
            
            if len(self.layers) == 0:
                outText = "Nothing to draw."
            else:
                outText = "Loading"
                for i in xrange(self.progress):
                    outText += "."
            
            painter.setPen(QColor.fromRgbF(1.0,1.0,1.0,1.0))
            painter.drawText(0,0,self.loadingImage.width(),self.loadingImage.height(),Qt.AlignCenter | Qt.AlignHCenter,outText)
            
            painter.end()'''
            pass
        else:
            eventResults = {'__EVENT__ABSORBED__':not self.underMouse()}
            for l in self.layers:
                if not eventResults.get('__EVENT__ABSORBED__',True):
                    eventResults.update(l.handleFrame(self.userState,signals=eventResults))
                if l.dynamic and not l.resized:
                    l.drawLayer()
                elif l.dirtyLayer or l.resized:
                    self.setDirty()
            if eventResults.get('__EVENT__ABSORBED__',True):
                if eventResults.has_key('__EVENT__ABSORBED__'):
                    del eventResults['__EVENT__ABSORBED__']
                self.handleEvents(self.userState,eventResults)
            self.userState.prepForNextFrame()
        self.update()
    
    def handleEvents(self, event, signals):
        raise NotImplementedError("You should never directly instantiate a layeredWidget, and all subclasses must implement the handleEvents(event, signals) method.")
    
    def drawStatic(self):
        lowX = None
        lowY = None
        highX = None
        highY = None
        rects = []
        
        #if self.parentWidget() != 0:
        #    rects.append(self.parentWidget().rect())
        for l in self.layers:
            rects.append(l.image.rect())
            l.resized = False
        
        for r in rects:
            lx,ly,hx,hy = r.getCoords()
            if lowX == None:
                lowX = lx
            else:
                lowX = min(lowX,lx)
            if lowY == None:
                lowY = ly
            else:
                lowY = min(lowY,ly)
            if highX == None:
                highX = hx
            else:
                highX = max(highX,hx)
            if highY == None:
                highY = hy
            else:
                highY = max(highY,hy)
        if lowX != None and lowY != None and highX != None and highY != None:
            newSize = QSize(highX-lowX,highY-lowY)
            self.setFixedSize(newSize)
        else:
            pass # TODO
        
        for l in self.layers:
            if not l.dynamic and l.dirtyLayer:
                l.drawLayer()
        self.isDirty = False
        
    def addLayer(self, newLayer, index=None):
        if index == None:
            self.layers.append(newLayer)
        else:
            self.layers.insert(index, newLayer)
    
    def setLayer(self, newLayer, index=None):
        if index == None:
            if len(self.layers) == 0:
                self.addLayer(newLayer)
            else:
                self.layers[len(self.layers)-1] = newLayer
        else:
            self.layers[index] = newLayer
    
    def clearAllLayers(self):
        self.layers = []
    
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
    
    def contextMenuEvent(self,event):
        self.userState.contextRequested = True
    
    def wheelEvent(self, event):
        self.userState.deltaWheel += event.delta()
        if not self.userState.retainWheelFocus:
            event.ignore()
