from resources.utils import chrLengths, chrOffsets
from resources.structures import recursiveDict, TwoTree, FourTree
import operator

class numberAxis:
    def __init__(self):
        self.tree = None
        self.rsValuePairs = []
        self.rsValues = {}
    
    def add(self, id, value):
        if self.tree != None:
            self.tree = None
        self.rsValuePairs.append((id,value))
        self.rsValues[id] = value

    def finish(self):
        self.rsValuePairs.sort(key=lambda i: i[1])
        self.tree = TwoTree(self.rsValuePairs)
    
    def select(self, low, high, includeMissing=False, includeMasked=False):
        if self.tree == None:
            print "ERROR: Attempted to query unfinished axis"
            sys.exit(1)
        
        return self.tree.select(low,high,includeMasked=includeMasked,includeUndefined=includeMissing,includeMissing=includeMissing)
    
    def getLabels(self, values):
        results = []
        for v in values:
            results.append("%.4f" % v)
        return results
    
    def getValues(self, rsNumbers):
        results = []
        for rs in rsNumbers:
            results.append(self.rsValues.get(rs,None))
        return results
    
    def getMin(self):
        return self.tree.root.low
    
    def getMax(self):
        return self.tree.root.high
    
    def getDataType(self):
        return "number"
    
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

class genomeAxis(numberAxis):
    def select(self, chromosome, low, high):
        return self.select(chrOffsets[chromosome]+low,chrOffsets[chromosome]+high)
    
    def getLabels(self, values):
        results = []
        for v in values:
            chr = "chr?"
            pos = -1
            lastPos = 0
            for c,p in chrOffsets:
                if v < p:
                    pos = value-lastPos
                    break
                chr = c
                lastPos = p
            if pos == -1:
                results.append("chr?:?")
            else:
                results.append("%s:%i" % (chr,pos))
        return results
    
    def getDataType(self):
        return "genome"

class stringAxis:
    def __init__(self):
        self.values = []
        self.rsToIndex = {}
        self.valueToIndex = {}  # just used for adding
        self.unsortedFrom = -1
        self.missingValues = set()
        
    def add(self, id, value):
        if value == None:
            self.missingValues.add(id)
        if not self.valueToIndex.has_key(value):
            index = len(self.values)
            self.valueToIndex[value] = index
            if self.unsortedFrom == -1:
                self.unsortedFrom = index
            self.values.append((value,set()))
        index = self.valueToIndex[value]
        self.rsToIndex[id] = index
        self.values[index][1].add(id)
    
    def finish(self):
        if self.unsortedFrom != -1:
            self.values[self.unsortedFrom:] = sorted(self.values[self.unsortedFrom:])
            self.fixIndices()
    
    def fixIndices(self, limit=None):
        if limit == None:
            limit = len(self.values)
        for i,valuePair in enumerate(self.values[self.unsortedFrom:limit]):
            value = valuePair[0]
            rsSet = valuePair[1]
            index = i + self.unsortedFrom
            self.valueToIndex[value] = index
            for rs in rsSet:
                self.rsToIndex[rs] = index
        self.unsortedFrom = -1
    
    def reorder(self, sourceIndex, endIndex):
        if sourceIndex < endIndex:
            temp = self.values[sourceIndex]
            index = sourceIndex
            while (index < endIndex):
                self.values[index] = self.values[index+1]
            self.values[endIndex] = temp
            self.unsortedFrom = sourceIndex
            self.fixIndices(endIndex+1)
        elif sourceIndex > endIndex:
            temp = self.values[sourceIndex]
            index = sourceIndex
            while (index > endIndex):
                self.values[index] = self.values[index-1]
            self.values[endIndex] = temp
            self.unsortedFrom = endIndex
            self.fixIndices(sourceIndex+1)

    def select(self, indices, includeMissing=False, includeMasked=False):
        if not self.unsortedFrom == -1:
            print "ERROR: Attempted to query unfinished axis"
            sys.exit(1)
        
        results = set()
        for i in indices:
            set.update(self.values[i][1])
        if includeMissing:  # ignore includeMasked
            set.update(self.missingValues)
        return results
    
    def getLabels(self, indices):
        if not self.unsortedFrom == -1:
            print "ERROR: Attempted to get labels from unfinished axis"
            sys.exit(1)
        
        results = []
        for i in indices:
            results.append(self.values[i][0])
        return results
    
    def getValues(self, rsNumbers):
        results = []
        for rs in rsNumbers:
            results.append(self.rsToIndex.get(rs,None))
        return results
    
    def getMin(self):
        return 0
    
    def getMax(self):
        return len(self.values)-1
    
    def hasMasked(self):
        return False    # impossible for strings
    
    def hasMissing(self):
        return len(self.missingValues) != 0
    
    def getDataType(self):
        return "string"

