from resources.structures import countingDict, TwoTree, FourTree
from copy import deepcopy
import operator, math, re, sys

selectionLabelRegex = re.compile('\(\d+\)')

class mixedAxis:
    def __init__(self, name):
        self.name = name
        
        self.tree = None
        self.rsValues = {}
        self.rsValuePairs = []
        
        self.rsLabels = {}
        self.labels = {'Missing':set(),'Allele Masked':set()}
        
        self.isfinished = False
        
        self.minimum = 0
        self.maximum = 0
    
    def add(self, id, value):
        self.isfinished = False
        
        if isinstance(value,list):
            # TODO: how do I handle this best?
            if len(value) == 0:
                value = None
            else:
                value = value[0]
            '''
            temp = ""
            for i in value:
                temp += str(i) + ","
            value = temp[:-1]'''
        
        if value == None:
            self.labels['Missing'].add(id)
        else:
            try:
                value = float(value)
                if math.isinf(value):
                    self.labels['Missing'].add(id)
                elif math.isnan(value):
                    self.labels['Allele Masked'].add(id)
                else:
                    self.rsValuePairs.append((id,value))
                    self.rsValues[id] = value
            except ValueError:
                if value == 'Numeric' or value == 'Missing' or value == 'Allele Masked':
                    value += ' (file attribute)'
                self.rsLabels[id] = value
                if not self.labels.has_key(value):
                    self.labels[value] = set()
                self.labels[value].add(id)
    
    def finish(self):
        if len(self.rsValuePairs) > 0:
            self.rsValuePairs.sort(key=lambda i: i[1])
            self.tree = TwoTree(self.rsValuePairs)
            self.findNaturalMinAndMax()
        else:
            self.tree = None
        
        self.isfinished = True
    
    def query(self, ranges=[], labels={}):    # ranges should be [(low,high)], and labels should be {label:bool}
        assert self.isfinished
        results = set()
        if self.tree != None:
            for low,high in ranges:
                results.update(self.tree.select(low,high,includeMasked=False,includeUndefined=False,includeMissing=False))  # I actually implement the missing/masked stuff outside the tree(s)
        for l,v in self.labels.iteritems():
            if labels.get(l,False):
                results.update(v)
        return results
    
    def getValues(self, rsNumbers):
        if not isinstance(rsNumbers, list):
            print "WARNING: returned rs numbers will be unordered!"
        results = []
        for rs in rsNumbers:
            if self.rsLabels.has_key(rs):
                results.append(self.rsLabels[rs])
            else:
                results.append(self.rsValues.get(rs,None))
        return results
    
    def getValue(self, rsNumber):
        if self.rsLabels.has_key(rsNumber):
            return self.rsLabels[rsNumber]
        else:
            return self.rsValues.get(rsNumber,None)
    
    def findNaturalMinAndMax(self):
        if not self.hasNumeric():
            self.minimum = 0
            self.maximum = 0
            return
        else:
            self.minimum = self.tree.root.low
            self.maximum = self.tree.root.high
            if self.minimum == self.maximum:
                self.minimum = 0
                if self.maximum == 0:
                    return
                    #self.maximum = 1    # though it would make sense, for some reason changing this to a 1 causes CGAffineTransformInvert: singular matrix...
            span = abs(self.maximum - self.minimum)
            if self.maximum > 0:
                nearestTenMax = 10**math.ceil(math.log10(self.maximum))
            elif self.maximum == 0:
                nearestTenMax = 0
            else:
                nearestTenMax = -10**math.floor(math.log10(-self.maximum))
            
            if self.minimum > 0:
                nearestTenMin = 10**math.floor(math.log10(self.minimum))
            elif self.minimum == 0:
                nearestTenMin = 0
            else:
                try:
                    nearestTenMin = -10**math.ceil(math.log10(-self.minimum))
                except:
                    print self.minimum
                    sys.exit(1)
            
            # prefer nearestTenMax if the gap between it and self.maximum is less than 25% the span of the data
            if nearestTenMax - self.maximum < 0.25*span:
                self.maximum = nearestTenMax
            #else:
            #    self.maximum += 0.05*span
            # prefer zero if the gap between it and self.minimum is less than 50% the span of the data, then 25% for nearestTenMin
            if self.minimum > 0.0 and self.minimum < 0.5*span:
                self.minimum = 0.0
            elif self.minimum - nearestTenMin < 0.25*span:
                self.minimum = nearestTenMin
            #else:
            #    self.minimum -= 0.05*span
    
    def getMin(self):
        return self.minimum
    
    def getMax(self):
        return self.maximum
    
    def hasNumeric(self):
        return not (self.tree == None or self.tree.root == None)
    
    def hasMasked(self):
        return len(self.labels['Allele Masked']) != 0
    
    def hasMissing(self):
        return len(self.labels['Missing']) != 0

