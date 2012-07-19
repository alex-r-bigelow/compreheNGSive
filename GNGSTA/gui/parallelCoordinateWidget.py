from layeredWidget import mutableSvgLayer, layeredWidget, layer
from resources.utils import fitInSevenChars
from dataModels.variantData import operation
from PySide.QtCore import *
from PySide.QtGui import *
import math

class axisHandler:
    def __init__(self, name, dataAxis, visAxis, visible, parent):
        self.name = name
        self.dataAxis = dataAxis
        self.visAxis = visAxis
        self.visible = visible
        self.parent = parent
        
        # handle
        # this is an ugly hack to get around SVG (and QtSvg)'s issues with text
        m = self.name.rfind('(')
        if m == -1:
            filename = ""
            attName = " ".join(self.name.split())
        else:
            filename = self.name[m:].strip()
            attName = " ".join(self.name[:m].strip().split())
        
        row1 = attName[:15]
        row2 = attName[15:]
        if len(row2) > 15:
            row2 = "..." + row2[-12:]
        row3 = filename
        if len(row3) > 15:
            row3 = row3[:12] + "..."
        
        self.visAxis.handle.label1.setText(row1)
        self.visAxis.handle.label2.setText(row2)
        self.visAxis.handle.label3.setText(row3)
        
        # numeric
        self.dataToPixelRatio = 1.0
        self.pixelToDataRatio = 1.0
        self.numericDataLow = self.dataAxis.getMin()
        self.numericDataHigh = self.dataAxis.getMax()
        self.numericPixelLow = self.visAxis.numeric.scrollDownBar.top()
        self.numericPixelHigh = self.visAxis.numeric.scrollUpBar.bottom()
        self.numericRanges = []
        if not self.dataAxis.hasNumeric():
            # TODO: hide/show at will....
            self.visAxis.numeric.delete()
            self.visAxis.categorical.scrollUpBar.translate(0,self.visAxis.spacer.top()-self.visAxis.categorical.scrollUpBar.top())
        else:
            if self.numericDataLow == self.numericDataHigh: # don't allow a numeric range of zero
                self.numericDataHigh += 1
            self.pixelToDataRatio = float(self.numericDataHigh-self.numericDataLow)/float(self.numericPixelHigh-self.numericPixelLow)
            self.dataToPixelRatio = 1.0/self.pixelToDataRatio
            self.visAxis.numeric.scrollUpBar.label.setText(fitInSevenChars(self.dataAxis.getMax()))
            self.visAxis.numeric.scrollDownBar.label.setText(fitInSevenChars(self.dataAxis.getMin()))
            self.numericRanges.append(self.visAxis.numeric.selectionGroup.selectionRange)
        
        self.draggedHandle = None
        self.draggedBoundIsLow = None
        self.draggedDistance = None
        self.draggedStart = None
        
        # categorical
        self.visibleLabels = {}
        self.visLabels = {}
        self.labelOrder = []
        self.bottomVisibleLabelIndex = 0
        self.topVisibleLabelIndex = 0
        
        # sort the items by set membership size, except put Allele Masked, Missing last
        temp = []
        for label,members in self.dataAxis.labels.iteritems():
            temp.append((len(members),label))
        
        numVisibles = 0
        for size,label in sorted(temp):
            if label == 'Allele Masked' or label == 'Missing':
                if size > 0:
                    self.visibleLabels[label] = True
                    numVisibles += 1
            else:
                self.labelOrder.append(label)    # include other labels, even if their sets are empty
                self.visibleLabels[label] = size > 0
                numVisibles += 1
        
        if self.visibleLabels.has_key('Allele Masked'):
            self.labelOrder.append('Allele Masked')
        else:
            self.visAxis.categorical.itemGroup.alleleMasked.delete()
        
        if self.visibleLabels.has_key('Missing'):
            self.labelOrder.append('Missing')
        else:
            self.visAxis.categorical.itemGroup.missing.delete()
        
        # draw the labels
        prototype = self.visAxis.categorical.itemGroup.textItem
        # attempt to distribute the labels evenly over the space we have... if there's not enough, leave a gap that's half the height of an element
        # TODO: also hide the arrows if we don't need them
        yTop = self.visAxis.categorical.scrollUpBar.bottom()
        self.labelTop = (self.visAxis.categorical.scrollUpBar.top()+yTop)/2
        yBottom = self.visAxis.categorical.scrollDownBar.top()
        self.labelBottom = (self.visAxis.categorical.scrollDownBar.bottom()+yBottom)/2
        self.itemHeight = prototype.height()
        
        numVisibles = max(1,numVisibles)
        self.yGap = max(self.itemHeight/2,(yBottom-(yTop+(numVisibles+1)*self.itemHeight))/numVisibles)  # the +1 accounts for a half height gap on the top and bottom
        yStart = yBottom-self.yGap-self.itemHeight
        yOffset = yStart
        xOffset = prototype.left()
        prototype.moveTo(xOffset,yOffset)
        
        # actually clone the elements bottom to top (we want to start with the missing/masked elements aligned if they exist)
        i = len(self.labelOrder)-1
        self.bottomVisibleLabelIndex = i
        for label in reversed(self.labelOrder):
            if label == 'Missing':
                self.visLabels[label] = self.visAxis.categorical.itemGroup.missing
            elif label == 'Allele Masked':
                self.visLabels[label] = self.visAxis.categorical.itemGroup.alleleMasked
            else:
                if yOffset < yTop:
                    continue
                self.visLabels[label] = prototype.clone()
                # this is an ugly hack to get around SVG (and QtSvg)'s issues with text
                screenLabel = label
                if len(screenLabel) > 15:
                    screenLabel = label[:7] + ".." + label[-6:]
                self.visLabels[label].label.setText(screenLabel)
            self.visLabels[label].translate(0,yOffset-yStart)
            self.visLabels[label].setAttribute('___label',label)
            if yOffset > yTop:
                self.topVisibleLabelIndex = i
            else:
                pass
                #self.visLabels[label].hide()
            yOffset -= self.yGap + self.itemHeight
            i -= 1
        prototype.delete()
        
        # (selections will be set by parallelCoordinateWidget.__init__'s call to updateParams)
    
    def dataToScreen(self, value):
        if not isinstance(value,str):
            if value == None or math.isinf(value):
                value = 'Missing'
            elif math.isnan(value):
                value = 'Allele Masked'
            else:
                return self.numericPixelLow + (value-self.numericDataLow)*self.dataToPixelRatio
        index = self.labelOrder.index(value)
        if index < self.topVisibleLabelIndex:
            return self.labelTop
        elif index > self.bottomVisibleLabelIndex:
            return self.labelBottom
        else:
            return (self.visLabels[value].background.top()+self.visLabels[value].background.bottom())/2
        
    
    def screenToData(self, value):
        return self.numericDataLow + (value-self.numericPixelLow)*self.pixelToDataRatio
    
    def updateParams(self, paramTuple):
        ranges = paramTuple[0]
        labels = paramTuple[1]
        
        if self.dataAxis.hasNumeric():
            while len(self.numericRanges) > len(ranges):
                self.numericRanges[-1].delete()
                del self.numericRanges[-1]
            
            while len(ranges) > len(self.numericRanges):
                self.numericRanges.append(self.numericRanges[-1].clone())
            
            for i,(low,high) in enumerate(ranges):
                v = self.numericRanges[i]
                screenLow = self.dataToScreen(low)
                screenHigh = self.dataToScreen(high)
                
                # are parts (or all) of the selection hidden?
                topPixel = self.dataToScreen(high)
                bottomPixel = self.dataToScreen(low)
                
                if topPixel < self.numericPixelHigh or topPixel - v.topHandle.height() > self.numericPixelLow:
                    v.topHandle.hide()
                else:
                    v.topHandle.label.setText(fitInSevenChars(high))
                    v.topHandle.moveTo(v.topHandle.left(),topPixel-v.topHandle.height())
                    v.topHandle.show()
                topPixel = max(topPixel,self.numericPixelHigh)
                topPixel = min(topPixel,self.numericPixelLow)
                
                if bottomPixel > self.numericPixelLow or bottomPixel + v.bottomHandle.height() < self.numericPixelHigh:
                    v.bottomHandle.hide()
                else:
                    v.bottomHandle.label.setText(fitInSevenChars(low))
                    v.bottomHandle.moveTo(v.bottomHandle.left(),bottomPixel)
                    v.bottomHandle.show()
                bottomPixel = min(self.numericPixelLow,bottomPixel)
                bottomPixel = max(self.numericPixelHigh,bottomPixel)
                
                if bottomPixel >= topPixel:
                    v.bar.setSize(v.bar.width(),1)
                
                v.bar.moveTo(v.bar.left(),topPixel)
                v.bar.setSize(v.bar.width(),bottomPixel-topPixel)
                v.bar.show()
        
        for label,element in self.visLabels.iteritems():
            if labels[label] == True:
                element.background.setAttribute('fill-opacity',0.19607843)
            elif labels[label] == False:
                element.background.setAttribute('fill-opacity',0.0)
    
    def startDrag(self, element):
        self.draggedHandle = element
        if self.draggedHandle.getAttribute('handleName') == 'top':
            self.draggedStart = element.top()
            self.draggedBoundIsLow = True
        else:
            self.draggedStart = element.bottom()
            self.draggedBoundIsLow = False
        self.draggedDistance = 0
    
    def handleDrag(self, element, delta):
        if self.draggedHandle == None:
            self.startDrag(element)
        original = self.draggedStart + self.draggedDistance
        projected = original + delta
        if self.draggedBoundIsLow:
            if delta < 0:
                projected = max(projected,self.draggedHandle.parent.topHandle.bottom(),self.numericPixelHigh)
            else:
                projected = min(projected,self.numericPixelLow)
        else:
            if delta < 0:
                projected = max(projected,self.numericPixelHigh)
            else:
                projected = min(projected,self.draggedHandle.parent.bottomHandle.top(),self.numericPixelLow)
                    
        delta = projected - original
        self.draggedDistance = projected - self.draggedStart
        
        self.draggedHandle.label.setText(fitInSevenChars(self.screenToData(projected)))
        return delta
    
    def endDrag(self):
        if self.draggedHandle == None:
            return
        start = self.screenToData(self.draggedStart)
        end = self.screenToData(self.draggedStart + self.draggedDistance)
        self.parent.app.newOperation(operation.NUMERIC_CHANGE,axis=self.dataAxis,start=start,end=end,isHigh=not self.draggedBoundIsLow)
        # this will eventually result in a call to self.notifySelection, so I don't really care about redrawing everything
        self.draggedBoundIsLow = None
        self.draggedDistance = None
        self.draggedStart = None
        self.draggedHandle = None
    
    def toggleLabel(self, label):
        self.parent.app.newOperation(operation.LABEL_TOGGLE,axis=self.dataAxis,label=label)
    
    def queryPixelRange(self, low, high):
        if self.dataAxis.hasNumeric():
            return self.dataAxis.tree.select(low=self.screenToData(low), high=self.screenToData(high), includeMasked=False, includeUndefined=False, includeMissing=False)
        else:
            return set()

