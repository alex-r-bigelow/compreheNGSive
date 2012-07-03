from resources.utils import chrLengths, chrOffsets
from resources.structures import recursiveDict, TwoTree, FourTree
import operator

class mixedAxis:
    def __init__(self):
        self.tree = None
        self.rsValues = {}
        self.rsValuePairs = []
        self.rsLabels = {}
        self.labels = {}
        self.labelOrder = []
        self.treeLabelIndex = None
        
        self.isfinished = False
    
    def add(self, id, value):
        self.isfinished = False
        
        if value == None:
            value = 'inf'
        if isinstance(value,list):
            value = ",".join(value)
        
        try:
            value = float(value)
            self.rsValuePairs.append((id,value))
            self.rsValues[id] = value
        except ValueError:
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
        
        if len(self.labelOrder) == 0:
            self.labelOrder = sorted(self.labels.iterkeys())
            if self.tree != None:
                self.treeLabelIndex = 0
                self.labelOrder.insert(0,(self.getMin(),self.getMax()))
        else:
            if self.tree != None:
                if self.treeLabelIndex == None:
                    self.treeLabelIndex = 0
                self.labelOrder[self.treeLabelIndex] = (self.getMin(),self.getMax())
            elif self.treeLabelIndex != None:
                del self.labelOrder[self.treeLabelIndex]
            
            for l in sorted(self.labels.iterkeys()):
                if l not in self.labelOrder:
                    self.labelOrder.append(l)
        self.isfinished = True
    
    def select(self, labels=set(), low=None, high=None, includeMissing=False, includeMasked=False):
        if not self.isfinished:
            print "ERROR: Attempted to query unfinished axis"
            sys.exit(1)
        if self.tree != None:
            results = self.tree.select(low,high,includeMasked=includeMasked,includeUndefined=includeMissing,includeMissing=includeMissing)
        else:
            results = set()
        for l in labels:
            results.add(self.labels[l])
        return results
    
    def getLabels(self):
        if not self.isfinished:
            print "ERROR: Attempted to get labels of unfinished axis"
            sys.exit(1)
        return self.labelOrder
    
    def reorder(self, remove, insertAfter):
        if not self.isfinished:
            print "ERROR: Attempted to reorder unfinished axis"
            sys.exit(1)
        self.labelOrder.remove(remove)
        target = self.labelOrder.index(insertAfter)+1
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
        if len(self.tree.maskedIDs) == 0:
            return False
        else:
            return True
    
    def hasMissing(self):
        if len(self.tree.undefinedIDs) == 0 and len(self.tree.missingIDs) == 0:
            return False
        else:
            return True
    
    def crossSection(self, other):
        if not self.isfinished:
            print "ERROR: Attempted to get cross section from unfinished axis"
        scatter = FourTree()
        myLabelAxes = {}
        otherLabelAxes = {}
        
        for rs,v in self.rsValues.iteritems():
            if other.rsLabels.has_key(rs):
                ov = other.rsLabels[rs]
                if not otherLabelAxes.has_key(ov):
                    otherLabelAxes[ov] = mixedAxis()
                otherLabelAxes[ov].add(rs,v)
            else:
                scatter.add(rs,v,other.rsValues.get(rs,None))
        
        for rs,v in self.rsLabels.iteritems():
            if other.rsLabels.has_key(rs):
                ov = other.rsLabels[rs]
                if not otherLabelAxes.has_key(ov):
                    otherLabelAxes[ov] = mixedAxis()
                otherLabelAxes[ov].add(rs,v)
                if not myLabelAxes.has_key(v):
                    myLabelAxes[v] = mixedAxis()
                myLabelAxes[v].add(rs,ov)
            else:
                ov = other.rsValues.get(rs,None)
                if not myLabelAxes.has_key(v):
                    myLabelAxes[v] = mixedAxis()
                myLabelAxes[v].add(rs,ov)
        
        for a in myLabelAxes.itervalues():
            a.finish()
        for a in otherLabelAxes.itervalues():
            a.finish()
        
        return (scatter,myLabelAxes,otherLabelAxes)
        

class variantData:
    def __init__(self):
        self.data = {}  # {rsNumber : variant object}
        self.axes = None
        
        self.scatter = None # current scatterplot of intersection of all numerical data
        self.scatterXs = None   # current 1d scatterplots for all non-numerical labels on the x axis
        self.scatterYs = None   # current 1d scatterplots for all non-numerical labels on the y axis
        
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
    
    def freeze(self, startingXaxis=None, startingYaxis=None):
        '''
        Builds query axes; prevents from loading more data. This is the longest process in the whole program - do this as little as possible (aka ONCE!)
        '''
        if self.isFrozen:
            return
        self.isFrozen = True
        print "...Freezing",
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
        
        for a in self.axes.itervalues():
            print ".",
            a.finish()
        print ""
        self.setScatterAxes(startingXaxis, startingYaxis)
    
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
    
    def setScatterAxes(self, attribute1, attribute2):
        '''
        Builds a FourTree for drawing the scatterplot - maybe could be sped up by some kind of sorting...
        '''
        print "...Setting scatter axes"
        if not self.isFrozen:
            self.freeze(attribute1,attribute2)
            return
        
        if not self.axes.has_key(attribute1):
            raise ValueError("Attempted to set non-existent axis to scatterplot: %s" % attribute1)
        
        if not self.axes.has_key(attribute2):
            raise ValueError("Attempted to set non-existent axis to scatterplot: %s" % attribute2)
        
        self.currentXattribute = attribute1
        self.currentYattribute = attribute2
        
        self.scatter,self.scatterXs,self.scatterYs = self.axes[attribute1].crossSection(self.axes[attribute2])
        
    def getData(self, rsNumbers, att):
        return self.axes[att].getValues(rsNumbers)
    
    def getDatum(self, rsNumber, att):
        return self.axes[att].getValue(rsNumber)
    
    def get2dData(self, rsNumbers, att1, att2):
        rsNumbers = list(rsNumbers) # ensure the order is the same
        return zip(self.axes[att1].getValues(rsNumbers),self.axes[att2].getValues(rsNumbers))
    
    def get2dDatum(self, rsNumber, att1, att2):
        return (self.axes[att1].getValue(rsNumber),self.axes[att2].getValue(rsNumber))

        