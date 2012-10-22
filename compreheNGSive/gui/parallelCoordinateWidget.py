from layeredWidget import mutableSvgLayer, layeredWidget, layer
from resources.generalUtils import fitInSevenChars
from resources.genomeUtils import variant
from dataModels.variantData import operation
from PySide.QtCore import Qt, QSize
from PySide.QtGui import QColor, QPen, QCursor, QMenu, QActionGroup, QAction, QPainter
import math

class labelHandler:
    def __init__(self, name, latticeNumber, p=None, n=None, pv=None, nv=None, visElement=None):
        self.name = name
        self.latticeNumber = latticeNumber
        self.p = p
        self.n = n
        self.pv = pv
        self.nv = nv
        self.visElement = visElement
        self.hidden = False

class axisHandler:
    def __init__(self, name, vData, visAxis, visible, parent):
        self.name = name
        self.vData = vData
        self.dataAxis = vData.axisLookups[self.name]
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
        self.numericDataLow = self.dataAxis.minimum
        self.numericDataHigh = self.dataAxis.maximum
        self.numericPixelLow = self.visAxis.numeric.scrollDownBar.top()
        self.numericPixelHigh = self.visAxis.numeric.scrollUpBar.bottom()
        self.numericRanges = []
        if not self.dataAxis.hasNumeric:
            #TODO: hide/show numeric area via context menu....
            self.visAxis.numeric.delete()
            self.visAxis.categorical.scrollUpBar.translate(0,self.visAxis.spacer.top()-self.visAxis.categorical.scrollUpBar.top())
        else:
            if self.numericDataLow == self.numericDataHigh: # don't allow a numeric range of zero
                self.numericDataHigh += 1
            self.pixelToDataRatio = float(self.numericDataHigh-self.numericDataLow)/float(self.numericPixelHigh-self.numericPixelLow)
            self.dataToPixelRatio = 1.0/self.pixelToDataRatio
            self.visAxis.numeric.scrollUpBar.label.setText(fitInSevenChars(self.dataAxis.maximum))
            self.visAxis.numeric.scrollDownBar.label.setText(fitInSevenChars(self.dataAxis.minimum))
            self.numericRanges.append(self.visAxis.numeric.selectionGroup.selectionRange)
        
        self.draggedHandle = None
        self.draggedBoundIsLow = None
        self.draggedDistance = None
        self.draggedStart = None
        
        # categorical
        self.rootCatNode = None
        self.tailCatNode = None
        self.catLattice = {-1:set()}    # lattice number to labelHandler; -1 and 1 more than the number of possible spaces are for offscreen, hidden nodes
        self.cats = {}  # label to lattice number
        self.visPool = {'Allele Masked':None,'Missing':None,'Text Items':[]}
        
        # figure out some globals
        self.labelTop = self.visAxis.categorical.scrollUpBar.bottom()
        self.labelBottom = self.visAxis.categorical.scrollDownBar.top()
        self.itemHeight = self.visAxis.categorical.itemGroup.alleleMasked.height()  # allele masked is the tallest one
        
        # sort the items by set membership size, except put Allele Masked, Missing last. Also populate the visPool with the right number of elements
        temp = []
        
        for label in self.dataAxis.categoricalKeys:
            if label == 'Allele Masked' or label == 'Missing':
                continue
            temp.append((self.dataAxis.lookup.count(label),label))
            poolItem = self.visAxis.categorical.itemGroup.textItem.clone()
            self.visPool['Text Items'].append(poolItem)
        temp = sorted(temp)
        self.visAxis.categorical.itemGroup.textItem.delete()
        
        numMasked = self.dataAxis.lookup.count('Allele Masked')
        if numMasked > 0:
            temp.append((numMasked,'Allele Masked'))
            self.visPool['Allele Masked'] = self.visAxis.categorical.itemGroup.alleleMasked
        else:
            self.visAxis.categorical.itemGroup.alleleMasked.delete()
        
        numMissing = self.dataAxis.lookup.count('Missing')
        if numMissing > 0:
            temp.append((numMissing,'Missing'))
            self.visPool['Missing'] = self.visAxis.categorical.itemGroup.missing
        else:
            self.visAxis.categorical.itemGroup.missing.delete()
        
        # Figure out some more globals now that we know how many/which items we have
        self.numVisibleCats = len(temp)
        self.allCatsVisible = self.maximizeLatticeSpace()
        
        # create nodes from the end of the list to the beginning - we know the bottom scroll arrow will start hidden
        self.visAxis.categorical.scrollDownBar.hide()
        if self.allCatsVisible:
            self.visAxis.categorical.scrollUpBar.hide()
        self.catLattice[self.latticeLength] = set()
        
        latticeNumber = self.latticeLength-1
        if self.numVisibleCats == 0:
            self.rootCatNode = None
        else:
            self.rootCatNode = labelHandler(temp[-1][1], latticeNumber)
            self.cats[temp[-1][1]] = latticeNumber
            self.assignVisElement(self.rootCatNode, None)
            
            lastNode = self.rootCatNode
            latticeNumber -= 1
            for size,label in reversed(temp[:-1]):
                newNode = labelHandler(label,latticeNumber)
                self.cats[label] = latticeNumber
                if latticeNumber > -1:
                    self.assignVisElement(newNode, lastNode)
                    self.catLattice[latticeNumber] = newNode
                    latticeNumber -= 1
                    if latticeNumber == 0:
                        self.tailCatNode = newNode
                else:
                    self.catLattice[-1].add(newNode)
                lastNode.p = newNode
                newNode.n = lastNode
                lastNode = newNode
        # hide everything that's unused in the visPool
        for v in self.visPool['Text Items']:
            v.hide()
                
        # (selections will be set by parallelCoordinateWidget.__init__'s call to updateParams)
    
    def maximizeLatticeSpace(self):
        # sets some globals, returns true if all the labels fit in the given space
        self.cellSize = (self.labelBottom-self.labelTop)/float(max(1,self.numVisibleCats))  # if they all can fit, use all the space
        if self.cellSize >= self.itemHeight:
            self.latticeLength = int((self.labelBottom-self.labelTop)/self.cellSize)
            return True
        else:
            self.latticeLength = int((self.labelBottom-self.labelTop)/self.itemHeight)
            self.cellSize = (self.labelBottom-self.labelTop)/float(self.latticeLength)  # otherwise use the most space we can
            return False
    
    def assignVisElement(self, newNode, lastNode):
        if newNode.name == 'Missing':
            newNode.visElement = self.visPool['Missing']
            newNode.visElement.show()
            self.visPool['Missing'] = None
        elif newNode.name == 'Allele Masked':
            newNode.visElement = self.visPool['Allele Masked']
            newNode.visElement.show()
            self.visPool['Allele Masked'] = None
        else:
            newNode.visElement = self.visPool['Text Items'].pop()
        screenLabel = newNode.name
        if len(screenLabel) > 15:
            screenLabel = screenLabel[:10] + ".." + screenLabel[-3:]
        newNode.visElement.label.setText(screenLabel)
        newNode.visElement.setAttribute('___label',newNode.name)
        newNode.visElement.translate(0,self.labelTop-newNode.visElement.top()+self.cellSize*newNode.latticeNumber+0.5*(self.cellSize-self.itemHeight))
        if lastNode != None:
            lastNode.pv = newNode
            newNode.nv = lastNode
    
    def unassignVisElement(self, node):
        # break the connections
        if node.pv != None:
            node.pv.nv = None
            node.pv = None
        if node.nv != None:
            node.nv.pv = None
            node.nv = None
        # strip the visElement off the node and return it to the pool
        if node.name == 'Allele Masked':
            node.visElement.hide()
            self.visPool['Allele Masked'] = node.visElement
        elif node.name == 'Missing':
            node.visElement.hide()
            self.visPool['Missing'] = node.visElement
        else:
            self.visPool['Text Items'].append(node.visElement)
        node.visElement = None
    
    def scrollDown(self):
        # find the new node to add stuff to (and make sure we even CAN scroll)
        nodeToAdd = self.tailCatNode
        while nodeToAdd != None and nodeToAdd.hidden == True:
            nodeToAdd = nodeToAdd.p
        if nodeToAdd == None or nodeToAdd == self.tailCatNode:
            return
        
        # Show the bottom scroll bar, do a quick check to see if we can hide the top
        self.visAxis.categorical.scrollDownBar.show()
        hasPrev = False
        temp = nodeToAdd.p
        while True:
            if temp == None:
                break
            if temp.hidden == True:
                temp = temp.p
            else:
                hasPrev = True
                break
        if not hasPrev:
            self.visAxis.categorical.scrollUpBar.hide()
        
        # update the lattice and move visElements - add one from everybody and reassign to the appropriate bins
        self.rootCatNode.latticeNumber = self.latticeLength
        self.catLattice[self.latticeLength].add(self.rootCatNode)
        temp = self.rootCatNode.pv
        while temp != None:
            temp.latticeNumber += 1
            self.catLattice[temp.latticeNumber] = temp
            temp.visElement.translate(0,self.cellSize)
            temp = temp.pv
        self.catLattice[-1].remove(nodeToAdd)
        nodeToAdd.latticeNumber = 0
        self.catLattice[0] = nodeToAdd
        
        # reassign the root node
        temp = self.rootCatNode.pv
        self.unassignVisElement(self.rootCatNode)
        self.rootCatNode = temp
        
        # reassign the tail node
        self.assignVisElement(nodeToAdd, self.tailCatNode, 0)
        self.tailCatNode = nodeToAdd
    
    def scrollUp(self):
        # TODO
        pass
    
    def dataToScreen(self, values):
        results = []
        if not isinstance(values,list):
            values = [values]
        for value in values:
            try:
                value = float(value)
                if math.isinf(value):
                    value = 'Missing'
                elif math.isinf(value):
                    value = 'Allele Masked'
            except (ValueError,TypeError):
                if value == variant.MISSING or value == None:
                    value = 'Missing'
                elif value == variant.ALLELE_MASKED:
                    value = 'Allele Masked'
            
            if isinstance(value,str):
                index = self.cats.get(value,len(self.cats)-1)
                if index < 0:
                    results.append(self.labelTop)
                elif index > self.latticeLength:
                    results.append(self.labelBottom)
                else:
                    results.append(self.labelTop + (index+0.5)*self.cellSize)
            else:
                results.append(self.numericPixelLow + (value-self.numericDataLow)*self.dataToPixelRatio)
        return results
    
    def screenToData(self, value):
        return self.numericDataLow + (value-self.numericPixelLow)*self.pixelToDataRatio
    
    def updateNumeric(self, ranges):
        if self.dataAxis.hasNumeric:
            while len(self.numericRanges) > len(ranges):
                self.numericRanges[-1].delete()
                del self.numericRanges[-1]
            
            while len(ranges) > len(self.numericRanges):
                self.numericRanges.append(self.numericRanges[-1].clone())
            
            for i,(low,high) in enumerate(ranges):
                v = self.numericRanges[i]
                
                # are parts (or all) of the selection hidden?
                topPixel = self.dataToScreen(high)[0]
                bottomPixel = self.dataToScreen(low)[0]
                
                if topPixel < self.numericPixelHigh or topPixel - v.topHandle.height() > self.numericPixelLow:
                    v.topHandle.hide()
                else:
                    v.topHandle.label.setText(fitInSevenChars(high))
                    v.topHandle.moveTo(v.topHandle.left(),topPixel-v.topHandle.height())
                    v.topHandle.show()
                topPixel = max(topPixel,self.numericPixelHigh)
                topPixel = min(topPixel,self.numericPixelLow)
                
                if bottomPixel > self.numericPixelLow+1 or bottomPixel + v.bottomHandle.height() < self.numericPixelHigh:
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
    
    def updateLabels(self, labels):
        n = self.rootCatNode
        while n != None:
            if n.name in labels:
                n.visElement.background.setAttribute('fill','#1B9E77')
                n.visElement.originalColor = '#1B9E77'
            else:
                n.visElement.background.setAttribute('fill','#FFFFFF')
                n.visElement.originalColor = '#FFFFFF'
            n = n.pv
    
    def updateParams(self, paramTuple):
        ranges = paramTuple[0]
        labels = paramTuple[1]
        
        self.updateNumeric(ranges)
        self.updateLabels(labels)
    
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
        self.parent.app.intMan.newOperation(operation.NUMERIC_CHANGE,att=self.name,start=start,end=end,isHigh=not self.draggedBoundIsLow)
        # this will eventually result in a call to self.notifySelection, so I don't really care about redrawing everything
        self.draggedBoundIsLow = None
        self.draggedDistance = None
        self.draggedStart = None
        self.draggedHandle = None
    
    def toggleLabel(self, label):
        self.parent.app.intMan.newOperation(operation.LABEL_TOGGLE,att=self.name,label=label)
        return label in self.parent.app.intMan.activeParams[self.name][1]
    
    def queryPixelRange(self, low, high):
        if self.dataAxis.hasNumeric:
            return self.dataAxis.query(ranges=[(self.screenToData(high), self.screenToData(low))],labels=set()) # reverse low and high
        else:
            return set()
    
    def scrollCat(self, delta):
        return
        while delta > 0:
            self.scrollUp()
            delta -= 1
        while delta < 0:
            self.scrollDown()
            delta += 1

