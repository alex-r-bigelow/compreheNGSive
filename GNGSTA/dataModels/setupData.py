from dataModels.variantData import variantData
from dataModels.featureData import featureData
from resources.utils import vcfFile,csvVariantFile,bedFile,gff3File
from PySide.QtCore import *
import os

class individual:
    def __init__(self, name):
        self.name = name
        self.originalText = name
        self.groups = set()
        self.hasDuplicateText = False
    
    def addToGroup(self, g, native=False):
        self.groups.add(g)
        success = False
        if native:
            if not g.nativeMembers.has_key(self):
                g.nativeMembers[self] = True
                success = True
        elif not g.nativeMembers.has_key(self) and not g.foreignMembers.has_key(self):
            g.foreignMembers[self] = True
            success = True
        
        if success and g.expanded == None:
            g.expanded = False
    
    def removeFromGroup(self, g):
        if g.foreignMembers.has_key(self):
            del g[self]
            if len(g.foreignMembers) == 0 and len(g.nativeMembers) == 0:
                g.expanded = None

class group:
    def __init__(self, name, userDefined=False, checked=False):
        self.name = name
        self.userDefined = userDefined
        
        self.nativeMembers = {}
        self.foreignMembers = {}
        self.includeGroups = set()
        
        self.expanded = None
        self.checked = checked
        self.alleleBasisGroup = None
        self.fallback = "ALT"
    
    def isChecked(self):
        if len(self.nativeMembers) == 0 and len(self.foreignMembers) == 0:
            return self.checked
        hasFalse = None
        hasTrue = None
        for i in self.nativeMembers.itervalues():
            if i:
                if hasTrue == None:
                    hasTrue = True
                elif hasFalse == True:
                    return None # None indicates that some are checked but others aren't
            else:
                if hasFalse == None:
                    hasFalse = True
                elif hasTrue == True:
                    return None
        for i in self.foreignMembers.itervalues():
            if i:
                if hasTrue == None:
                    hasTrue = True
                elif hasFalse == True:
                    return None # None indicates that some are checked but others aren't
            else:
                if hasFalse == None:
                    hasFalse = True
                elif hasTrue == True:
                    return None
        # If we've gotten this far, there are only two possibilities - they're all true, or all false
        if hasFalse:
            return False
        else:
            return True
    
    def check(self, on=True):
        self.checked = on
        for i in self.nativeMembers.iterkeys():
            self.nativeMembers[i] = on
        for i in self.foreignMembers.iterkeys():
            self.foreignMembers[i] = on
    
    def includeGroup(self, g):
        if self.userDefined:
            self.includeGroups.add(g)
            for i in g.nativeMembers.iterkeys():
                i.addToGroup(self)
            for i in g.foreignMembers.iterkeys():
                i.addToGroup(self)
    
    def removeMembership(self, g):
        if self.userDefined:
            self.groupMemberships.discard(g)
            for i in g.nativeMembers.iterkeys():
                i.removeFromGroup(self)
            for i in g.foreignMembers.iterkeys():
                i.removeFromGroup(self)
    
    def getCheckedIndividualNames(self):
        results = []
        for i,include in self.nativeMembers.iteritems():
            if include:
                results.append(i)
        for i,include in self.foreignMembers.iteritems():
            if include:
                results.append(i)
        return results

class fileObj:
    def __init__(self, path, nameAppend):
        self.path = path
        self.name = os.path.split(path)[1] + nameAppend
        self.format = os.path.splitext(path)[1]
        
        self.checked = True
        self.expanded = False
        self.attributes = {}            # {attribute str:checked bool}
        for a in self.extractHeaders():
            self.attributes[a] = True
        if len(self.attributes) == 0:
            self.expanded = None
        
        self.individuals = set(self.extractIndividuals())
        if len(self.individuals) == 0:
            self.hasGenotypes = False
        else:
            self.hasGenotypes = True
    
    def extractHeaders(self):
        inFile = open(self.path)
        if self.format == '.vcf':
            results = vcfFile.extractVariantAttributesInFile(inFile)
        elif self.format == '.gvf':
            raise NotImplementedError('gvf not implemented yet')
            results = []
        elif self.format == '.csv':
            results = csvVariantFile.extractVariantAttributesInFile(inFile)
        elif self.format == '.tsv':
            results = csvVariantFile.extractVariantAttributesInFile(inFile,'\t',"Chromosome","Position",refHeader="rsNumber")
        elif self.format == '.bed':
            raise NotImplementedError('bed not implemented yet')
            results = []
        elif self.format == '.gff3':
            raise NotImplementedError('gff3 not implemented yet')
            results = []
        inFile.close()
        return results
            
    
    def extractIndividuals(self):
        inFile = open(self.path)
        if self.format == '.vcf':
            results = vcfFile.extractIndividualsInFile(inFile)
        elif self.format == '.gvf':
            raise NotImplementedError('gvf not implemented yet')
            results = []
        else:
            results = []
        inFile.close()
        return results
        
    def load(self, vData, fData):
        inFile = open(self.path,'r')
        if self.format == '.vcf':
            vcfFile.parseVcfFile(inFile,functionToCall=self.addVariant,callbackArgs={'vData':vData},individualsToExclude=[],individualsToInclude=[],mask=None,returnFileObject=False,skipFiltered=False,skipVariantAttributes=False,skipGenotypes=False,skipGenotypeAttributes=True,includeAdditionalHeaderInfo=False,forceAlleleMatching=True)
        elif self.format == '.gvf':
            raise NotImplementedError('gvf not implemented yet')
        elif self.format == '.csv':
            csvVariantFile.parseCsvVariantFile(inFile,"Chromosome","Position",refHeader="rsNumber",functionToCall=self.addVariant,callbackArgs={'vData':vData},returnFileObject=False)
        elif self.format == '.tsv':
            csvVariantFile.parseCsvVariantFile(inFile,"Chromosome","Position",refHeader="rsNumber",functionToCall=self.addVariant,callbackArgs={'vData':vData},returnFileObject=False,delimiter='\t')
        elif self.format == '.bed':
            raise NotImplementedError('bed not implemented yet')
        elif self.format == '.gff3':
            raise NotImplementedError('gff3 not implemented yet')
        inFile.close()
    
    def addVariant(self, variantObject, vData):
        for att,include in self.attributes.iteritems():
            if variantObject.attributes.has_key(att):
                if include:
                    variantObject.attributes[att + " (" + self.name + ")"] = variantObject.attributes[att]
                del variantObject.attributes[att]
        vData.addVariant(variantObject)
    
    def isChecked(self):
        if len(self.attributes) == 0:
            return self.checked
        hasFalse = None
        hasTrue = None
        for i in self.attributes.itervalues():
            if i:
                if hasTrue == None:
                    hasTrue = True
                elif hasFalse == True:
                    return None # None indicates that some are checked but others aren't
            else:
                if hasFalse == None:
                    hasFalse = True
                elif hasTrue == True:
                    return None
        # If we've gotten this far, there are only two possibilities - they're all true, or all false
        if hasFalse:
            return False
        else:
            return True
    
    def check(self, on=True):
        self.checked = on
        for a in self.attributes.iterkeys():
            self.attributes[a] = on
        
