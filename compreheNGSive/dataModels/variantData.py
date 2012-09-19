from resources.structures import countingDict
from resources.genomeUtils import variant
from durus.file_storage import FileStorage
from durus.connection import Connection
from durus.persistent import Persistent
from copy import deepcopy
import math, sys, os

class cancelButtonException(Exception):
    pass

class variantRangeIndex(Persistent):
    TICK_INTERVAL = 10000
    
    def __init__(self, name, data, key, forceCategorical = False, callback = None):
        Persistent.__init__(self)
        
        # TODO: throw this away when you update the vis bits of code
        self.name = name
        
        self.numerics = []
        self.nonNumerics = {'Missing':set(),'Allele Masked':set()}
        
        self.key = key
        self.forceCategorical = forceCategorical
        
        self.minimum = None
        self.maximum = None
        
        lineCount = 0
        nextTick = variantRangeIndex.TICK_INTERVAL
        keyList = list(data['variant keys'])
        keyList.sort(key=lambda x:self.getAttribute(data[x]))
        for k in keyList:
            v = data[k]
            lineCount += 1160
            if callback != None and lineCount >= nextTick:
                nextTick += 1
                if callback():
                    raise cancelButtonException('cancel pressed')
            
            values = self.getAttribute(v)
            if not isinstance(values,list):
                values = [values]
            
            for value in values:
                if value == None or value == variant.MISSING or value == "":
                    self.nonNumerics['Missing'].add(v)
                elif value == variant.ALLELE_MASKED:
                    self.nonNumerics['Allele Masked'].add(v)
                elif self.forceCategorical:
                    if not self.nonNumerics.has_key(value):
                        self.nonNumerics[value] = set()
                    self.nonNumerics[value].add(v)
                else:
                    try:
                        value = float(value)
                        if math.isinf(value):
                            if not self.nonNumerics.has_key('Inf'):
                                self.nonNumerics['Inf'] = set()
                            self.nonNumerics['Inf'].add(v)
                        elif math.isnan(value):
                            if not self.nonNumerics.has_key('NaN'):
                                self.nonNumerics['NaN'] = set()
                            self.nonNumerics['NaN'].add(v)
                        else:
                            if self.minimum == None or value < self.minimum:
                                self.minimum = value
                            if self.maximum == None or value > self.maximum:
                                self.maximum = value
                            self.numerics.append(v)
                    except ValueError:
                        if not self.nonNumerics.has_key(value):
                            self.nonNumerics[value] = set()
                        self.nonNumerics[value].add(v)
        self.findNaturalMinAndMax()
    
    def getAttribute(self, v):
        if self.key == None:
            return v.genomePosition
        else:
            return v.getAttribute(self.key)
    
    def selectRangeVariants(self, low, high):
        lowIndex = 0
        highIndex = len(self.numerics)
        
        if high < low:
            temp = high
            high = low
            low = temp
        
        while highIndex-lowIndex > 1:
            midIndex = (highIndex+lowIndex)/2
            if self.getAttribute(self.numerics[midIndex]) <= low:
                lowIndex = midIndex
            else:
                highIndex = midIndex
        
        results = set()
        if self.getAttribute(self.numerics[lowIndex]) >= low:
            results.add(self.numerics[lowIndex])
        while highIndex < len(self.numerics) and self.getAttribute(self.numerics[highIndex]) <= high:
            results.add(self.numerics[highIndex])
            highIndex += 1
        return results
    
    def selectRangeNames(self, low, high):
        lowIndex = 0
        highIndex = len(self.numerics)
        
        if high < low:
            temp = high
            high = low
            low = temp
        
        while highIndex-lowIndex > 1:
            midIndex = (highIndex+lowIndex)/2
            if self.getAttribute(self.numerics[midIndex]) <= low:
                lowIndex = midIndex
            else:
                highIndex = midIndex
        
        results = set()
        if self.getAttribute(self.numerics[lowIndex]) >= low:
            results.add(self.numerics[lowIndex].name)
        while highIndex < len(self.numerics) and self.getAttribute(self.numerics[highIndex]) <= high:
            results.add(self.numerics[highIndex].name)
            highIndex += 1
        return results
    
    def countIntersection(self, low, high, other, otherLow, otherHigh, maxCount = None):
        '''
        First searches the bounding indices on valid ranges for each
        variantRangeIndex; then counts the number of intersecting elements
        by iterating the shortest sublist, and searching the longer
        sublist; to actually return elements, just replace incrementing
        count with adding to a set
        
        Counting complexity (assuming lists M and N of size m and n):
        
        2log(m) + 2log(n) + min(|M'|, |N'|) log (max(|M'|, |N'|))
        
        where M' and N' are the sublists of M and N that fit the range criteria;
        in theory, the final term could be m log n or n log m if the high and low
        bounds are broad, though in practice these should be very narrow.
        The final term can also be replaced by a constant maxCount if provided
        (though the the returned value will be maxCount if maxCount is exceeded)
        
        '''
        # find the start and end bounding indices for the subset of self
        if high < low:
            temp = high
            high = low
            low = temp
        
        lowIndex = 0
        highIndex = len(self.numerics)
        while highIndex-lowIndex > 1:
            midIndex = (highIndex+lowIndex)/2
            if self.getAttribute(self.numerics[midIndex]) <= low:   # we want to be flexible on the endpoint, which we'll handle directly
                lowIndex = midIndex
            else:
                highIndex = midIndex
        startIndex = lowIndex if self.getAttribute(self.numerics[lowIndex]) >= low else lowIndex + 1    # this disambiguates whether the endpoint is inclusive (it forces it to be)
        # can reuse lowIndex for a little speed gain, since we know high is bigger
        highIndex = len(self.numerics)
        while highIndex-lowIndex > 1:
            midIndex = (highIndex+lowIndex)/2
            if self.getAttribute(self.numerics[midIndex]) >= high:  # we want to be flexible on the endpoint, which we'll handle directly
                highIndex = midIndex
            else:
                lowIndex = midIndex
        endIndex = highIndex if self.getAttribute(self.numerics[highIndex]) <= high else highIndex - 1    # this disambiguates whether the endpoint is inclusive (it forces it to be)
        
        # find the start and end bounding indices for the subset of other
        if high < low:
            temp = high
            high = low
            low = temp
        
        lowIndex = 0
        highIndex = len(other.numerics)
        while highIndex-lowIndex > 1:
            midIndex = (highIndex+lowIndex)/2
            if other.getAttribute(other.numerics[midIndex]) <= low:   # we want to be flexible on the endpoint, which we'll handle directly
                lowIndex = midIndex
            else:
                highIndex = midIndex
        otherStartIndex = lowIndex if other.getAttribute(other.numerics[lowIndex]) >= low else lowIndex + 1    # this disambiguates whether the endpoint is inclusive (it forces it to be)
        # can reuse lowIndex for a little speed gain, since we know high is bigger
        highIndex = len(other.numerics)
        while highIndex-lowIndex > 1:
            midIndex = (highIndex+lowIndex)/2
            if other.getAttribute(other.numerics[midIndex]) >= high:  # we want to be flexible on the endpoint, which we'll handle directly
                highIndex = midIndex
            else:
                lowIndex = midIndex
        otherEndIndex = highIndex if other.getAttribute(other.numerics[highIndex]) <= high else highIndex - 1    # this disambiguates whether the endpoint is inclusive (it forces it to be)
        
        # Now we want to use the longer list as a binary search tree, and iterate the shorter one, counting matches
        count = 0
        if endIndex-startIndex > otherEndIndex-otherStartIndex:
            # Search me, iterate him
            i = otherStartIndex
            while i <= otherEndIndex:
                value = self.getAttribute(other.numerics[i])    # get the value that I'll be looking for
                lowIndex = startIndex
                highIndex = endIndex
                while highIndex-lowIndex > 1:
                    midIndex = (highIndex+lowIndex)/2
                    if self.getAttribute(self.numerics[midIndex]) <= value:
                        lowIndex = midIndex
                    else:
                        highIndex = midIndex
                # lowIndex now has the earliest possible place a match could be
                while self.getAttribute(self.numerics[lowIndex]) <= value:
                    if self.numerics[lowIndex] == other.numerics[i]:
                        count += 1
                        if maxCount != None and count >= maxCount:
                            return count
                        break
                    lowIndex += 1
        else:
            # Search him, iterate me
            i = startIndex
            while i <= endIndex:
                value = other.getAttribute(self.numerics[i])    # get the value that he'll be looking for
                lowIndex = startIndex
                highIndex = endIndex
                while highIndex-lowIndex > 1:
                    midIndex = (highIndex+lowIndex)/2
                    if other.getAttribute(other.numerics[midIndex]) <= value:
                        lowIndex = midIndex
                    else:
                        highIndex = midIndex
                # lowIndex now has the earliest possible place a match could be
                while other.getAttribute(other.numerics[lowIndex]) <= value:
                    if other.numerics[lowIndex] == self.numerics[i]:
                        count += 1
                        if maxCount != None and count >= maxCount:
                            return count
                        break
                    lowIndex += 1
        return count
    
    def findNaturalMinAndMax(self):
        if len(self.numerics) == 0:
            return
        else:
            if self.minimum == self.maximum:
                self.minimum = 0
                if self.maximum == 0:
                    self.minimum = -1
                    self.maximum = 1
                    return
            elif self.minimum > self.maximum:
                temp = self.maximum
                self.maximum = self.minimum
                self.minimum = temp
            
            span = self.maximum - self.minimum
            
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
                nearestTenMin = -10**math.ceil(math.log10(-self.minimum))
            
            # prefer nearestTenMax if the gap between it and self.maximum is less than 25% the span of the data
            if abs(nearestTenMax - self.maximum) < 0.25*span:
                self.maximum = nearestTenMax
            
            # prefer zero if the gap between it and self.minimum is less than 50% the span of the data, then 25% for nearestTenMin
            if self.minimum > 0 and self.minimum < 0.5*span:
                self.minimum = 0
            elif abs(self.minimum - nearestTenMin) < 0.25*span:
                self.minimum = nearestTenMin
    
    def query(self, ranges=[], labels={}):
        results = set()
        if len(self.numerics) > 0:
            for low,high in ranges:
                results.update(self.selectRangeNames(low, high))
        for l,i in labels.iteritems():
            if i:
                for v in self.nonNumerics.get(l,set()):
                    results.add(v.name)
        return results
    
    def hasNumeric(self):
        return len(self.numerics) > 0
    
    def hasMasked(self):
        return len(self.nonNumerics.get('Allele Masked',set())) > 0
    
    def hasMissing(self):
        return len(self.nonNumerics.get('Missing',set())) > 0

