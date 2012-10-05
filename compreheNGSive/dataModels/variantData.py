from resources.structures import rangeDict
from resources.genomeUtils import variant
from durus.file_storage import FileStorage
from durus.connection import Connection
from durus.persistent import Persistent
from copy import deepcopy
import math, sys, os

class attributeIndex(Persistent):
    def __init__(self, attributeName, forceCategorical = False):
        Persistent.__init__(self)
        self.attributeName = attributeName
        
        self.lookup = rangeDict()
        self.categoricalKeys = set()
        
        self.forceCategorical = forceCategorical
        
        self.minimum = None
        self.maximum = None
        
        self.hasNumeric = False
        self.hasMasked = False
        self.hasMissing = False
    
    def add(self, position, values):
        if not isinstance(values,list):
            values = [values]
        
        for value in values:
            if value == None or value == variant.MISSING or value == "":
                value = 'Missing'
                #self.lookup['Missing'] = position  # this looks like things are being replaced, but that's the weirdness of rangeDict
                #self.categoricalKeys.add('Missing')
                #self.hasMissing = True
            elif value == variant.ALLELE_MASKED:
                value = 'Allele Masked'
                #self.lookup['Allele Masked'] = position
                #self.categoricalKeys.add('Allele Masked')
                #self.hasMasked = True
            if self.forceCategorical:
                self.lookup[value] = position
                self.categoricalKeys.add(value)
            else:
                try:
                    value = float(value)
                    if math.isinf(value):
                        self.lookup['Inf'] = position
                        self.categoricalKeys.add('Inf')
                    elif math.isnan(value):
                        self.lookup['NaN'] = position
                        self.categoricalKeys.add('NaN')
                    else:
                        self.lookup[value] = position
                        self.hasNumeric = True
                        if self.minimum == None or value < self.minimum:
                            self.minimum = value
                        if self.maximum == None or value > self.maximum:
                            self.maximum = value
                except ValueError:
                    self.lookup[value] = position
                    self.categoricalKeys.add(value)
    
    def findNaturalMinAndMax(self):
        self.hasMissing = self.lookup.count('Missing') > 0
        self.hasMasked = self.lookup.count('Allele Masked') > 0
        if self.minimum == None or self.maximum == None:
            self.minimum = None
            self.maximum = None
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
    
    def query(self, ranges=[], labels=set()):
        results = set()
        if self.lookup.len() > 0:
            for low,high in ranges:
                results.update(self.lookup[low:high])
        for l in labels:
            results.update(self.lookup[l])
        return results

