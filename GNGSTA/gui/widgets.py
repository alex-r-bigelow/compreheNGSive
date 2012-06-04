from svgHelpers import SvgWrapper
from PySide.QtCore import *
from PySide.QtGui import *

class customSvgWidget(QWidget):
    '''
    An abstract widget that utilizes svg elements to draw itself (the svg parameter can accept
    both a path (str) or an SvgWrapper object). This abstracts away much of the Qt drawing
    components; subclasses should call addLayer and pass in their own draw functions (that
    accept a QPainter object as a parameter). Layers will be drawn in the order that they are
    created. A layer can be dynamic or static; a dynamic layer will be continually redrawn,
    while a static layer will only be redrawn if it is resized or its setDirty() function is
    called. Layers that can be drawn quickly should be dynamic, but if it takes longer than
    approximately a second to draw, the layer should be static (and a "loading" screen
    will be drawn while it is updating).
    '''
    def __init__(self, svg, bounds = None, title = "Custom SVG Widget", parent = None):
        QWidget.__init__(self, parent)
        self.controller = None
        
        self.setWindowTitle(self.tr(title))
        
        if isinstance(svg,str):
            svg = SvgWrapper(svg)
        self.svg = svg
        
        self.setMouseTracking()
        
        if bounds == None:
            self.bounds = svg.getBounds()
        else:
            self.bounds = bounds
        self.setFixedSize(self.bounds.width(),self.bounds.height())
                
        self.loadingImage = QPixmap(self.bounds.size().toSize())
        self.layers = []
        
        self.dirty = True
        self.progress = 0
        
        self.drawingTimer = QTimer()
        self.drawingTimer.setSingleShot(True)
        self.connect(self.drawingTimer, SIGNAL("timeout()"), self.drawStatic)
        self.setDirty()
        
        self.animationTimer = QTimer()
        self.animationTimer.setSingleShot(False)
        self.connect(self.animationTimer, SIGNAL("timeout()"), self.animate)
        self.animationTimer.start(25)
    
    def bindController(self, controller):
        self.controller = controller
    
    def sizeHint(self):
        return self.bounds.size().toSize()
    
    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.dirty:
            painter.drawPixmap(0,0,self.loadingImage)
        else:
            for l in self.layers:
                painter.drawPixmap(0,0,l.image)
        painter.end()
    
    def setDirty(self):
        self.dirty = True
        self.drawingTimer.start(25)
    
    def animate(self):
        if self.dirty:
            painter = QPainter()
            
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
            for layer in self.layers:
                if layer.dynamic:
                    layer.draw()
                elif layer.dirty:
                    self.setDirty()
    
    def drawStatic(self):
        for layer in self.layers:
            if not layer.dynamic and layer.dirty:
                layer.draw()
        self.dirty = False
    
    def addLayer(self, drawFunction, size=None, dynamic=False, index=None):
        if size == None:
            size = self.bounds.size().toSize()
        
        newLayer = customSvgWidget.layer(size,drawFunction,dynamic)
        if index == None:
            self.layers.append(newLayer)
        else:
            self.layers.insert(index, newLayer)
        return newLayer
    
    class layer:
        def __init__(self, size, drawFunction, dynamic):
            self.image = QPixmap(size)
            self.drawFunction = drawFunction
            self.dynamic = dynamic
            self.dirty = True
        
        def resize(self, size):
            self.image = QPixmap(size)
            self.dirty = True
        
        def draw(self):
            painter = QPainter()
            painter.begin(self.image)
            
            self.drawFunction(painter)
            
            painter.end()
            self.dirty = False
        
        def setDirty(self):
            self.dirty = True
    
    # TODO: add events that are forwarded to the controller if it exists... for now the controller has to
    # figure out what was clicked, etc but maybe I should generate these from the SVG attributes?
    
    #def mouseMoveEvent(self, event):
    #    self.controller.mouseMoveEvent(event)

class scatterPlot(customSvgWidget):
    def __init__(self, svg, bounds = None, title = "Scatter Plot", parent = None):
        customSvgWidget.__init__(self, svg, bounds, title, parent)
        
        self.backgroundColor = QColor.fromRgbF(1.0,1.0,1.0,0.75)  # TODO: get this from SVG as well
        
        self.backgroundLayer = self.addLayer(self.drawBackground,dynamic=False)
    
    def drawBackground(self, painter):
        width,height = self.sizeHint().toTuple()
        painter.fillRect(0,0,width,height,self.backgroundColor)

