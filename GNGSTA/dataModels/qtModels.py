from dataModels.variantData import variantData
from dataModels.featureData import featureData
from resources.utils import vcfFile,csvVariantFile,bedFile,gff3File
from PySide.QtCore import *
import os

class group:
    def __init__(self, name, editable=False, checked=False):
        self.name = name
        self.isEditable = editable
        self.nativeMembers = set()      # set(individual)
        self.localMembers = set()       # set(individual)
        self.includeGroups = set()      # set(group)
        self.alleleBasisGroup = None    # group
        self.fallback="ALT"             # REF, ALT, ALT_n, or None
        if checked:
            self.included = Qt.Checked
        else:
            self.included = Qt.Unchecked    # can also be Qt.PartiallyChecked
    
    def canAddGroup(self, g):
        if g in self.includeGroups:
            return False
        else:
            for myG in self.includeGroups:
                if not myG.canAddGroup(g):
                    return False
            return True
    
    def addGroup(self, g):
        if self.canAddGroup(g):
            self.includeGroups.add(g)
    
    def getIndividuals(self):
        results = set()
        results.update(self.nativeMembers)
        results.update(self.localMembers)
        for myG in self.includeGroups:
            results.update(myG.getIndividuals())
        return results

class fileObj:
    def __init__(self, path, nameAppend, vData, fData):
        self.path = path
        self.name = os.path.split(path)[1] + nameAppend
        self.format = os.path.splitext(path)[1]
        self.attributes = {}            # {attribute str:included bool}
        self.checkable = True
        self.hasGenotypes = False
        self.individuals = set()
        
        inFile = open(path,'r')
        if self.format == '.vcf':
            vcfFile.parseVcfFile(inFile,functionToCall=self.addVariant,callbackArgs={'vData':vData},individualsToExclude=[],individualsToInclude=[],mask=None,returnFileObject=False,skipFiltered=False,skipVariantAttributes=False,skipGenotypes=False,skipGenotypeAttributes=True,includeAdditionalHeaderInfo=False,forceAlleleMatching=True)
            self.hasGenotypes = True
        elif self.format == '.gvf':
            print 'gvf not implemented yet'
            # TODO: gvf
            self.hasGenotypes = True
        elif self.format == '.csv' or ext == '.tsv':
            # TODO: auto-figure out delimiter, chromosome, position headers?
            csvVariantFile.parseCsvVariantFile(inFile,"Chromosome","Position",refHeader="rsNumber",altHeader=None,nameHeader=None,attemptRepairsWhenComparing=True,forceAlleleMatching=True,delimiter="\t",functionToCall=self.addVariant,callbackArgs={'vData':vData},mask=None,returnFileObject=False)
        elif self.format == '.bed':
            print 'bed not implemented yet'
            # TODO: BED
        elif self.format == '.gff3':
            print 'gff3 not implemented yet'
            # TODO: gff3
        inFile.close()
    
    def addVariant(self, variantObject, vData):
        vData.addVariant(variantObject)
        for a in variantObject.attributes.iterkeys():
            self.attributes[a] = True
        if len(self.attributes) == 0:
            self.checkable = False
        if self.hasGenotypes and len(self.individuals) == 0:
            for i in variantObject.genotypes.iterkeys():
                self.individuals.add(i)
    
    def isChecked(self):
        if not self.checkable:
            return False
        hasFalse = None
        hasTrue = None
        for i in self.attributes.itervalues():
            if i:
                if hasTrue == None:
                    hasTrue = True
                elif hasTrue == False:
                    return None # None indicates that some are checked but others aren't
            else:
                if hasFalse == None:
                    hasFalse = True
                elif hasFalse == False:
                    return None
        # If we've gotten this far, there are only two possibilities - they're all true, or all false
        if hasFalse:
            return False
        else:
            return True
    
    def checkAll(self, on=True):
        for a in self.attributes.iterkeys():
            self.attributes[a] = True
    
    def generateGroup(self):
        if not self.hasGenotypes:
            return None
        else:
            newGroup = group(self.name, editable=False, checked=False)
            newGroup.nativeMembers.update(self.individuals)
            # TODO: handle subgroups of special files like KGP
            return newGroup
        
class svOptionsModel:
    def __init__(self):
        self.vData = variantData()
        self.fData = featureData()
        
        self.groups = {}        # {group name : group}
        self.groupOrder = []    # group name
        self.files = {}         # {file name : fileObj}
        self.fileOrder = []     # file name
    
    def loadFile(self, path):
        nameAppend = ""
        i = 1
        while self.files.has_key(os.path.split(path)[1] + nameAppend):
            i += 1
            nameAppend = " (%i)" % i
        newFile = fileObj(path, nameAppend, self.vData, self.fData)
        self.files[newFile.name] = newFile
        self.fileOrder.insert(0,newFile.name)
        
        if newFile.hasGenotypes:
            self.groups[newFile.name] = newFile.generateGroup()
            self.groupOrder.insert(0,newFile.name)
    
    def hasGroup(self, text):
        return text in self.groupOrder
    
    def addGroup(self, text):
        self.groups[text] = group(text, editable=True, checked=True)
        self.groupOrder.insert(0,text)
    
    def editGroup(self, oldText, text):
        self.groupOrder[self.groupOrder.index(oldText)] = text
        self.groups[text] = self.groups[oldText]
        del self.groups[oldText]
    
    def removeGroup(self, text):
        self.groupOrder.remove(text)
        del self.groups[text]