class variantData:
    COMMIT_FREQ = 1000
    VARIANTS_ADDED = 0
    def __init__(self, vcfPath, vcfAttributes, forcedCategoricals):
        for fileToClear in ['Data.db','Data.db.lock','Data.db.tmp','Data.db.prepack','Axes.db','Axes.db.lock','Axes.db.tmp','Axes.db.prepack']:
            if os.path.exists(fileToClear):
                os.remove(fileToClear)
        
        self.forcedCategoricals = forcedCategoricals
        
        self.dataConnection = Connection(FileStorage("Data.db"))
        self.data = self.dataConnection.get_root()
        # I assume that there is only one variant line per genome position (I use str(genome position) as the key for this dict)
        
        #self.axisConnection = Connection(FileStorage("Axes.db"))
        self.axisLookups = {}   #self.axisConnection.get_root()
        for att in vcfAttributes['variant attributes']:
            if att == 'Genome Position':
                raise Exception('"Genome Position" attribute key is reserved in compreheNGSive')
            else:
                self.axisLookups[att] = attributeIndex(att, att in self.forcedCategoricals)
        
    def addVariant(self, variantObject):
        self.data[str(variantObject.genomePosition)] = variantObject
        
        for k,a in self.axisLookups.iteritems():
            a.add(variantObject.genomePosition, variantObject.getAttribute(k))
        
        variantData.VARIANTS_ADDED += 1
        if variantData.VARIANTS_ADDED >= variantData.COMMIT_FREQ:
            variantData.VARIANTS_ADDED = 0
            self.dataConnection.commit()
            #self.axisConnection.commit()
        '''for k,v in variantObject.attributes.iteritems():
            if not self.axisLookups.has_key(k):
                print k, self.axisLookups.iterkeys()
                self.axisLookups[k] = attributeIndex(k, k in self.forcedCategoricals)   # TODO: technically, I should throw an error (this is a .vcf file that doesn't define one of its INFO fields in the header)
            self.axisLookups[k].add(variantObject.genomePosition, v)'''
    
    def getData(self, positions, att):
        if not isinstance(positions, list):
            sys.stderr.write("WARNING: Results will be unordered!")
        return ['Missing' if not self.data.has_key(str(p)) else self.data[str(p)].getAttribute(att) for p in positions]
    
    def getDatum(self, position, att):
        return 'Missing' if not self.data.has_key(str(position)) else self.data[str(position)].getAttribute(att)
    
    def get2dData(self, positions, att1, att2):
        if not isinstance(positions,list):
            positions = list(positions) # ensure the order is the same
        return zip(self.getData(positions,att1),self.getData(positions,att2))
    
    def get2dDatum(self, position, att1, att2):
        return (self.getDatum(position, att1),self.getDatum(position, att2))
    
    def query(self, att, ranges, labels):
        return self.axisLookups[att].query(ranges,labels)
    
    def query2D(self, att1, ranges1, labels1, att2, ranges2, labels2, limit=None):
        return rangeDict.intersection((self.axisLookups[att1].lookup,ranges1,labels1),(self.axisLookups[att2].lookup,ranges2,labels2))
    
    def count(self, att, ranges, labels):
        return self.axisLookups[att].count(ranges,labels)
    
    def count2D(self, att1, ranges1, labels1, att2, ranges2, labels2, limit=None):
        return rangeDict.count2D(self.axisLookups[att1].lookup,ranges1,labels1,self.axisLookups[att2].lookup,ranges2,labels2,limit=limit)
    
    def getConstraintSatisfiers(self, constraints, limit=None):
        '''
        constraints: (att,resources.genomeUtils.valueFilter)
        If limit is not None, returns early with an incomplete set once the set of passing variants exceeds size of limit
        '''
        ranges = [] # [[]]
        minSize = sys.maxint
        minIndex = None
        for i,(att,fil) in enumerate(constraints):
            ranges.append([])
            size = 0
            for l,h in fil.getRanges():
                low = self.axisLookups[att].myList.bisect(l,rangeDict.MIN)
                high = self.axisLookups[att].myList.bisect(h,rangeDict.MAX)
                ranges[i].append((low,high))
                size += high-low
            for k in fil.getValues():
                low = self.axisLookups[att].myList.bisect(k,rangeDict.MIN)
                high = self.axisLookups[att].myList.bisect(k,rangeDict.MAX)
                ranges[i].append((low,high))
                size += high-low
            if size < minSize:
                minIndex = i
                minSize = size
        
        if minIndex == None:
            return set()
        smallestDict = constraints[minIndex][0]
        
        results = set()
        for r in ranges[minIndex]:
            i = r[0]
            while i <= r[1]:    # <= or < ?
                pos = smallestDict[i]
                v = self.data[str(pos)]
                passedAll = True
                for j,(att,fil) in enumerate(constraints):
                    if j == i:
                        continue
                    if not fil.isValid(v.getAttribute(att)):
                        passedAll = False
                        break
                if passedAll:
                    results.add(pos)
                i += 1
                if len(results) >= limit:
                    return results
        return results