'''class rasterLayer(layer):
    def __init__(self, size, dynamic, controller, prototypeDot, opaqueBack = False):
        layer.__init__(self,size,dynamic)
        self.controller = controller
        if opaqueBack:
            self.backgroundColor = Qt.white
        else:
            self.backgroundColor = Qt.transparent
        
        dotColor = QColor()
        dotColor.setNamedColor(prototypeDot.getAttribute('fill'))
        dotColor.setAlphaF(float(prototypeDot.getAttribute('fill-opacity')))
        self.pen = QPen(dotColor)
        
        self.dotWidth = prototypeDot.width()
        self.dotHeight = prototypeDot.height()
        
        self.halfDotWidth = self.dotWidth/2
        self.halfDotHeight = self.dotHeight/2'''

class selectionLayer(layer):
    def __init__(self, size, dynamic, controller, prototypeLine, opaqueBack = False):
        layer.__init__(self,size,dynamic)
        self.controller = controller
        self.points = set()
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
    
    def refreshLines(self, points):
        self.points = points
        self.setDirty()
    
    def draw(self,painter):
        if len(self.points) >= self.controller.app.resolution_threshold:
            return
        pointList = list(self.points)
        self.image.fill(self.backgroundColor)
        painter.setPen(self.pen)
        painter.setRenderHint(QPainter.Antialiasing)
        lastA = self.controller.axisOrder[0]
        lastValues = self.controller.vData.getData(pointList,lastA)
        lastX = self.controller.axes[lastA].visAxis.axisLine.left()
        for a in self.controller.axisOrder[1:]:
            if not self.controller.axes[a].visible:
                continue
            values = self.controller.vData.getData(pointList,a)
            x = self.controller.axes[a].visAxis.axisLine.left()
            for y0,y1 in zip(lastValues,values):
                y0 = self.controller.axes[lastA].dataToScreen(y0)
                y1 = self.controller.axes[a].dataToScreen(y1)
                if len(y0) > len(y1):
                    if len(y1) > 1:
                        raise Exception("Mismatched number of values between attributes: %s %s" % (y0,y1))
                    else:
                        for y00 in y0:
                            painter.drawLine(lastX,y00,x,y1[0])
                elif len(y1) > len(y0):
                    if len(y0) > 1:
                        raise Exception("Mismatched number of values between attributes: %s %s" % (y0,y1))
                    else:
                        for y11 in y1:
                            painter.drawLine(lastX,y0[0],x,y11)
                else:
                    for i,y00 in enumerate(y0):
                        painter.drawLine(lastX,y00,x,y1[i])
            lastA = a
            lastValues = values
            lastX = x

