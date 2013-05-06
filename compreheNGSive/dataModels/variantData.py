from resources.structures import categoricalIndex, numericIndex, mixedIndex
from resources.genomeUtils import variantFile
from durus.file_storage import FileStorage
from durus.connection import Connection
from copy import deepcopy
import sys, tempfile

class variantData(variantFile):
    COMMIT_FREQ = 1000
    VARIANTS_ADDED = 0
    GENOME_LABEL = "#genome_position#"
    AXIS_TYPES = {variantFile.cvfAttributeDetails.CATEGORICAL:categoricalIndex,
                  variantFile.cvfAttributeDetails.NUMERIC:numericIndex,
                  variantFile.cvfAttributeDetails.MIXED:mixedIndex,
                  variantFile.cvfAttributeDetails.IGNORE:None,
                  variantFile.cvfAttributeDetails.CHR:None,
                  variantFile.cvfAttributeDetails.POS:None,
                  variantFile.cvfAttributeDetails.ID:None
                  }
    
    def __init__(self, path, tickFunction, columnsToIndex):
        variantFile.__init__(self,path)
        
        # Set up disk-based storage
        tempFile = tempfile.NamedTemporaryFile()
        tempPath = tempFile.name
        tempFile.close()
        
        self.dataConnection = Connection(FileStorage(tempPath))
        self.data = self.dataConnection.get_root()
        
        # set up query structures
        self.data[variantData.GENOME_LABEL] = numericIndex()   # GENOME_LABEL references ALL per-variant lists; other indexes just map values to position
        self.columnIndices = {}
        for att in columnsToIndex:
            if att == variantData.GENOME_LABEL:
                raise Exception("Can not use reserved column header: %s" % variantData.GENOME_LABEL)
            indexType = variantData.AXIS_TYPES[self.variantAttributes[att].columnType]
            self.data[att] = indexType(att,self.variantAttributes[att].low,self.variantAttributes[att].high,self.variantAttributes[att].values)
            self.columnIndices[att] = self.variantAttributeOrder.index(att)
        
        # Load the cvf file
        if self.lengthEstimate == None:
            self.lengthEstimate = 10000000
        tickInterval = self.lengthEstimate/variantData.COMMIT_FREQ
        nextTick = tickInterval
        for i,(attributes,genomePos) in enumerate(self.readCvfLines()):
            self.data[genomePos] = attributes
            for att in columnsToIndex:
                self.data[att] = attributes[self.columnIndices[att]]
                self.axisLookups[att][genomePos] = attributes[self.columnIndices[att]]
            if i >= nextTick:
                tickFunction()
                self.dataConnection.commit()
                nextTick += tickInterval
        self.dataConnection.commit()
        self.findNaturalMinsAndMaxes()
    
    def getRange(self, att):
        if isinstance(self.data[att],numericIndex):
            return (self.data[att].minimum,self.data[att].maximum)
        elif isinstance(self.data[att],mixedIndex):
            return (self.data[att].numerics.minimum,self.data[att].maximum)
        else:
            return None
    
    def getKeys(self, att):
        if isinstance(self.data[att],categoricalIndex):
            return self.data[att].data.keys()
        elif isinstance(self.data[att],mixedIndex):
            return self.data[att].categoricals.data.keys()
        else:
            return set()
    
    def findNaturalMinsAndMaxes(self):
        for att in self.columnIndices.iterkeys():
            if isinstance(self.data[att],numericIndex):
                self.data[att].findNaturalMinAndMax()
            elif isinstance(self.data[att],mixedIndex):
                self.data[att].numerics.findNaturalMinAndMax()
        self.dataConnection.commit()
    
    def getData(self, positions, att):
        if not isinstance(positions, list):
            sys.stderr.write("WARNING: Results will be unordered!")
        return [self.getDatum(p, att) for p in positions]
    
    def getDatum(self, position, att):
        return 'Missing' if not self.data[variantData.GENOME_LABEL].has_key(position) else self.data[variantData.GENOME_LABEL][position][self.columnIndices[att]]
    
    def get2dData(self, positions, att1, att2):
        return [self.get2dDatum(position, att1, att2) for position in positions]
    
    def get2dDatum(self, position, att1, att2):
        return (self.getDatum(position, att1),self.getDatum(position, att2))
    
    def query(self, att, ranges=None, labels=None):
        temp = set()
        if ranges != None:
            for low,high in ranges:
                temp.update(self.data[att][low:high])
        if labels != None:
            temp.update(self.data[att][labels])
        return temp
    
    def query2D(self, att1, att2, ranges1=None, ranges2=None, labels1=None, labels2=None):
        temp = set()
        if ranges1 == None:
            for low,high in ranges1:
                temp.update(self.data[att1][low:high])
        if labels1 == None:
            temp.update(self.data[att1][labels1])
        if ranges2 != None:
            for low,high in ranges2:
                temp.intersection_update(self.data[att2][low:high])
        if labels2 != None:
            temp.intersection_update(self.data[att2][labels2])
        return temp
    
    def count(self, att, ranges=None, labels=None):
        temp = 0
        if ranges == None:
            return self.data[att].count(labels)
        elif labels == None:
            temp = 0
            for low,high in ranges:
                temp += self.data[att].count(low,high)
            return temp
        else:
            return self.data[att].count(low,high,keys=labels)
    
    def count2D(self, att1, att2, ranges1=None, ranges2=None, labels1=None, labels2=None, limit=None):
        return self.countConstraintSatisfiers({att1:(ranges1,labels1),att2:(ranges2,labels2)}, limit)
        '''count = 0
        for pos in self.query(att1,ranges1,labels1):
            value2 = self.data[variantData.GENOME_LABEL][pos][self.columnIndices[att2]]
            if value2 in labels2:
                count += 1
                if limit != None and count >= limit:
                    return count
                continue
            elif ranges2 != None:
                for low,high in ranges2:
                    if value2 >= low and value2 <= high:
                        count += 1
                        if limit != None and count >= limit:
                            return count
                        continue
        return count'''
    
    def countConstraintSatisfiers(self, params, limit=None):
        # params {str:([(float,float)],set(str)}
        
        # TODO: find the cheapest, smallest set of positions to iterate over
        paramItems = params.iteritems()
        att,(ranges,labels) = paramItems.next()    # cheap and dirty way of pulling an arbitrary attribute
        
        count = 0
        for pos in self.query(att,ranges,labels):
            values = self.data[variantData.GENOME_LABEL][pos]
            passedAll = True
            for att2,(ranges2,labels2) in paramItems:
                value2 = values[self.columnIndices[att2]]
                if value2 not in labels2:
                    passedThis = False
                    for low,high in ranges2:
                        if value2 >= low and value2 <= high:
                            passedThis = True
                            break
                    if not passedThis:
                        passedAll = False
                        break
            if passedAll:
                count += 1
                if limit != None and count >= limit:
                    return count
        return count
    
    def getConstraintSatisfiers(self, params, limit=None):
        # params {str:([(float,float)],set(str)}
        
        # TODO: find the cheapest, smallest set of positions to iterate over
        paramItems = params.iteritems()
        att,(ranges,labels) = paramItems.next()    # cheap and dirty way of pulling an arbitrary attribute
        
        results = set()
        for pos in self.query(att,ranges,labels):
            values = self.data[variantData.GENOME_LABEL][pos]
            passedAll = True
            for att2,(ranges2,labels2) in paramItems:
                value2 = values[self.columnIndices[att2]]
                if value2 not in labels2:
                    passedThis = False
                    for low,high in ranges2:
                        if value2 >= low and value2 <= high:
                            passedThis = True
                            break
                    if not passedThis:
                        passedAll = False
                        break
            if passedAll:
                results.add(pos)
                if limit != None and len(results) >= limit:
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
                raise Exception('Prefilters no longer supported')
                self.applyCustomFilters(prefilters, applyImmediately=True)
    
    def updateResult(self):
        self.result = self.vdata.getConstraintSatisfiers(self.params)
    
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
    
    def applySelectAll(self, applyImmediately=True):
        self.params = {}    # {str:([(float,float)],set(str)}
        
        for att in self.vdata.columnIndices.iterkeys():
            ranges = []
            r = self.vdata.getRange(att)
            if r != None:
                ranges.append(r)
            labels = set(self.vdata.getKeys(att))
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
        self.params[att][1].update(self.vdata.getKeys(att))
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
        raise Exception('Not implemented yet.')
        '''if isHigh:
            return self.vdata.axisLookups[att].query((self.params[att][0][index][0],newValue),set())
        else:
            return self.vdata.axisLookups[att].query((newValue,self.params[att][0][index][1]),set())'''
    
    def previewLabelSelection(self, att, label, include=True):
        raise Exception('Not implemented yet.')
        #return self.vdata.axisLookups[att].query((),set(label))

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