class selection:
    namelessIndex = 1
    def __init__(self, data, name=None, result=None, params=None):
        if not data.isFrozen:
            data.freeze(None,None,None)
        self.data = data
        
        if name == None:
            self.name = "Group %s" % selection.namelessIndex
            selection.namelessIndex += 1
        else:
            self.name = name
        
        if result != None and params != None:
            self.result = set(result)
            self.params = params.copy()
        else:
            self.params = {}    # {axis:([(low,high)],{str:bool})}
            # Default initial selection: select the top 5% of the two scatterplot axes
            # (including all non-numerics - unless the axis has no numerics. In that
            # case select nothing), and everything from all other axes
            
            # do the x axis first so we have an initial selection
            ax = self.data.axes[self.data.currentXattribute]
            if ax.hasNumeric():
                self.applySelectAll(ax, applyImmediately=False)
                self.applySelectTopFivePercent(ax, applyImmediately=False)
            else:
                self.applySelectNone(ax, applyImmediately=False)
            self.result = ax.query(self.params[ax][0],self.params[ax][1])
            # now do all the others that will cut that selection down
            for a,ax in self.data.axes.iteritems():
                if a == self.data.currentXattribute:
                    continue
                elif a == self.data.currentYattribute:
                    if ax.hasNumeric():
                        self.applySelectAll(ax, applyImmediately=False)
                        self.applySelectTopFivePercent(ax, applyImmediately=False)
                    else:
                        self.applySelectNone(ax, applyImmediately=False)
                else:
                    self.applySelectAll(ax, applyImmediately=False)
                self.result.intersection_update(ax.query(self.params[ax][0],self.params[ax][1]))
    
    def findClosestEndpoints(self, axis, value):
        highDiff = sys.float_info.max
        closestHigh = -1
        lowDiff = sys.float_info.min
        closestLow = -1
        
        for i,(low,high) in enumerate(self.params[axis][0]):
            temp = abs(high-value)
            if temp < highDiff:
                closestHigh = i
                highDiff = temp 
            temp = abs(low-value)
            if temp < lowDiff:
                closestLow = i
                lowDiff = temp
        return (closestHigh,highDiff,closestLow,lowDiff)
    
    def findClosestRange(self, axis, value, isHigh=None):
        diff = sys.float_info.max
        closest = -1
        
        if isHigh == None:
            isHigh = False
            repeat = 0
        else:
            repeat = 1
        
        while repeat < 2:
            for i,(low,high) in enumerate(self.params[axis][0]):
                if isHigh:
                    newDiff = abs(high-value)
                else:
                    newDiff = abs(low-value)
                if newDiff < diff:
                    closest = i
                    diff = newDiff
            repeat += 1
            isHigh = not isHigh
        
        if closest == -1:
            return None
        else:
            return closest
    
    def simplifyNumericSelections(self, axis):
        selectedRanges = self.params[axis][0]
        if len(selectedRanges) == 0:
            return
        selectedRanges.sort()
        prevLow,prevHigh = selectedRanges[0]
        newRanges = [(prevLow,prevHigh)]
        i = 0
        for low,high in selectedRanges[1:]:
            if prevHigh >= low:
                newRanges[i] = (newRanges[i][0],max(high,prevHigh))
            else:
                newRanges.append((low,high))
                prevLow = low
                prevHigh = high
                i += 1
        
        self.params[axis] = (newRanges,self.params[axis][1])
    
    def updateResult(self, axis=None):
        if axis == None:
            axis = self.params.itervalues().next()    # ugly way of pulling out one of the axes
        self.result = axis.query(self.params[axis][0],self.params[axis][1])
        for ax in self.data.axes.itervalues():
            if ax == axis:
                continue
            self.result.intersection_update(ax.query(self.params[ax][0],self.params[ax][1]))
    
    def addNumericRange(self, axis, newLow, newHigh, applyImmediately=True):
        self.params[axis][0].append((newLow,newHigh))
        if applyImmediately:
            self.simplifyNumericSelections(axis)
            self.updateResult(axis)
    
    def removeNumericRange(self, axis, value, applyImmediately=True):
        index = self.findClosestRange(axis, value, isHigh=None)
        del self.param[axis][0][index]
        if applyImmediately:
            self.updateResult(axis)
    
    def applyNumericSelection(self, axis, index, isHigh, newValue, applyImmediately=True):
        if isHigh:
            self.params[axis][0][index] = (self.params[axis][0][index][0],newValue)
        else:
            self.params[axis][0][index] = (newValue,self.params[axis][0][index][1])
        if applyImmediately:
            self.simplifyNumericSelections(axis)
            self.updateResult(axis)
    
    def applyLabelToggle(self, axis, label, applyImmediately=True):
        self.params[axis][1][label] = not self.params[axis][1][label]
        if applyImmediately:
            self.updateResult(axis)
    
    def applyLabelSelection(self, axis, label, include, applyImmediately=True):
        self.params[axis][1][label] = include
        if applyImmediately:
            self.updateResult(axis)
    
    def applySelectAllLabels(self, axis, include=True, applyImmediately=True):
        for l in self.params[axis][1].iterkeys():
            self.params[axis][1][l] = include
        if applyImmediately:
            self.updateResult(axis)
    
    def applySelectAll(self, axis, applyImmediately=True):
        ranges = [(axis.getMin(),axis.getMax())]
        labels = {}
        for k in axis.labels.iterkeys():
            labels[k] = True
        self.params[axis] = (ranges,labels)
        if applyImmediately:
            self.updateResult(axis)
    
    def applySelectNone(self, axis, applyImmediately=True):
        ranges = [(axis.getMax(),axis.getMax())]
        labels = {}
        for k in axis.labels.iterkeys():
            labels[k] = False
        self.params[axis] = (ranges,labels)
        if applyImmediately:
            self.updateResult(axis)
    
    def applySelectTopFivePercent(self, axis, applyImmediately=True):
        if not axis.hasNumeric():
            ranges = []
        else:
            fivePercent = (axis.getMax()-axis.getMin()) * 0.05
            ranges = [(axis.getMax()-fivePercent,axis.getMax())]
        self.params[axis] = (ranges,self.params[axis][1])
        if applyImmediately:
            self.updateResult(axis)
    
    def getUnion(self, others):
        new = selection(self.data, name=None, result=self.result, params=self.params)
        
        for other in others:
            for ax,(ranges,labels) in other.params.iteritems():
                for low,high in ranges:
                    new.addNumericRange(ax, low, high, applyImmediately=False)
                for label,include in labels.iteritems():
                    new.params[ax][1][label] = include or new.params[ax][1][label]
        
        firstAxis = None
        for ax in new.params.iterkeys():
            new.simplifyNumericSelections(ax)
            if firstAxis == None:
                firstAxis = ax
        
        new.updateResult(firstAxis)
        return new
    
    def getIntersection(self, others):
        new = selection(self.data, name=None, result=self.result, params=self.params)
        
        firstAxis = None
        
        for other in others:
            for ax,(ranges,labels) in other.params.iteritems():
                if firstAxis == None:
                    firstAxis = ax
                
                newRanges = []
                for low,high in ranges:
                    for myLow,myHigh in new.params[ax][0]:
                        newLow = max(myLow,low)
                        newHigh = min(myHigh,high)
                        if newLow <= newHigh:
                            newRanges.append((newLow,newHigh))
                
                newLabels = {}
                for label,include in labels.iteritems():
                    newLabels[label] = include and new.params[ax][1][label]
                
                new.params[ax] = (newRanges,newLabels)
        
        new.updateResult(firstAxis)
        return new
    
    def getDifference(self, others):
        new = selection(self.data, name=None, result=self.result, params=self.params)
        
        firstAxis = None
        
        for other in others:
            for ax,(ranges,labels) in other.params.iteritems():
                if firstAxis == None:
                    firstAxis = ax
                
                for i,(myLow,myHigh) in enumerate(new.params[ax][0]):
                    for low,high in ranges:
                        if myLow >= low and myLow <= high:
                            myLow = high
                        if myHigh >= low and myHigh <= high:
                            myHigh = low
                        new.params[ax][0][i] = (myLow,myHigh)
                
                for label,include in labels.iteritems():
                    new.params[ax][1][label] = new.params[ax][1][label] and not include
        
        new.updateResult(firstAxis)
        return new
    
    def getInverse(self):
        newParams = {}
        
        for ax,(ranges,labels) in self.params.iteritems():
            newLabels = {}
            for label in labels.iterkeys():
                newLabels[label] = True
            newParams[ax] = ([(ax.getMin(),ax.getMax())],newLabels)
        new = selection(self.data, name=None, result=set(), params=([(self.getMin(),self.getMax())],{}))
        return new.getDifference(self)
    
    def previewUnion(self, others):
        tempResult = set(self.result)
        for o in others:
            tempResult.update(o.result)
        return tempResult
    
    def previewParameterUnion(self, others):
        tempResult = {}
        for ax,(ranges,labels) in self.params.iteritems():
            tempResult[ax] = (deepcopy(ranges),deepcopy(labels))
        
        for o in others:
            for ax,(ranges,labels) in o.params.iteritems():
                tempResult[ax][0].extend(ranges)    # don't bother to consolidate... make it obvious that multiple selections are active
                for label in tempResult[ax][1].iterkeys():
                    tempResult[ax][1][label] = tempResult[ax][1][label] or labels[label]
        return tempResult
    
    def previewNumericSelection(self, axis, index, isHigh, newValue):
        if isHigh:
            return axis.query((self.params[axis][0][index][0],newValue),{})
        else:
            return axis.query((newValue,self.params[axis][0][index][1]),{})
    
    def previewLabelSelection(self, axis, label, include=True):
        return axis.query((),{label:include})

