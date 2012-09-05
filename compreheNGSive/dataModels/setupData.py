from dataModels.variantData import variantData
from dataModels.featureData import featureData
from resources.genomeUtils import variantFile   #,csvVariantFile,bedFile,gff3File
from pyquery import PyQuery
import os, sys

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
    
    def getCheckedIndividuals(self):
        results = []
        for i,include in self.nativeMembers.iteritems():
            if include:
                results.append(i)
        for i,include in self.foreignMembers.iteritems():
            if include:
                results.append(i)
        return results

class fileObj:
    def __init__(self, path, name):
        self.path = path
        self.name = name
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
        inFile = self.path
        if self.format == '.vcf':
            results = variantFile.extractVcfFileInfo(inFile)
        elif self.format == '.gvf':
            raise NotImplementedError('gvf not implemented yet')
            results = []
        elif self.format == '.csv':
            raise NotImplementedError('csv not implemented yet')
            results = []
        elif self.format == '.tsv':
            raise NotImplementedError('tsv not implemented yet')
            results = []
        elif self.format == '.bed':
            raise NotImplementedError('bed not implemented yet')
            results = []
        elif self.format == '.gff3':
            raise NotImplementedError('gff3 not implemented yet')
            results = []
        inFile.close()
        return results
        
    def load(self, vData, fData):
        raise NotImplementedError('todo...')
        '''
        inFile = open(self.path,'r')
        if self.format == '.vcf':
            variantFile.parseVcfFile(inFile,functionToCall=self.addVariant,callbackArgs={'vData':vData},individualsToExclude=[],individualsToInclude=[],mask=None,returnFileObject=False,skipFiltered=False,skipVariantAttributes=False,skipGenotypes=False,skipGenotypeAttributes=True,includeAdditionalHeaderInfo=False,forceAlleleMatching=True)
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
        '''
    
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

class prefilterObj:
    def __init__(self, direction, percent, excludeMissing):
        self.direction = direction
        self.percent = percent
        self.excludeMissing = excludeMissing

class svOptionsModel:
    def __init__(self, fromFile=None):
        self.individuals = {}   # {file name:{individual name : individual}}
        self.groups = {}        # {group name : group}
        self.groupOrder = []    # group name
        self.files = {}         # {file name : fileObj}
        self.fileOrder = []     # file name
        
        self.startingXattribute = None
        self.startingYattribute = None
        self.prefilters = {}    # attribute name : 'top5', 'bottom5'
        self.alleleMode = '.vcf'
        
        if fromFile != None:
            self.buildFromFile(fromFile)
    
    def buildFromFile(self, path):
        queryObj = PyQuery(filename=path)
        for fobj in queryObj('file'):
            newName = self.addFile(fobj.attrib['path'], fobj.attrib.get('id',None))
            self.files[newName].check(on=False)
            for c in fobj.iterchildren():
                if c.tag == 'attribute':
                    self.files[newName].attributes[c.text] = True
            
        for gobj in queryObj('group'):
            if self.hasGroup(gobj.attrib['id']):
                self.groups[gobj.attrib['id']].check(True)  # include the existing group
            else:
                self.addGroup(gobj.attrib['id'])
                for c in gobj.iterchildren():
                    if c.tag == 'sample':
                        self.individuals[c.attrib['file']][c.text].addToGroup(self.groups[gobj.attrib['id']])
        
        prefs = queryObj('prefs')[0]
        self.startingXattribute = prefs.attrib.get('xaxis',None)
        if self.startingXattribute in self.groups.iterkeys():
            self.startingXattribute = "%s AF" % self.startingXattribute
        self.startingYattribute = prefs.attrib.get('yaxis',None)
        if self.startingYattribute in self.groups.iterkeys():
            self.startingYattribute = "%s AF" % self.startingYattribute
        self.alleleMode = prefs.attrib.get('alleleMode','.vcf')
                
        for pObj in prefs.iterchildren():
            if pObj.tag == 'prefilter':
                att = pObj.attrib['axis']
                if att in self.groups.iterkeys():
                    att = "%s AF" % att
                self.prefilters[att] = prefilterObj(pObj.attrib['direction'],float(pObj.attrib['percent'])/100.0,pObj.attrib['excludeMissing'].strip().lower() == "true")
    
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
        if self.alleleMode == ".vcf":
            basisGroup = None
        else:
            basisGroup = self.groups[self.alleleMode].getCheckedIndividuals()
        for gName,gObj in self.groups.iteritems():
            if gObj.isChecked() == True:
                individuals = gObj.getCheckedIndividuals()
                vData.recalculateAlleleFrequencies(individuals, gName, basisGroup)
            
            if progressWidget.wasCanceled():
                return None
            index += 1
            progressWidget.setValue(index)
                
        return (vData,fData)
    
    def addFile(self, path, name=None):
        if name == None:
            fileNameChunk = os.path.split(path)[1]
            nameAppend = ""
            i = 1
            while self.files.has_key(fileNameChunk + nameAppend):
                i += 1
                nameAppend = " (%i)" % i
            name = fileNameChunk + nameAppend
        newFile = fileObj(path, name)
        self.files[newFile.name] = newFile
        self.fileOrder.insert(0,newFile.name)
        
        if newFile.hasGenotypes:
            newGroup = group(newFile.name, userDefined=False, checked=False)
            if self.groups.has_key(newGroup.name):
                print "ERROR: Duplicate group"
                sys.exit(1)
            
            # Create all individuals in the file, and add them as native members
            self.individuals[newFile.name] = {}
            for i in newFile.individuals:
                newIndividual = individual(i)
                newIndividual.addToGroup(newGroup, native=True)
                self.individuals[newFile.name][newIndividual.name] = newIndividual
            
            # Finally add it to our groups
            self.groups[newGroup.name] = newGroup
            self.groupOrder.insert(0,newGroup.name)
            
            # don't include the file-based groups by default
            newGroup.check(on=False)
        return newFile.name
    
    def hasGroup(self, text):
        return text in self.groupOrder
    
    def addGroup(self, text):
        self.groups[text] = group(text, userDefined=True, checked=True)
        self.groupOrder.insert(0,text)
        
    def removeGroup(self, text):
        self.groupOrder.remove(text)
        del self.groups[text]