class selection:
    NAMELESS_INDEX = 1
    def __init__(self, vdata, name=None, result=None, params=None, prefilters=None):
        self.vdata = vdata
        
        if name == None:
            self.name = "Group %s" % selection.NAMELESS_INDEX
            selection.NAMELESS_INDEX += 1
        else:
            self.name = name
        
        if result != None and params != None:
            self.result = set(result)
            self.params = params.copy()
        else:
            if prefilters == None:
                self.applySelectAll(applyImmediately=True)
            else:
                self.applyCustomFilters(prefilters, applyImmediately=True)
    
    def updateResult(self):
        args = []
        for att,p in self.params.iteritems():
            args.append((self.vdata.axisLookups[att].lookup,p[0],p[1]))
        self.result = rangeDict.intersection(*args)
    
    def findClosestEndpoints(self, att, value):
        highDiff = sys.float_info.max
        closestHigh = -1
        lowDiff = sys.float_info.min
        closestLow = -1
        
        for i,(low,high) in enumerate(self.params[att][0]):
            temp = abs(high-value)
            if temp < highDiff:
                closestHigh = i
                highDiff = temp 
            temp = abs(low-value)
            if temp < lowDiff:
                closestLow = i
                lowDiff = temp
        return (closestHigh,highDiff,closestLow,lowDiff)
    
    def findClosestRange(self, att, value, isHigh=None):
        diff = sys.float_info.max
        closest = -1
        
        if isHigh == None:
            isHigh = False
            repeat = 0
        else:
            repeat = 1
        
        while repeat < 2:
            for i,(low,high) in enumerate(self.params[att][0]):
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
    
    def simplifyNumericSelections(self, att):
        selectedRanges = self.params[att][0]
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
        
        self.params[att] = (newRanges,self.params[att][1])
    
    def applyCustomFilters(self, prefilters, applyImmediately=True):
        # If we're getting called, only select stuff that's been specified
        self.params = {}
        
        for att in self.vdata.axisLookups.iterkeys():
            if prefilters.has_key(att):
                if prefilters[att].ranges == None:
                    ranges = [(self.vdata.axisLookups[att].minimum,self.vdata.axisLookups[att].maximum)]
                else:
                    ranges = list(prefilters[att].ranges)
                if prefilters[att].ranges == None:
                    values = set(self.vdata.axisLookups[att].categoricalKeys)
                else:
                    values = set(prefilters[att].values)
            else:
                ranges = []
                values = set()
            self.params[att] = (ranges,values)
        
        if applyImmediately:
            self.updateResult()
    
    def applySelectAll(self, applyImmediately=True):
        self.params = {}    # {str:([(float,float)],set(str)}
        
        for att,axis in self.vdata.axisLookups.iteritems():
            ranges = [(axis.minimum,axis.maximum)]
            labels = set(axis.categoricalKeys)
            self.params[att] = (ranges,labels)
        
        if applyImmediately:
            self.updateResult()
    
    def applySelectNone(self, applyImmediately=True):
        self.params = {}
        self.result = set()
    
    def addNumericRange(self, att, newLow, newHigh, applyImmediately=True):
        self.params[att][0].append((newLow,newHigh))
        if applyImmediately:
            self.simplifyNumericSelections(att)
            self.updateResult()
    
    def removeNumericRange(self, att, value, applyImmediately=True):
        index = self.findClosestRange(att, value, isHigh=None)
        del self.param[att][0][index]
        if applyImmediately:
            self.updateResult()
    
    def applyNumericSelection(self, att, index, isHigh, newValue, applyImmediately=True):
        if isHigh:
            self.params[att][0][index] = (self.params[att][0][index][0],newValue)
        else:
            self.params[att][0][index] = (newValue,self.params[att][0][index][1])
        if applyImmediately:
            self.simplifyNumericSelections(att)
            self.updateResult()
    
    def applyLabelToggle(self, att, label, applyImmediately=True):
        if label in self.params[att][1]:
            self.params[att][1].discard(label)
        else:
            self.params[att][1].add(label)
        if applyImmediately:
            self.updateResult()
    
    def applyLabelSelection(self, att, label, include, applyImmediately=True):
        if include:
            self.params[att][1].add(label)
        else:
            self.params[att][1].discard(label)
        if applyImmediately:
            self.updateResult()
    
    def applySelectAllLabels(self, att, include=True, applyImmediately=True):
        self.params[att][1].update(self.vdata.axisLookups[att].categoricalKeys)
        if applyImmediately:
            self.updateResult()
    
    def getUnion(self, others):
        new = selection(self.vdata, name=None, result=self.result, params=self.params)
        
        for other in others:
            for att,(ranges,labels) in other.params.iteritems():
                for low,high in ranges:
                    new.addNumericRange(att, low, high, applyImmediately=False)
                new.params[att][1].update(labels)
        
        for att in new.params.iterkeys():
            new.simplifyNumericSelections(att)
        
        new.updateResult()
        return new
    
    def getIntersection(self, others):
        new = selection(self.vdata, name=None, result=self.result, params=self.params)
                
        for other in others:
            for att,(ranges,labels) in other.params.iteritems():
                newRanges = []
                for low,high in ranges:
                    for myLow,myHigh in new.params[att][0]:
                        newLow = max(myLow,low)
                        newHigh = min(myHigh,high)
                        if newLow <= newHigh:
                            newRanges.append((newLow,newHigh))
                
                newLabels = self.params[att][1].intersection(labels)
                
                new.params[att] = (newRanges,newLabels)
        
        new.updateResult()
        return new
    
    def getDifference(self, others):
        new = selection(self.vdata, name=None, result=self.result, params=self.params)
        
        for other in others:
            for att,(ranges,labels) in other.params.iteritems():
                for i,(myLow,myHigh) in enumerate(new.params[att][0]):
                    for low,high in ranges:
                        if myLow >= low and myLow <= high:
                            myLow = high
                        if myHigh >= low and myHigh <= high:
                            myHigh = low
                        new.params[att][0][i] = (myLow,myHigh)
                
                new.params[att][1].difference_update(labels)
        
        new.updateResult()
        return new
    
    def getInverse(self):
        raise Exception('Not implemented yet.')
        '''newParams = {}
        
        for att in self.params.iterkeys():
            newParams[att] = ([(att.minimum,att.maximum)],self.vdata.axisLookups[att].categoricalKeys.difference(self.params[att][1]))
        new = selection(self.vdata, name=None, result=set(), params=([(self.minimum,self.maximum)],set()))
        return new.getDifference(self)'''
    
    def previewUnion(self, others):
        tempResult = set(self.result)
        for o in others:
            tempResult.update(o.result)
        return tempResult
    
    def previewParameterUnion(self, others):
        tempResult = {}
        for att,(ranges,labels) in self.params.iteritems():
            tempResult[att] = (list(ranges),set(labels))
        
        for o in others:
            for att,(ranges,labels) in o.params.iteritems():
                tempResult[att][0].extend(ranges)    # don't bother to consolidate... make it obvious that multiple selections are active
                tempResult[att][1].update(labels)
        return tempResult
    
    def previewNumericSelection(self, att, index, isHigh, newValue):
        if isHigh:
            return self.vdata.axisLookups[att].query((self.params[att][0][index][0],newValue),set())
        else:
            return self.vdata.axisLookups[att].query((newValue,self.params[att][0][index][1]),set())
    
    def previewLabelSelection(self, att, label, include=True):
        return self.vdata.axisLookups[att].query((),set(label))

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
    
    def getActivePoints(self):
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
    
    ATT_REQUIRED = set([NUMERIC_CHANGE,NUMERIC_ADD,MULTI_ADD,NUMERIC_REMOVE,NUMERIC_TOP_FIVE_PERCENT,LABEL_TOGGLE,ALL,NONE])
    
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
                
                if self.opType in operation.ATT_REQUIRED:
                    assert self.kwargs.has_key('att')
                    self.att = self.kwargs['att']
                    
                    if self.opType in operation.SINGLE_LOSSY:
                        self.previousParams = deepcopy(self.activeSelection.params[self.att])
            
            else:
                assert self.opType not in operation.SINGLE_SELECTION_REQUIRED
                self.activeSelections = self.selections.activeSelections
                
                if self.opType == operation.SELECTION_DELETE:
                    self.previousParams = {}
                    for s in self.activeSelections:
                        self.previousParams[s.name] = {}
                        for att,(ranges,labels) in s.params.iteritems():
                            self.previousParams[s.name][att] = (list(ranges),set(labels))
            
            # operation-specific inits
            if self.opType == operation.NUMERIC_CHANGE:
                assert self.kwargs.has_key('start') and self.kwargs.has_key('end') and self.kwargs.has_key('isHigh')
                self.start = self.kwargs['start']
                self.end = self.kwargs['end']
                self.isHigh = self.kwargs['isHigh']
                self.rangeIndex = self.activeSelection.findClosestRange(self.att, self.start, self.isHigh)
            elif self.opType == operation.LABEL_TOGGLE:
                assert self.kwargs.has_key('label')
                self.label = self.kwargs['label']
            elif self.opType == operation.NUMERIC_ADD or self.opType == operation.NUMERIC_REMOVE:
                assert self.kwargs.has_key('position')
                self.position = self.kwargs['position']
            elif self.opType == operation.MULTI_ADD:
                assert self.kwargs.has_key('secondAtt') and self.kwargs.has_key('position') and self.kwargs.has_key('secondPosition')
                self.secondAtt = self.kwargs['secondAtt']
                
                self.position = self.kwargs['position']
                self.secondPosition = self.kwargs['secondPosition']
                
                self.includeAllLabels = self.kwargs.get('includeAllLabels',False)
                self.includeAllSecondLabels = self.kwargs.get('includeAllSecondLabels',False)
                
                self.secondPreviousParams = deepcopy(self.activeSelection.params[self.secondAtt])
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
                for att,(ranges,labels) in self.activeSelection.params.iteritems():
                    self.previousParams[att] = (list(ranges),set(labels))
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
            self.activeSelection.applyNumericSelection(self.att, self.rangeIndex, self.isHigh, self.end)
        elif self.opType == operation.NUMERIC_ADD:
            self.activeSelection.addNumericRange(self.att, self.position)
        elif self.opType == operation.NUMERIC_REMOVE:
            self.activeSelection.removeNumericRange(self.att, self.position)
        elif self.opType == operation.MULTI_ADD:
            if self.includeAllLabels:
                self.activeSelection.applySelectAllLabels(self.att, applyImmediately=False)
            if self.includeAllSecondLabels:
                self.activeSelection.applySelectAllLabels(self.secondAtt, applyImmediately=False)
            self.activeSelection.addNumericRange(self.att, self.position, applyImmediately=False)
            self.activeSelection.addNumericRange(self.secondAtt, self.secondPosition)
        elif self.opType == operation.NUMERIC_TOP_FIVE_PERCENT:
            self.activeSelection.applySelectTopFivePercent(self.att)
        elif self.opType == operation.ALL:
            self.activeSelection.applySelectAll(self.att)
        elif self.opType == operation.NONE:
            self.activeSelection.applySelectNone(self.att)
        elif self.opType == operation.LABEL_TOGGLE:
            self.activeSelection.applyLabelToggle(self.att,self.label)
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
            for att,(ranges,labels) in self.previousParams.iteritems():
                self.activeSelection.params[att] = (deepcopy(ranges),deepcopy(labels))
            self.activeSelection.updateResult()
        elif self.opType in operation.SINGLE_LOSSY:
            self.activeSelection.params[self.att] = deepcopy(self.previousParams)
            if self.opType == operation.MULTI_ADD:
                self.activeSelection.params[self.secondAtt] = deepcopy(self.secondPreviousParams)
            self.activeSelection.updateResult()
        
        # fix easy to restore operations
        if self.opType == operation.LABEL_TOGGLE:
            self.activeSelection.applyLabelToggle(self.att,self.label)
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