class selectionState:
    def __init__(self, data):
        self.data = data
        
        startingSelection = selection(self.data)
        self.selectionOrder = [startingSelection.name]
        self.allSelections = {startingSelection.name:startingSelection}
        self.activeSelections = [startingSelection]
    
    def registerNew(self, s):
        self.activeSelections = [s]
        self.allSelections[s.name] = s
        self.selectionOrder.append(s.name)
    
    def remove(self, s):
        self.selectionOrder.remove(s.name)
        del self.allSelections[s.name]
    
    def hasMultipleActiveSelections(self):
        return len(self.activeSelections) > 1
    
    def startNewSelection(self):
        self.registerNew(selection(self.data))
    
    def deleteActiveSelections(self):
        for s in self.activeSelections:
            self.remove(s)
        
        if len(self.allSelections) == 0:
            self.startNewSelection()
        else:
            self.activeSelections = [self.allSelections[self.selectionOrder[-1]]]
    
    def duplicateActiveSelection(self):
        s = self.activeSelections[0]
        newSelection = selection(self.data,s.name + "(2)",s.result,s.params)
        self.registerNew(newSelection)
    
    def invertActiveSelection(self):
        s = self.activeSelections[0]
        self.allSelections[s.name] = s.getInverse()
    
    def unionActiveSelections(self):
        first = self.activeSelections[0]
        newSelection = first.getUnion(self.activeSelections[1:])
        self.registerNew(newSelection)
    
    def intersectionActiveSelections(self):
        first = self.activeSelections[0]
        newSelection = first.getIntersection(self.activeSelections[1:])
        self.registerNew(newSelection)
    
    def differenceActiveSelections(self):
        first = self.activeSelections[0]
        newSelection = first.getDifference(self.activeSelections[1:])
        self.registerNew(newSelection)
    
    def renameSelection(self, newText):
        if self.allSelections.has_key(newText):
            return
        s = self.activeSelections[0]
        oldName = s.name
        
        self.allSelections[newText] = s
        del self.allSelections[oldName]
        
        i = self.selectionOrder.index(oldName)
        self.selectionOrder[i] = newText
    
    def activateSelection(self, name):
        self.activeSelections.append(self.allSelections[name])
    
    def deactivateSelection(self, name):
        self.activeSelections.remove(self.allSelections[name])
    
    def getActiveRsNumbers(self):
        return self.activeSelections[0].previewUnion(self.activeSelections[1:])
    
    def getActiveParameters(self):
        return self.activeSelections[0].previewParameterUnion(self.activeSelections[1:])

