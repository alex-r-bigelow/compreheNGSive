from resources.utils import chrLengths, chrOffsets
from resources.structures import recursiveDict, TwoTree, FourTree
import operator, math

class mixedAxis:
    def __init__(self):
        self.tree = None
        self.rsValues = {}
        self.rsValuePairs = []
        self.rsLabels = {}
        self.labels = {'Missing':set(),'Allele Masked':set()}
        self.labelOrder = ['Numeric','Missing','Allele Masked']
        
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
        if len(self.rsValuePairs) > 0:
            self.rsValuePairs.sort(key=lambda i: i[1])
            self.tree = TwoTree(self.rsValuePairs)
        else:
            self.tree = None
        
        if len(self.labelOrder) <= 3:
            self.labelOrder = ['Numeric','Missing','Allele Masked']
        
        for l in sorted(self.labels.iteritems()):
            if l not in self.labelOrder:
                self.labelOrder.append(l)
        self.isfinished = True
    
    def select(self, labels=set(), ranges=set(), includeMissing=False, includeMasked=False):
        assert self.isfinished
        results = set()
        if self.tree != None:
            for low,high in ranges:
                results.update(self.tree.select(low,high,includeMasked=includeMasked,includeUndefined=includeMissing,includeMissing=includeMissing))
        for l in labels:
            results.add(self.labels[l])
        return results
    
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
    
    def getMin(self):
        if self.tree == None or self.tree.root == None:
            return None
        else:
            return self.tree.root.low
    
    def getMax(self):
        if self.tree == None or self.tree.root == None:
            return None
        else:
            return self.tree.root.high
    
    def hasMasked(self):
        return len(self.labels['Allele Masked']) != 0
    
    def hasMissing(self):
        return len(self.labels['Missing']) != 0

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

        