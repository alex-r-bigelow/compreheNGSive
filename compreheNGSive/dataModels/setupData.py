import os
from lxml import etree
from resources.genomeUtils import genomeUtils, variantLoadingParameters, variantFile, featureFile, valueFilter, parseException
from dataModels.variantData import variantData
from dataModels.featureData import featureData

class prefs:
    def __init__(self, startingXsource, startingYsource, startingXaxis, startingYaxis, files={}, groups={}, statistics={}):
        self.startingXsource = startingXsource
        self.startingYsource = startingYsource
        self.startingXaxis = startingXaxis
        self.startingYaxis = startingYaxis
        self.files=files
        self.groups=groups
        self.statistics = statistics
        
        self.loadingEstimates={}
        self.loadingPercentages={}
        total = 0.0
        numGenotypedLines = 0
        self.maxTicks = 200.0 # boosting this number will make the progress widget more responsive while loading files
        for fileID,f in self.files.iteritems():
            numLines = max(f.fileAttributes.get('number of lines',1000),1)
            total += numLines
            if f.format == '.vcf':
                numGenotypedLines = max(numGenotypedLines,numLines)
            self.loadingEstimates[fileID] = numLines
        for fileID,f in self.files.iteritems():
            self.loadingPercentages[fileID] = (100.0*total)/(self.maxTicks*self.loadingEstimates[fileID])
        groupTicks = 50.0 # boosting this number will make the progress widget more responsive while calculating group statistics
        self.maxTicks += groupTicks
        self.loadingPercentages[None] = numGenotypedLines/groupTicks    # this one is just number of lines per tick, not percentage of total ticks...
    
    def loadDataObjects(self, callback=None):
        # Try to parse files in order by format (some files are more informative than others,
        # and we want to start off with the best information) ... this may get shaken up
        # when we support masking/specific loci
        gff3Files = []
        bedFiles = []
        
        vcfFiles = []
        csvFiles = []
        axisLabels = set()
        individualsToInclude = self.getAllSamples()
        
        for fileID,f in self.files.iteritems():
            if f.format == '.vcf':
                vcfFiles.append(fileID)
                axisLabels.update(f.hardFilters.iterkeys())
            elif f.format == '.csv':
                csvFiles.append(fileID)
                axisLabels.update(f.hardFilters.iterkeys())
            elif f.format == '.gff3':
                gff3Files.append(fileID)
            elif f.format == '.bed':
                bedFiles.append(fileID)
        
        vData = variantData(axisLabels)
        fData = featureData()
        
        for fileID in gff3Files:
            pass
        for fileID in bedFiles:
            pass
        for fileID in vcfFiles:
            if callback != None:
                callback(numTicks=0,message='Loading %s' % fileID)
            parameters = variantLoadingParameters(build=self.files[fileID].build,
                                                passFunction=vData.addVariant,
                                                rejectFunction=None,
                                                callbackArgs={},
                                                tickFunction=callback,
                                                tickInterval=self.loadingPercentages[fileID],
                                                individualsToInclude=individualsToInclude,
                                                individualAppendString=" (%s)" % fileID,
                                                lociToInclude=None, # TODO: support masking and specfic loci
                                                mask=None,
                                                attributesToInclude=self.files[fileID].hardFilters,
                                                attributeAppendString=" (%s)" % fileID,
                                                skipGenotypeAttributes=True)
            if variantFile.parseVcfFile(self.files[fileID].path, parameters) == "ABORTED":
                return (None,None)
        
        for fileID in csvFiles:
            if callback != None:
                callback(numTicks=0,message='Loading %s' % fileID)
            parameters = variantLoadingParameters(build=self.files[fileID].build,
                                                passFunction=vData.addVariant,
                                                rejectFunction=None,
                                                callbackArgs={},
                                                tickFunction=callback,
                                                tickInterval=self.loadingPercentages[fileID],
                                                individualsToInclude=[],    # .csv files don't have genotypes
                                                individualAppendString="",
                                                lociToInclude=None, # TODO: support masking and specfic loci
                                                mask=None,
                                                attributesToInclude=self.files[fileID].hardFilters,
                                                attributeAppendString=" (%s)" % fileID,
                                                skipGenotypeAttributes=True)
            if variantFile.parseCsvFile(self.files[fileID].path, parameters) == "ABORTED":
                return (None,None)
        
        # Now that we've loaded the files, do our group calculations
        callback(numTicks=0,message='Calculating group statistics')
        vData.performGroupCalculations(self.groups, self.statistics, callback, self.loadingPercentages[None])
        
        return (vData,fData)
    
    def getSoftFilters(self):
        filters = {}    # att:[softfilter,...]
        for f in self.files.itervalues():
            for a in f.attributes:
                filters[a.attributeID] = a.softFilter
        for s in self.statistics.itervalues():
            filters[s.statisticID] = s.softFilter
        return filters
    
    def getAllSamples(self):
        results = []
        for g in self.groups.itervalues():
            for s in g.samples:
                results.append(s)
        return results
    
    @staticmethod
    def generateFromText(text):
        root = etree.fromstring(text)
        try:
            groupReferences=set()
            
            # handle globals
            xNode = root.find('startingXaxis')
            startingXsource = xNode.attrib.get('source',None)
            if startingXsource != None:
                startingXaxis = "%s (%s)" % (xNode.attrib['attribute'],startingXsource)
            else:
                startingXaxis = xNode.attrib['statistic']
            
            yNode = root.find('startingYaxis')
            startingYsource = yNode.attrib.get('source',None)
            if startingYsource != None:
                startingYaxis = "%s (%s)" % (yNode.attrib['attribute'],startingYsource)
            else:
                startingYaxis = yNode.attrib['statistic']
            
            # handle statistics
            statistics = {}
            for s in root.findall('statistic'):
                assert not statistics.has_key(s.attrib['id'])
                parameters = {}
                for k,v in s.attrib.iteritems():
                    if k != 'id' and k != 'type':
                        parameters[k] = v
                statObj = statistic(s.attrib['id'],s.attrib['type'],hardFilter.generateFromParent(s),softFilter.generateFromParent(s),parameters)
                statistics[s.attrib['id']] = statObj
                groupReferences.update(statObj.getExternalReferences())
            
            # handle groups
            groups = {}
            for g in root.findall('group'):
                assert not groups.has_key(g.attrib['id'])
                groupReferences.discard(g.attrib['id'])
                samples = groupObject.generateSampleStrings(g)
                groups[g.attrib['id']] = groupObject(g.attrib['id'],samples)
            
            # handle files
            files = {}
            for f in root.findall('file'):
                path = f.attrib['path']
                if not f.attrib.has_key('id'):
                    f.set('id',os.path.split(path)[1])
                fileID = f.attrib.get('id',os.path.split(path)[1])
                assert not files.has_key(fileID)
                if f.attrib['build'].strip().lower() == 'hg19':
                    build = genomeUtils.hg19
                elif f.attrib['build'].strip().lower() == 'hg18':
                    build = genomeUtils.hg18
                else:
                    raise parseException('Unsupported build: %s' % f.attrib['build'])
                attributes = attribute.generateFromParent(f)
                files[fileID] = fileObject(fileID,path,build,attributes)
            
            # generate any missing groups from files
            for fileID in groupReferences:
                assert not groups.has_key(fileID)
                groups[fileID] = files[fileID].makeGroup()
            
            # handle required stuff
            prefsObj = prefs(startingXsource,startingYsource,startingXaxis,startingYaxis,files,groups,statistics)
            return prefsObj
        except (AssertionError, AttributeError, KeyError, ValueError):
            raise parseException('Bad Prefs string')