class operation:
    NUMERIC_CHANGE = 1
    NUMERIC_ADD = 2
    MULTI_ADD = 3
    NUMERIC_REMOVE = 4
    NUMERIC_TOP_FIVE_PERCENT = 5
    LABEL_TOGGLE = 6
    ALL = 7
    NONE = 8
    SELECTION_COMPLEMENT = 9
    SELECTION_DUPLICATE = 10
    SELECTION_RENAME = 11
    SELECTION_UNION = 12
    SELECTION_DIFFERENCE = 13
    SELECTION_INTERSECTION = 14
    SELECTION_NEW = 15
    SELECTION_DELETE = 16
    SELECTION_INCLUDE = 17
    SELECTION_EXCLUDE = 18
    SELECTION_SWITCH = 19
    NO_OP = 20
    
    # shortcuts that classify types of operations
    SINGLE_SELECTION_REQUIRED = set([NUMERIC_CHANGE,NUMERIC_ADD,MULTI_ADD,NUMERIC_REMOVE,NUMERIC_TOP_FIVE_PERCENT,LABEL_TOGGLE,ALL,NONE,SELECTION_COMPLEMENT,SELECTION_DUPLICATE,SELECTION_RENAME])
    MULTIPLE_SELECTION_REQUIRED = set([SELECTION_UNION,SELECTION_DIFFERENCE,SELECTION_INTERSECTION])
    STATELESS = set([SELECTION_NEW,SELECTION_DELETE,SELECTION_INCLUDE,SELECTION_EXCLUDE,NO_OP,SELECTION_SWITCH])
    
    AXIS_REQUIRED = set([NUMERIC_CHANGE,NUMERIC_ADD,MULTI_ADD,NUMERIC_REMOVE,NUMERIC_TOP_FIVE_PERCENT,LABEL_TOGGLE,ALL,NONE])
    
    SINGLE_LOSSY = set([NUMERIC_CHANGE,NUMERIC_ADD,MULTI_ADD,NUMERIC_REMOVE,NUMERIC_TOP_FIVE_PERCENT,ALL,NONE])
    
    DOESNT_DIRTY = set([SELECTION_RENAME,SELECTION_DUPLICATE,NO_OP])
    
    def __init__(self, opType, selections, previousOp=None, **kwargs):
        self.opType = opType
        self.selections = selections
        self.previousOp = previousOp
        self.nextOp = None
        self.kwargs = kwargs
        self.isLegal = True
        self.finished = False
        
        # check that types and parameters are appropriate
        try:
            if len(self.selections.activeSelections) == 1:
                assert self.opType not in operation.MULTIPLE_SELECTION_REQUIRED
                self.activeSelection = self.selections.activeSelections[0]
                
                if self.opType in operation.AXIS_REQUIRED:
                    assert self.kwargs.has_key('axis')
                    self.axis = self.kwargs['axis']
                    
                    if self.opType in operation.SINGLE_LOSSY:
                        self.previousParams = deepcopy(self.activeSelection.params[self.axis])
            
            else:
                assert self.opType not in operation.SINGLE_SELECTION_REQUIRED
                self.activeSelections = self.selections.activeSelections
                
                if self.opType == operation.SELECTION_DELETE:
                    self.previousParams = {}
                    for s in self.activeSelections:
                        self.previousParams[s.name] = {}
                        for ax,(ranges,labels) in s.params.iteritems():
                            self.previousParams[s.name][ax] = (deepcopy(ranges),deepcopy(labels))
            
            # operation-specific inits
            if self.opType == operation.NUMERIC_CHANGE:
                assert self.kwargs.has_key('start') and self.kwargs.has_key('end') and self.kwargs.has_key('isHigh')
                self.start = self.kwargs['start']
                self.end = self.kwargs['end']
                self.isHigh = self.kwargs['isHigh']
                self.rangeIndex = self.activeSelection.findClosestRange(self.axis, self.start, self.isHigh)
            elif self.opType == operation.LABEL_TOGGLE:
                assert self.kwargs.has_key('label')
                self.label = self.kwargs['label']
            elif self.opType == operation.NUMERIC_ADD or self.opType == operation.NUMERIC_REMOVE:
                assert self.kwargs.has_key('position')
                self.position = self.kwargs['position']
            elif self.opType == operation.MULTI_ADD:
                assert self.kwargs.has_key('secondAxis') and self.kwargs.has_key('position') and self.kwargs.has_key('secondPosition')
                self.secondAxis = self.kwargs['secondAxis']
                
                self.position = self.kwargs['position']
                self.secondPosition = self.kwargs['secondPosition']
                
                self.includeAllLabels = self.kwargs.get('includeAllLabels',False)
                self.includeAllSecondLabels = self.kwargs.get('includeAllSecondLabels',False)
                
                self.secondPreviousParams = deepcopy(self.activeSelection.params[self.secondAxis])
            elif self.opType == operation.SELECTION_RENAME or self.opType == operation.SELECTION_INCLUDE:
                assert self.kwargs.has_key('name')
                self.oldName = self.activeSelection.name
                self.name = self.kwargs['name']
            elif self.opType == operation.SELECTION_INCLUDE:
                assert self.kwargs.has_key('name')
                self.name = self.kwargs['name']
            elif self.opType == operation.SELECTION_EXCLUDE:
                assert self.kwargs.has_key('name') and len(self.activeSelections) > 1
                self.name = self.kwargs['name']
            elif self.opType == operation.SELECTION_SWITCH:
                assert self.kwargs.has_key('name')
                self.name = self.kwargs['name']
                self.oldNames = []
                for s in selections.activeSelections:
                    self.oldNames.append(s.name)
            elif self.opType == operation.SELECTION_COMPLEMENT:
                self.previousParams = {}
                for ax,(ranges,labels) in self.activeSelection.params.iteritems():
                    self.previousParams[ax] = (deepcopy(ranges),deepcopy(labels))
            
        except AssertionError:
            self.isLegal = False
        
        if self.isLegal:
            if self.previousOp != None:
                self.previousOp.nextOp = self
            self.applyOp()
    
    def applyOp(self):
        assert self.isLegal
        if self.finished:
            return
        self.finished = True
        
        if self.opType == operation.NUMERIC_CHANGE:
            self.activeSelection.applyNumericSelection(self.axis, self.rangeIndex, self.isHigh, self.end)
        elif self.opType == operation.NUMERIC_ADD:
            self.activeSelection.addNumericRange(self.axis, self.position)
        elif self.opType == operation.NUMERIC_REMOVE:
            self.activeSelection.removeNumericRange(self.axis, self.position)
        elif self.opType == operation.MULTI_ADD:
            if self.includeAllLabels:
                self.activeSelection.applySelectAllLabels(self.axis, applyImmediately=False)
            if self.includeAllSecondLabels:
                self.activeSelection.applySelectAllLabels(self.secondAxis, applyImmediately=False)
            self.activeSelection.addNumericRange(self.axis, self.position, applyImmediately=False)
            self.activeSelection.addNumericRange(self.secondAxis, self.secondPosition)
        elif self.opType == operation.NUMERIC_TOP_FIVE_PERCENT:
            self.activeSelection.applySelectTopFivePercent(self.axis)
        elif self.opType == operation.ALL:
            self.activeSelection.applySelectAll(self.axis)
        elif self.opType == operation.NONE:
            self.activeSelection.applySelectNone(self.axis)
        elif self.opType == operation.LABEL_TOGGLE:
            self.activeSelection.applyLabelToggle(self.axis,self.label)
        elif self.opType == operation.SELECTION_COMPLEMENT:
            self.selections.invertActiveSelection()
        elif self.opType == operation.SELECTION_DELETE:
            self.selections.deleteActiveSelections()
        elif self.opType == operation.SELECTION_DIFFERENCE:
            self.selections.differenceActiveSelections()
        elif self.opType == operation.SELECTION_DUPLICATE:
            self.selections.duplicateActiveSelection()
        elif self.opType == operation.SELECTION_EXCLUDE:
            self.selections.deactivateSelection(self.name)
        elif self.opType == operation.SELECTION_INCLUDE:
            self.selections.activateSelection(self.name)
        elif self.opType == operation.SELECTION_SWITCH:
            for n in self.oldNames:
                self.selections.deactivateSelection(n)
            self.selections.activateSelection(self.name)
        elif self.opType == operation.SELECTION_INTERSECTION:
            self.selections.intersectionActiveSelections()
        elif self.opType == operation.SELECTION_NEW:
            self.selections.startNewSelection()
        elif self.opType == operation.SELECTION_RENAME:
            self.selections.renameSelection(self.name)
        elif self.opType == operation.SELECTION_UNION:
            self.selections.unionActiveSelections()
    
    def undo(self):
        assert self.isLegal
        if not self.finished:
            return
        self.finished = False
        
        # restore data lost by operations
        if self.opType == operation.SELECTION_DELETE:
            for name,params in self.previousParams.iteritems():
                newSelection = selection(self.data,name,set(),params)
                newSelection.updateResult()
                self.selections.registerNew(newSelection)
            for name in self.previousParams.iterkeys():
                self.selections.activateSelection(name)
        elif self.opType == operation.SELECTION_COMPLEMENT:
            self.activeSelection.params = {}
            for ax,(ranges,labels) in self.previousParams.iteritems():
                self.activeSelection.params[ax] = (deepcopy(ranges),deepcopy(labels))
            self.activeSelection.updateResult()
        elif self.opType in operation.SINGLE_LOSSY:
            self.activeSelection.params[self.axis] = deepcopy(self.previousParams)
            if self.opType == operation.MULTI_ADD:
                self.activeSelection.params[self.secondAxis] = deepcopy(self.secondPreviousParams)
            self.activeSelection.updateResult(self.axis)
        
        # fix easy to restore operations
        if self.opType == operation.LABEL_TOGGLE:
            self.axis.applyLabelToggle(self.axis,self.label)
        elif self.opType == operation.SELECTION_RENAME:
            self.selections.renameSelection(self.oldName)
        elif self.opType == operation.SELECTION_EXCLUDE:
            self.selections.activateSelection(self.name)
        elif self.opType == operation.SELECTION_INCLUDE:
            self.selections.deactivateSelection(self.name)
        elif self.opType == operation.SELECTION_SWITCH:
            self.selections.deactivateSelection(self.name)
            for n in self.oldNames:
                self.selections.activeSelections(n)

