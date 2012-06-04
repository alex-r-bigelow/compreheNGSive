import math
"""
Note: this code may be kind of confusing because there are three data spaces at work:
datum, dataLow, dataHigh - data space
TODO: data index space
value, low, high - controller space from 0 to 1
pixel, pixelLow, pixelHigh - screen space (that may in some cases have multiple equivalent points when there are multiple viewing ranges)

Variables are named accordingly
"""

class controller:
    def __init__(self, data, app):
        self.data = data
        self.app = app
        
        self.app.bindController(self)
        
        self.axes = {}
        for att,ax in data.axes.iteritems():
            if ax.getDataType() == "number":
                visArgs = app.parallelCoordinates.addAxis(att,"number")
                self.axes[att] = numberAxis(ax,**visArgs)
            #elif ax.getDataType() == "string":
                #self.axes[att] = stringAxis(ax)
            #elif ax.getDataType() == "genome"
                #self.axes[att] = genomeAxis(ax)
        
        self.scatterPlot = scatter(self.data, self.axes)
        
        self.currentSelection = selection()
        self.selections = {self.currentSelection.name:self.currentSelection}
        self.highlighted = set()
    
    def getSelected(self):
        return list(self.currentSelection.current)
    
    def getHighlighted(self):
        return list(self.highlighted)
    
    def highlight(self, newSet):
        self.highlighted = newSet
    
    def getPoints(self, att, rsNumbers):
        return self.axes[att].getPixels(rsNumbers)

class visRange:
    def __init__(self, low, high, pixelLow, pixelHigh):
        self.low = low
        self.high = high
        self.pixelLow = pixelLow
        self.pixelHigh = pixelHigh
    
    def translateToScreen(self, value):
        if value < self.low or value > self.high:
            return None
        rangePosition = (value-self.low)/(self.high-self.low)
        return int(self.pixelLow + rangePosition*(self.pixelHigh-self.pixelLow))
    
    def translateFromScreen(self, pixel):
        rangePosition = (pixel-self.pixelLow)/(self.pixelHigh-self.pixelLow)
        return self.low + rangePosition*(self.high-self.low)
    
    def getSelections(self, selectionRanges):
        '''
        Takes list of tuple ranges in 0.0-1.0 controller space and returns pixel-space ranges for any visible ranges
        '''
        results = []
        for r in selectionRanges:
            firstPoint = None
            secondPoint = None
            if r[0] < self.low:
                if r[1] >= self.low:
                    firstPoint = self.low
            elif r[0] <= self.high:
                firstPoint = r[0]
            
            if r[1] > self.high:
                if r[0] <= self.high:
                    secondPoint = self.high
            elif r[1] >= self.low:
                secondPoint = r[1]
            
            if firstPoint != None and secondPoint != None:
                results.append((self.translateToScreen(firstPoint),self.translateToScreen(secondPoint)))

class scatter:
    def __init__(self, data, axes):
        self.data = data
        self.axes = axes
        self.currentXaxis = data.currentXattribute
        self.currentYaxis = data.currentYattribute
        
    def setNewXAxis(self, att):
        self.currentXaxis = att
        self.data.setScatterAxes(att,self.currentYaxis)
    
    def setNewYAxis(self, att):
        self.currentYaxis = att
        self.data.setScatterAxes(self.currentXaxis,att)
    
    def translateToData(self, x, y):
        return (self.axes[self.currentXaxis].translateToData(x),self.axes[self.currentYaxis].translateToData(y))
    
    def translateFromData(self, x, y):
        return (self.axes[self.currentXaxis].translateFromData(x),self.axes[self.currentYaxis].translateFromData(y))
    
    def countPopulation(x,y,x2,y2):
        x,y = self.translateToData(x,y)
        x2,y2 = self.translateToData(x,y)
        
        includeMaskedX = self.axes[currentXaxis].selectMasked
        includeUndefinedX = self.axes[currentXaxis].selectMissing
        includeMissingX = includeUndefinedX
        
        includeMaskedY = self.axes[currentYaxis].selectMasked
        includeUndefinedY = self.axes[currentYaxis].selectMissing
        includeMissingY = includeUndefinedY
        
        return self.data.scatter.countPopulation(x,y,x2,y2,includeMaskedX, includeMaskedY, includeUndefinedX, includeUndefinedY, includeMissingX, includeMissingY)

