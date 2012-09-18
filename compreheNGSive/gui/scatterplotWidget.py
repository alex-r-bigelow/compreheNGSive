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
    
    def setup(self, scatter):
        self.scatter = scatter
        
        self.xIncrement = self.controller.xAxisRatio
        self.yIncrement = self.controller.yAxisRatio
        
        self.xRadius = self.dotWidth*self.xIncrement/2.0
        self.yRadius = self.dotHeight*self.yIncrement/2.0
        
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
                weight = self.scatter[self.controller.currentXaxis.name].countIntersection(xDat-self.xRadius, xDat+self.xRadius, self.scatter[self.controller.currentYaxis.name], yDat-self.yRadius, yDat+self.yRadius, 5)
                painter.setPen(self.dotColors[min(weight,len(self.dotColors)-1)])
                painter.drawPoint(xPix,yPix)
                xPix += 1
                xDat += self.xIncrement
            yPix += 1
            yDat += self.yIncrement
        
        # Draw the missing values in x
        if self.controller.currentYaxis.hasNumeric():
            yPix = self.controller.scatterBounds[1]
            yDat = self.controller.currentYaxis.maximum
            while yPix <= self.controller.scatterBounds[3]:
                rsNumsInRange = self.controller.currentYaxis.tree.select(low=yDat-self.yRadius, high=yDat+self.yRadius, includeMasked=False, includeUndefined=False, includeMissing=False)
                rsNumsInRange.difference_update(self.controller.currentXaxis.rsValues.iterkeys())
                weight = len(rsNumsInRange)
                painter.setPen(self.dotColors[min(len(rsNumsInRange),len(self.dotColors)-1)])
                painter.drawLine(self.xNonNumeric,yPix,self.xNonNumeric+self.dotWidth-1,yPix)
                yPix += 1
                yDat += self.yIncrement
        # Draw the missing values in y
        if self.controller.currentXaxis.hasNumeric():
            xPix = self.controller.scatterBounds[0]
            xDat = self.controller.currentXaxis.minimum
            while xPix <= self.controller.scatterBounds[2]:
                rsNumsInRange = self.controller.currentXaxis.tree.select(low=xDat-self.xRadius, high=xDat+self.xRadius, includeMasked=False, includeUndefined=False, includeMissing=False)
                rsNumsInRange.difference_update(self.controller.currentYaxis.rsValues.iterkeys())
                weight = len(rsNumsInRange)
                painter.setPen(self.dotColors[min(len(rsNumsInRange),len(self.dotColors)-1)])
                painter.drawLine(xPix,self.yNonNumeric,xPix,self.yNonNumeric+self.dotHeight-1)
                xPix += 1
                xDat += self.xIncrement

class selectionLayer(layer):
    def __init__(self, size, dynamic, controller, prototypeDot, rsNumbers):
        layer.__init__(self,size,dynamic)
        self.controller = controller
        self.rsNumbers = rsNumbers
        
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
    
    def update(self, rsNumbers):
        self.rsNumbers = rsNumbers
    
    def draw(self,painter):
        if not hasattr(self.controller,'xAxisRatio') or not hasattr(self.controller,'yAxisRatio'):
            return
        self.reverseXratio = 1.0/self.controller.xAxisRatio
        self.reverseYratio = 1.0/self.controller.yAxisRatio
        
        rsList = list(self.rsNumbers)
        
        self.image.fill(Qt.transparent)
        for x,y in zip(self.controller.currentXaxis.getValues(rsList),self.controller.currentYaxis.getValues(rsList)):
            if x == None or (not isinstance(x,int) and not isinstance(x,float)) or math.isinf(x) or math.isnan(x):
                x = self.xNonNumeric
            else:
                x = self.xoffset + x*self.reverseXratio
            
            if y == None or (not isinstance(y,int) and not isinstance(y,float)) or math.isinf(y) or math.isnan(y):
                y = self.yNonNumeric
            else:
                y = self.yoffset + y*self.reverseYratio
            
            painter.fillRect(x,y,self.dotWidth,self.dotHeight,self.dotColor)
    
    def getRsNumbers(self, x, y):
        lowX=self.controller.screenToDataSpace(x-self.controller.cursorXradius, self.controller.scatterBounds[0], self.controller.currentXaxis.minimum, self.controller.xAxisRatio)
        lowY=self.controller.screenToDataSpace(y-self.controller.cursorYradius, self.controller.scatterBounds[3], self.controller.currentYaxis.minimum, self.controller.yAxisRatio)
        highX=self.controller.screenToDataSpace(x+self.controller.cursorXradius, self.controller.scatterBounds[0], self.controller.currentXaxis.minimum, self.controller.xAxisRatio)
        highY=self.controller.screenToDataSpace(y+self.controller.cursorYradius, self.controller.scatterBounds[3], self.controller.currentYaxis.minimum, self.controller.yAxisRatio)
        
        rsNumbers = self.controller.data.scatter.select(lowX=lowX,lowY=lowY,highX=highX,highY=highY,
                                             includeMaskedX=False, includeMaskedY=False, includeUndefinedX=False, includeUndefinedY=False, includeMissingX=False, includeMissingY=False)
        
        showXnonNumerics = (x + self.controller.cursorXradius >= self.xNonNumeric) and (x - self.controller.cursorXradius <= self.xNonNumeric + self.dotWidth)
        if showXnonNumerics:
            rsInRange = self.controller.currentYaxis.tree.select(low=lowY, high=highY, includeMasked=False, includeUndefined=False, includeMissing=False)
            rsInRange.difference_update(self.controller.currentXaxis.rsValues.iterkeys())
            rsNumbers.update(rsInRange)
        showYnonNumerics = (y + self.controller.cursorYradius >= self.yNonNumeric) and (y - self.controller.cursorYradius <= self.yNonNumeric + self.dotHeight)
        if showYnonNumerics:
            rsInRange = self.controller.currentXaxis.tree.select(low=lowX, high=highX, includeMasked=False, includeUndefined=False, includeMissing=False)
            rsInRange.difference_update(self.controller.currentYaxis.rsValues.iterkeys())
            rsNumbers.update(rsInRange)
        # TODO: show both
        return rsNumbers