class parallelCoordinateWidget(layeredWidget):
    def __init__(self, vData, app, parent=None):
        layeredWidget.__init__(self, parent)
        self.vData = vData
        self.app = app
        
        self.svgLayer = mutableSvgLayer('gui/svg/parallelCoordinates.svg',self)
        self.addLayer(self.svgLayer)
        
        self.axes = {}
        self.axisOrder = sorted(self.vData.axisLookups.iterkeys())
        self.numVisibleAxes = len(self.axisOrder)
        
        prototype = self.svgLayer.svg.axis
        
        self.axisTop = prototype.top()
        self.axisWidth = prototype.spacer.width()
        self.columnConversion = 1.0/self.axisWidth
        self.axisHeight = prototype.spacer.height()
        
        for att in self.axisOrder:
            current = prototype.clone()
            self.axes[att] = axisHandler(att,self.vData,current,True,self)
            self.axes[att].updateParams(self.app.intMan.activeParams[att])
        
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
        
        self.normalHandleColor = self.svgLayer.svg.normalHandleBackground.getAttribute('fill')
        self.activeHandleColor = self.svgLayer.svg.activeHandleBackground.getAttribute('fill')
        
        self.lastMouseAxis = None
        self.lastMouseLabel = None
        self.lastMouseNumeric = None
        
        self.highlightedLayer = selectionLayer(self.svgLayer.size,False,self,self.svgLayer.svg.highlightedLinePrototype)
        self.addLayer(self.highlightedLayer,0)
        
        self.selectedLayer = selectionLayer(self.svgLayer.size,False,self,self.svgLayer.svg.selectedLinePrototype,opaqueBack=True)
        self.addLayer(self.selectedLayer,0)
        
        self.alignAxes(set())
    
    def alignAxes(self, activePoints, refreshImmediately=True):
        xOffset = 0
        for a in self.axisOrder:
            self.axes[a].visAxis.moveTo(xOffset,self.axisTop)
            if self.axes[a].visible:
                self.axes[a].visAxis.show()
                xOffset += self.axisWidth
            else:
                self.axes[a].visAxis.hide()
        
        self.axes[self.app.currentXattribute].visAxis.handle.background.setAttribute('fill',self.activeHandleColor)
        self.axes[self.app.currentYattribute].visAxis.handle.background.setAttribute('fill',self.activeHandleColor)
        
        self.totalWidth = xOffset
        newSize = QSize(xOffset,self.axisHeight)
        if refreshImmediately:
            self.svgLayer.resize(newSize)
            self.highlightedLayer.resize(newSize)
            self.selectedLayer.resize(newSize)
            self.selectedLayer.refreshLines(activePoints)
    
    def toggleVisible(self, att, refreshImmediately=True):
        self.axes[att].visible = not self.axes[att].visible
        if not self.axes[att].visible:
            self.axisOrder.remove(att)
            self.axisOrder.append(att)
            self.numVisibleAxes -= 1
        else:
            self.numVisibleAxes += 1
        self.alignAxes(self.app.intMan.activePoints,refreshImmediately)
    
    def swapAxes(self, left, right, refreshImmediately=True):
        temp = self.axisOrder[left]
        self.axisOrder[left] = self.axisOrder[right]
        self.axisOrder[right] = temp
        self.alignAxes(self.app.intMan.activePoints,refreshImmediately)
    
    def findAxisIndex(self, x):
        target = int(x*self.columnConversion)
        target = max(0,target)
        target = min(self.numVisibleAxes-1,target)
        return target
    
    def canAdjustSelection(self):
        return not self.app.intMan.multipleSelected()
    
    def startAxisDrag(self, element, x):
        if self.dragAxis != None:
            self.endAxisDrag()
        self.dragStartIndex = self.findAxisIndex(x)
        self.dragAxis = self.axisOrder[self.dragStartIndex]
        self.dragStartPixel = (self.dragStartIndex + 0.5)*self.axisWidth
        self.dragTargetPixel = self.dragStartPixel
    
    def axisDrag(self, element, x, delta):
        if self.dragAxis == None:
            self.startAxisDrag(element, x)
        original = self.dragTargetPixel
        self.dragTargetPixel += delta
        self.dragTargetPixel = max(-self.axisWidth*0.5,self.dragTargetPixel)
        self.dragTargetPixel = min(self.totalWidth+self.axisWidth*0.5,self.dragTargetPixel)
        delta = self.dragTargetPixel - original
        if delta != 0:
            self.axes[self.dragAxis].visAxis.translate(delta,0)
            if abs(self.dragTargetPixel-self.dragStartPixel) > self.axisWidth:
                targetIndex = self.findAxisIndex(self.dragTargetPixel)
                direction = 1 if targetIndex - self.dragStartIndex > 0 else -1
                while self.dragStartIndex != targetIndex:
                    nextIndex = self.dragStartIndex + direction
                    if nextIndex >= 0 and nextIndex <= self.numVisibleAxes-1:
                        self.axes[self.axisOrder[nextIndex]].visAxis.translate(-direction*self.axisWidth,0)
                        self.dragStartPixel += direction*self.axisWidth
                        self.swapAxes(nextIndex, self.dragStartIndex, refreshImmediately=False)
                    self.dragStartIndex = nextIndex
    
    def endAxisDrag(self):
        if self.dragAxis != None:
            self.alignAxes(self.app.intMan.activePoints,refreshImmediately=True)
            self.dragAxis = None
            self.dragTargetPixel = None
            self.dragStartIndex = None
            self.dragTargetPixel = None
        
    def notifySelection(self, activePoints, params):
        for att,axHandler in self.axes.iteritems():
            axHandler.updateParams(params[att])
        self.selectedLayer.refreshLines(activePoints)
    
    def numericRangeDrag(self, element, delta):
        if self.numericRangeAxis == None:
            self.numericRangeAxis = self.findAxisIndex(element.left())
        return self.axes[self.axisOrder[self.numericRangeAxis]].handleDrag(element, delta)
    
    def endNumericRangeDrag(self):
        if self.numericRangeAxis != None:
            self.axes[self.axisOrder[self.numericRangeAxis]].endDrag()
        self.numericRangeAxis = None
    
    def toggleLabel(self, x, element):
        axis = self.axes[self.axisOrder[self.findAxisIndex(x)]]
        return axis.toggleLabel(element.getAttribute('___label'))
    
    def notifyAxisChange(self):
        self.alignAxes(self.app.intMan.activePoints, refreshImmediately=True)
    
    def notifyHighlight(self, rsNumbers):
        self.highlightedLayer.refreshLines(rsNumbers)
    
    def mouseLabel(self, x, element):
        axis = self.axes[self.axisOrder[self.findAxisIndex(x)]]
        label = element.getAttribute('___label')
        
        self.lastMouseLabel = label
        self.lastMouseAxis = axis
        self.app.notifyHighlight(self.app.intMan.activePoints.intersection(axis.dataAxis.query(ranges=[],labels={label:True})))
    
    def unMouseLabel(self):
        if self.lastMouseAxis == None and self.lastMouseLabel == None:
            return
        self.lastMouseLabel = None
        self.lastMouseAxis = None
        self.app.notifyHighlight(set())
        
    def mouseIn(self, x, y):
        self.setCursor(self.mouseOverCursor)
        self.lastMouseNumeric = self.axes[self.axisOrder[self.findAxisIndex(x)]]
        self.app.notifyHighlight(self.app.intMan.activePoints.intersection(self.lastMouseNumeric.queryPixelRange(y-self.mouseOverRadius,y+self.mouseOverRadius)))
    
    def mouseOut(self):
        if self.lastMouseNumeric == None:
            return
        self.lastMouseNumeric = None
        self.setCursor(self.normalCursor)
        self.app.notifyHighlight(set())
    
    def scrollCat(self, x, delta):
        self.axes[self.axisOrder[self.findAxisIndex(x)]].scrollCat(delta)
    
    def handleEvents(self, event, signals):
        att = self.axisOrder[self.findAxisIndex(event.x)]
        # context menu
        if event.contextRequested:
            contextMenu = QMenu(self)
            
            contextMenu.addAction(u'Select all')
            contextMenu.addAction(u'Select none')
            
            contextMenu.addSeparator()
            
            
            act = QAction(u'Hide Axis', self)
            contextMenu.addAction(act)
            if len(self.axisOrder) <= 1:
                act.setEnabled(False)
            
            axesMenu = QMenu(u'Show/Hide Axes', self)
            axesActions = QActionGroup(self)
            for a in self.axisOrder:
                act = QAction(a,self,checkable=True)
                if self.axes[a].visible:
                    act.toggle()
                if len(self.axisOrder) <= 1:
                    act.setEnabled(False)
                axesActions.addAction(act)
            for act in axesActions.actions():
                axesMenu.addAction(act)
            contextMenu.addMenu(axesMenu)
            
            contextMenu.addSeparator()
            
            contextMenu.addAction(u'Use as X axis')
            contextMenu.addAction(u'Use as Y axis')
            
            resultAction = contextMenu.exec_(QCursor.pos())
            
            if resultAction != None and resultAction != 0:
                # Select all
                if resultAction.text() == u'Select all':
                    self.app.intMan.newOperation(operation.ALL,att=att.dataAxis)
                
                # Select none
                if resultAction.text() == u'Select none':
                    self.app.intMan.newOperation(operation.NONE,att=att.dataAxis)
                
                # Hide axis
                if resultAction.text() == u'Hide Axis':
                    self.toggleVisible(att)
                
                # Toggle axis
                if resultAction.actionGroup() == axesActions:
                    self.toggleVisible(resultAction.text())

                # X axis
                if resultAction.text() == u'Use as X axis':
                    if self.app.currentYattribute != self.app.currentXattribute:
                        self.axes[self.app.currentXattribute].visAxis.handle.background.setAttribute('fill',self.normalHandleColor)
                        self.axes[self.app.currentXattribute].visAxis.handle.originalBackgroundColor = self.normalHandleColor
                    self.axes[att].visAxis.handle.background.setAttribute('fill',self.activeHandleColor)
                    self.axes[att].visAxis.handle.originalBackgroundColor = self.activeHandleColor
                    
                    self.app.notifyAxisChange(att,xAxis=True)
                
                # Y axis
                if resultAction.text() == u'Use as Y axis':
                    if self.app.currentXattribute != self.app.currentYattribute:
                        self.axes[self.app.currentYattribute].visAxis.handle.background.setAttribute('fill',self.normalHandleColor)
                        self.axes[self.app.currentYattribute].visAxis.handle.originalBackgroundColor = self.normalHandleColor
                    self.axes[att].visAxis.handle.background.setAttribute('fill',self.activeHandleColor)
                    self.axes[att].visAxis.handle.originalBackgroundColor = self.activeHandleColor
                    
                    self.app.notifyAxisChange(att,xAxis=False)
        
        #if linesMoved:
        #    self.highlightedLayer.refreshLines(self.app.highlightedRsNumbers)
        
        return signals

