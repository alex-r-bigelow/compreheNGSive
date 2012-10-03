from layeredWidget import mutableSvgLayer, layeredWidget, layer
from resources.generalUtils import fitInSevenChars
from dataModels.variantData import operation
from PySide.QtCore import Qt,QSize
from PySide.QtGui import QColor, QCursor
import math

class rasterLayer(layer):
    def __init__(self, size, dynamic, controller):
        layer.__init__(self,size,dynamic)
        self.controller = controller
        self.ready = False
        
        dotColor = QColor()
        dotColor.setNamedColor(self.controller.svgLayer.svg.dotPrototype.getAttribute('fill'))
        dotColor.setAlphaF(float(self.controller.svgLayer.svg.dotPrototype.getAttribute('fill-opacity')))
        self.dotColors = []
        i = 0
        while i <= 1.0:
            self.dotColors.append(QColor.fromRgbF(dotColor.redF(),dotColor.greenF(),dotColor.blueF(),i))
            i += dotColor.alphaF()
        
        self.dotWidth = self.controller.svgLayer.svg.dotPrototype.width()
        self.dotHeight = self.controller.svgLayer.svg.dotPrototype.height()
        
        self.halfDotWidth = self.dotWidth/2
        self.halfDotHeight = self.dotHeight/2
        
        self.xoffset = self.controller.scatterBounds[0]-self.halfDotWidth
        self.yoffset = self.controller.scatterBounds[3]-self.halfDotHeight
        
        self.xNonNumeric = (self.controller.svgLayer.svg.xNonNumericIcon.left() + self.controller.svgLayer.svg.xNonNumericIcon.right())/2 - self.halfDotWidth
        self.yNonNumeric = (self.controller.svgLayer.svg.yNonNumericIcon.top() + self.controller.svgLayer.svg.yNonNumericIcon.bottom())/2 - self.halfDotHeight
    
    def setup(self):
        self.xIncrement = self.controller.xAxisRatio
        self.yIncrement = self.controller.yAxisRatio
        
        self.xRadius = self.dotWidth*self.xIncrement/2.0
        self.yRadius = -self.dotHeight*self.yIncrement/2.0
        
        self.ready = True
        self.setDirty()
    
    def handleFrame(self, event, signals):
        return signals
    
    def draw(self,painter):
        if not self.ready:
            return
        self.image.fill(Qt.white)
        
        yPix = self.controller.scatterBounds[1]
        yDat = self.controller.currentYaxis.maximum    # reversed coordinates
        while yPix <= self.controller.scatterBounds[3]:
            xPix = self.controller.scatterBounds[0]
            xDat = self.controller.currentXaxis.minimum
            while xPix <= self.controller.scatterBounds[2]:
                weight = self.controller.vData.count2D(self.controller.app.currentXattribute,[(xDat-self.xRadius,xDat+self.xRadius)],set(),
                                                       self.controller.app.currentYattribute,[(yDat-self.yRadius,yDat+self.yRadius)],set(),limit=len(self.dotColors))
                painter.setPen(self.dotColors[min(weight,len(self.dotColors)-1)])
                painter.drawPoint(xPix,yPix)
                xPix += 1
                xDat += self.xIncrement
            yPix += 1
            yDat += self.yIncrement
        
        # Draw the missing values in x
        if self.controller.vData.axisLookups[self.controller.app.currentYattribute].hasNumeric:
            yPix = self.controller.scatterBounds[1]
            yDat = self.controller.currentYaxis.maximum
            while yPix <= self.controller.scatterBounds[3]:
                weight = self.controller.vData.count2D(self.controller.app.currentXattribute,[],self.controller.vData.axisLookups[self.controller.app.currentXattribute].categoricalKeys,
                                                       self.controller.app.currentYattribute,[(yDat-self.yRadius,yDat+self.yRadius)],set(),limit=len(self.dotColors))
                painter.setPen(self.dotColors[min(weight,len(self.dotColors)-1)])
                painter.drawLine(self.xNonNumeric,yPix,self.xNonNumeric+self.dotWidth-1,yPix)
                yPix += 1
                yDat += self.yIncrement
        # Draw the missing values in y
        if self.controller.vData.axisLookups[self.controller.app.currentXattribute].hasNumeric:
            xPix = self.controller.scatterBounds[0]
            xDat = self.controller.currentXaxis.minimum
            while xPix <= self.controller.scatterBounds[2]:
                weight = self.controller.vData.count2D(self.controller.app.currentXattribute,[(xDat-self.xRadius,xDat+self.xRadius)],set(),
                                                       self.controller.app.currentYattribute,[],self.controller.vData.axisLookups[self.controller.app.currentYattribute].categoricalKeys,limit=len(self.dotColors))
                painter.setPen(self.dotColors[min(weight,len(self.dotColors)-1)])
                painter.drawLine(xPix,self.yNonNumeric,xPix,self.yNonNumeric+self.dotHeight-1)
                xPix += 1
                xDat += self.xIncrement