class scatterplotWidget(layeredWidget):
    def __init__(self, data, app, parent = None):
        layeredWidget.__init__(self, parent)
        self.data = data
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
        
        self.highlightedLayer = selectionLayer(self.svgLayer.size,False,self,self.svgLayer.svg.highlightedDotPrototype,self.app.highlightedRsNumbers)
        self.addLayer(self.highlightedLayer,0)
        
        self.selectedLayer = selectionLayer(self.svgLayer.size,False,self,self.svgLayer.svg.selectedDotPrototype,self.app.activeRsNumbers)
        self.addLayer(self.selectedLayer,0)
        
        self.allDataLayer = rasterLayer(self.svgLayer.size,False,self)
        self.addLayer(self.allDataLayer,0)
        
        self.xRanges = [self.svgLayer.svg.xRange]
        self.yRanges = [self.svgLayer.svg.yRange]
        
        self.currentXaxis = self.data.data[self.data.currentXattribute]
        self.currentYaxis = self.data.data[self.data.currentYattribute]
        
        self.notifyAxisChange(True,False)
        self.notifyAxisChange(False)
        
        self.draggedHandle = None
        self.draggedAxisIsX = None
        self.draggedBoundIsLow = None
        self.draggedDistance = None
        self.draggedStart = None
    
    def notifyAxisChange(self, xAxis=True,applyImmediately=True):
        if xAxis:
            self.currentXaxis = self.data.data[self.data.currentXattribute]
            ax = self.svgLayer.svg.xAxis
            ax.label.setText(self.data.currentXattribute)
            ax.lowLabel.setText(fitInSevenChars(self.currentXaxis.minimum))
            ax.highLabel.setText(fitInSevenChars(self.currentXaxis.maximum))
            self.xAxisRatio = float(self.currentXaxis.maximum - self.currentXaxis.minimum) / float(self.scatterBounds[2] - self.scatterBounds[0])
            if self.xAxisRatio == 0:
                self.xAxisRatio = 1.0 / float(self.scatterBounds[2]-self.scatterBounds[0])
            if self.currentXaxis.minimum <= 0 and self.currentXaxis.maximum >= 0:
                self.svgLayer.svg.xZeroBar.show()
                self.svgLayer.svg.xZeroBar.moveTo(self.dataToScreenSpace(0.0, self.scatterBounds[0], self.currentXaxis.minimum, self.xAxisRatio)-self.svgLayer.svg.xZeroBar.width()/2,self.svgLayer.svg.xZeroBar.top())
            else:
                self.svgLayer.svg.xZeroBar.hide()
            self.notifySelection(self.app.activeRsNumbers,self.app.activeParams,self.currentXaxis)
            if applyImmediately:
                self.allDataLayer.setup(self.data.data)
                self.selectedLayer.updateAxes()
                self.highlightedLayer.updateAxes()
        else:
            self.currentYaxis = self.data.data[self.data.currentYattribute]
            ax = self.svgLayer.svg.yAxis
            ax.label.setText(self.data.currentYattribute)
            ax.lowLabel.setText(fitInSevenChars(self.currentYaxis.minimum))
            ax.highLabel.setText(fitInSevenChars(self.currentYaxis.maximum))
            self.yAxisRatio = float(self.currentYaxis.maximum - self.currentYaxis.minimum) / float(self.scatterBounds[1] - self.scatterBounds[3])
            if self.yAxisRatio == 0:
                self.yAxisRatio = 1.0 / float(self.scatterBounds[1]-self.scatterBounds[3])
            if self.currentYaxis.minimum <= 0 and self.currentYaxis.maximum >= 0:
                self.svgLayer.svg.yZeroBar.show()
                self.svgLayer.svg.yZeroBar.moveTo(self.svgLayer.svg.yZeroBar.left(),self.dataToScreenSpace(0.0, self.scatterBounds[3], self.currentYaxis.minimum, self.yAxisRatio)-self.svgLayer.svg.yZeroBar.height()/2)
            else:
                self.svgLayer.svg.yZeroBar.hide()
            self.notifySelection(self.app.activeRsNumbers,self.app.activeParams,self.currentYaxis)
            if applyImmediately:
                self.allDataLayer.setup(self.data.data)
                self.selectedLayer.updateAxes()
                self.highlightedLayer.updateAxes()
    
    def notifySelection(self, rsNumbers, params, axis=None):
        self.selectedLayer.update(rsNumbers)
        self.selectedLayer.setDirty()
        # pull out the sizes of things once before we manipulate everything - this should help minimize re-rendering
        if not axis == self.currentXaxis and not axis == self.currentYaxis:
            return  # ignore axes that aren't in the scatterplot
        if axis == self.currentXaxis:
            dataAxis = self.currentXaxis
            visRanges = self.xRanges
            pixelRatio = self.xAxisRatio
            numericLeftPixel = self.scatterBounds[0]
            numericRightPixel = self.scatterBounds[2]
            if len(self.xRanges) == 0:
                print self.xRanges
                print self.yRanges
                raise Exception('short ranges!')
            rightHandleSize = self.xRanges[0].rightHandle.width()
            rightHandleTop = self.xRanges[0].rightHandle.top()
            leftHandleSize = self.xRanges[0].leftHandle.width()
            leftHandleTop = self.xRanges[0].leftHandle.top()
            barSize = self.xRanges[0].bar.height()
            barTop = self.xRanges[0].bar.top()
        if axis == self.currentYaxis:
            dataAxis = self.currentYaxis
            visRanges = self.yRanges
            pixelRatio = self.yAxisRatio
            numericBottomPixel = self.scatterBounds[3]
            numericTopPixel = self.scatterBounds[1]
            topHandleSize = self.yRanges[0].topHandle.height()
            topHandleLeft = self.yRanges[0].topHandle.left()
            bottomHandleSize = self.yRanges[0].bottomHandle.height()
            bottomHandleLeft = self.yRanges[0].bottomHandle.left()
            barSize = self.yRanges[0].bar.width()
            barLeft = self.yRanges[0].bar.left()
        
        # remove, duplicate the number of svg selection groups to fit the data
        
        i = len(visRanges) - 1
        while len(visRanges) > len(params[dataAxis][0]):
            visRanges[i].delete()
            del visRanges[i]
            i -= 1
        
        while len(visRanges) < len(params[dataAxis][0]):
            visRanges.append(visRanges[0].clone())
        
        # adjust each selection group to the data
        if axis == self.currentXaxis:
            for i,r in enumerate(params[dataAxis][0]):
                l = r[0]
                h = r[1]
                
                v = visRanges[i]
                
                # are parts (or all) of the selection hidden?
                rightPixel = numericRightPixel - float(dataAxis.maximum-h)/pixelRatio
                leftPixel = numericLeftPixel + float(l-dataAxis.minimum)/pixelRatio
                
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
                    v.bar.setSize(1,barSize)
                
                v.bar.moveTo(leftPixel,barTop)
                v.bar.setSize(rightPixel-leftPixel,barSize)
                v.bar.show()
        else: # axis == self.currentYaxis:
            for i,r in enumerate(params[dataAxis][0]):
                l = r[0]
                h = r[1]
                
                v = visRanges[i]
                
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
                    v.bar.setSize(barSize,1)
                
                v.bar.moveTo(barLeft,topPixel)
                v.bar.setSize(barSize,bottomPixel-topPixel)
                v.bar.show()
    
    def handleEvents(self, event, signals):
        pass
    
    def notifyHighlight(self, rsNumbers):
        self.highlightedLayer.update(rsNumbers)
        self.highlightedLayer.setDirty()
    
    def canAdjustSelection(self):
        return not self.app.multipleSelected()
    
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
            self.app.newOperation(operation.NUMERIC_CHANGE,axis=self.currentXaxis,start=self.draggedStart,end=end,isHigh=not self.draggedBoundIsLow)
        else:
            start = self.screenToDataSpace(self.draggedStart, self.scatterBounds[3], self.currentYaxis.minimum, self.yAxisRatio)
            end = self.screenToDataSpace(self.draggedStart + self.draggedDistance, self.scatterBounds[3], self.currentYaxis.minimum, self.yAxisRatio)
            self.app.newOperation(operation.NUMERIC_CHANGE,axis=self.currentYaxis,start=start,end=end,isHigh=not self.draggedBoundIsLow)
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
            rsNumbers = self.highlightedLayer.getRsNumbers(x,y)
            self.app.notifyHighlight(rsNumbers)
    
    def handleMouseClick(self):
        print self.app.highlightedRsNumbers