class parallelCoordinates(customSvgWidget):
    def __init__(self, svg, bounds = None, title = "Parallel Coordinates", parent = None):
        customSvgWidget.__init__(self, svg, bounds, title, parent)
        
        self.selectionColor = QColor.fromRgbF(0.0,0.0,1.0,1.0)  # TODO: get this from SVG as well
        self.highlightColor = QColor.fromRgbF(1.0,1.0,0.0,1.0)  # TODO: get this from SVG as well
        
        self.selectionLayer = self.addLayer(self.drawSelection,dynamic=False)
        self.highlightedLayer = self.addLayer(self.drawHighlighted,dynamic=True)
        self.axisLayer = self.addLayer(self.drawAxes,dynamic=True)
        
        self.visibleAxes = []
        self.axisWidth = self.svg.getBounds("numberAxis").width()
    
    def drawSelection(self, painter):
        painter.save()
        
        painter.setPen(self.selectionColor)
        
        rsNumbers = self.controller.getSelected()
        lastYs = None
        x = self.axisWidth/2
        lastX = x
        for att,ax in self.visibleAxes:
            myYs = self.controller.getPoints(att,rsNumbers)
            if lastYs != None:
                for i,rs in enumerate(rsNumbers):
                    for lastY in lastYs[i]:
                        for y in myYs[i]:
                            painter.drawLine(lastX,lastY,x,y)
            lastYs = myYs
            lastX = x
            x += self.axisWidth
        
        painter.restore()
    
    def drawHighlighted(self, painter):
        painter.save()
        
        painter.setPen(self.highlightColor)
        
        rsNumbers = self.controller.getHighlighted()
        lastYs = None
        x = self.axisWidth/2
        lastX = x
        for att,ax in self.visibleAxes:
            myYs = self.controller.getPoints(att,rsNumbers)
            if lastYs != None:
                for i,rs in enumerate(rsNumbers):
                    for lastY in lastYs[i]:
                        for y in myYs[i]:
                            painter.drawLine(lastX,lastY,x,y)
            lastYs = myYs
            lastX = x
            x += self.axisWidth
        
        painter.restore()
    
    def drawAxes(self, painter):
        for label,axis in self.visibleAxes:
            axis.draw(painter)
    
    def addAxis(self, label, type="number"):
        xOffset = self.axisWidth * len(self.visibleAxes)
        yOffset = 0
        if type == "number":
            temp = self.svg.getElement("numberAxis").clone(xOffset,yOffset)
        elif type == "string":
            temp = self.svg.getElement("stringAxis").clone(xOffset,yOffset)
        elif type == "genome":
            temp = self.svg.getElement("genomeAxis").clone(xOffset,yOffset)
        
        screenLabel = label
        if len(screenLabel) > 14:
            screenLabel = screenLabel[:8] + "..." + screenLabel[-3:]
        temp.setText(screenLabel,"label")
                
        self.visibleAxes.append((label,temp))
        self.updateSize()
        
        visArgs = {"pixelWidth":self.axisWidth,"pixelLow":temp.getBounds("low").top(),"pixelHigh":temp.getBounds("high").bottom(),"missingPixelY":temp.getBounds("missing").center().y(),"maskedPixelY":temp.getBounds("masked").center().y()}
        return visArgs
    
    def updateSize(self):
        newWidth = len(self.visibleAxes)*self.axisWidth
        
        self.setFixedWidth(newWidth)
        self.selectionLayer.resize(QSize(newWidth,self.rect().height()))
        self.highlightedLayer.resize(QSize(newWidth,self.rect().height()))
        self.axisLayer.resize(QSize(newWidth,self.rect().height()))
    
    def hideAxis(self, index):
        del self.visibleAxes[index]
        self.updateSize()

class rsList(customSvgWidget):
    def __init__(self, svg, bounds = None, title = "RS Number List", parent = None):
        customSvgWidget.__init__(self, svg, bounds, title, parent)
        
        self.backgroundColor = QColor.fromRgbF(1.0,1.0,1.0,0.75)  # TODO: get this from SVG as well
        
        self.backgroundLayer = self.addLayer(self.drawBackground,dynamic=False)
    
    def drawBackground(self, painter):
        width,height = self.sizeHint().toTuple()
        painter.fillRect(0,0,width,height,self.backgroundColor)

class selectionManager(customSvgWidget):
    def __init__(self, svg, bounds = None, title = "Selection Manager", parent = None):
        customSvgWidget.__init__(self, svg, bounds, title, parent)
        
        self.backgroundColor = QColor.fromRgbF(1.0,1.0,1.0,0.75)  # TODO: get this from SVG as well
        
        self.backgroundLayer = self.addLayer(self.drawBackground,dynamic=False)
    
    def drawBackground(self, painter):
        width,height = self.sizeHint().toTuple()
        painter.fillRect(0,0,width,height,self.backgroundColor)

class genomeBrowser(customSvgWidget):
    def __init__(self, svg, bounds = None, title = "Genome Browser", parent = None):
        customSvgWidget.__init__(self, svg, bounds, title, parent)
        
        self.backgroundColor = QColor.fromRgbF(1.0,1.0,1.0,0.75)  # TODO: get this from SVG as well
        
        self.backgroundLayer = self.addLayer(self.drawBackground,dynamic=False)
    
    def drawBackground(self, painter):
        width,height = self.sizeHint().toTuple()
        painter.fillRect(0,0,width,height,self.backgroundColor)



    