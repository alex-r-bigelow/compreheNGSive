from layeredWidget import mutableSvgLayer, layeredWidget, layer
from resources.utils import fitInSevenChars
from dataModels.variantData import operation
from PySide.QtCore import Qt,QSize
from PySide.QtGui import QColor

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
    
    def setup(self, queryObject):
        self.queryObject = queryObject
        
        self.xIncrement = self.controller.xAxisRatio
        self.yIncrement = self.controller.yAxisRatio
        
        self.xRadius = self.controller.svgLayer.svg.dotPrototype.width()*self.xIncrement/2.0
        self.yRadius = self.controller.svgLayer.svg.dotPrototype.height()*self.yIncrement/2.0
        
        self.ready = True
        self.setDirty()
    
    def handleFrame(self, event, signals):
        return signals
    
    def draw(self,painter):
        if not self.ready:
            return
        width,height = self.size.toTuple()
        painter.eraseRect(0,0,width,height)
        
        yPix = self.controller.scatterBounds[1]
        yDat = self.controller.currentYaxis.getMax()    # reversed coordinates
        while yPix <= self.controller.scatterBounds[3]:
            xPix = self.controller.scatterBounds[0]
            xDat = self.controller.currentXaxis.getMin()
            while xPix <= self.controller.scatterBounds[2]:
                weight = self.queryObject.countPopulation(xDat-self.xRadius, lowY=yDat-self.yRadius, highX=xDat+self.xRadius, highY=yDat+self.yRadius, includeMasked=False, includeUndefined=False, includeMissing=False)
                painter.setPen(self.dotColors[min(weight,len(self.dotColors)-1)])
                painter.drawPoint(xPix,yPix)
                xPix += 1
                xDat += self.xIncrement
            yPix += 1
            yDat += self.yIncrement