class selectionLayer(layer):
    def __init__(self, size, dynamic, controller, prototypeDot):
        layer.__init__(self,size,dynamic)
        self.controller = controller
        self.points = set()
        
        self.dotColor = QColor()
        self.dotColor.setNamedColor(prototypeDot.getAttribute('fill'))
        self.dotColor.setAlphaF(float(prototypeDot.getAttribute('fill-opacity')))
        self.dotWidth = prototypeDot.width()
        self.xoffset = self.controller.svgLayer.svg.xZeroBar.left()-self.dotWidth/2+1
        #self.xoffset = self.controller.scatterBounds[0]-self.dotWidth/2+1
        self.dotHeight = prototypeDot.height()
        self.yoffset = self.controller.svgLayer.svg.yZeroBar.bottom()-self.dotWidth/2+1
        #self.yoffset = self.controller.scatterBounds[3]-self.dotHeight/2+1
        self.xNonNumeric = (self.controller.svgLayer.svg.xNonNumericIcon.left() + self.controller.svgLayer.svg.xNonNumericIcon.right())/2 - self.dotWidth/2
        self.yNonNumeric = (self.controller.svgLayer.svg.yNonNumericIcon.top() + self.controller.svgLayer.svg.yNonNumericIcon.bottom())/2 - self.dotHeight/2
    
    def handleFrame(self, event, signals):
        return signals
    
    def updateAxes(self):
        self.xoffset = self.controller.svgLayer.svg.xZeroBar.left()-self.dotWidth/2+1
        self.yoffset = self.controller.svgLayer.svg.yZeroBar.bottom()-self.dotWidth/2+1
    
    def update(self, points):
        self.points = points
    
    def draw(self,painter):
        self.reverseXratio = 1.0/self.controller.xAxisRatio
        self.reverseYratio = 1.0/self.controller.yAxisRatio
        
        self.image.fill(Qt.transparent)
        for x,y in self.controller.vData.get2dData(self.points,self.controller.app.currentXattribute,self.controller.app.currentYattribute):
            if x == None or (not isinstance(x,int) and not isinstance(x,float)) or math.isinf(x) or math.isnan(x):
                x = self.xNonNumeric
            else:
                x = self.xoffset + x*self.reverseXratio
            
            if y == None or (not isinstance(y,int) and not isinstance(y,float)) or math.isinf(y) or math.isnan(y):
                y = self.yNonNumeric
            else:
                y = self.yoffset + y*self.reverseYratio
            painter.fillRect(x,y,self.dotWidth,self.dotHeight,self.dotColor)
    
    def getPoints(self, x, y):
        lowX=self.controller.screenToDataSpace(x-self.controller.cursorXradius, self.controller.scatterBounds[0], self.controller.currentXaxis.minimum, self.controller.xAxisRatio)
        lowY=self.controller.screenToDataSpace(y+self.controller.cursorYradius, self.controller.scatterBounds[3], self.controller.currentYaxis.minimum, self.controller.yAxisRatio)
        highX=self.controller.screenToDataSpace(x+self.controller.cursorXradius, self.controller.scatterBounds[0], self.controller.currentXaxis.minimum, self.controller.xAxisRatio)
        highY=self.controller.screenToDataSpace(y-self.controller.cursorYradius, self.controller.scatterBounds[3], self.controller.currentYaxis.minimum, self.controller.yAxisRatio)
        
        if (x + self.controller.cursorXradius >= self.xNonNumeric) and (x - self.controller.cursorXradius <= self.xNonNumeric + self.dotWidth):
            xSet = self.controller.vData.axisLookups[self.controller.app.currentXattribute].categoricalKeys
        else:
            xSet = set()
        if (y + self.controller.cursorYradius >= self.yNonNumeric) and (y - self.controller.cursorYradius <= self.yNonNumeric + self.dotHeight):
            ySet = self.controller.vData.axisLookups[self.controller.app.currentXattribute].categoricalKeys
        else:
            ySet = set()
        
        return self.controller.vData.query2D(self.controller.app.currentXattribute,[(lowX,highX)],xSet,
                                             self.controller.app.currentYattribute,[(lowY,highY)],ySet)

