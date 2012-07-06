from resources.utils import chrLengths, chrOffsets
from resources.structures import recursiveDict, TwoTree, FourTree
from copy import deepcopy
import operator, math, re

selectionLabelRegex = re.compile('\(\d+\)')

class mixedAxis:
    def __init__(self):
        self.tree = None
        self.rsValues = {}
        self.rsValuePairs = []
        self.selectedValueRanges = set()   # set(tuple(low,high))
        
        self.rsLabels = {}
        self.labels = {'Missing':set(),'Allele Masked':set()}
        self.selectedLabels = {}    # {label:bool}
        
        self.labelOrder = ['Numeric','Missing','Allele Masked']
        self.visibleLabels = {}
        self.isfinished = False
    
    def add(self, id, value):
        self.isfinished = False
        
        if isinstance(value,list):
            value = ",".join(value)
        
        if value == None:
            self.labels['Missing'].add(value)
        else:
            try:
                value = float(value)
                if math.isinf(value):
                    self.labels['Missing'].add(value)
                elif math.isnan(value):
                    self.labels['Allele Masked'].add(value)
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
        self.visibleLabels = {}
        if len(self.rsValuePairs) > 0:
            self.rsValuePairs.sort(key=lambda i: i[1])
            self.tree = TwoTree(self.rsValuePairs)
            self.findNaturalMinAndMax()
            if len(self.selectedValueRanges) == 0:
                self.selectedValueRanges.add((self.getMin(),self.getMax()))
            self.visibleLabels['Numeric']=True
            self.selectedLabels['Numeric']=True
        else:
            self.tree = None
            self.selectedValueRanges = set()
            self.visibleLabels['Numeric']=None
            self.selectedLabels['Numeric']=False
        
        if len(self.labelOrder) <= 3:
            self.labelOrder = ['Numeric','Missing','Allele Masked']
            miss = self.hasMissing()
            mask = self.hasMasked()
            self.selectedLabels['Missing'] = miss
            self.selectedLabels['Allele Masked'] = mask
            if not miss:
                miss = None
            if not mask:
                mask = None
            self.visibleLabels['Missing'] = miss
            self.visibleLabels['Allele Masked'] = mask
        
        for l in sorted(self.labels.iterkeys()):
            if l not in self.labelOrder:
                self.labelOrder.append(l)
                self.selectedLabels[l] = True
                self.visibleLabels[l] = True
        self.isfinished = True
    
    def getSelected(self):
        assert self.isfinished
        results = set()
        if self.tree != None:
            for low,high in self.selectedValueRanges:
                results.update(self.tree.select(low,high,includeMasked=False,includeUndefined=False,includeMissing=False))  # I actually implement the missing/masked stuff outside the tree(s)
        for l,include in self.selectedLabels.iteritems():
            if include:
                results.add(self.labels[l])
        return results
    
    def simplifyNumericSelections(self):
        while True:
            numSelections = len(self.selectedValueRanges)
            
            newValueRanges = []
            for low,high in self.selectedValueRanges:
                for pair in newValueRanges:
                    if (low >= pair[0] and low <= pair[1]) or (high >= pair[0] and high <= pair[1]):
                        pair[0] = min(low,pair[0])
                        pair[1] = max(high,pair[1])
                    else:
                        newValueRanges.append((low,high))
            self.selectedValueRanges = set(newValueRanges)
            
            if len(self.selectedValueRanges) == numSelections:
                return
    
    def modifyNumericSelection(self, oldLow, oldHigh, newLow, newHigh):
        self.selectedValueRanges.remove((oldLow,oldHigh))
        self.selectedValueRanges.add((newLow,newHigh))
    
    def modifyLabelSelection(self, label, include):
        self.selectedLabels[label] = include
        if include:
            self.visibleLabels[label] = None
        else:
            self.visibleLabels[label] = True
    
    def getLabels(self):
        assert self.isfinished
        return self.labelOrder
    
    def reorder(self, remove, insertBefore):
        assert self.isfinished
        self.labelOrder.remove(remove)
        target = self.labelOrder.index(insertBefore)
        self.labelOrder.insert(target,remove)
    
    def getValues(self, rsNumbers):
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
        if self.tree == None or self.tree.root == None:
            self.minimum = None
            self.maximum = None
            return
        else:
            self.minimum = self.tree.root.low
            self.maximum = self.tree.root.high
            if self.minimum == self.maximum:
                self.minimum = 0
                if self.maximum == 0:
                    self.maximum = 1
            '''span = self.maximum - self.minimum
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
            
            # prefer nearestTenMax if the gap between it and self.maximum is less than 25% the span of the data; otherwise just add a 5% margin to the top
            if nearestTenMax - self.maximum < 0.25*span:
                self.maximum = nearestTenMax
            else:
                self.maximum += 0.05*span
            # prefer zero if the gap between it and self.minimum is less than 50% the span of the data, then 25% for nearestTenMin, otherwise 5% margin to the bottom
            if self.minimum > 0.0 and self.minimum < 0.5*span:
                self.minimum = 0.0
            elif nearestTenMin < 0.25*span:
                self.minimum = nearestTenMin
            else:
                self.minimum -= 0.05*span'''
    
    def getMin(self):
        return self.minimum
    
    def getMax(self):
        return self.maximum
    
    def hasNumeric(self):
        return self.tree != None
    
    def hasMasked(self):
        return len(self.labels['Allele Masked']) != 0
    
    def hasMissing(self):
        return len(self.labels['Missing']) != 0

