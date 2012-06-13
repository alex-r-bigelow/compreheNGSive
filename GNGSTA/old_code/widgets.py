    

class scatterPlot(layeredWidget):
    def __init__(self, svg, bounds = None, title = "Scatter Plot", parent = None):
        layeredWidget.__init__(self, svg, bounds, title, parent)
        
        self.backgroundColor = QColor.fromRgbF(1.0,1.0,1.0,0.75)  # TODO: get this from SVG as well
        
        self.backgroundLayer = self.addLayer(self.drawBackground,dynamic=False)
    
    def drawBackground(self, painter):
        width,height = self.sizeHint().toTuple()
        painter.fillRect(0,0,width,height,self.backgroundColor)

class parallelCoordinates(layeredWidget):
    def __init__(self, svg, bounds = None, title = "Parallel Coordinates", parent = None):
        layeredWidget.__init__(self, svg, bounds, title, parent)
        
        self.setMouseTracking(True)
        
        self.selectionColor = QColor.fromRgbF(0.0,0.0,1.0,1.0)  # TODO: get this from SVG as well
        self.highlightColor = QColor.fromRgbF(1.0,1.0,0.0,1.0)  # TODO: get this from SVG as well
        
        self.selectionLayer = self.addLayer(self.drawSelection,dynamic=False)
        self.highlightedLayer = self.addLayer(self.drawHighlighted,dynamic=True)
        self.axisLayer = self.addLayer(self.drawAxes,dynamic=True)
        
        self.visibleAxes = []
        self.axisWidth = self.svg.getBounds("numberAxis").width()
        
        self.isStub = False
    
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

class rsList(layeredWidget):
    def __init__(self, svg, bounds = None, title = "RS Number List", parent = None):
        layeredWidget.__init__(self, svg, bounds, title, parent)
        
        self.backgroundColor = QColor.fromRgbF(1.0,1.0,1.0,0.75)  # TODO: get this from SVG as well
        
        self.backgroundLayer = self.addLayer(self.drawBackground,dynamic=False)
    
    def drawBackground(self, painter):
        width,height = self.sizeHint().toTuple()
        painter.fillRect(0,0,width,height,self.backgroundColor)

class selectionManager(layeredWidget):
    def __init__(self, svg, bounds = None, title = "Selection Manager", parent = None):
        layeredWidget.__init__(self, svg, bounds, title, parent)
        
        self.backgroundColor = QColor.fromRgbF(1.0,1.0,1.0,0.75)  # TODO: get this from SVG as well
        
        self.backgroundLayer = self.addLayer(self.drawBackground,dynamic=False)
    
    def drawBackground(self, painter):
        width,height = self.sizeHint().toTuple()
        painter.fillRect(0,0,width,height,self.backgroundColor)

class genomeBrowser(layeredWidget):
    def __init__(self, svg, bounds = None, title = "Genome Browser", parent = None):
        layeredWidget.__init__(self, svg, bounds, title, parent)
        
        self.backgroundColor = QColor.fromRgbF(1.0,1.0,1.0,0.75)  # TODO: get this from SVG as well
        
        self.backgroundLayer = self.addLayer(self.drawBackground,dynamic=False)
    
    def drawBackground(self, painter):
        width,height = self.sizeHint().toTuple()
        painter.fillRect(0,0,width,height,self.backgroundColor)



    