class numberAxis:
    def __init__(self, dataAxis, pixelWidth, pixelLow, pixelHigh, missingPixelY, maskedPixelY):
        self.dataAxis = dataAxis
        self.dataLow,self.dataHigh = self.findSensibleRange(dataAxis.getMin(), dataAxis.getMax())
        self.hasMissing = dataAxis.hasMissing()
        self.hasMasked = dataAxis.hasMasked()
        
        self.selectRanges = [] # [(low,high)]
        self.selectMissing = False
        self.selectMasked = False
        
        self.pixelWidth = pixelWidth
        self.pixelLow = pixelLow
        self.pixelHigh = pixelHigh
        self.missingPixelY = missingPixelY
        self.maskedPixelY = maskedPixelY
        self.reset()
    
    def translateToData(self, value):
        if value == None or math.isnan(value) or math.isinf(value):
            return value
        return self.dataLow + value*(self.dataHigh-self.dataLow)
    
    def translateFromData(self, datum):
        if datum == None or math.isnan(datum) or math.isinf(datum):
            return datum
        return (value-self.dataLow)/float(self.dataHigh-self.dataLow)
    
    def translateToScreens(self, value):
        if value == None or math.isinf(value):
            return [self.missingPixelY]
        elif math.isnan(value):
            return [self.maskedPixelY]
        results = []
        for r in self.visRanges:
            results.append(r.translateToScreen(value))
        return results
    
    def translateFromScreen(self, pixel):
        return self.visRanges[self.getRangeIndex(pixel)].translateFromScreen(pixel)
    
    def getRangeIndex(self, pixel):
        index = None
        for i,r in enumerate(self.visRanges):
            if pixel >= r.pixelLow and pixel <= r.pixelHigh:
                return i
    
    @staticmethod
    def findSensibleRange(dataLow,dataHigh):
        # TODO
        return (dataLow,dataHigh)
    
    def selectNone(self):
        self.selectRanges = []
        self.selectRanges.append((self.dataHigh,self.dataHigh))
        self.selectMissing = False
        self.selectMasked = False
    
    def selectAll(self):
        self.selectRanges = []
        self.selectRanges.append((self.dataLow,self.dataLow))
        self.selectMissing = True
        self.selectMasked = True
    
    def select(self, pixelLow, pixelHigh, includeMissing=False, includeMasked=False):
        # TODO: register action
        return self.dataAxis.select(self.translateToData(self.translateFromScreen(pixelLow)),self.translateToData(self.translateFromScreen(pixelHigh)),includeMissing,includeMasked)
    
    def getValues(self, rsNumbers):
        query = self.dataAxis.getValues(rsNumbers)
        for i,datum in enumerate(query):
            query[i] = self.translateFromData(datum)
        return query
    
    def getPixels(self, rsNumbers):
        query = self.getValues(rsNumbers)
        results = []
        for v in enumerate(query):
            results.append(self.translateToScreens(v))  # note there could be 0 or more y-coordinates for an rs number on screen, depending on viewing windows/zoom
        return results
    
    def getLabels(self, values):
        for i,v in enumerate(values):
            values[i] = self.translateToData(v)
        return self.dataAxis.getLabels(values)
    
    def getDataType(self):
        return self.dataAxis.getDataType()
    
    def handleEvent(self, event):
        pass
        # TODO: handle events, return object that says what was highlighted, what selected, etc, e.g.:
        #if self.svg.bounds.contains(x,y):
    
    def splitRange(self):
        pass
    
    def addSelection(self, pixel):
        pass
    
    def reset(self):
        self.visRanges = []
        self.visRanges.append(visRange(0.0,1.0,self.pixelLow,self.pixelHigh))

# TODO: genome axis

# TODO: string axis
'''
class stringAxis:
    def __init__(self, dataAxis):
        self.dataAxis = dataAxis
        self.low = dataAxis.getMin()
        self.high = dataAxis.getMax()
        self.hasMissing = dataAxis.hasMissing()
        self.hasMasked = dataAxis.hasMasked()
        
        self.selectedIndices = set()
        self.selectMissing = False
        self.selectMasked = False
    
    def translateToData(self, value):
        return int(self.low + value*(self.high-self.low))
    
    def translateFromData(self, value):
        return (value-self.low)/float(self.high-self.low)
    
    def selectNone(self):
        self.selectedIndices.clear()
        self.selectMissing = False
    
    def selectAll(self):
        self.selectedIndices = set(xrange(self.high+1))
        self.selectMissing = True
    
    def select(self, indices, includeMissing=False, includeMasked=False):
        dataIndices = [self.translateToData(i) for i in indices]
        return self.dataAxis.select(dataIndices,includeMissing,includeMasked)
    
    def getValues(self, rsNumbers):
        query = self.dataAxis.getValues(rsNumbers)
        for i,t in enumerate(query):
            query[i] = (t[0],self.translateFromData(t[1]))
        return query
    
    def getLabels(self, values):
        for i,v in enumerate(values):
            values[i] = self.translateToData(v)
        return self.dataAxis.getLabels(values)
    
    def getDataType(self):
        return self.dataAxis.getDataType()'''

class filterAction:
    def __init__(self):
        self.idsAdded = set()
        self.idsRemoved = set()
        self.exclusionsAdded = set()
        self.exclusionsRemoved = set()
        
        self.groupsChanged = [] # (group str, bool - true=included)
        self.rangesChanged = [] # (att str, range index, deltaX, deltaY)
        self.rangesAdded = []   # (att str, x0, y0)
        self.rangesRemoved = [] # (att str, range index, x0, y0)

class selection:
    i = 1
    def __init__(self, name = None):
        if name == None:
            self.name = "Selection %i" % selection.i
            selection.i += 1
        else:
            self.name = name
                
        self.current = set()
        self.excluded = set()
        self.currentAction = -1
        self.actions = []
    
    def duplicate(self):
        #Performs a deep copy with unique name
        temp = copy.deepcopy(self)
        temp.name = "%s copy" % self.name
        return temp
    
    def rename(self, name):
        self.name = name
    
    def add(self, rsNumbers):
        # TODO: add action
        self.current.update(rsNumbers)