class operation:
    def __init__(self, name):
        self.name = name
        self.applied = True
        self.isFirstOp = True
        
        self.previousOp = None
        self.nextOp = None
        
        self.result = set()
        self.preview = set()
    
    def updatePreview(self):
        self.preview = set()
    
    def apply(self, allData):
        return self
    
    def undo(self):
        return self
    
class setOperation(operation):
    def __init__(self, name, previousOps, op="UNION"):
        self.name = name
        self.applied = False
        self.isFirstOp = False
        
        self.nextOp = None
        assert len(previousOps) > 0
        self.previousOps = previousOps
        for o in previousOps:
            assert o.applied == True
            o.nextOp = self
        
        self.result = set()
        self.preview = set()
        
        self.updatePreview()
        
        self.op = op
    
    def adjust(self, opToAdd=None, opToRemove=None):
        assert self.applied == False
        if opToRemove != None and opToAdd == None and len(self.previousOps) <= 1:
            return
        if opToRemove != None:
            assert opToRemove.applied == True
            self.previousOps.remove(opToRemove)
            opToRemove.nextOp = None
        if opToAdd != None:
            assert opToAdd.applied == True
            self.previousOps.append(opToAdd)
            opToAdd.nextOp = self
        self.updatePreview()
    
    def updatePreview(self):
        self.preview = set()
        for o in self.previousOps:
            self.preview.update(o.result)
    
    def apply(self, allData):
        self.applied = True
        
        if self.op == "UNION" or self.op == "COMPLEMENT":
            self.result = set()
            for o in self.previousOps:
                assert o.applied
                self.result.update(o.result)
        elif self.op == "INTERSECTION":
            self.result = None
            for o in self.previousOps:
                if self.result == None:
                    self.result = set(o.result)
                else:
                    self.result.intersection_update(o.result)
        elif self.op == "DIFFERENCE":
            self.result = None
            for o in self.previousOps:
                if self.result == None:
                    self.result = set(o.result)
                else:
                    self.result.difference_update(o.result)
        
        if self.op == "COMPLEMENT":
            temp = set(allData.data.iterkeys())
            temp.difference_update(self.result)
            self.result = temp
        
        self.preview = set(self.result)
        
        return self
    
    def undo(self):
        self.applied = False
        self.result = set()
        return list(self.previousOps)
    
    def abort(self):
        for o in self.previousOps:
            o.nextOp = None
        