class selectionLayer(layer):
    def __init__(self, size, dynamic, controller, prototypeLine, rsNumbers, opaqueBack = False):
        layer.__init__(self,size,dynamic)
        self.controller = controller
        self.rsNumbers = rsNumbers
        if opaqueBack:
            self.backgroundColor = Qt.white
        else:
            self.backgroundColor = Qt.transparent
        
        
        lineColor = QColor()
        lineColor.setNamedColor(prototypeLine.getAttribute('stroke'))
        lineColor.setAlphaF(float(prototypeLine.getAttribute('stroke-opacity')))
        self.pen = QPen(lineColor)
        
        self.pen.setWidthF(prototypeLine.getAttribute('stroke-width'))
    
    def handleFrame(self, event, signals):
        return signals
    
    def refreshLines(self, rsNumbers):
        self.rsNumbers = rsNumbers
        self.setDirty()
    
    def draw(self,painter):
        rsList = list(self.rsNumbers)
        
        self.image.fill(self.backgroundColor)
        painter.setPen(self.pen)
        lastA = self.controller.axisOrder[0]
        lastValues = self.controller.axes[lastA].dataAxis.getValues(rsList)
        lastX = self.controller.axes[lastA].visAxis.axisLine.left()
        for a in self.controller.axisOrder[1:]:
            values = self.controller.axes[a].dataAxis.getValues(rsList)
            x = self.controller.axes[a].visAxis.axisLine.left()
            for y0,y1 in zip(lastValues,values):
                y0 = self.controller.axes[lastA].dataToScreen(y0)
                y1 = self.controller.axes[a].dataToScreen(y1)
                painter.drawLine(lastX,y0,x,y1)
            lastA = a
            lastValues = values
            lastX = x