class selection:
    namelessIndex = 1
    def __init__(self, vdata, name=None, result=None, params=None, prefilters=None):
        if not vdata.isFrozen:
            vdata.freeze(None)
        self.vdata = vdata
        
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
            assert prefilters != None and len(prefilters) > 0
            # build the selection from the prefiltered axes first... 
            att_0,fil_0 = prefilters.iteritems().next()   # ugly way of grabbing one of the prefilters
            ax = self.vdata.data[att_0]
            self.applySelectAll(ax, applyImmediately=False)
            self.applyCustomFilters(ax, fil_0, applyImmediately=False)
            self.result = ax.query(self.params[ax][0],self.params[ax][1])
            # now do the rest of the prefilters to cut that selection down
            for att,fil in prefilters.iteritems():
                if att == att_0:
                    continue
                else:
                    if not self.vdata.data.has_key(att):
                        print att
                        print self.vdata.allAxes
                    ax = self.vdata.data[att]
                    self.applySelectAll(ax, applyImmediately=False)
                    self.applyCustomFilters(ax, fil, applyImmediately=False)
                    self.result.intersection_update(ax.query(self.params[ax][0],self.params[ax][1]))
            # now do the rest of the attributes
            for att in self.vdata.allAxes:
                ax = self.vdata.data[att]
                if att in prefilters.iterkeys():
                    continue
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
        for att in self.vdata.allAxes:
            ax = self.vdata.data[att]
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
        ranges = []
        if axis.hasNumeric():
            ranges.append((axis.minimum,axis.maximum))
        labels = {}
        for k in axis.nonNumerics.iterkeys():
            labels[k] = True
        self.params[axis] = (ranges,labels)
        if applyImmediately:
            self.updateResult(axis)
    
    def applySelectNone(self, axis, applyImmediately=True):
        ranges = []
        if axis.hasNumeric():
            ranges.append((axis.maximum,axis.maximum))
        labels = {}
        for k in axis.nonNumerics.iterkeys():
            labels[k] = False
        self.params[axis] = (ranges,labels)
        if applyImmediately:
            self.updateResult(axis)
    
    def applySelectTopFivePercent(self, axis, applyImmediately=True):
        if not axis.hasNumeric():
            ranges = []
        else:
            fivePercent = (axis.maximum-axis.minimum) * 0.05
            ranges = [(axis.maximum-fivePercent,axis.maximum)]
        self.params[axis] = (ranges,self.params[axis][1])
        if applyImmediately:
            self.updateResult(axis)
    
    def applyCustomFilters(self, axis, fil, applyImmediately=True):
        ranges = []
        if axis.hasNumeric():
            if fil.percentages == None or len(fil.percentages) == 0:
                ranges.append((axis.minimum,axis.maximum))
            else:
                for p in fil.percentages:
                    if p < 0:
                        ranges.append((axis.minimum,-(axis.maximum-axis.minimum)*p+axis.minimum))
                    else:
                        ranges.append((axis.maximum-(axis.maximum-axis.minimum)*p,axis.maximum))
        labels = {}
        # First limit to labels that exist, but deselect them all
        if fil.values == None:
            for l in self.params[axis][1].iterkeys():
                labels[l] = True
            if fil.excludeMissing and labels.has_key('Missing'):
                labels['Missing'] = False
            if fil.excludeMasked and labels.has_key('Allele Masked'):
                labels['Allele Masked'] = False
        else:
            for l in self.params[axis][1].iterkeys():
                labels[l] = False
            for l in fil.values:
                if labels.has_key(l):
                    labels[l] = True
            if not fil.excludeMissing and labels.has_key('Missing'):
                labels['Missing'] = True
            if not fil.excludeMasked and labels.has_key('Allele Masked'):
                labels['Allele Masked'] = True
        self.params[axis] = (ranges,labels)
        self.simplifyNumericSelections(axis)
        if applyImmediately:
            self.updateResult(axis)
    
    def getUnion(self, others):
        new = selection(self.vdata, name=None, result=self.result, params=self.params)
        
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
        new = selection(self.vdata, name=None, result=self.result, params=self.params)
        
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
        new = selection(self.vdata, name=None, result=self.result, params=self.params)
        
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
            newParams[ax] = ([(ax.minimum,ax.maximum)],newLabels)
        new = selection(self.vdata, name=None, result=set(), params=([(self.minimum,self.maximum)],{}))
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
    def __init__(self, vdata, prefilters=None):
        self.vdata = vdata
        
        startingSelection = selection(self.vdata,prefilters=prefilters)
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
        self.registerNew(selection(self.vdata))
    
    def deleteActiveSelections(self):
        for s in self.activeSelections:
            self.remove(s)
        
        if len(self.allSelections) == 0:
            self.startNewSelection()
        else:
            self.activeSelections = [self.allSelections[self.selectionOrder[-1]]]
    
    def duplicateActiveSelection(self):
        s = self.activeSelections[0]
        newSelection = selection(self.vdata,s.name + "(2)",s.result,s.params)
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
    COMMIT_FREQ=1000
    COMMIT=0
    def __init__(self, axisLabels, statisticLabels, forcedCategoricals, startingXattribute, startingYattribute):
        for fileToClear in ['Data.db','Data.db.lock','Data.db.tmp','Data.db.prepack']:
            if os.path.exists(fileToClear):
                os.remove(fileToClear)
        
        self.dataConnection = Connection(FileStorage("Data.db"))
        self.data = self.dataConnection.get_root()
        # possible key:value pairs (this is a little bizarre, but I can only have one database (as objects reference each other),
        # and for performance I want to keep all variant objects and axes on the root level:
        
        # variant name : variant object
        # 'variant keys' : a set of all variant names    (I would keep this in memory, but even it might get really big)
        # axis name : variantRangeIndex object
        
        self.data['variant keys'] = set()
        
        self.axisLabels = axisLabels
        self.forcedCategoricals = forcedCategoricals
        self.statisticLabels = statisticLabels
        
        self.allAxes = self.defaultAxisOrder()
        
        # TODO: throw these away when you update the vis bits of code
        self.currentXattribute = startingXattribute
        self.currentYattribute = startingYattribute
        
        self.isFrozen = False
    
    def addVariant(self, variantObject):
        if self.isFrozen:
            self.thaw()
        
        if variantObject.attributes.has_key('Genome Position'):
            raise Exception("Using \"Genome Position\" as an attribute key is reserved.")
        
        if variantObject.name in self.data['variant keys']:
            self.data[variantObject.name].repair(variantObject)
        else:
            assert variantObject.name != 'variant keys'
            self.data['variant keys'].add(variantObject.name)
            self.data[variantObject.name] = variantObject
        
        variantData.COMMIT += 1
        if variantData.COMMIT >= variantData.COMMIT_FREQ:
            variantData.COMMIT = 0
            self.dataConnection.commit()
    
    def performGroupCalculations(self, groupDict, statisticDict, callback, tickInterval):
        from setupData import statistic
        if self.isFrozen:
            self.thaw()
        
        currentLine = 0
        nextTick = tickInterval
        
        targetAlleleGroups = {}
        for s in statisticDict.itervalues():
            if s.statisticType == statistic.ALLELE_FREQUENCY:
                if s.parameters.has_key('alleleGroup'):
                    index = s.parameters['alleleMode']
                    if index >= 1:
                        index -= 1  # they'll specify 1 as the most frequent, but we're in 0-based computer land; -1 is still the same though
                    targetAlleleGroups[s.parameters['alleleGroup']] = s.parameters['alleleMode']
                else:
                    targetAlleleGroups['vcf override'] = s.parameters['alleleMode']
        if len(targetAlleleGroups) == 0:    # nothing to calculate
            return
        
        for key in self.data['variant keys']:
            variantObject = self.data[key]
            currentLine += 1
            if currentLine >= nextTick:
                nextTick += tickInterval
                self.dataConnection.commit()
                if callback():  # abort?
                    return "ABORTED"
            
            if variantObject == None or variantObject.poisoned:
                continue
            
            # First find all the target alleles
            targetAlleles = {}
            for group,mode in targetAlleleGroups.iteritems():
                if group == 'vcf override':
                    alleles = variantObject.alleles
                else:
                    # First see if we can find a major allele with the people in basisGroup
                    alleleCounts = countingDict()
                    for i in groupDict[group].samples:
                        if variantObject.genotypes.has_key(i):
                            allele1 = variantObject.genotypes[i].allele1
                            allele2 = variantObject.genotypes[i].allele2
                            if allele1.text != None:
                                alleleCounts[allele1] += 1
                            if allele2.text != None:
                                alleleCounts[allele2] += 1
                    alleles = [x[0] for x in sorted(alleleCounts.iteritems(), key=lambda x: x[1])]
                
                if mode >= len(alleles) or mode < -len(alleles):
                    targetAlleles[group] = None
                else:
                    targetAlleles[group] = variantObject.alleles[mode]
            
            for statisticID,s in statisticDict.iteritems():
                targetAllele = targetAlleles[s.parameters.get('alleleGroup','vcf override')]
                if s.statisticType == statistic.ALLELE_FREQUENCY:
                    if targetAllele == None:
                        variantObject.setAttribute(statisticID,variant.ALLELE_MASKED)    # the original group didn't have the allele, so we're masked
                        continue
                    
                    allCount = 0
                    targetCount = 0
                    
                    for i in groupDict[s.parameters['group']].samples:
                        if variantObject.genotypes.has_key(i):
                            allele1 = variantObject.genotypes[i].allele1
                            allele2 = variantObject.genotypes[i].allele2
                            if allele1 != None:
                                allCount += 1
                                if allele1 == targetAllele:
                                    targetCount += 1
                            if allele2 != None:
                                allCount += 1
                                if allele2 == targetAllele:
                                    targetCount += 1
                    if allCount == 0:
                        variantObject.setAttribute(statisticID,variant.MISSING)    # We had no data for this variant, so this thing is undefined
                    else:
                        variantObject.setAttribute(statisticID,float(targetCount)/allCount)
        self.dataConnection.commit()
    
    def estimateTicks(self):
        return len(self.allAxes)*len(self.data['variant keys'])/variantRangeIndex.TICK_INTERVAL
    
    def freeze(self, callback=None):
        '''
        Builds query structures; prevents from loading more data. This is the longest process in the whole program - do this as little as possible (aka ONCE!)
        '''
        if self.isFrozen:
            return True
        self.isFrozen = True
        
        callback(numTicks=0,message='Cleaning...')
        staleDataKeys = []
        '''print len(self.data['variant keys'])
        for k in self.data['variant keys']:
            v = self.data[k]
            if k != None and k != self.data[k].name:
                staleDataKeys.append((k,v))
        print len(staleDataKeys)
        for k,v in staleDataKeys:
            assert v.name != 'variant keys'
            self.data[v.name]=v
        self.dataConnection.commit()
        
        for k,v in staleDataKeys:
            del self.data[k]
        self.dataConnection.pack()'''
                
        try:
            for att in self.allAxes:
                callback(numTicks=0,message='Indexing %s' % att)
                assert att not in self.data['variant keys']
                key = None if att == 'Genome Position' else att # None is a sneaky key to help reduce the number of string compares when building an index for Genome Position
                self.data[att] = variantRangeIndex(att,self.data,key=key,forceCategorical=att in self.forcedCategoricals,callback=callback)
                self.dataConnection.commit()
        except cancelButtonException:
            self.thaw()
        
        return self.isFrozen
    
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
        result = []
        for a in sorted(self.statisticLabels):
            result.append(a)
        for a in sorted(self.axisLabels):
            if not self.data.has_key(a):
                result.append(a)    # if we haven't built the axes yet, just add them in order; we'll worry about numeric, etc next time
            elif self.data[a].hasNumeric() and a not in self.statisticLabels:
                result.append(a)
        
        for a in sorted(self.axisLabels):
            if self.data.has_key(a) and not self.data[a].hasNumeric() and a not in self.statisticLabels:
                result.append(a)
        result.append('Genome Position')
        return result
    
    def thaw(self):
        '''
        Throws out all query structures; allows us to load more data
        '''
        for a in self.allAxes:
            if self.data.has_key(a):
                del self.data[a]
        self.dataConnection.pack()
        
        self.isFrozen = False
        
    def getData(self, rsNumbers, att):
        if not isinstance(rsNumbers, list):
            sys.stderr.write("WARNING: Results will be unordered!")
        results = []
        for rs in rsNumbers:
            if not rs in self.data['variant keys']:
                results.append(variant.MISSING)
            else:
                results.append(self.data[rs].getAttribute(att))
        return results
    
    def getDatum(self, rsNumber, att):
        if not rsNumber in self.data['variant keys']:
            return None
        else:
            return self.data[rsNumber].getAttribute(att)
    
    def get2dData(self, rsNumbers, att1, att2):
        if not isinstance(rsNumbers,list):
            rsNumbers = list(rsNumbers) # ensure the order is the same
        return zip(self.getData(rsNumbers,att1),self.getData(rsNumbers,att2))
    
    def get2dDatum(self, rsNumber, att1, att2):
        return (self.getDatum(rsNumber, att1),self.getDatum(rsNumber, att2))

        