class scatterplotWidget(layeredWidget):
    def __init__(self, data, app, parent = None):
        layeredWidget.__init__(self, parent)
        self.data = data
        self.app = app
        
        self.svgLayer = mutableSvgLayer('gui/svg/scatterplot.svg',self)
        self.addLayer(self.svgLayer)
        
        self.allDataLayer = rasterLayer(self.svgLayer.size,False,self)
        self.addLayer(self.allDataLayer,0)
        
        self.scatterBounds = self.svgLayer.svg.scatterBounds.getBounds()
        
        self.xRanges = [self.svgLayer.svg.xRange]
        self.yRanges = [self.svgLayer.svg.yRange]
        
        self.currentXaxis = self.data.axes[self.data.currentXattribute]
        self.currentYaxis = self.data.axes[self.data.currentYattribute]
        
        self.notifyAxisChange(True,False)
        self.notifyAxisChange(False)
        
        self.draggedHandle = None
        self.draggedAxisIsX = None
        self.draggedBoundIsLow = None
        self.draggedDistance = None
        self.draggedStart = None
    
    def notifyAxisChange(self, xAxis=True,applyImmediately=True):
        if xAxis:
            self.currentXaxis = self.data.axes[self.data.currentXattribute]
            ax = self.svgLayer.svg.xAxis
            ax.label.setText(self.data.currentXattribute)
            ax.lowLabel.setText(fitInSevenChars(self.currentXaxis.getMin()))
            ax.highLabel.setText(fitInSevenChars(self.currentXaxis.getMax()))
            self.xAxisRatio = float(self.currentXaxis.getMax() - self.currentXaxis.getMin()) / float(self.scatterBounds[2] - self.scatterBounds[0])
            if self.xAxisRatio == 0:
                self.xAxisRatio = 1.0 / float(self.scatterBounds[2]-self.scatterBounds[0])
            if self.currentXaxis.getMin() <= 0 and self.currentXaxis.getMax() >= 0:
                self.svgLayer.svg.xZeroBar.show()
                self.svgLayer.svg.xZeroBar.moveTo(self.dataToScreenSpace(0.0, self.scatterBounds[0], self.currentXaxis.getMin(), self.xAxisRatio)-self.svgLayer.svg.xZeroBar.width()/2,self.svgLayer.svg.xZeroBar.top())
            else:
                self.svgLayer.svg.xZeroBar.hide()
            if applyImmediately:
                self.notifySelection(self.app.activeRsNumbers,self.app.activeParams,self.currentXaxis)
                self.allDataLayer.setup(self.data.scatter)
        else:
            self.currentYaxis = self.data.axes[self.data.currentYattribute]
            ax = self.svgLayer.svg.yAxis
            ax.label.setText(self.data.currentYattribute)
            ax.lowLabel.setText(fitInSevenChars(self.currentYaxis.getMin()))
            ax.highLabel.setText(fitInSevenChars(self.currentYaxis.getMax()))
            self.yAxisRatio = float(self.currentYaxis.getMax() - self.currentYaxis.getMin()) / float(self.scatterBounds[1] - self.scatterBounds[3])
            if self.xAxisRatio == 0:
                self.xAxisRatio = 1.0 / float(self.scatterBounds[1]-self.scatterBounds[3])
            if self.currentYaxis.getMin() <= 0 and self.currentYaxis.getMax() >= 0:
                self.svgLayer.svg.yZeroBar.show()
                self.svgLayer.svg.yZeroBar.moveTo(self.svgLayer.svg.yZeroBar.left(),self.dataToScreenSpace(0.0, self.scatterBounds[3], self.currentYaxis.getMin(), self.yAxisRatio)-self.svgLayer.svg.yZeroBar.height()/2)
            else:
                self.svgLayer.svg.yZeroBar.hide()
            if applyImmediately:
                self.notifySelection(self.app.activeRsNumbers,self.app.activeParams,self.currentYaxis)
                self.allDataLayer.setup(self.data.scatter)
    
    def notifySelection(self, rsNumbers, params, axis=None):
        # pull out the sizes of things once before we manipulate everything - this should help minimize re-rendering
        if axis == self.currentXaxis:
            dataAxis = self.currentXaxis
            visRanges = self.xRanges
            pixelRatio = self.xAxisRatio
            numericLeftPixel = self.scatterBounds[0]
            numericRightPixel = self.scatterBounds[2]
            rightHandleSize = self.xRanges[0].rightHandle.width()
            rightHandleTop = self.xRanges[0].rightHandle.top()
            leftHandleSize = self.xRanges[0].leftHandle.width()
            leftHandleTop = self.xRanges[0].leftHandle.top()
            barSize = self.xRanges[0].bar.height()
            barTop = self.xRanges[0].bar.top()
        elif axis == self.currentYaxis:
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
        else:
            return  # ignore axes that aren't in the scatterplot
        
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
                rightPixel = numericRightPixel - float(dataAxis.getMax()-h)/pixelRatio
                leftPixel = numericLeftPixel + float(l-dataAxis.getMin())/pixelRatio
                
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
                topPixel = self.dataToScreenSpace(h, self.scatterBounds[3], self.currentYaxis.getMin(), self.yAxisRatio)
                bottomPixel = self.dataToScreenSpace(l, self.scatterBounds[3], self.currentYaxis.getMin(), self.yAxisRatio)
                
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
    
    def notifyHighlight(self):
        pass
    
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
            self.draggedHandle.label.setText(fitInSevenChars(self.screenToDataSpace(projected, self.scatterBounds[0], self.currentXaxis.getMin(), self.xAxisRatio)))
        else:
            self.draggedHandle.label.setText(fitInSevenChars(self.screenToDataSpace(projected, self.scatterBounds[3], self.currentYaxis.getMin(), self.yAxisRatio)))
        return delta
    
    def finishDrag(self):
        if self.draggedHandle == None:
            return
        if self.draggedAxisIsX:
            start = self.screenToDataSpace(self.draggedStart, self.scatterBounds[0], self.currentXaxis.getMin(), self.xAxisRatio)
            end = self.screenToDataSpace(self.draggedStart + self.draggedDistance, self.scatterBounds[0], self.currentXaxis.getMin(), self.xAxisRatio)
            self.app.newOperation(operation.NUMERIC_CHANGE,axis=self.currentXaxis,start=self.draggedStart,end=end,isHigh=not self.draggedBoundIsLow)
        else:
            start = self.screenToDataSpace(self.draggedStart, self.scatterBounds[3], self.currentYaxis.getMin(), self.yAxisRatio)
            end = self.screenToDataSpace(self.draggedStart + self.draggedDistance, self.scatterBounds[3], self.currentYaxis.getMin(), self.yAxisRatio)
            self.app.newOperation(operation.NUMERIC_CHANGE,axis=self.currentYaxis,start=start,end=end,isHigh=not self.draggedBoundIsLow)
        # this will eventually result in a call to self.notifySelection, so I don't really care about redrawing everything
        self.draggedAxisIsX = None
        self.draggedBoundIsLow = None
        self.draggedDistance = None
        self.draggedStart = None
        self.draggedHandle = None