class fileObject:
    def __init__(self, fileID, path, build, attributes=[]):
        self.fileID=fileID
        self.path=path
        self.format=os.path.splitext(path)[1].lower()
        if self.format == ".vcf":
            self.fileAttributes = variantFile.extractVcfFileInfo(path)
        elif self.format == ".csv":
            self.fileAttributes = variantFile.extractCsvFileInfo(path)
        elif self.format == ".bed":
            raise Exception('bed not supported yet')
            #self.fileAttributes = featureFile.extractBedFileInfo(path)
        elif self.format == ".gff3":
            raise Exception('gff3 not supported yet')
        else:
            raise Exception("%s format not supported" % self.format)
        self.build=build
        self.attributes=attributes
        self.hardFilters = {}
        for a in self.attributes:
            self.hardFilters[a.attributeID] = a.hardFilter
    
    def makeGroup(self):
        samples = []
        for i in self.fileAttributes["INDIVIDUALS"]:
            samples.append("%s (%s)"%(i,self.fileID))
        return groupObject(self.fileID,samples)

class attribute:
    def __init__(self, attributeID, forceCategorical=None, hardFilter=None, softFilter=None):
        self.attributeID=attributeID
        self.forceCategorical=forceCategorical
        self.hardFilter=hardFilter
        self.softFilter=softFilter
    
    @staticmethod
    def generateFromParent(node):
        results = []
        for r in node.findall('attribute'):
            attributeID = "%s (%s)" % (r.attrib['id'],node.attrib['id'])
            forceCategorical = True if r.attrib.get('forceCategorical','false') == 'true' else False
            softfilter=softFilter.generateFromParent(r)
            hardfilter=hardFilter.generateFromParent(r)
            results.append(attribute(attributeID,forceCategorical,hardfilter,softfilter))
        return results