class variantData:
    def __init__(self):
        self.data = {}
        self.axes = None
        self.scatter = None
        self.currentXattribute = None
        self.currentYattribute = None
        
        self.attributeTypes = {}
        
        self.isFrozen = False
    
    def addVariant(self, variantObject):
        if self.isFrozen:
            self.thaw()
        
        if variantObject.attributes.has_key("Genome Position"):
            print "ERROR: \"Genome Position\" column header is reserved."
            sys.exit(1)
        
        for att,val in variantObject.attributes.iteritems():
            if val == "":
                variantObject.attributes[att] = None
            else:
                if not self.attributeTypes.has_key(att):
                    try:
                        dummy = int(val)
                        self.attributeTypes[att] = 1
                    except ValueError:
                        try:
                            dummy = float(val)
                            self.attributeTypes[att] = 2
                        except ValueError:
                            self.attributeTypes[att] = 3
                dataType = self.attributeTypes[att]
                if dataType == 1:
                    try:
                        variantObject.attributes[att] = int(val)
                    except ValueError:
                        variantObject.attributes[att] = float(val)  # it's possible to get an int first, and find out it's a float later. This doesn't really affect the TwoTree much, but it's good to know in advance
                        self.attributeTypes[att] = 2
                elif dataType == 2:
                    variantObject.attributes[att] = float(val)
                # else # already a string - don't do anything
        
        if self.data.has_key(variantObject.name):
            self.data[variantObject.name].repair(variantObject)
        else:
            self.data[variantObject.name] = variantObject
    
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
        self.axes = {"Genome Position":genomeAxis()}
        
        for att,type in self.attributeTypes.iteritems():
            if type == 1 or type == 2:
                self.axes[att] = numberAxis()
            else:
                self.axes[att] = stringAxis()
            
            if startingXaxis == None:
                startingXaxis = att
            elif startingYaxis == None:
                startingYaxis = att
        
        for v in self.data.itervalues():
            self.axes["Genome Position"].add(v.name,v.genomePosition)
            for att,val in v.attributes.iteritems():
                self.axes[att].add(v.name, val) # ints and floats have been converted already
        
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
        WARNING: this will need to be re-called every time someone reorders a string axis if the string axis is in the scatterplot
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
        
        xtype = 0
        ytype = 0
        if self.attributeTypes[attribute1] == 3:
            if attribute1 == "Genome Position":
                xtype = 2
            xtype = 1
        if self.attributeTypes[attribute1] == 3:
            if attribute1 == "Genome Position":
                ytype = 2
            ytype = 1
        
        self.scatter = FourTree()
        
        for rsNumber,v in self.data.iteritems():
            if xtype == 2:
                x = v.genomePosition
            else:
                x = v.attributes.get(attribute1,None)
                if xtype == 1:
                    x = self.axes[attribute1].valueToIndex[x]
            if ytype == 2:
                y = v.genomePosition
            else:
                y = v.attributes.get(attribute2,None)
                if ytype == 1:
                    y = self.axes[attribute2].valueToIndex[y]
            self.scatter.add(rsNumber,x,y)
    
    def getData(self, rsNumber, att):
        return self.data[rsNumber].attributes.get(att,None)
    
    def get2dData(self, rsNumber, att1, att2):
        return (self.data[rsNumber].attributes.get(att1,None),self.data[rsNumber].attributes.get(att2,None))

        