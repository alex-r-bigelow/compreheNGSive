from layeredWidget import mutableSvgLayer, layeredWidget
from PySide.QtCore import *
from PySide.QtGui import *

class axisWrapper:
    def __init__(self, dataAxis, visAxis):
        self.dataAxis = dataAxis
        self.visAxis = visAxis

class parallelCoordinateWidget(layeredWidget):
    def __init__(self, data, parent = None):
        layeredWidget.__init__(self, parent)
        self.data = data
        
        self.axes = {}
        self.axisOrder = []
        
        # Init axes, svg layer
        
        self.svgLayer = mutableSvgLayer('gui/svg/parallelCoordinates.svg',self)
        
        prototype = self.svgLayer.svg.getElement('axis')
        self.w = prototype.spacer.width()
        self.h = prototype.spacer.height()
        self.yOffset = prototype.top()
        xOffset = 0
        for att,ax in self.data.axes.iteritems():
            self.axisOrder.append(att)
            current = prototype.clone()
            
            # Label
            # this is an ugly hack to get around SVG (and QtSvg)'s issues with text
            m = att.rfind('(')
            if m == -1:
                filename = ""
                attName = " ".join(att.split())
            else:
                filename = att[m:].strip()
                attName = " ".join(att[:m].strip().split())
            
            row1 = attName[:16]
            row2 = attName[16:]
            if len(row2) > 16:
                row2 = "..." + row2[-13:]
            row3 = filename
            if len(row3) > 16:
                row3 = row3[:13] + "..."
            
            current.handle.label1.setText(row1)
            current.handle.label2.setText(row2)
            current.handle.label3.setText(row3)
            current.moveTo(xOffset,self.yOffset)
            current.setAttribute('att',att)
            
            # Items
            y = current.itemGroup.top()
            itemGap = current.scrollUpBar.height()
            
            keepNumeric = False
            keepAlleleMasked = False
            keepMissing = False
            
            ax.visItems = {}
            
            for l in ax.getLabels():
                if l == 'Numeric':
                    if ax.hasNumeric():
                        keepNumeric = True
                        
                        high = ax.getMax()
                        low = ax.getMin()
                        bottom = current.numeric.scrollDownBar.top()
                        top = current.numeric.scrollUpBar.bottom()
                        ratio = float(high-low)/float(bottom-top)
                        if ratio == 0:
                            ratio = 1
                        
                        current.numeric.bottomValue = low
                        current.numeric.topValue = high
                        current.numeric.numberToPixelRatio = ratio
                        current.numeric.scrollUpBar.label.setText(self.fitInSevenChars(high))
                        current.numeric.scrollDownBar.label.setText(self.fitInSevenChars(low))
                        current.numeric.visRanges = {(low,high):current.numeric.selectionGroup.selectionRange}
                        self.settleNumericView(ax,current)
                        
                elif l == 'Allele Masked':
                    if ax.hasMasked():
                        keepAlleleMasked = True
                        current.itemGroup.alleleMasked.moveTo(current.itemGroup.alleleMasked.left(),y)
                        y += current.itemGroup.alleleMasked.height() + itemGap
                        ax.visItems[l] = current.itemGroup.alleleMasked
                elif l == 'Missing':
                    if ax.hasMissing():
                        keepMissing = True
                        current.itemGroup.missing.moveTo(current.itemGroup.missing.left(),y)
                        y += current.itemGroup.missing.height() + itemGap
                        ax.visItems[l] = current.itemGroup.missing
                else:
                    newItem = current.itemGroup.textItem.clone()
                    newItem.moveTo(newItem.left(),y)
                    y += newItem.height() + itemGap
                    ax.visItems[l] = newItem
                    
                    # this is an ugly hack to get around SVG (and QtSvg)'s issues with text
                    screenLabel = l
                    if len(screenLabel) > 15:
                        screenLabel = l[:7] + ".." + l[-6:]
                    newItem.label.setText(screenLabel)
                    
            
            if not keepNumeric:
                current.numeric.delete()
                current.scrollUpBar.moveTo(current.scrollUpBar.left(),0)
            if not keepAlleleMasked:
                current.itemGroup.alleleMasked.delete()
            if not keepMissing:
                current.itemGroup.missing.delete()
            current.itemGroup.textItem.delete()
            
            self.axes[att] = axisWrapper(ax,current)
            xOffset += self.w
        prototype.delete()
        
        self.svgLayer.resize(QSize(xOffset-self.w,self.h))
        
        self.addLayer(self.svgLayer)
        
        self.sourceIndex = None
        self.currentAtt = self.axisOrder[0]
        
        # Init selection, mouse layers
    
    def scrollNumeric(self, axis, factor):
        factor = factor*axis.visAxis.numeric.numberToPixelRatio
        axis.visAxis.numeric.topValue += factor
        axis.visAxis.numeric.bottomValue += factor
        self.settleNumericView(axis.dataAxis, axis.visAxis)
    
    def zoom(self, axis, factor):
        midpoint = (axis.visAxis.numeric.topValue + axis.visAxis.numeric.bottomValue)/2
        axis.visAxis.numeric.topValue = (axis.visAxis.numeric.topValue - midpoint)/factor + midpoint
        axis.visAxis.numeric.bottomValue = midpoint - (midpoint - axis.visAxis.numeric.bottomValue)/factor
        axis.visAxis.numeric.numberToPixelRatio /= factor
        self.settleNumericView(axis.dataAxis, axis.visAxis)
    
    def settleNumericView(self, dataAxis, visAxis):
        numberItem = visAxis.numeric
        numberItem.scrollUpBar.label.setText(self.fitInSevenChars(numberItem.topValue))
        numberItem.scrollDownBar.label.setText(self.fitInSevenChars(numberItem.bottomValue))
        
        for r in dataAxis.selectedValueRanges:
            l = r[0]
            h = r[1]
            
            v = numberItem.visRanges[(l,h)]
            t = numberItem.scrollUpBar.bottom()
            b = numberItem.scrollDownBar.top()
            r = numberItem.numberToPixelRatio
            
            # are parts (or all) of the selection hidden?
            topPixel = (numberItem.topValue-h)/r
            bottomPixel = topPixel + (h-l)/r
            
            if topPixel < 0 or topPixel - v.topHandle.height() > b:
                v.topHandle.hide()
            else:
                v.topHandle.label.setText(self.fitInSevenChars(h))
                v.topHandle.moveTo(v.topHandle.left(),t+topPixel-v.topHandle.height())
                v.topHandle.show()
            topPixel = max(topPixel,0)
            topPixel = min(topPixel,b)
            
            if bottomPixel > b or bottomPixel + v.bottomHandle.height() < 0:
                v.bottomHandle.hide()
            else:
                v.bottomHandle.label.setText(self.fitInSevenChars(l))
                v.bottomHandle.moveTo(v.bottomHandle.left(),t+bottomPixel)
                v.bottomHandle.show()
            bottomPixel = min(b,bottomPixel)
            bottomPixel = max(0,bottomPixel)
            
            if bottomPixel == topPixel:
                v.bar.hide()
            else:
                v.bar.moveTo(v.bar.left(),t+topPixel)
                v.bar.setSize(v.bar.width(),bottomPixel-topPixel)
                v.bar.show()
    
    def fitInSevenChars(self, value):
        result = "{:7G}".format(value)
        while len(result) > 7:
            if 'E' in result and result[1] != 'E':
                eind = result.find('E')
                offset = 1
                original = result
                while len(result) > 7 and result[1] != 'E':
                    result = original[:eind-offset] + original[eind:]
                    offset += 1
                if len(result) > 7:
                    result = "INF"
            else:
                while len(result) > 7:
                    result = result[:-1]
        while len(result) < 7:
            result = ' ' + result
        return result
    
    def hideAxis(self, att):
        assert att in self.axisOrder and len(self.axisOrder) > 1
        
        self.axes[att].visAxis.hide()
        index = self.axisOrder.index(att)
        del self.axisOrder[index]
        
        for a in self.axisOrder[index:]:
            self.axes[a].visAxis.translate(-self.w,0)
        self.svgLayer.resize(QSize(self.w*len(self.axisOrder),self.h))
    
    def showAxis(self, att):
        assert att not in self.axisOrder
        newIndex = len(self.axisOrder)
        self.axisOrder.append(att)
        self.axes[att].visAxis.show()
        self.axes[att].visAxis.moveTo(newIndex*self.w,self.yOffset)
        self.svgLayer.resize(QSize(self.w*len(self.axisOrder),self.h))
    
    def handleEvents(self, event, signals):
        linesMoved = False
        
        index = int(event.x/self.w)
        att = self.axisOrder[index]
        axis = self.axes[att]
        
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
            
            itemsMenu = QMenu("Show/Hide Values",parent=self)
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
            
            contextMenu.addSeparator()
            
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
                
                # Toggle item
                '''if resultAction.actionGroup() == itemsActions:
                    label = resultAction.text()
                    hide = axis.dataAxis.visibleLabels[label]
                    if hide:
                        axis.visAxis[label].hide()
                    else:
                        axis.visAxis[label].show()
                    linesMoved = True'''
                    
                
                # X axis
                if resultAction.text() == u'Use as X axis':
                    splash = QProgressDialog("Loading", "Cancel", 0, 100, parent=None)
                    splash.setWindowModality(Qt.WindowModal)
                    
                    self.data.setScatterAxes(att,self.data.currentYattribute,splash)
                    
                    splash.close()
                
                # Y axis
                if resultAction.text() == u'Use as Y axis':
                    splash = QProgressDialog("Loading", "Cancel", 0, 100, parent=None)
                    splash.setWindowModality(Qt.WindowModal)
                    
                    self.data.setScatterAxes(self.data.currentXattribute,att,splash)
                    
                    splash.close()
        
        # horizontal rearranging of axes
        if signals.has_key('dragAxisStart'):
            self.sourceIndex = index
        
        if signals.has_key('dragAxis') and self.sourceIndex != None:
            targetIndex = int((axis.visAxis.left()+axis.visAxis.right())/(2*self.w))
            
            while targetIndex != self.sourceIndex:
                if targetIndex > self.sourceIndex:
                    i = self.sourceIndex+1
                else:
                    i = self.sourceIndex-1
                temp = self.axisOrder[i]
                self.axes[temp].visAxis.translate((self.sourceIndex-i)*self.w,0)
                self.axisOrder[i] = self.axisOrder[self.sourceIndex]
                self.axisOrder[self.sourceIndex] = temp
                self.sourceIndex = i
        
        if signals.has_key('dragAxisEnd'):
            axis.visAxis.moveTo(self.sourceIndex*self.w,self.yOffset)
            linesMoved = True
        
        # vertical scrolling of axes - all handled by svg, but we need to note that the lines moved
        if signals.has_key('axisScrolled'):
            linesMoved = True
        
        # rearrangement/resizing of axis items
        
        # scrolling/zooming numeric area
        if signals.has_key('numericScrolled'):
            self.scrollNumeric(axis, signals['numericScrolled'])
            linesMoved = True
        
        if signals.has_key('numericZoomed'):
            self.zoom(axis, signals['numericZoomed'])
            linesMoved = True
        
        # adjustment of selections
        if signals.has_key('rangeAdjusted'):
            #print signals['rangeAdjusted']
            pass
        
        
        # moused-over data
        
        
        if linesMoved:
            pass
        
        # update selections
        
        # update moused layer