class groupObject:
    def __init__(self, groupID, samples=[]):
        self.groupID=groupID
        self.samples=samples
    
    @staticmethod
    def generateSampleStrings(node):
        results = []
        for s in node.findall('sample'):
            sampleID = "%s (%s)" % (s.attrib['id'],s.attrib['file'])
            results.append(sampleID)
        return results

class statistic:
    ALLELE_FREQUENCY = 0
    def __init__(self, statisticID, statisticType,hardfilter=None,softfilter=None,parameters={}):
        self.statisticID = statisticID
        if statisticType.strip().lower() == 'allele frequency':
            self.statisticType = statistic.ALLELE_FREQUENCY
        else:
            raise Exception('Unsupported statistic: %s' % statisticType)
        self.hardFilter = hardfilter
        self.softFilter = softfilter
        self.parameters = parameters
        
        # statistic-specific stuff
        if self.statisticType == statistic.ALLELE_FREQUENCY:
            alleleMode = self.parameters['alleleMode'].strip().lower()
            if alleleMode.startswith('vcf'):
                self.parameters['alleleMode'] = int(alleleMode[3:])
                self.parameters['vcf override'] = True
            else:
                assert self.parameters.has_key('alleleGroup')
                if alleleMode == 'leastfrequent':
                    self.parameters['alleleMode'] = -1
                elif alleleMode == 'mostfrequent':
                    self.parameters['alleleMode'] = 1
                else:
                    self.parameters['alleleMode'] = int(alleleMode)
                self.parameters['vcf override'] = False
    
    def getExternalReferences(self):
        if self.statisticType == 'allele frequency':
            result = set([self.parameters['group']])
            if self.parameters.has_key('alleleGroup'):
                assert self.parameters['alleleGroup'] != 'vcf override'
                result.add(self.parameters['alleleGroup'])
            return result
        else:
            return []

class softFilter:
    def __init__(self, excludeMissing=True, excludeMasked=True, values=[], percentages=[]):
        self.excludeMissing=excludeMissing
        self.excludeMasked=excludeMasked
        self.values=values
        self.percentages=percentages
    
    @staticmethod
    def generateFromParent(node):
        f = node.find('softFilter')
        if f == None:
            return softFilter(excludeMissing=False,excludeMasked=False,values=None,percentages=None)
        else:
            excludeMissing = False if f.attrib.get('excludeMissing','true') == 'false' else True
            excludeMasked = False if f.attrib.get('excludeMasked','true') == 'false' else True
            values=[]
            for v in f.findall('value'):
                values.append(v.attrib['text'])
            percentages=[]
            for p in f.findall('percentage'):
                value = float(p.attrib['percent'])
                assert value > 0 and value < 100
                if p.attrib['direction'] == 'bottom':
                    value = -value
                percentages.append(0.01*value)
            return softFilter(excludeMissing,excludeMasked,values,percentages)

class hardFilter(valueFilter):
    @staticmethod
    def generateFromParent(node):
        f = node.find('hardFilter')
        if f == None:
            return hardFilter(values=None, ranges=None, includeNone=True, includeInf=True, includeNaN=True, listMode=valueFilter.LIST_MUTILATE)
        else:
            excludeMissing = False if f.attrib.get('excludeMissing','true') == 'false' else True
            excludeMasked = False if f.attrib.get('excludeMasked','true') == 'false' else True
            values=[]
            for v in f.findall('value'):
                values.append(v.attrib['text'])
            if len(values) == 0:
                values = None   # include everything
            ranges=[]
            for r in f.findall('range'):
                ranges.append((float(r.attrib['low']),float(r.attrib['high'])))
            if len(ranges) == 0:
                ranges = None   # include everything
            return hardFilter(values=values, ranges=ranges, includeNone=not excludeMissing, includeInf=not excludeMissing, includeNaN=not excludeMasked, listMode=valueFilter.LIST_MUTILATE)