class interactionManager:
    def __init__(self, vData, prefilters):
        self.vData = vData
        self.app = None
        
        # some final tidying up of the data object
        for a in self.vData.axisLookups.itervalues():
            a.findNaturalMinAndMax()
        self.vData.dataConnection.commit()
        #self.vData.axisConnection.commit()
        
        self.selections = selectionState(self.vData, prefilters)
        self.currentOperation = operation(operation.NO_OP, self.selections, previousOp = None)
        
        self.highlightedPoints = set()
        self.activePoints = self.selections.getActivePoints()
        self.activeParams = self.selections.getActiveParameters()
    
    def setApp(self, app):
        self.app = app
        self.app.notifyOperation(self.currentOperation)
        self.app.notifySelection(self.activePoints,self.activeParams)
    
    def newOperation(self, opCode, **kwargs):
        newOp = operation(opCode, self.selections, previousOp=self.currentOperation, **kwargs)
        if newOp.isLegal:
            self.currentOperation = newOp
            if newOp.opType not in operation.DOESNT_DIRTY:
                self.activePoints = self.selections.getActivePoints()
                self.activeParams = self.selections.getActiveParameters()
                self.app.notifySelection(self.activePoints,self.activeParams)
            self.app.notifyOperation(newOp)
        return newOp.isLegal
    
    def multipleSelected(self):
        return False    # TODO
    
    def undo(self):
        assert self.currentOperation.previousOp != None and (self.currentOperation.nextOp == None or self.currentOperation.nextOp.finished == False)
        self.currentOperation.undo()
        self.currentOperation = self.currentOperation.previousOp
        self.selections = self.currentOperation.selections
        self.activePoints = self.selections.getActivePoints()
        self.activeParams = self.selections.getActiveParameters()
        self.app.notifyOperation(self.currentOperation)
        self.app.notifySelection(self.activePoints,self.activeParams)
    
    def redo(self):
        assert self.currentOperation.nextOp != None and self.currentOperation.nextOp.finished == False
        self.currentOperation = self.currentOperation.nextOp
        self.currentOperation.applyOp()
        self.selections = self.currentOperation.selections
        self.activePoints = self.selections.getActivePoints()
        self.activeParams = self.selections.getActiveParameters()
        self.app.notifyOperation(self.currentOperation)
        self.app.notifySelection(self.activePoints,self.activeParams)