class numericOperation(operation):
    def __init__(self, name, previousOp, axis, lowStart, highStart):
        self.name = name
        self.applied = False
        self.isFirstOp = False
        
        self.nextOp = None
        self.previousOp = previousOp
        
        assert previousOp.applied == True
        previousOp.nextOp = self
        
        self.result = self.previousOp.result
        self.startPreview = self.axis.getSelected()
        self.preview = set()
        
        self.oldRanges = set(axis.selectedValueRanges)
        
        self.axis = axis
        self.lowStart = lowStart
        self.highStart = highStart
        self.low = lowStart
        self.high = highStart
    
    def adjust(self, deltaLow, deltaHigh):
        assert self.applied == False
        self.low += deltaLow
        self.high += deltaHigh
        self.updatePreview()
    
    def updatePreview(self):
        newSet = set()
        if self.axis.tree != None:
            newSet.update(self.axis.tree.select(self.low,self.high,includeMasked=False,includeUndefined=False,includeMissing=False))
        self.preview = self.startPreview.difference(newSet)
    
    def apply(self, allData):
        self.applied = True
        if self.low == self.lowStart and self.high == self.highStart:
            self.axis.selectedValueRanges.add((self.low,self.high))
            self.axis.simplifyNumericSelections()
        else:
            self.axis.modifyNumericSelection(self.lowStart,self.highStart,self.low,self.high)
            self.axis.simplifyNumericSelections()
        
        self.result = self.axis.getSelected()
        for a in allData.axes.itervalues():
            if len(a) == 0:
                break
            if a != self.axis:
                self.result.intersection_update(a.getSelected())
        
        self.preview = set(self.result)
        return self
        
    def undo(self):
        self.applied = False
        self.result = self.previousOp.result
        self.axis.selectedValueRanges = set(self.oldRanges)
        if self.low == self.lowStart and self.high == self.highStart:
            self.axis.selectedValueRanges.remove((self.low,self.high))
        else:
            self.axis.modifyNumericSelection(self.low,self.high,self.lowStart,self.highStart)
        return self.previousOp

