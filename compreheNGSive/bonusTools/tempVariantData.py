from resources.structures import countingDict
from resources.genomeUtils import variant, variantFile
from durus.file_storage import FileStorage
from durus.connection import Connection
from durus.persistent import Persistent
from copy import deepcopy
import math, sys, os

class cancelButtonException(Exception):
    pass

class tempVariantData:
    TICK_INTERVAL=10000
    COMMIT_FREQ=1000
    COMMIT=0
    def __init__(self, axisLabels, statisticLabels, forcedCategoricals, startingXattribute, startingYattribute):
        for fileToClear in ['Data.db','Data.db.lock','Data.db.tmp','Data.db.prepack']:
            if os.path.exists(fileToClear):
                os.remove(fileToClear)
        
        self.dataConnection = Connection(FileStorage("Data.db"))
        self.data = self.dataConnection.get_root()
        # possible key:value pairs (this is a little bizarre, but I can only have one database (as objects reference each other),
        # and for performance I want to keep all variant objects and axes on the root level:
        
        self.data['variant keys'] = set()
        
        self.axisLabels = axisLabels
        self.forcedCategoricals = forcedCategoricals
        self.statisticLabels = statisticLabels
        
        self.allAxes = self.defaultAxisOrder()
    
    def addVariant(self, variantObject):
        if variantObject.attributes.has_key('RSID'):
            variantObject.name = variantObject.attributes['RSID']
        if variantObject.name in self.data['variant keys']:
            self.data[variantObject.name].repair(variantObject)
        else:
            assert variantObject.name != 'variant keys'
            self.data['variant keys'].add(variantObject.name)
            self.data[variantObject.name] = variantObject
        
        tempVariantData.COMMIT += 1
        if tempVariantData.COMMIT >= tempVariantData.COMMIT_FREQ:
            tempVariantData.COMMIT = 0
            self.dataConnection.commit()
    
    def performGroupCalculations(self, groupDict, statisticDict, callback, tickInterval):
        from dataModels.setupData import statistic
        
        currentLine = 0
        nextTick = tickInterval
        
        targetAlleleGroups = {}
        for s in statisticDict.itervalues():
            if s.statisticType == statistic.ALLELE_FREQUENCY:
                if s.parameters.has_key('alleleGroup'):
                    index = s.parameters['alleleMode']
                    if index >= 1:
                        index -= 1  # they'll specify 1 as the most frequent, but we're in 0-based computer land; -1 is still the same though
                    targetAlleleGroups[s.parameters['alleleGroup']] = s.parameters['alleleMode']
                else:
                    targetAlleleGroups['vcf override'] = s.parameters['alleleMode']
        if len(targetAlleleGroups) == 0:    # nothing to calculate
            return
        
        for key in self.data['variant keys']:
            variantObject = self.data[key]
            currentLine += 1
            if currentLine >= nextTick:
                nextTick += tickInterval
                self.dataConnection.commit()
                if callback():  # abort?
                    return "ABORTED"
            
            if variantObject == None or variantObject.poisoned:
                continue
            
            # First find all the target alleles
            targetAlleles = {}
            for group,mode in targetAlleleGroups.iteritems():
                if group == 'vcf override':
                    alleles = variantObject.alleles
                else:
                    # First see if we can find a major allele with the people in basisGroup
                    alleleCounts = countingDict()
                    for i in groupDict[group].samples:
                        if variantObject.genotypes.has_key(i):
                            allele1 = variantObject.genotypes[i].allele1
                            allele2 = variantObject.genotypes[i].allele2
                            if allele1.text != None:
                                alleleCounts[allele1] += 1
                            if allele2.text != None:
                                alleleCounts[allele2] += 1
                    alleles = [x[0] for x in sorted(alleleCounts.iteritems(), key=lambda x: x[1])]
                
                if mode >= len(alleles) or mode < -len(alleles):
                    targetAlleles[group] = None
                else:
                    targetAlleles[group] = variantObject.alleles[mode]
            
            for statisticID,s in statisticDict.iteritems():
                targetAllele = targetAlleles[s.parameters.get('alleleGroup','vcf override')]
                if s.statisticType == statistic.ALLELE_FREQUENCY:
                    if targetAllele == None:
                        variantObject.setAttribute(statisticID,variant.ALLELE_MASKED)    # the original group didn't have the allele, so we're masked
                        continue
                    
                    allCount = 0
                    targetCount = 0
                    
                    for i in groupDict[s.parameters['group']].samples:
                        if variantObject.genotypes.has_key(i):
                            allele1 = variantObject.genotypes[i].allele1
                            allele2 = variantObject.genotypes[i].allele2
                            if allele1 != None:
                                allCount += 1
                                if allele1 == targetAllele:
                                    targetCount += 1
                            if allele2 != None:
                                allCount += 1
                                if allele2 == targetAllele:
                                    targetCount += 1
                    if allCount == 0:
                        variantObject.setAttribute(statisticID,variant.MISSING)    # We had no data for this variant, so this thing is undefined
                    else:
                        variantObject.setAttribute(statisticID,float(targetCount)/allCount)
        self.dataConnection.commit()
    
    def estimateTicks(self):
        return len(self.allAxes)*len(self.data['variant keys'])/tempVariantData.TICK_INTERVAL
    
    def getFirstAxes(self):
        temp = self.defaultAxisOrder()
        if len(temp) < 2:
            raise ValueError("You should have at least two data attributes (columns in your .csv file or INFO fields in your .vcf file)\n" +
                             "to use this program (otherwise you probably should be using LibreOffice Calc or IGV to explore your data instead).")
        return (temp[0],temp[1])
    
    def defaultAxisOrder(self):
        # gives priority to axes (each subgroup is sorted alphabetically):
        # program-generated allele frequencies are first
        # numeric other values are next
        # categorical other values are last
        result = []
        for a in sorted(self.statisticLabels):
            result.append(a)
        for a in sorted(self.axisLabels):
            if not self.data.has_key(a):
                result.append(a)    # if we haven't built the axes yet, just add them in order; we'll worry about numeric, etc next time
            elif self.data[a].hasNumeric() and a not in self.statisticLabels:
                result.append(a)
        
        for a in sorted(self.axisLabels):
            if self.data.has_key(a) and not self.data[a].hasNumeric() and a not in self.statisticLabels:
                result.append(a)
        result.append('Genome Position')
        return result
    
    def dumpVcfFile(self, path, callback):
        outfile = open(path,'w')
        outfile.write('##fileformat=VCFv4.0\n')
        outfile.write('##FILTER=<ID=s50,Description="Less than 50% of samples are fully called">\n')
        outfile.write('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">')
        for a in self.allAxes:
            if a.startswith('FILTER') or a.startswith('QUAL'):
                continue
            outfile.write('##INFO=<ID=%s,Number=1,Type=Float,Description="%s">\n' % (a,a))
        outfile.write('#CHROM  POS     ID      REF     ALT     QUAL    FILTER  INFO    FORMAT\n')
        i = 0
        nextTick = tempVariantData.TICK_INTERVAL
        for k,v in self.data.iteritems():
            if k == 'variant keys':
                continue
            outfile.write(variantFile.composeVcfLine(v,{}) + "\n")
            i += 1
            if i > nextTick:
                nextTick += tempVariantData.TICK_INTERVAL
                if callback():
                    outfile.close()
                    return False
        outfile.close()
        return True
        