class variantData:
    def __init__(self):
        self.data = {}  # {rsNumber : variant object}
        self.axes = None
        
        self.scatter = None # current scatterplot of intersection of all numerical data
        self.scatterXs = None   # current 1d scatterplot for all non-numerical values on the x axis
        self.scatterYs = None   # current 1d scatterplot for all non-numerical values on the y axis
        self.scatterNones = None    # current set of all non-numerical values in both directions
        
        self.currentXattribute = None
        self.currentYattribute = None
        
        self.axisLabels = set()
        self.alleleFrequencyLabels = []
        
        self.isFrozen = False
    
    def addVariant(self, variantObject):
        if self.isFrozen:
            self.thaw()
        
        if variantObject.attributes.has_key("Genome Position"):
            print "ERROR: \"Genome Position\" column header is reserved."
            sys.exit(1)
        
        self.axisLabels.update(variantObject.attributes.iterkeys())
        
        if self.data.has_key(variantObject.name):
            self.data[variantObject.name].repair(variantObject)
        else:
            self.data[variantObject.name] = variantObject
    
    def discardAttribute(self, att):
        if self.isFrozen:
            self.thaw()
        self.axisLabels.discard(att)
    
    def recalculateAlleleFrequencies(self, individuals, groupName, basisGroup=[], fallback="REF"):
        if self.isFrozen:
            self.thaw()
        att = "Allele Frequency (%s)" % groupName
        self.axisLabels.add(att)
        if att not in self.alleleFrequencyLabels:
            self.alleleFrequencyLabels.append(att)
        
        for variantObject in self.data.itervalues():
            # First see if we can find a minor allele with stuff in basisGroup
            alleleCounts = countingDict()
            for i in basisGroup:
                if variantObject.genotypes.has_key(i):
                    allele1 = variantObject.genotypes[i].allele1
                    allele2 = variantObject.genotypes[i].allele2
                    if allele1 != None:
                        alleleCounts[allele1] += 1
                    if allele2 != None:
                        alleleCounts[allele2] += 1
            if len(alleleCounts) > 1:
                majorAllele = max(alleleCounts.iteritems(), key=operator.itemgetter(1))[0]
            else:
                # Okay, we don't have any data for our basisGroup (or our basisGroup is empty)... use the fallback
                if fallback == "None":
                    # No minor allele found and no fallback - we've got a masked allele frequency!
                    variantObject.attributes[att] = float('NaN')
                    continue
                elif fallback == "REF":
                    majorAllele = 0
                else:
                    majorAllele = int(fallback[4:])
                    if majorAllele > len(variantObject.alt):
                        # Tried to define minor allele as a nonexistent secondary allele
                        variantObject.attributes[att] = float('NaN')
                        continue
            # Okay, we've found our reference allele; now let's see how frequent the others are
            counts = countingDict()
            allCount = 0
            for i in individuals:
                if variantObject.genotypes.has_key(i.name):
                    allele1 = variantObject.genotypes[i.name].allele1
                    allele2 = variantObject.genotypes[i.name].allele2
                    if allele1 != None:
                        allCount += 1
                        if allele1 != majorAllele:
                            counts[allele1] += 1
                    if allele2 != None:
                        allCount += 1
                        if allele2 != majorAllele:
                            counts[allele2] += 1
            if allCount == 0:
                variantObject.attributes[att] = float('Inf')
            else:
                result = []
                for c in counts.itervalues():
                    result.append(c/float(allCount))
                variantObject.attributes[att] = sorted(result)
    
    def freeze(self, startingXaxis=None, startingYaxis=None, progressWidget=None):
        '''
        Builds query axes; prevents from loading more data. This is the longest process in the whole program - do this as little as possible (aka ONCE!)
        '''
        if self.isFrozen:
            return True     # indicates that we weren't interrrupted
        self.isFrozen = True
        
        if progressWidget != None:
            progressWidget.reset()
            progressWidget.setMinimum(0)
            progressWidget.setMaximum(len(self.axisLabels))
            progressWidget.show()
            
            index = 0
            progressWidget.setLabelText('Filling in Holes')
        
        self.axes = {"Genome Position":mixedAxis("Genome Position")}
        
        for att in self.axisLabels:
            self.axes[att] = mixedAxis(att)
        
        for v in self.data.itervalues():
            self.axes["Genome Position"].add(v.name,v.genomePosition)
            for att in self.axisLabels:
                self.axes[att].add(v.name, v.attributes.get(att,None))
        
        if progressWidget != None:
            progressWidget.setLabelText('Building Axes')
        
        for a in self.axes.itervalues():
            a.finish()
            if progressWidget != None:
                if progressWidget.wasCanceled():
                    return False
                
                index += 1
                progressWidget.setValue(index)
        
        if startingXaxis == None or startingYaxis == None:
            x,y = self.getFirstAxes()
            if startingXaxis == None:
                startingXaxis = x
                if startingYaxis == None:
                    startingYaxis = y
            elif startingYaxis == None:
                startingYaxis = x
        
        return self.setScatterAxes(startingXaxis, startingYaxis, progressWidget)
    
    def getFirstAxes(self):
        temp = self.defaultAxisOrder()
        if len(temp) < 2:
            raise ValueError("You should have at least two data attributes (columns in your .csv file or INFO fields in your .vcf file)\n" +
                             "to use this program (otherwise you probably should be using LibreOffice Calc or IGV to explore your data instead).")
        return (temp[0],temp[1])
    
    def defaultAxisOrder(self):
        # gives priority to axes (each subgroup is sorted alphabetically):
        # program-generated allele frequencies are first
        # numeric other values are next
        # categorical other values are last
        if not self.isFrozen:
            self.freeze(None, None, None)
        result = []
        for a in sorted(self.alleleFrequencyLabels):
            result.append(a)
        for a,ax in sorted(self.axes.iteritems()):
            if ax.hasNumeric() and a not in self.alleleFrequencyLabels:
                result.append(a)
        for a,ax in sorted(self.axes.iteritems()):
            if not ax.hasNumeric() and a not in self.alleleFrequencyLabels:
                result.append(a)
        return result
    
    def thaw(self):
        '''
        Throws out all query structures; allows us to load more data
        '''
        print "...Thawing"
        self.axes = None
        self.scatter = None
        self.isFrozen = False
        self.currentXattribute = None
        self.currentYattribute = None
    
    def setScatterAxes(self, attribute1, attribute2, progressWidget=None):
        '''
        Builds a FourTree for drawing the scatterplot - maybe could be sped up by some kind of sorting...
        '''
        if not self.isFrozen:
            self.freeze(attribute1,attribute2,progressWidget)
            return
        
        if self.currentXattribute == attribute1 and self.currentYattribute == attribute2:
            return
        
        if progressWidget != None:
            divisions = 100
            increment = max(1,int(len(self.data)/divisions))
            
            progressWidget.reset()
            progressWidget.setMinimum(0)
            progressWidget.setMaximum(increment)
            progressWidget.show()
            
            index = 0
            threshold = increment
            
            progressWidget.setLabelText('Building K-d Tree')
        
        if not self.axes.has_key(attribute1):
            print self.axes.keys()
            print attribute1
            sys.exit(1)
        axis1 = self.axes[attribute1]
        assert axis1.isfinished
        axis2 = self.axes[attribute2]
        assert axis2.isfinished
        
        originalXattribute = self.currentXattribute
        originalYattribute = self.currentYattribute
        
        self.currentXattribute = attribute1
        self.currentYattribute = attribute2
        
        originalScatter = self.scatter
        originalScatterXs = self.scatterXs
        originalScatterYs = self.scatterYs
        originalScatterNones = self.scatterNones
        
        self.scatter = FourTree()
        self.scatterXs = mixedAxis(self.currentXattribute)
        self.scatterYs = mixedAxis(self.currentYattribute)
        self.scatterNones = set()
        
        for rs in self.data.iterkeys():
            if axis1.rsValues.has_key(rs):
                if axis2.rsValues.has_key(rs):
                    self.scatter.add(rs,axis1.rsValues[rs],axis2.rsValues[rs])
                else:
                    self.scatterXs.add(rs,axis1.rsValues.get(rs,None))
            else:
                if axis2.rsValues.has_key(rs):
                    self.scatterYs.add(rs,axis2.rsValues.get(rs,None))
                else:
                    self.scatterNones.add(rs)
            if progressWidget != None:
                index += 1
                if index > threshold:
                    threshold += increment
                    if progressWidget != None:
                        if progressWidget.wasCanceled():
                            self.currentXattribute = originalXattribute
                            self.currentYattribute = originalYattribute
                            
                            self.scatter = originalScatter
                            self.scatterXs = originalScatterXs
                            self.scatterYs = originalScatterYs
                            self.scatterNones = originalScatterNones
                            return False
                        progressWidget.setValue(index/divisions)
            if progressWidget != None:
                progressWidget.setValue(increment)
        return True
        
    def getData(self, rsNumbers, att):
        return self.axes[att].getValues(rsNumbers)
    
    def getDatum(self, rsNumber, att):
        return self.axes[att].getValue(rsNumber)
    
    def get2dData(self, rsNumbers, att1, att2):
        rsNumbers = list(rsNumbers) # ensure the order is the same
        return zip(self.axes[att1].getValues(rsNumbers),self.axes[att2].getValues(rsNumbers))
    
    def get2dDatum(self, rsNumber, att1, att2):
        return (self.axes[att1].getValue(rsNumber),self.axes[att2].getValue(rsNumber))

        