'''
init
        layeredWidget.__init__(self, parent)
        self.data = data
        self.app = app
        
        self.svgLayer = mutableSvgLayer('gui/svg/scatterplot.svg',self)
        self.addLayer(self.svgLayer)
        
        self.scatterBounds = self.svgLayer.svg.scatterBounds.getBounds()
        
        self.xRanges = [self.svgLayer.svg.xRange]
        self.yRanges = [self.svgLayer.svg.yRange]
        
        self.xAxisRatio = 1.0
        self.yAxisRatio = 1.0
        
        self.latestAxisUpdate = self.data.currentXattribute
        
        self.notifyAxisChange(True)
        self.notifyAxisChange(False)


handleevents
# adjustment of selections
        if signals.has_key('startAdjust'):
            axis,old = signals['startAdjust']
            if axis == 'x':
                axis = self.currentXaxis
                old = self.currentXaxis.getMin() + (old-self.scatterBounds[0])*self.xAxisRatio
                self.latestAxisUpdate = self.data.currentXattribute
            elif axis == 'y':
                axis = self.currentYaxis
                old = self.currentYaxis.getMax() - (self.scatterBounds[3]-old)*self.yAxisRatio
                self.latestAxisUpdate = self.data.currentYattribute
            else:
                assert False
            self.data.startNumericOperation(axis,old)
        
        if signals.has_key('adjust'):
            element,axis,oldLow,oldHigh,newLow,newHigh = signals['adjust']
            if axis == 'x':
                axis = self.currentXaxis
                oldLow = self.currentXaxis.getMin() + (oldLow-self.scatterBounds[0])*self.xAxisRatio
                oldHigh = self.currentXaxis.getMin() + (oldHigh-self.scatterBounds[0])*self.xAxisRatio
                newLow = self.currentXaxis.getMin() + (newLow-self.scatterBounds[0])*self.xAxisRatio
                newHigh = self.currentXaxis.getMin() + (newHigh-self.scatterBounds[0])*self.xAxisRatio
                
                element.leftHandle.label.setText(self.fitInSevenChars(newLow))
                element.rightHandle.label.setText(self.fitInSevenChars(newHigh))
                self.latestAxisUpdate = self.data.currentXattribute
            elif axis == 'y':
                axis = self.currentYaxis
                oldLow = self.currentYaxis.getMax() - (self.scatterBounds[3]-oldLow)*self.yAxisRatio
                oldHigh = self.currentYaxis.getMax() - (self.scatterBounds[3]-oldHigh)*self.yAxisRatio
                newLow = self.currentYaxis.getMax() - (self.scatterBounds[3]-newLow)*self.yAxisRatio
                newHigh = self.currentYaxis.getMax() - (self.scatterBounds[3]-newHigh)*self.yAxisRatio
                
                element.bottomHandle.label.setText(self.fitInSevenChars(newLow))
                element.topHandle.label.setText(self.fitInSevenChars(newHigh))
                self.latestAxisUpdate = self.data.currentYattribute
            else:
                assert False
            self.data.adjustNumericOperation(axis,oldLow,oldHigh,newLow,newHigh)
        
        if signals.has_key('endAdjust'):
            self.data.applyCurrentOperation()
            self.app.notifySelection(self.latestAxisUpdate)

notifyaxischange
if xAxis:
            self.currentXaxis = self.data.axes[self.data.currentXattribute]
            ax = self.svgLayer.svg.xAxis
            ax.label.setText(self.data.currentXattribute)
            ax.lowLabel.setText(self.fitInSevenChars(self.currentXaxis.getMin()))
            ax.highLabel.setText(self.fitInSevenChars(self.currentXaxis.getMax()))
            self.xAxisRatio = float(self.currentXaxis.getMax() - self.currentXaxis.getMin()) / float(self.scatterBounds[2] - self.scatterBounds[0])
            self.notifySelection(self.data.currentXattribute)
        else:
            self.currentYaxis = self.data.axes[self.data.currentYattribute]
            ax = self.svgLayer.svg.yAxis
            ax.label.setText(self.data.currentYattribute)
            ax.lowLabel.setText(self.fitInSevenChars(self.currentYaxis.getMin()))
            ax.highLabel.setText(self.fitInSevenChars(self.currentYaxis.getMax()))
            self.yAxisRatio = float(self.currentYaxis.getMax() - self.currentYaxis.getMin()) / float(self.scatterBounds[3] - self.scatterBounds[1])
            self.notifySelection(self.data.currentYattribute)
notifyselection
            if axis == self.data.currentXaxis:
            dataAxis = self.currentXaxis
            visRanges = self.xRanges
            pixelRatio = self.xAxisRatio
            numericLeftPixel = self.scatterBounds[0]
            numericRightPixel = self.scatterBounds[2]
            
            i = len(visRanges) - 1
            while len(visRanges) > len(dataAxis.selectedValueRanges):
                visRanges[i].delete()
                del visRanges[i]
                i -= 1
            
            while len(visRanges) < len(dataAxis.selectedValueRanges):
                visRanges.append(visRanges[0].clone())
            
            for i,r in enumerate(dataAxis.selectedValueRanges):
                l = r[0]
                h = r[1]
                
                v = visRanges[i]
                
                # are parts (or all) of the selection hidden?
                rightPixel = numericRightPixel - (dataAxis.getMax()-h)/pixelRatio
                leftPixel = numericLeftPixel + (l-dataAxis.getMin())/pixelRatio
                
                if rightPixel + v.rightHandle.width() < numericLeftPixel or rightPixel > numericRightPixel:
                    v.rightHandle.hide()
                else:
                    v.rightHandle.label.setText(self.fitInSevenChars(h))
                    v.rightHandle.moveTo(rightPixel,v.rightHandle.top())
                    v.rightHandle.show()
                rightPixel = max(rightPixel,numericLeftPixel)
                rightPixel = min(rightPixel,numericRightPixel)
                
                if leftPixel < numericLeftPixel or leftPixel - v.leftHandle.width() > numericRightPixel:
                    v.leftHandle.hide()
                else:
                    v.leftHandle.label.setText(self.fitInSevenChars(l))
                    v.leftHandle.moveTo(leftPixel - v.leftHandle.width(), v.leftHandle.top())
                    v.leftHandle.show()
                leftPixel = min(numericRightPixel,leftPixel)
                leftPixel = max(numericLeftPixel,leftPixel)
                
                if leftPixel >= rightPixel:
                    v.bar.setSize(1,v.bar.height())
                
                v.bar.moveTo(leftPixel,v.bar.top())
                v.bar.setSize(rightPixel-leftPixel,v.bar.height())
                v.bar.show()
                
        elif axis == self.data.currentYaxis:
            dataAxis = self.currentYaxis
            visRanges = self.yRanges
            pixelRatio = self.yAxisRatio
            numericBottomPixel = self.scatterBounds[3]
            numericTopPixel = self.scatterBounds[1]
            
            i = len(visRanges) - 1
            while len(visRanges) > len(dataAxis.selectedValueRanges):
                visRanges[i].delete()
                del visRanges[i]
                i -= 1
            
            while len(visRanges) < len(dataAxis.selectedValueRanges):
                visRanges.append(visRanges[0].clone())
            
            for i,r in enumerate(dataAxis.selectedValueRanges):
                l = r[0]
                h = r[1]
                
                v = visRanges[i]
                
                # are parts (or all) of the selection hidden?
                topPixel = numericTopPixel + (dataAxis.getMax()-h)/pixelRatio
                bottomPixel = numericBottomPixel - (l-dataAxis.getMin())/pixelRatio
                
                if topPixel - v.topHandle.height() > numericBottomPixel or topPixel < numericTopPixel:
                    v.topHandle.hide()
                else:
                    v.topHandle.label.setText(self.fitInSevenChars(h))
                    v.topHandle.moveTo(v.topHandle.left(),topPixel - v.topHandle.height())
                    v.topHandle.show()
                topPixel = max(topPixel,numericTopPixel)
                topPixel = min(topPixel,numericBottomPixel)
                
                if bottomPixel > numericBottomPixel or bottomPixel + v.bottomHandle.height() < numericTopPixel:
                    v.bottomHandle.hide()
                else:
                    v.bottomHandle.label.setText(self.fitInSevenChars(l))
                    v.bottomHandle.moveTo(v.bottomHandle.left(),bottomPixel)
                    v.bottomHandle.show()
                bottomPixel = min(bottomPixel,numericBottomPixel)
                bottomPixel = max(bottomPixel,numericTopPixel)
                
                if topPixel >= bottomPixel:
                    v.bar.setSize(v.bar.width(),1)
                
                v.bar.moveTo(v.bar.left(),topPixel)
                v.bar.setSize(v.bar.width(),bottomPixel-topPixel)
                v.bar.show()
        else:
            return


'''