class scatterplotWidget(layeredWidget):
    def __init__(self, vData, app, parent = None):
        layeredWidget.__init__(self, parent)
        self.vData = vData
        self.app = app
        
        self.svgLayer = mutableSvgLayer('gui/svg/scatterplot.svg',self)
        self.addLayer(self.svgLayer)
        
        self.cursorXradius = self.svgLayer.svg.pointCursor.width()/2
        self.cursorYradius = self.svgLayer.svg.pointCursor.height()/2
        self.normalCursor = QCursor(Qt.CrossCursor)
        self.highlightCursor = self.svgLayer.svg.generateCursor(self.svgLayer.svg.pointCursor)
        self.svgLayer.svg.pointCursor.hide()
        
        self.setCursor(self.normalCursor)
        
        self.scatterBounds = self.svgLayer.svg.scatterBounds.getBounds()
        
        self.highlightedLayer = selectionLayer(self.svgLayer.size,False,self,self.svgLayer.svg.highlightedDotPrototype)
        self.addLayer(self.highlightedLayer,0)
        
        self.selectedLayer = selectionLayer(self.svgLayer.size,False,self,self.svgLayer.svg.selectedDotPrototype)
        self.addLayer(self.selectedLayer,0)
        
        self.allDataLayer = rasterLayer(self.svgLayer.size,False,self)
        self.addLayer(self.allDataLayer,0)
        
        self.xRanges = [self.svgLayer.svg.xRange]
        self.yRanges = [self.svgLayer.svg.yRange]
        
        self.notifyAxisChange(True)
        
        self.draggedHandle = None
        self.draggedAxisIsX = None
        self.draggedBoundIsLow = None
        self.draggedDistance = None
        self.draggedStart = None
    
    def notifyAxisChange(self, applyImmediately=True):
        # x axis
        att = self.app.currentXattribute
        self.currentXaxis = self.vData.axisLookups[att]
        low = self.currentXaxis.minimum
        high = self.currentXaxis.maximum
        ax = self.svgLayer.svg.xAxis
        right = self.scatterBounds[2]
        left = self.scatterBounds[0]
        ax.label.setText(att)
        ax.lowLabel.setText(fitInSevenChars(low))
        ax.highLabel.setText(fitInSevenChars(high))
        self.xAxisRatio = float(high - low) / float(right - left)
        if self.xAxisRatio == 0:
            self.xAxisRatio = 1.0 / float(right-left)
        if low <= 0 and high >= 0:
            self.svgLayer.svg.xZeroBar.show()
            self.svgLayer.svg.xZeroBar.moveTo(self.dataToScreenSpace(0.0, left, low, self.xAxisRatio)-self.svgLayer.svg.xZeroBar.width()/2,self.svgLayer.svg.xZeroBar.top())
        else:
            self.svgLayer.svg.xZeroBar.hide()
        
        # y axis
        att = self.app.currentYattribute
        self.currentYaxis = self.vData.axisLookups[att]
        low = self.currentYaxis.minimum
        high = self.currentYaxis.maximum
        ax = self.svgLayer.svg.yAxis
        bottom = self.scatterBounds[3]
        top = self.scatterBounds[1]
        ax.label.setText(att)
        ax.lowLabel.setText(fitInSevenChars(low))
        ax.highLabel.setText(fitInSevenChars(high))
        self.yAxisRatio = float(high - low) / float(top-bottom)
        if self.yAxisRatio == 0:
            self.yAxisRatio = 1.0 / float(top-bottom)
        if low <= 0 and high >= 0:
            self.svgLayer.svg.yZeroBar.show()
            self.svgLayer.svg.yZeroBar.moveTo(self.svgLayer.svg.yZeroBar.left(),self.dataToScreenSpace(0.0, bottom, low, self.yAxisRatio)-self.svgLayer.svg.yZeroBar.height()/2)
        else:
            self.svgLayer.svg.yZeroBar.hide()
        
        if applyImmediately:
            self.notifySelection(self.app.intMan.activePoints, self.app.intMan.activeParams)
            self.allDataLayer.setup()
            self.selectedLayer.updateAxes()
            self.highlightedLayer.updateAxes()
    
    def notifySelection(self, activePoints, activeParams):
        self.selectedLayer.update(activePoints)
        self.selectedLayer.setDirty()
        # pull out the sizes of things once before we manipulate everything - this should help minimize re-rendering
        xAtt = self.app.currentXattribute
        numericLeftPixel = self.scatterBounds[0]
        numericRightPixel = self.scatterBounds[2]
        
        rightHandleSize = self.xRanges[0].rightHandle.width()
        rightHandleTop = self.xRanges[0].rightHandle.top()
        leftHandleSize = self.xRanges[0].leftHandle.width()
        leftHandleTop = self.xRanges[0].leftHandle.top()
        xBarSize = self.xRanges[0].bar.height()
        xBarTop = self.xRanges[0].bar.top()
        
        yAtt = self.app.currentYattribute
        numericBottomPixel = self.scatterBounds[3]
        numericTopPixel = self.scatterBounds[1]
        topHandleSize = self.yRanges[0].topHandle.height()
        topHandleLeft = self.yRanges[0].topHandle.left()
        bottomHandleSize = self.yRanges[0].bottomHandle.height()
        bottomHandleLeft = self.yRanges[0].bottomHandle.left()
        yBarSize = self.yRanges[0].bar.width()
        yBarLeft = self.yRanges[0].bar.left()
        
        # remove, duplicate the number of svg selection groups to fit the data
        # x axis
        i = len(self.xRanges) - 1
        while len(self.xRanges) > len(activeParams[xAtt][0]):
            self.xRanges[i].delete()
            del self.xRanges[i]
            i -= 1
        
        while len(self.xRanges) < len(activeParams[xAtt][0]):
            self.xRanges.append(self.xRanges[0].clone())
        # y axis
        i = len(self.yRanges) - 1
        while len(self.yRanges) > len(activeParams[yAtt][0]):
            self.yRanges[i].delete()
            del self.yRanges[i]
            i -= 1
        
        while len(self.yRanges) < len(activeParams[yAtt][0]):
            self.yRanges.append(self.yRanges[0].clone())
        
        # adjust each selection group to the data
        # x axis
        for i,r in enumerate(activeParams[xAtt][0]):
            l = r[0]
            h = r[1]
            
            v = self.xRanges[i]
            
            # are parts (or all) of the selection hidden?
            rightPixel = numericRightPixel - float(self.currentXaxis.maximum-h)/self.xAxisRatio
            leftPixel = numericLeftPixel + float(l-self.currentXaxis.minimum)/self.xAxisRatio
            
            if rightPixel + rightHandleSize < numericLeftPixel or rightPixel > numericRightPixel:
                v.rightHandle.hide()
            else:
                v.rightHandle.label.setText(fitInSevenChars(h))
                v.rightHandle.moveTo(rightPixel,rightHandleTop)
                v.rightHandle.show()
            rightPixel = max(rightPixel,numericLeftPixel)
            rightPixel = min(rightPixel,numericRightPixel)
            
            if leftPixel < numericLeftPixel or leftPixel - leftHandleSize > numericRightPixel:
                v.leftHandle.hide()
            else:
                v.leftHandle.label.setText(fitInSevenChars(l))
                v.leftHandle.moveTo(leftPixel - leftHandleSize, leftHandleTop)
                v.leftHandle.show()
            leftPixel = min(numericRightPixel,leftPixel)
            leftPixel = max(numericLeftPixel,leftPixel)
            
            if leftPixel >= rightPixel:
                v.bar.setSize(1,xBarSize)
            
            v.bar.moveTo(leftPixel,xBarTop)
            v.bar.setSize(rightPixel-leftPixel,xBarSize)
            v.bar.show()
        # y axis
        for i,r in enumerate(activeParams[yAtt][0]):
            l = r[0]
            h = r[1]
            
            v = self.yRanges[i]
            
            # are parts (or all) of the selection hidden?
            topPixel = self.dataToScreenSpace(h, self.scatterBounds[3], self.currentYaxis.minimum, self.yAxisRatio)
            bottomPixel = self.dataToScreenSpace(l, self.scatterBounds[3], self.currentYaxis.minimum, self.yAxisRatio)
            
            if topPixel - topHandleSize > numericBottomPixel or topPixel < numericTopPixel:
                v.topHandle.hide()
            else:
                v.topHandle.label.setText(fitInSevenChars(h))
                v.topHandle.moveTo(topHandleLeft,topPixel - topHandleSize)
                v.topHandle.show()
            topPixel = max(topPixel,numericTopPixel)
            topPixel = min(topPixel,numericBottomPixel)
            
            if bottomPixel > numericBottomPixel or bottomPixel + bottomHandleSize < numericTopPixel:
                v.bottomHandle.hide()
            else:
                v.bottomHandle.label.setText(fitInSevenChars(l))
                v.bottomHandle.moveTo(bottomHandleLeft,bottomPixel)
                v.bottomHandle.show()
            bottomPixel = min(bottomPixel,numericBottomPixel)
            bottomPixel = max(bottomPixel,numericTopPixel)
            
            if topPixel >= bottomPixel:
                v.bar.setSize(yBarSize,1)
            
            v.bar.moveTo(yBarLeft,topPixel)
            v.bar.setSize(yBarSize,bottomPixel-topPixel)
            v.bar.show()
    
    def handleEvents(self, event, signals):
        pass
    
    def notifyHighlight(self, activePoints):
        self.highlightedLayer.update(activePoints)
        self.highlightedLayer.setDirty()
    
    def canAdjustSelection(self):
        return not self.app.intMan.multipleSelected()
    
    def screenToDataSpace(self, value, screenLow, dataLow, ratio):
        return dataLow + float(value-screenLow)*ratio
    
    def dataToScreenSpace(self, value, screenLow, dataLow, ratio):
        return round(screenLow + float(value-dataLow)/ratio)
    
    def startDrag(self, element):
        self.draggedHandle = element
        handleName = self.draggedHandle.getAttribute('handleName')
        if handleName.startswith('bottom'):
            self.draggedAxisIsX = True
            if handleName == 'bottomLeft':
                self.draggedStart = element.right()
                self.draggedBoundIsLow = True
            else:
                self.draggedStart = element.left()
                self.draggedBoundIsLow = False
        else:
            self.draggedAxisIsX = False
            if handleName == 'leftBottom':
                self.draggedStart = element.top()
                self.draggedBoundIsLow = True
            else:
                self.draggedStart = element.bottom()
                self.draggedBoundIsLow = False
        self.draggedDistance = 0
    
    def handleDrag(self, delta):
        if self.draggedHandle == None:
            return 0
        original = self.draggedStart + self.draggedDistance
        projected = original + delta
        if self.draggedAxisIsX:
            if self.draggedBoundIsLow:
                if delta < 0:
                    projected = max(projected,self.scatterBounds[0])
                else:
                    projected = min(projected,self.draggedHandle.parent.rightHandle.left(),self.scatterBounds[2])
            else:
                if delta < 0:
                    projected = max(projected,self.draggedHandle.parent.leftHandle.right(),self.scatterBounds[0])
                else:
                    projected = min(projected,self.scatterBounds[2])
        else:
            if self.draggedBoundIsLow:
                if delta < 0:
                    projected = max(projected,self.draggedHandle.parent.topHandle.bottom(),self.scatterBounds[1])
                else:
                    projected = min(projected,self.scatterBounds[3])
            else:
                if delta < 0:
                    projected = max(projected,self.scatterBounds[1])
                else:
                    projected = min(projected,self.draggedHandle.parent.bottomHandle.top(),self.scatterBounds[3])
                    
        delta = projected - original
        self.draggedDistance = projected - self.draggedStart
        if self.draggedAxisIsX:
            self.draggedHandle.label.setText(fitInSevenChars(self.screenToDataSpace(projected, self.scatterBounds[0], self.currentXaxis.minimum, self.xAxisRatio)))
        else:
            self.draggedHandle.label.setText(fitInSevenChars(self.screenToDataSpace(projected, self.scatterBounds[3], self.currentYaxis.minimum, self.yAxisRatio)))
        return delta
    
    def finishDrag(self):
        if self.draggedHandle == None:
            return
        if self.draggedAxisIsX:
            start = self.screenToDataSpace(self.draggedStart, self.scatterBounds[0], self.currentXaxis.minimum, self.xAxisRatio)
            end = self.screenToDataSpace(self.draggedStart + self.draggedDistance, self.scatterBounds[0], self.currentXaxis.minimum, self.xAxisRatio)
            self.app.intMan.newOperation(operation.NUMERIC_CHANGE,att=self.app.currentXattribute,start=start,end=end,isHigh=not self.draggedBoundIsLow)
        else:
            start = self.screenToDataSpace(self.draggedStart, self.scatterBounds[3], self.currentYaxis.minimum, self.yAxisRatio)
            end = self.screenToDataSpace(self.draggedStart + self.draggedDistance, self.scatterBounds[3], self.currentYaxis.minimum, self.yAxisRatio)
            self.app.intMan.newOperation(operation.NUMERIC_CHANGE,att=self.app.currentYattribute,start=start,end=end,isHigh=not self.draggedBoundIsLow)
        # this will eventually result in a call to self.notifySelection, so I don't really care about redrawing everything
        self.draggedAxisIsX = None
        self.draggedBoundIsLow = None
        self.draggedDistance = None
        self.draggedStart = None
        self.draggedHandle = None
    
    def handleMouseOver(self, x, y):
        if x == None or y == None:
            self.setCursor(self.normalCursor)
            self.app.notifyHighlight(set())
        else:
            self.setCursor(self.highlightCursor)
            points = self.highlightedLayer.getPoints(x,y)
            self.app.notifyHighlight(points)
    
    def handleMouseClick(self):
        pass