class svOptionsModel:
    def __init__(self):
        self.individuals = {}   # {individual name : individual}
        self.groups = {}        # {group name : group}
        self.groupOrder = []    # group name
        self.files = {}         # {file name : fileObj}
        self.fileOrder = []     # file name
    
    def buildDataObjects(self, progressWidget):
        progressWidget.reset()
        progressWidget.setMinimum(0)
        progressWidget.setMaximum(len(self.files) + len(self.groups))
        progressWidget.show()
        index = 0
        
        vData = variantData()
        fData = featureData()
        
        progressWidget.setLabelText('Loading Files')
        for fName,fObj in self.files.iteritems():
            fObj.load(vData,fData)
            for att,checked in fObj.attributes.iteritems():
                if not checked:
                    vData.discardAttribute(att)
            
            if progressWidget.wasCanceled():
                return None
            index += 1
            progressWidget.setValue(index)
        
        progressWidget.setLabelText('Recalculating Allele Frequencies')
        for gName,gObj in self.groups.iteritems():
            individuals = gObj.getCheckedIndividualNames()
            if gObj.alleleBasisGroup == None:
                basisGroup = []
            else:
                basisGroup = gObj.alleleBasisGroup.getCheckedIndividualNames()
            vData.recalculateAlleleFrequencies(individuals, gName, basisGroup, gObj.fallback)
            
            if progressWidget.wasCanceled():
                return None
            index += 1
            progressWidget.setValue(index)
        
        return (vData,fData)
    
    def addFile(self, path):
        fileNameChunk = os.path.split(path)[1]
        nameAppend = ""
        i = 1
        while self.files.has_key(fileNameChunk + nameAppend):
            i += 1
            nameAppend = " (%i)" % i
        newFile = fileObj(path, nameAppend)
        self.files[newFile.name] = newFile
        self.fileOrder.insert(0,newFile.name)
        
        if newFile.hasGenotypes:
            newGroup = group(newFile.name, userDefined=False, checked=False)
            hadDuplicate = False
            if self.groups.has_key(newGroup.name):
                # kick out an existing group if it has my name...
                while self.groups.has_key(fileNameChunk + nameAppend):
                    i += 1
                    nameAppend = " (%i)" % i
                # update that group's native individual screen names
                hadDuplicate = True
                for i in self.groups[newGroup.name].nativeMembers:
                    del self.individuals[i.name]
                    i.name = i.originalText + " (" + fileNameChunk + nameAppend + ")"
                    i.hasDuplicateText = True
                    self.individuals[i.name] = i
                # move that group
                self.groups[fileNameChunk + nameAppend] = self.groups[newGroup.name]
            # Create all individuals in the file, and add them as native members
            for i in newFile.individuals:
                newIndividual = individual(i)
                if hadDuplicate:
                    newIndividual.name += newIndividual.originalText + " (" + newGroup.name + ")"
                    newIndividual.hasDuplicateText = True
                newIndividual.addToGroup(newGroup, native=True)
                self.individuals[newIndividual.name] = newIndividual
            
            # Finally add it to our groups
            self.groups[newGroup.name] = newGroup
            self.groupOrder.insert(0,newGroup.name)
    
    def hasGroup(self, text):
        return text in self.groupOrder
    
    def addGroup(self, text):
        self.groups[text] = group(text, userDefined=True, checked=True)
        self.groupOrder.insert(0,text)
        
    def removeGroup(self, text):
        for i in self.groups[text].nativeMembers.iterkeys():
            del self.individuals[i]
        self.groupOrder.remove(text)
        del self.groups[text]