class parallelCoordinateWidget(layeredWidget):
    def __init__(self, data, app, parent=None):
        layeredWidget.__init__(self, parent)
        self.data = data
        self.app = app
        
        self.svgLayer = mutableSvgLayer('gui/svg/parallelCoordinates.svg',self)
        self.addLayer(self.svgLayer)
        
        self.axes = {}
        self.axisOrder = self.data.defaultAxisOrder()
        
        prototype = self.svgLayer.svg.axis
        
        self.axisTop = prototype.top()
        self.axisWidth = prototype.spacer.width()
        self.axisHeight = prototype.spacer.height()
        
        for a in self.axisOrder:
            current = prototype.clone()
            dataObj = self.data.axes[a]
            self.axes[a] = axisHandler(a,dataObj,current,True,self)
            self.axes[a].updateParams(self.app.activeParams[dataObj])
        
        prototype.delete()
        
        self.dragStartPixel = None
        self.dragStartIndex = None
        self.dragAxis = None
        self.dragTargetPixel = None
        
        self.numericRangeAxis = None
        
        self.normalCursor = QCursor(Qt.CrossCursor)
        self.mouseOverCursor = self.svgLayer.svg.generateCursor(self.svgLayer.svg.rangeCursor)
        self.mouseOverRadius = self.svgLayer.svg.rangeCursor.height()/2
        self.setCursor(self.normalCursor)
        self.svgLayer.svg.rangeCursor.delete()
        
        self.lastMouseAxis = None
        self.lastMouseLabel = None
        self.lastMouseNumeric = None
        
        self.highlightedLayer = selectionLayer(self.svgLayer.size,False,self,self.svgLayer.svg.highlightedLinePrototype,self.app.highlightedRsNumbers)
        self.addLayer(self.highlightedLayer,0)
        
        self.selectedLayer = selectionLayer(self.svgLayer.size,False,self,self.svgLayer.svg.selectedLinePrototype,self.app.activeRsNumbers,opaqueBack=True)
        self.addLayer(self.selectedLayer,0)
        
        self.alignAxes()
    
    def alignAxes(self):
        xOffset = 0
        for a in self.axisOrder:
            if self.axes[a].visible:
                self.axes[a].visAxis.moveTo(xOffset,self.axisTop)
                self.axes[a].visAxis.show()
                xOffset += self.axisWidth
            else:
                self.axes[a].visAxis.hide()
        self.totalWidth = xOffset
        newSize = QSize(xOffset,self.axisHeight)
        self.highlightedLayer.resize(newSize)
        self.selectedLayer.resize(newSize)
        self.svgLayer.resize(newSize)
        self.selectedLayer.refreshLines(self.app.activeRsNumbers)
    
    def toggleVisible(self, toggleVisible, applyImmediately=False):
        self.axes[toggleVisible].visible = not self.axes[toggleVisible].visible
        if applyImmediately:
            self.alignAxes()
    
    def swapAxes(self, left, right, applyImmediately=False):
        temp = self.axisOrder[left]
        self.axisOrder[left] = self.axisOrder[right]
        self.axisOrder[right] = temp
        if applyImmediately:
            self.alignAxes()
    
    def findVisibleAxisIndex(self, xPosition):
        index = int(xPosition/self.axisWidth)
        i = 0
        while i < index:
            if not self.axes[self.axisOrder[i]].visible:
                index += 1
            i += 1
        return index
    
    def startAxisDrag(self, element, x):
        if self.dragAxis != None:
            self.endAxisDrag()
        self.dragStartIndex = self.findVisibleAxisIndex(x)
        self.dragAxis = self.axisOrder[self.dragStartIndex]
        self.dragStartPixel = (self.dragStartIndex + 0.5)*self.axisWidth
        self.dragTargetPixel = self.dragStartPixel
    
    def axisDrag(self, element, x, delta):
        if self.dragAxis == None:
            self.startAxisDrag(element, x)
        original = self.dragTargetPixel
        self.dragTargetPixel += delta
        self.dragTargetPixel = max(-self.axisWidth/2,self.dragTargetPixel)
        self.dragTargetPixel = min(self.totalWidth+self.axisWidth/2,self.dragTargetPixel)
        delta = self.dragTargetPixel - original
        if delta != 0:
            self.axes[self.dragAxis].visAxis.translate(delta,0)
            if abs(self.dragTargetPixel-self.dragStartPixel) > self.axisWidth:
                targetIndex = self.findVisibleAxisIndex(self.dragTargetPixel)
                while self.dragStartIndex != targetIndex:
                    direction = 1 if targetIndex - self.dragStartIndex > 0 else -1
                    nextVisible = self.dragStartIndex + direction
                    while not self.axes[self.axisOrder[nextVisible]].visible:
                        self.swapAxes(nextVisible, self.dragStartIndex, applyImmediately=False)
                        nextVisible += direction
                    self.axes[self.axisOrder[nextVisible]].visAxis.translate(-direction*self.axisWidth,0)
                    self.swapAxes(nextVisible, self.dragStartIndex, applyImmediately=False)
                    self.dragStartIndex = nextVisible
                self.dragStartPixel = (self.dragStartIndex + 0.5)*self.axisWidth
                    
    
    def endAxisDrag(self):
        if self.dragAxis != None:
            self.axes[self.dragAxis].visAxis.translate(self.dragStartPixel-self.dragTargetPixel,0)
            self.dragAxis = None
            self.dragTargetPixel = None
            self.dragStartIndex = None
            self.dragTargetPixel = None
            self.selectedLayer.refreshLines(self.app.activeRsNumbers)
    
    def hideAxis(self, a):
        self.axes[a].visible = False
        self.alignAxes()
    
    def showAxis(self, a):
        self.axes[a].visible = True
        self.alignAxes()
    
    def notifySelection(self, rsNumbers, params, axis=None):
        if axis != None:
            self.axes[axis.name].updateParams(params[axis])
        else:
            for a,axHandler in self.axes.iteritems():
                axHandler.updateParams(params[axHandler.dataAxis])
        self.selectedLayer.refreshLines(rsNumbers)
    
    def canAdjustSelection(self):
        return not self.app.multipleSelected()
    
    def numericRangeDrag(self, element, delta):
        if self.numericRangeAxis == None:
            self.numericRangeAxis = self.findVisibleAxisIndex(element.left())
        return self.axes[self.axisOrder[self.numericRangeAxis]].handleDrag(element, delta)
    
    def endNumericRangeDrag(self):
        if self.numericRangeAxis != None:
            self.axes[self.axisOrder[self.numericRangeAxis]].endDrag()
        self.numericRangeAxis = None
    
    def toggleLabel(self, x, element):
        axis = self.axes[self.axisOrder[self.findVisibleAxisIndex(x)]]
        axis.toggleLabel(element.getAttribute('___label'))
    
    def notifyHighlight(self, rsNumbers):
        self.highlightedLayer.refreshLines(rsNumbers)
    
    def mouseLabel(self, x, element):
        return
        axis = self.axes[self.axisOrder[self.findVisibleAxisIndex(x)]]
        label = element.getAttribute('___label')
        #if self.lastMouseLabel != label or self.lastMouseAxis != axis:
        self.lastMouseLabel = label
        self.lastMouseAxis = axis
        self.app.notifyHighlight(axis.dataAxis.labels[label])
    
    def unMouseLabel(self):
        return
        if self.lastMouseAxis == None and self.lastMouseLabel == None:
            return
        self.lastMouseLabel = None
        self.lastMouseAxis = None
        self.app.notifyHighlight(set())
        
    def mouseIn(self, x, y):
        self.setCursor(self.mouseOverCursor)
        self.lastMouseNumeric = self.axes[self.axisOrder[self.findVisibleAxisIndex(x)]]
        self.app.notifyHighlight(self.lastMouseNumeric.queryPixelRange(y-self.mouseOverRadius,y+self.mouseOverRadius))
    
    def mouseOut(self):
        if self.lastMouseNumeric == None:
            return
        self.lastMouseNumeric = None
        self.setCursor(self.normalCursor)
        self.app.notifyHighlight(set())
    
    def handleEvents(self, event, signals):
        linesMoved = False
        att = self.axisOrder[self.findVisibleAxisIndex(event.x)]
        # context menu
        if event.contextRequested:
            contextMenu = QMenu(self)
            act = QAction(u'Hide Axis', self)
            contextMenu.addAction(act)
            if len(self.axisOrder) <= 1:
                act.setEnabled(False)
            
            axesMenu = QMenu(u'Show/Hide Axes', self)
            axesActions = QActionGroup(self)
            for a in self.axes.iterkeys():
                if a not in self.axisOrder:
                    act = QAction(a,self,checkable=True)
                    axesActions.addAction(act)
            for a in self.axisOrder:
                act = QAction(a,self,checkable=True)
                act.toggle()
                if len(self.axisOrder) <= 1:
                    act.setEnabled(False)
                axesActions.addAction(act)
            for act in axesActions.actions():
                axesMenu.addAction(act)
            contextMenu.addMenu(axesMenu)
            
            contextMenu.addSeparator()
            '''itemsMenu = QMenu("Show/Hide Values",parent=self)
            itemsActions = QActionGroup(self)
            # TODO - include icons for Numerical, Missing, and Allele Masked?
            for label in axis.dataAxis.labelOrder:
                act = QAction(label,self,checkable=True)
                if axis.dataAxis.visibleLabels[label] == None:
                    # disable labels if they're selected (force visible) or if they're empty (missing or masked, force hidden)
                    act.setEnabled(False)
                    if axis.dataAxis.selectedLabels[label]:
                        act.toggle()
                elif axis.dataAxis.visibleLabels[label] == True:
                    act.toggle()
                itemsActions.addAction(act)
            for act in itemsActions.actions():
                itemsMenu.addAction(act)
            contextMenu.addMenu(itemsMenu)
            
            contextMenu.addSeparator()'''
            contextMenu.addAction(u'Use as X axis')
            contextMenu.addAction(u'Use as Y axis')
            
            resultAction = contextMenu.exec_(QCursor.pos())
            
            if resultAction != None and resultAction != 0:
                # Hide axis
                if resultAction.text() == u'Hide Axis':
                    if att in self.axisOrder:
                        self.hideAxis(att)
                    linesMoved = True
                
                # Toggle axis
                if resultAction.actionGroup() == axesActions:
                    if resultAction.text() in self.axisOrder:
                        self.hideAxis(resultAction.text())
                    else:
                        self.showAxis(resultAction.text())
                    linesMoved = True
                '''
                # Toggle item
                if resultAction.actionGroup() == itemsActions:
                    label = resultAction.text()
                    hide = axis.dataAxis.visibleLabels[label]
                    if hide:
                        axis.visAxis[label].hide()
                    else:
                        axis.visAxis[label].show()
                    linesMoved = True
                '''
                # X axis
                if resultAction.text() == u'Use as X axis':
                    splash = QProgressDialog("Loading", "Cancel", 0, 100, parent=None)
                    splash.setWindowModality(Qt.WindowModal)
                    
                    self.data.setScatterAxes(att,self.data.currentYattribute,splash)
                    self.app.notifyAxisChange(xAxis=True)
                    splash.close()
                
                # Y axis
                if resultAction.text() == u'Use as Y axis':
                    splash = QProgressDialog("Loading", "Cancel", 0, 100, parent=None)
                    splash.setWindowModality(Qt.WindowModal)
                    
                    self.data.setScatterAxes(self.data.currentXattribute,att,splash)
                    self.app.notifyAxisChange(xAxis=False)
                    splash.close()
        
        if linesMoved:
            self.highlightedLayer.refreshLines(self.app.highlightedRsNumbers)
        
        return signals