class labelOperation(operation):
    def __init__(self, name, previousOp, axis, label, checked=True):
        self.name = name
        self.applied = False
        self.isFirstOp = False
        
        self.axis = axis
        self.label = label
        self.checked = checked
        
        self.previousOp = previousOp
        assert previousOp.applied == True
        self.previousOp.nextOp = self
        self.nextOp = None
        
        self.result = previousOp.result
        self.preview = self.axis.labels[label]
        
    def apply(self, allData):
        self.applied = True
        self.axis.modifyLabelSelection(self.label, self.checked)
        
        self.result = self.axis.getSelected()
        for a in allData.axes.itervalues():
            if len(a) == 0:
                break
            if a != self.axis:
                self.result.intersection_update(a.getSelected())
        
        return self
    
    def undo(self):
        self.applied = False
        self.result = self.previousOp.result
        self.axis.modifyLabelSelection(self.label, not self.checked)
        
        return self.previousOp

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
        
        self.activeSelection = None
        self.nonPreviewSetOps = []
        self.selectionOrder = []
        self.selections = {}
        self.newSelectionNumber = 1
        self.multipleSelected = False
        self.newSelection()
        
        self.isFrozen = False
    
    def getSelectionList(self):
        pass    # need a list of all selections in order, with flags for which are selected and which one was the first selection
    
    def getCurrentPreview(self):
        return self.activeSelection.preview
    
    def getCurrentSelection(self):
        return self.activeSelection.result
    
    def addSelection(self, new, changeToNew = True):
        self.selectionOrder.append(new.name)
        self.selections[new.name] = new
        if changeToNew:
            self.changeSelection(new.name)
    
    def changeSelection(self, name):
        if self.multipleSelected:
            self.activeSelection.abort()
            self.nonPreviewSetOps = []
        
        self.activeSelection = self.selections[name]
    
    def newSelection(self):
        new = operation('Selection %s' % self.newSelectionNumber)
        self.newSelectionNumber += 1
        self.addSelection(new)
        
    def duplicateSelection(self, name=None):
        if name == None:
            name = self.activeSelection.name
        if self.multipleSelected:
            for o in self.nonPreviewSetOps:
                self.duplicateSelection(o.name)
            self.changeSelection(self.selectionOrder[-1])
        else:
            new = deepcopy(self.selections[name])
            m = selectionLabelRegex.search(new.name)
            if m == None:
                new.name += " (2)"
            else:
                new.name = new.name[:m.start()] + "(%i)" % (int(new.name[m.start()+1:m.end()-1])+1) + new.name[m.end():]
            
            if name == self.activeSelection.name:
                self.addSelection(new)
            else:
                self.addSelection(new, False)
    
    def deleteSelection(self, name=None):
        if name == None:
            name = self.activeSelection.name
        if self.multipleSelected:
            for o in self.nonPreviewSetOps:
                self.deleteSelection(o.name)
            self.nonPreviewSetOps = []
        
        del self.selections[name]
        self.selectionOrder.remove(name)
        
        if name == self.activeSelections.name:
            if len(self.selectionOrder) == 0:
                self.newSelection()
            else:
                self.changeSelection(self.selectionOrder[-1])
    
    def previewSetOp(self, name):
        if self.multipleSelected:
            if name in self.nonPreviewSetOps:
                if len(self.activeSelection.previousOps) > 1:
                    self.activeSelection.adjust(opToRemove=self.selections[name])
            else:
                self.activeSelection.adjust(opToAdd=self.selections[name])
    
    def changeSetOp(self,name):
        if self.multipleSelected:
            if name in self.nonPreviewSetOps:
                self.nonPreviewSetOps.remove(name)
            else:
                self.nonPreviewSetOps.append(name)
    
    def startSetOp(self):
        if self.multipleSelected:
            return
        newText = "Merged"
        newIndex = 1
        while newText in self.selectionOrder:
            newText = "Merged (%i)" % newIndex
            newIndex += 1
        
        self.nonPreviewSetOps = [self.activeSelection.name]
        self.activeSelection = setOperation(newText,previousOps=list(self.nonPreviewSetOps))
        self.selectionOrder.append(newText)
        self.selections[newText] = self.activeSelection
    
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
    
    def recalculateAlleleFrequencies(self, individuals, groupName, basisGroup=[], fallback="ALT"):
        att = "%s Allele Frequency" % groupName
        for variantObject in self.data.itervalues():
            # First see if we can find a minor allele with stuff in basisGroup
            alleleCounts = {}
            for i in basisGroup:
                if variantObject.genotypes.has_key(i):
                    allele1 = variantObject.genotypes[i].allele1
                    allele2 = variantObject.genotypes[i].allele2
                    if allele1 != None:
                        alleleCounts[allele1] = alleleCounts.get(allele1,0) + 1
                    if allele2 != None:
                        alleleCounts[allele2] = alleleCounts.get(allele2,0) + 1
            if len(alleleCounts) > 1:
                minorAllele = max(alleleCounts.iteritems(), key=operator.itemgetter(1))[0]
            else:
                # Okay, we don't have any data for our basisGroup (or our basisGroup is empty)... use the fallback
                if fallback == None:
                    # No minor allele found and no fallback - we've got a masked allele frequency!
                    variantObject.attributes[att] = float('NaN')
                    continue
                elif fallback == "REF":
                    minorAllele = variantObject.ref
                elif fallback == "ALT":
                    minorAllele = variantObject.alt[0]
                else:
                    index = int(fallback[4:])
                    if index < len(variantObject.alt):
                        minorAllele = variantObject.alt[index]
                    else:
                        # Tried to define minor allele as a nonexistent secondary allele
                        variantObject.attributes[att] = float('NaN')
                        continue
            # Okay, we've found our alternate allele; now let's see how frequent it is
            minorCount = 0
            allCount = 0
            for i in individuals:
                if variantObject.genotypes.has_key(i):
                    allele1 = variantObject.genotypes[i].allele1
                    allele2 = variantObject.genotypes[i].allele2
                    if allele1 != None:
                        allCount += 1
                        if allele1 == minorAllele:
                            minorCount += 1
                    if allele2 != None:
                        allCount += 1
                        if allele2 == minorAllele:
                            minorCount += 1
            if allCount == 0:
                variantObject.attributes[att] = float('Inf')
            else:
                variantObject.attributes[att] = minorCount/float(allCount)
    
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
        
        self.axes = {"Genome Position":mixedAxis()}
        
        for att in self.axisLabels:
            self.axes[att] = mixedAxis()
            
            if startingXaxis == None:
                startingXaxis = att
            elif startingYaxis == None:
                startingYaxis = att
        
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
        
        return self.setScatterAxes(startingXaxis, startingYaxis, progressWidget)
    
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
        self.scatterXs = mixedAxis()
        self.scatterYs = mixedAxis()
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

        