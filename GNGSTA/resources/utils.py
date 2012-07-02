import sys
import os
from collections import defaultdict
from structures import recursiveDict

####################
# Helper constants #
####################

# Chromosome lengths and offsets for GRCh37.p8 (rCRS for chrM) 
chrLengths =   {"chr1":249250621,
                "chr2":243199373,
                "chr3":198022430,
                "chr4":191154276,
                "chr5":180915260,
                "chr6":171115067,
                "chr7":159138663,
                "chr8":146364022,
                "chr9":141213431,
                "chr10":135534747,
                "chr11":135006516,
                "chr12":133851895,
                "chr13":115169878,
                "chr14":107349540,
                "chr15":102531392,
                "chr16":90354753,
                "chr17":81195210,
                "chr18":78077248,
                "chr19":59128983,
                "chr20":63025520,
                "chr21":48129895,
                "chr22":51304566,
                "chrX":155270560,
                "chrY":59373566,
                "chrM":16569}

chrOffsets =   {"chr1":0,
                "chr2":249250621,
                "chr3":492449994,
                "chr4":690472424,
                "chr5":881626700,
                "chr6":1062541960,
                "chr7":1233657027,
                "chr8":1392795690,
                "chr9":1539159712,
                "chr10":1680373143,
                "chr11":1815907890,
                "chr12":1950914406,
                "chr13":2084766301,
                "chr14":2199936179,
                "chr15":2307285719,
                "chr16":2409817111,
                "chr17":2500171864,
                "chr18":2581367074,
                "chr19":2659444322,
                "chr20":2718573305,
                "chr21":2781598825,
                "chr22":2829728720,
                "chrX":2881033286,
                "chrY":3036303846,
                "chrM":3095677412,
                }

####################
# Helper functions #
####################

def tail(fname, window):
    """
    Read last N lines from file fname.
    This function borrowed from http://code.activestate.com/recipes/577968-log-watcher-tail-f-log/ on 3 Feb 2012
    
    Author: Giampaolo Rodola' <g.rodola [AT] gmail [DOT] com>
    License: MIT
    
    Slightly tweaked from original version
    """
    f = open(fname, 'r')

    BUFSIZ = 1024
    f.seek(0, os.SEEK_END)
    fsize = f.tell()
    block = -1
    data = ""
    exit = False
    while not exit:
        step = (block * BUFSIZ)
        if abs(step) >= fsize:
            f.seek(0)
            exit = True
        else:
            f.seek(step, os.SEEK_END)
        data = f.read().strip()
        if data.count('\n') >= window:
            break
        else:
            block -= 1
    return data.splitlines()[-window:]


##################
# Helper classes #
##################

class genotype:
    def __init__(self, text, attemptRepairsWhenComparing=True):
        self.text = text
        
        if "|" in text:
            temp = text.split("|")
            self.isPhased = True
        else:
            temp = text.split("/")
            self.isPhased = False
            
        if temp[0] == ".":
            self.allele1 = None
        else:
            self.allele1 = int(temp[0])
            if self.allele1 > 9:
                print "ERROR: Highest supported alternate allele is 9."
                sys.exit(1)
        
        if temp[1] == ".":
            self.allele2 = None
        else:
            self.allele2 = int(temp[1])
            if self.allele2 > 9:
                print "ERROR: Highest supported alternate allele is 9."
                sys.exit(1)
        
        self.attributes = {}
        self.attemptRepairsWhenComparing = attemptRepairsWhenComparing
    
    def exchangeAttributes(self, other):
        """
        Attempts to share attributes between two genotypes; will leave both untouched if mismatching existing data for the same attribute is encountered
        """
        newAttributes = {}
        
        for k,v in other.attributes.iteritems():
            if self.attributes.has_key(k):
                if v != self.attributes[k]:
                    return False
            else:
                newAttributes[k] = v
        
        for k,v in self.attributes.iteritems():
            if other.attributes.has_key(k):
                if v != other.attributes[k]:
                    return False
            else:
                newAttributes[k] = v
        
        self.attributes.update(newAttributes)
        other.attributes.update(newAttributes)
    
    def isMissingData(self):
        return self.allele1 == None or self.allele2 == None
    
    def numSharedAlleles(self, other):
        if self.allele1 == other.allele1:
            if self.allele2 == other.allele2:
                return 2
            else:
                return 1
        elif self.allele1 == other.allele2:
            if self.allele2 == other.allele1:
                return 2
            else:
                return 1
        elif self.allele2 == other.allele2:
            return 1
        else:
            return 0
    
    def __hash__(self):
        """
        Does some fancy math to make genotypes hash to the same place regardless of their allele ordering, as well as ensuring
        good hash usage (0/0->0, 0/1 or 1/0->1, 1/1->2, 2/0 or 0/2->3, ...) NOTE: this ignores any attribute or contextual
        information. You probably want to use genotypes directly on rare occasions.
        """
        if self.allele1 == None or self.allele2 == None:
            return -1
        temp = sorted([self.allele1,self.allele2])
        normalizer = 0
        i = temp[0]
        while i > 0:
            normalizer += 10-i
            i-=1
        return int("".join(str(y) for y in temp))-normalizer
    
    def __eq__(self, other):
        if other == None:
            return False
        if (self.allele1 == other.allele1 and self.allele2 == other.allele2) or (self.allele1 == other.allele2 and self.allele2 == other.allele1):
            if self.attemptRepairsWhenComparing:
                self.exchangeAttributes(other)
            return True
        else:
            return False
    
    def __ne__(self, other):
        return not self.__eq__(other)

class allele:
    """
    A helper class for variant (not used in genotype) to match regexes between variants
    """
    def __init__(self, text, attemptRepairsWhenComparing=True):
        self.text = text
        self.attemptRepairsWhenComparing = attemptRepairsWhenComparing
    
    def __eq__(self, other):
        '''
        For now, alleles match if and only if their text lengths are the same and there are no possible letter conflicts;
        the "?" wildcard will allow some mismatches (but the lengths must remain the same)
        
        TODO: do real regex comparisons, repairs
        '''
        if other == None:
            return False
        if len(self.text) != len(other.text):
            return False
        for i,c in enumerate(self.text):
            if c != other.text[i] and c != "?" and other.text[i] != "?":
                return False
        #self.repair(other)
        return True
    
    def repair(self, other):
        if self.attemptRepairsWhenComparing and other.attemptRepairsWhenComparing:
            i = self.text.find("?")
            while i != -1:
                if other.text[i] == "?":
                    known = i+1
                    i = self.text[known:].find("?")
                    if i > -1:
                        i += known
                    continue
                self.text = self.text[:i] + other.text[i] + self.text[i+1:]
                i = self.text.find("?")
            i = other.text.find("?")
            while i != -1:
                if self.text[i] == "?":
                    known = i+1
                    i = other.text[known:].find("?")
                    if i > -1:
                        i += known
                    continue
                other.text = other.text[:i] + self.text[i] + other.text[i+1:]
                i = other.text.find("?")
        return True
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __str__(self):
        return self.text

class variant:
    """
    Options:
    name: rs number, or chr_start_ref_alt will be used if None
    ref: reference allele
    alt: alternate allele
    attemptRepairsWhenComparing: will attempt to repair missing information in the other variant if they are determined to be the same variant
    forceAlleleMatching: by default, comparison will check alleles as well as genome position, but this can be bypassed by setting to False
    """
    def __init__(self, chromosome, start, ref="?", alt="?", name=None, attemptRepairsWhenComparing=True, forceAlleleMatching=True):
        if not chromosome.startswith("chr"):
            chromosome = "chr" + chromosome
        if not chrOffsets.has_key(chromosome):
            print "ERROR: unknown chromosome: %s" % chromosome
            sys.exit(1)
        self.chromosome = chromosome
        self.start = int(start)
        self.stop = self.start + len(ref) - 1
        self.genomePosition = self.start + chrOffsets[self.chromosome]
        self.ref = allele(ref)
        self.alt = []
        if isinstance(alt,list):
            for a in alt:
                self.alt.append(allele(a,attemptRepairsWhenComparing))
        else:
            self.alt.append(allele(alt,attemptRepairsWhenComparing))
        if len(alt) != 1:
            self.isIndel = True
        else:
            self.isIndel = False
        self.attributes = {}
        self.genotypes = {}
        self.hashCode = "%s_%i" % (self.chromosome,self.start)
        if name == None or name == ".":
            name = self.hashCode
        self.name = name
        self.attemptRepairsWhenComparing = attemptRepairsWhenComparing
        self.forceAlleleMatching = forceAlleleMatching
    
    def addGenotype(self, individual, genotypeText):
        self.genotypes[individual] = genotype(genotypeText, self.attemptRepairsWhenComparing)
    
    def __hash__(self):
        return hash(self.hashCode)
    
    def __eq__(self, other):
        """
        We want to say two variants are equal if their chromosome and position match AND
        two matches occur (involving both reference alleles) between variant objects
        """
        if other == None:
            return False
        if self.chromosome != other.chromosome:
            return False
        elif self.start != other.start:
            return False
        elif not self.forceAlleleMatching:
            return True
        elif self.ref != other.ref:
            selfAltAllele = None
            for s in other.alt:
                if self.ref == s:
                    selfAltAllele = s
                    break;
            otherAltAllele = None
            for s in self.alt:
                if other.ref == s:
                    otherAltAllele = s
                    break;
            if selfAltAllele == None or otherAltAllele == None:
                return False
            else:
                self.repair(other, selfAltAllele, otherAltAllele)
                return True
        else:
            for a in self.alt:
                if a in other.alt:
                    self.repair(other)
                    return True
            # We got through all alt alleles, and nothing matched
            return False
        
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    @staticmethod
    def numXYMCompare(x, y):
        if x == y:
            return variant.positionCompare(x,y)
        xChr = x.chromosome[3:]
        yChr = y.chromosome[3:]
        try:
            xc = int(xChr)
        except ValueError:
            if xChr == 'X':
                xc = 23
            elif xChr == 'Y':
                xc = 24
            elif xChr == 'M':
                xc = 25
            else:
                print "WARNING: I don't know how to sort %s" % xChr
                xc = 26
        try:
            yc = int(yChr)
        except ValueError:
            if yChr == 'X':
                yc = 23
            elif yChr == 'Y':
                yc = 24
            elif yChr == 'M':
                yc = 25
            else:
                print "WARNING: I don't know how to sort %s" % yChr
                yc = 26
        if xc == yc:
            return variant.positionCompare(x,y)
        else:
            return xc-yc
            
    @staticmethod
    def unixCompare(x, y):
        if x.chromosome == y.chromosome:
            return variant.positionCompare(x,y)
        if x.chromosome > y.chromosome:
            return 1;
        else:
            return -1
    @staticmethod
    def positionCompare(x,y):
        return x.start-y.start
    
    def repair(self, other, selfAltAllele=None, otherAltAllele=None):
        """
        Attempt to update self and other's information... if some existing data mismatches, leave
        them unchanged
        """
        #if self.name == "rs3834129" or other.name == "rs3834129":
        #    print "Self: %s\t%i\t%s\t%s\t%s"%(self.chromosome,self.start,self.name,str(self.ref),",".join([str(a) for a in self.alt]))
        #    print "Other:%s\t%i\t%s\t%s\t%s"%(other.chromosome,other.start,other.name,str(other.ref),",".join([str(a) for a in other.alt]))
        
        if self.attemptRepairsWhenComparing and other.attemptRepairsWhenComparing:
            # attempt to update names
            newName = None
            if self.name != self.hashCode:
                newName = self.name
            if other.name != other.hashCode:
                newName = other.name
            if newName != None and self.name != other.name:
                return
            
            # TODO: attempt to fix reversed ref-alt configurations... this requires reversing genotypes!!!
            # For now, I just update missing allele letters, but leave them in their ref-alt configurations
            if selfAltAllele != None and otherAltAllele != None:
                selfAltAllele.repair(otherAltAllele)
            
            # attempt to update attributes
            newAttributes = self.exchangeAttributes(other)
            if newAttributes == None:
                return
            
            # attempt to update genotypes
            newGenotypes = self.exchangeGenotypes(other)
            if newGenotypes == None:
                return
            
            # Okay, we've made it... update everything
            if newName != None:
                self.name = newName
                other.name = newName
            
            self.attributes.update(newAttributes)
            other.attributes.update(newAttributes)
            
            self.genotypes.update(newGenotypes)
            other.genotypes.update(newGenotypes)
    
    def exchangeAttributes(self, other):
        newAttributes = {}
        
        for k,v in other.attributes.iteritems():
            if self.attributes.has_key(k):
                if v != self.attributes[k]:
                    return None
            else:
                newAttributes[k] = v
        
        for k,v in self.attributes.iteritems():
            if other.attributes.has_key(k):
                if v != other.attributes[k]:
                    return None
            else:
                newAttributes[k] = v
        return newAttributes
    
    def exchangeGenotypes(self, other):
        newGenotypes = {}
        
        for k,v in other.genotypes.iteritems():
            if self.genotypes.has_key(k):
                if v != self.genotypes[k]:
                    return None
            else:
                newGenotypes[k] = v
        
        for k,v in self.genotypes.iteritems():
            if other.genotypes.has_key(k):
                if v != other.genotypes[k]:
                    return None
            else:
                newGenotypes[k] = v
        
        return newGenotypes
    
    def isPolymorphic(self):
        temp = genotype("./.",False)
        setFirst = False
        for g in self.genotypes.itervalues():
            if not setFirst:
                temp.allele1 = g.allele1
                temp.allele2 = g.allele2
                continue
            if temp != g:
                return True
        return False

class feature:
    def __init__(self, chromosome, start, stop=None, name=None, attemptRepairsWhenComparing=True):
        if not chromosome.startswith("chr"):
            chromosome = "chr" + chromosome
        self.chromosome = chromosome
        self.start = start
        if stop == None:
            self.stop = self.start+1
        else:
            self.stop = stop
        self.hashCode = "%s_%i_%i" % (self.chromosome,self.start,self.stop)
        if name==None:
            self.name = self.hashCode
        else:
            self.name = name
        self.attributes = {}
        self.attemptRepairsWhenComparing = attemptRepairsWhenComparing
    
    def contains(self, chromosome, position):
        if self.chromosome != chromosome:
            return False
        position = int(position)
        if position >= self.start and position < self.stop:
            return True
        else:
            return False
    
    def overlap(self, otherFeature):
        if self.chromosome != otherFeature.chromosome:
            return False
        if self.start > otherFeature.stop:
            return False
        if otherFeature.start > self.stop:
            return False
        return True
    @staticmethod
    def numXYMCompare(x, y):
        if x == y:
            return feature.positionCompare(x,y)
        xChr = x.chromosome[3:]
        yChr = y.chromosome[3:]
        try:
            xc = int(xChr)
        except ValueError:
            if xChr == 'X':
                xc = 23
            elif xChr == 'Y':
                xc = 24
            elif xChr == 'M':
                xc = 25
            else:
                print "WARNING: I don't know how to sort %s" % xChr
                xc = 26
        try:
            yc = int(yChr)
        except ValueError:
            if yChr == 'X':
                yc = 23
            elif yChr == 'Y':
                yc = 24
            elif yChr == 'M':
                yc = 25
            else:
                print "WARNING: I don't know how to sort %s" % yChr
                y = 26
        if xc == yc:
            return feature.positionCompare(x,y)
        else:
            return xc-yc
    @staticmethod
    def unixCompare(x, y):
        if x.chromosome == y.chromosome:
            return feature.positionCompare(x,y)
        if x.chromosome > y.chromosome:
            return 1;
        else:
            return -1
    @staticmethod
    def positionCompare(x,y):
        return x.start-y.start
    
    def __hash__(self):
        return self.hashCode
    
    def __eq__(self, other):
        if self.hashCode == other.hashCode:
            if self.attemptRepairsWhenComparing:
                self.exchangeAttributes(other)
            return True
        else:
            return False
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def exchangeAttributes(self, other):
        newAttributes = {}
        
        for k,v in other.attributes.iteritems():
            if self.attributes.has_key(k):
                if v != self.attributes[k]:
                    return
            else:
                newAttributes[k] = v
        
        for k,v in self.attributes.iteritems():
            if other.attributes.has_key(k):
                if v != other.attributes[k]:
                    return
            else:
                newAttributes[k] = v
        
        self.attributes.update(newAttributes)
        other.attributes.update(newAttributes)

class bedFile:
    def __init__(self):
        self.regions = []
    
    def numRegions(self):
        return len(self.regions)
    
    def contains(self, chromosome, position):
        # TODO: this could probably be optimized...
        for r in self.regions:
            if r.contains(chromosome, position):
                return True
        return False
    
    def overlap(self, f):
        # TODO: this could probably be optimized...
        for r in self.regions:
            if r.overlap(f):
                return True
        return False
    
    @staticmethod
    def parseBedFile(fileObject,functionToCall=None,callbackArgs={},mask=None,returnFileObject=True):
        if returnFileObject:
            newFileObject = bedFile()
        for line in fileObject:
            columns = line.split()
            newRegion = feature(columns[0],int(columns[1])+1,int(columns[2]),columns[3])    # the +1 converts from BED coordinates
            if mask != None and not mask.overlap(newRegion):
                continue
            if functionToCall != None:
                functionToCall(newRegion,**callbackArgs)
            if returnFileObject:
                newFileObject.regions.append(newRegion)
        if returnFileObject:
            return newFileObject
        else:
            return None # Normally we return file attributes, but the bed file is too simple
    
    def writeBedFile(self, fileObject, sortMethod=None):
        if sortMethod == "UNIX":
            featureList = sorted(self.regions, cmp=feature.unixCompare)
        elif sortMethod == "NUMXYM":
            featureList = sorted(self.regions, cmp=feature.numXYMCompare)
        else:
            featureList = self.regions
        
        for f in featureList:
            fileObject.write(bedFile.composeBedLine(f) + "\n")
    
    @staticmethod
    def composeBedLine(f):
        return "%s\t%i\t%i\t%s" % (f.chromosome,f.start-1,f.stop,f.name)  # the -1 converts back to BED coordinates

class csvVariantFile:
    def __init__(self):
        self.fileAttributes = {}
        self.variants = set()
    
    @staticmethod
    def extractVariantAttributesInFile(fileObject,delimiter=',',*args,**kwargs):
        for line in fileObject:
            results = line[:-1].split(delimiter)
            break
        
        for a in args:
            if a in results:
                results.remove(a)
        for a in kwargs.itervalues():
            if a in results:
                results.remove(a)
        return results
    
    @staticmethod
    def parseCsvVariantFile(fileObject,chromosomeHeader,startHeader,refHeader=None,altHeader=None,nameHeader=None,attemptRepairsWhenComparing=True,forceAlleleMatching=True,delimiter=",",functionToCall=None,callbackArgs={},mask=None,returnFileObject=True):
        '''
        Assuming every row in a .csv file, we create the same sort of functionality as if it were one of these other standard formats
        '''
        if returnFileObject:
            newFileObject = csvVariantFile()
        
        headerMappings = {}
        headers = []
        firstLine = True
        
        for line in fileObject:
            columns = line[:-1].split(delimiter)
            if firstLine:
                headers = columns
                if chromosomeHeader not in headers or startHeader not in headers:
                    print "ERROR: %s and %s headers required." % (chromosomeHeader,startHeader)
                    sys.exit(1)
                headerMappings[headers.index(chromosomeHeader)] = "chromosome"
                headerMappings[headers.index(startHeader)] = "start"
                
                if refHeader != None and refHeader in headers:
                    headerMappings[headers.index(refHeader)] = "ref"
                if altHeader != None and altHeader in headers:
                    headerMappings[headers.index(altHeader)] = "alt"
                if nameHeader != None and nameHeader in headers:
                    headerMappings[headers.index(nameHeader)] = "name"
                firstLine = False
            else:
                varArgs = {"attemptRepairsWhenComparing":attemptRepairsWhenComparing,"forceAlleleMatching":forceAlleleMatching}
                tempAttributes = {}
                for i,c in enumerate(columns):
                    if headerMappings.has_key(i):
                        varArgs[headerMappings[i]] = c
                    else:
                        tempAttributes[headers[i]] = c
                
                newVariant = variant(**varArgs)
                newVariant.attributes.update(tempAttributes)
                
                if mask != None and not mask.contains(chromosome=varArgs["chromosome"],position=varArgs["start"]):
                    continue
                if functionToCall != None:
                    functionToCall(newVariant,**callbackArgs)
                if returnFileObject:
                    newFileObject.variants.add(newVariant)
        if returnFileObject:
            newFileObject.fileAttributes["HEADER_MAPPINGS"] = headerMappings
            newFileObject.fileAttributes["ALL_HEADERS"] = headers
            return newFileObject
        else:
            return {"HEADER_MAPPINGS":headerMappings,"ALL_HEADERS":headers}

class vcfFile:
    def __init__(self):
        self.fileAttributes = {}
        self.variants = set()
        self.individuals = []
    
    def addVariant(self, v):
        self.variants.add(v)
        self.individuals = list(set(v.genotypes.iterkeys()).union(self.individuals))
    
    def addAttributes(self, a):
        if not self.fileAttributes.has_key("fileformat"):
            self.fileAttributes["fileformat"] = "VCFv4.1"
        if not self.fileAttributes.has_key("INFO"):
            self.fileAttributes["INFO"] = {}
        if not self.fileAttributes.has_key("FORMAT"):
            self.fileAttributes["FORMAT"] = {}
        if not self.fileAttributes.has_key("FILTER"):
            self.fileAttributes["FILTER"] = {}
        for k,v in a.iteritems():
            if k == "INFO":
                self.fileAttributes["INFO"].update(v)
            elif k == "FORMAT":
                self.fileAttributes["FORMAT"].update(v)
            elif k == "FILTER":
                self.fileAttributes["FILTER"].update(v)
            else:
                self.fileAttributes[k] = v
    
    @staticmethod
    def extractIndividualsInFile(fileObject):
        for line in fileObject:
            if line.startswith("#CHROM") or line.startswith("#chrom"):
                columns = line.split()
                return columns[9:]
        return None
    
    @staticmethod
    def extractVariantAttributesInFile(fileObject):
        results = []
        for line in fileObject:
            if len(line) <= 1:
                continue
            elif line.startswith("##"):
                line = line.strip()[2:]
                if line.startswith("FILTER") and 'FILTER' not in results:
                    results.append('FILTER')
                elif line.startswith("INFO"):
                    text = line[6:-1]
                    temp = text[text.find("ID=")+3:]
                    temp = temp[:temp.find(",")]
                    results.append(temp)
            else:
                break
        return results
    
    @staticmethod
    def parseVcfFile(fileObject,functionToCall=None,callbackArgs={},individualsToExclude=[],individualsToInclude=[],mask=None,returnFileObject=True,skipFiltered=True,skipVariantAttributes=False,skipGenotypes=False,skipGenotypeAttributes=False,includeAdditionalHeaderInfo=False,forceAlleleMatching=True):
        """
        Parses a .vcf file and calls functionToCall with each new variant found (optionally including callbackArgs as parameters).
        Mask is a bedFile object; if included, variants outside the region will be ignored
        skipFiltered, if True, will skip any variants not containing "PASS" in their FILTER field
        skipVariantAttributes,skipGenotypes,skipGenotypeAttributes,includeAdditionalHeaderInfo, are all options that will ignore
        irrelevant information in the .vcf file, giving some speed gains
        returnFileObject will store all the information from the vcf file - if you only want to do a single iteration through
        the file, setting this to false can save a lot of memory and computation
        """
        
        def parseHeader(text):
            tempDict = {}
            for key in ["ID=","Type=","Number="]:
                if key in text:
                    temp = text[text.find(key) + len(key):]
                    temp = temp[:temp.find(",")]
                    tempDict[key[:-1]] = temp
            tempDict["Description"] = text.split("\"")[1]
            return tempDict
        
        if returnFileObject:
            vcfObject = vcfFile()
        
        variants = []
        individuals = []
        fileAttributes=recursiveDict()
        for regLine in fileObject:
            if len(regLine) <= 1:
                # ignore blank lines
                continue
            line = regLine.strip()
            
            if line[0:2] == "##":
                line = line[2:]
                if not skipVariantAttributes:
                    if line.startswith("FILTER"):
                        headerData = parseHeader(line[8:-1])
                        fileAttributes["FILTER"][headerData["ID"]] = headerData
                    elif line.startswith("INFO"):
                        headerData = parseHeader(line[6:-1])
                        fileAttributes["INFO"][headerData["ID"]] = headerData
                    elif line.startswith("FORMAT"):
                        if skipGenotypeAttributes:
                            continue
                        headerData = parseHeader(line[8:-1])
                        fileAttributes["FORMAT"][headerData["ID"]] = headerData
                    elif includeAdditionalHeaderInfo:
                        fileAttributes[line[:line.find("=")]] = line[line.find("=")+1:]
                continue
            elif line[0] == "#":
                # column headers - get individuals from this
                columns = line.split()
                for c in columns[9:]:
                    individuals.append(c)
                if len(individualsToInclude) > 0:
                    fileAttributes["INDIVIDUALS"] = [set(individuals).intersection(set(individualsToInclude)).difference(set(individualsToExclude))]
                else:
                    fileAttributes["INDIVIDUALS"] = [set(individuals).difference(set(individualsToExclude))]
            else:
                # actual data - a row is a variant
                columns = line.strip().split("\t")
                
                if not columns[0].startswith("chr"):
                    columns[0] = "chr" + columns[0]
                                
                if mask != None and not mask.contains(chromosome=columns[0],position=columns[1]):
                    continue
                                
                if skipFiltered and "PASS" not in columns[6].split(";"):
                    continue
                                                
                rsNumber = columns[2]
                if columns[2] == ".":
                    rsNumber = None
                
                newVariant = variant(chromosome=columns[0],start=columns[1],ref=columns[3],alt=columns[4].split(","),name=columns[2],forceAlleleMatching=forceAlleleMatching)
                
                # Handle QUAL, FILTER, and INFO
                if not skipVariantAttributes:
                    # Add the QUAL column
                    newVariant.attributes["QUAL"] = columns[5]
                    
                    # Add the filters if there are any
                    if not skipFiltered:
                        newVariant.attributes["FILTER"] = []
                        temp = columns[6].split(";")
                        for f in temp:
                            newVariant.attributes["FILTER"].append(f)
                    else:
                        if "PASS" not in columns[6]:
                            continue
                        newVariant.attributes["FILTER"] = ["PASS"]
                    
                    # Add the INFO fields
                    temp = columns[7].split(";")
                    for a in temp:
                        if "=" in a:
                            temp2 = a.split("=")
                            newVariant.attributes[temp2[0]] = temp2[1]
                        else:
                            newVariant.attributes[a] = a
                # Handle sample columns
                if not skipGenotypes:
                    formatPattern = columns[8].split(":")
                    if len(formatPattern) > 0:
                        if formatPattern[0] != "GT":
                            print "ERROR in vcf file (GT field required):\n%s" % line
                            sys.exit(1)
                        for person,c in enumerate(columns[9:]):
                            temp = c.split(":")
                            if len(temp) > len(formatPattern) and temp[0] != "./." and temp[0] != ".|.":
                                print "ERROR in vcf file (too many values in FORMAT column):\n%s" % line
                                sys.exit(1)
                            if len(individualsToInclude) > 0 and individuals[person] not in individualsToInclude:
                                continue
                            if individuals[person] in individualsToExclude:
                                continue
                            
                            newGenotype = genotype(text=temp[0], attemptRepairsWhenComparing=newVariant.attemptRepairsWhenComparing)
                            
                            if not skipGenotypeAttributes:
                                for i,a in enumerate(formatPattern):
                                    if a == "GT":
                                        if temp[i] == "./." or temp[i] == ".|.":
                                            break
                                        continue
                                    # It is possible to list FORMAT columns that only some individuals have data - I assume, however, that this must always be the last column?
                                    if i < len(temp) and temp[i] != ".":
                                        newGenotype.attributes[a] = temp[i]
                            
                            newVariant.genotypes[individuals[person]] = newGenotype
                if functionToCall != None:
                    functionToCall(newVariant,**callbackArgs)
                if returnFileObject:
                    vcfObject.addVariant(newVariant)
        
        if returnFileObject:
            vcfObject.addAttributes(fileAttributes)
            return vcfObject
        else:
            return fileAttributes
    
    def writeVcfFile(self, fileObject, sortMethod=None):
        self.fileAttributes["INDIVIDUALS"] = sorted(self.individuals)
        
        if sortMethod == "UNIX":
            variantList = sorted(self.variants, cmp=variant.unixCompare)
        elif sortMethod == "NUMXYM":
            variantList = sorted(self.variants, cmp=variant.numXYMCompare)
        else:
            variantList = list(self.variants)
        
        fileObject.write(vcfFile.composeVcfHeader(self.fileAttributes) + "\n")
        
        for v in variantList:
            fileObject.write(vcfFile.composeVcfLine(v, self.fileAttributes) + "\n")
        fileObject.close()
    
    @staticmethod
    def composeVcfHeader(fileAttributes):
        outString = ""
        outString += "##fileformat=%s\n" % fileAttributes["fileformat"]
        for k,v in fileAttributes.iteritems():
            if k == "fileformat" or k == "INDIVIDUALS":
                continue
            elif k == "INFO" or k == "FORMAT" or k == "FILTER":
                for id,values in v.iteritems():
                    outString += "##%s=<ID=%s" % (k,id)
                    if values.has_key("Number"):
                        outString += ",Number=%s" % values["Number"]
                    if values.has_key("Type"):
                        outString += ",Type=%s" % values["Type"]
                    for k2,v2 in values.iteritems():
                        if k2 == "ID" or k2 == "Number" or k2 == "Type":
                            continue
                        if k2 == "Description":
                            outString += ",%s=\"%s\"" % (k2,v2)
                        else:
                            outString += ",%s=%s" % (k2,v2)
                    outString += ">\n"
            else:
                outString += "##%s=%s\n" % (k,v)
        outString += "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT"
        
        for i in sorted(fileAttributes["INDIVIDUALS"]):
            outString += "\t%s" % i
        
        return outString
    
    @staticmethod
    def composeVcfLine(v,fileAttributes):
        outString = ""
        rsNumber = v.name
        if v.hashCode == v.name:
            rsNumber = "."
        # basics
        outString += "%s\t%i\t%s\t%s\t%s"%(v.chromosome,v.start,rsNumber,str(v.ref),",".join([str(a) for a in v.alt]))
        
        # attributes
        info = ""
        for k,val in v.attributes.iteritems():
            if k == "QUAL" or k == "FILTER":
                continue
            info += "%s=%s;" % (k,val)
        info = info[:-1]    # strip last semicolon
        outString += "\t%s\t%s\t%s"%(v.attributes["QUAL"],";".join(v.attributes["FILTER"]),info)
        
        # genotypes - the VCF spec requires that every column must have the same fields for a variant, so we'll trust the first one
        formatString = "GT"
        formatList = ["GT"]
        for k in v.genotypes[fileAttributes["INDIVIDUALS"][0]].attributes.iterkeys():
            if k == "GT":
                continue
            formatString += ":%s" % k
            formatList.append(k)
        
        outString += "\t%s" % formatString
        
        for i in fileAttributes["INDIVIDUALS"]:
            outString += "\t%s" % v.genotypes[i].text
            if len(v.genotypes[i].attributes) == 0:
                continue
            for f in formatList:
                if f == "GT":
                    continue
                if v.genotypes[i].attributes.has_key(f):    # again, assuming any missing values will be the last ones...
                    outString += ":%s"%(v.genotypes[i].attributes[f])
        return outString

class gff3File:
    def __init__(self):
        self.headerList = []
        self.regions = []
    
    @staticmethod
    def parseGff3File(fileObject,functionToCall=None,callbackArgs={},columnsToExclude=[],mask=None,returnFileObject=True):
        if returnFileObject:
            newFileObject = gff3File()
        else:
            headerList = []
        
        for line in fileObject:
            if len(line) <= 1:
                continue
            
            if line.startswith("#"):
                if returnFileObject:
                    newFileObject.headerList.append(line.strip())
                else:
                    headerList.append(line.strip())
                continue
            
            columns = line.split()
            chromosome = columns[0]
            start = int(columns[3])
            stop = int(columns[4])
            
            newFeature=feature(chromosome,start,stop)
            if mask != None and not mask.overlap(newFeature):
                continue
            
            newFeature.attributes["SOURCE"] = columns[1]
            newFeature.attributes["TYPE"] = columns[2]
            newFeature.attributes["SCORE"] = columns[5]
            newFeature.attributes["STRAND"] = columns[6]
            newFeature.attributes["PHASE"] = columns[7]
            
            for pair in columns[8].split(";"):
                temp = pair.split("=")
                newFeature.attributes[temp[0]] = temp[1]
            
            if functionToCall != None:
                functionToCall(newFeature,**callbackArgs)
            if returnFileObject:
                newFileObject.regions.append(newFeature)
        
        if returnFileObject:
            return newFileObject
        else:
            return headerList
    
    @staticmethod
    def composeGff3Line(f):
        attributeSection = ""
        for k,v in f.attributes.iteritems():
            if k not in ["SOURCE","TYPE","SCORE","STRAND","PHASE"]:
                attributeSection += "%s=%s;" % (k,v)
        attributeSection = attributeSection[:-1]
        return "%s\t%s\t%s\t%i\t%i\t%s\t%s\t%s\t%s" % (f.chromosome,f.attributes["SOURCE"],f.attributes["TYPE"],f.start,f.stop,f.attributes["SCORE"],f.attributes["STRAND"],f.attributes["PHASE"],attributeSection)
    
    def writeGff3File(self, fileObject, sortMethod=None):
        for h in self.headerList:
            fileObject.write(h + "\n")
        
        if sortMethod == "UNIX":
            featureList = sorted(self.regions, cmp=feature.unixCompare)
        elif sortMethod == "NUMXYM":
            featureList = sorted(self.regions, cmp=feature.numXYMCompare)
        else:
            featureList = self.regions
        
        for f in featureList:
            fileObject.write(gff3File.composeGff3Line(f) + "\n")

class phastconsFile:    # TODO: get to know this format better... continuous data?
    def __init__(self):
        self.regions = []
    
    @staticmethod
    def parsePhastconsFile(fileObject,functionToCall=None,callbackArgs={},mask=None,returnFileObject=True):
        if returnFileObject:
            newFileObject = phastconsFile()
        for line in fileObject:
            if len(line) <= 1:
                continue
            columns = line.split()
            newRegion = feature(columns[0],int(columns[1]))
            if mask != None and not mask.overlap(newRegion):
                continue
            newRegion.attributes["PHASTCONS_SCORE"] = float(columns[2])
            if functionToCall != None:
                functionToCall(newRegion,**callbackArgs)
            if returnFileObject:
                newFileObject.regions.append(newRegion)
        if returnFileObject:
            return newFileObject
        else:
            return None # Normally we return file attributes, but the phastcons file is too simple
    
    def writePhastconsFile(self, fileObject, sortMethod=None):
        if sortMethod == "UNIX":
            featureList = sorted(self.regions, cmp=feature.unixCompare)
        elif sortMethod == "NUMXYM":
            featureList = sorted(self.regions, cmp=feature.numXYMCompare)
        else:
            featureList = self.regions
        
        for f in featureList:
            fileObject.write(phastconsFile.composePhastconsLine(f) + "\n")
    
    @staticmethod
    def composePhastconsLine(f):
        return "%s\t%i\t%f" % (f.chromosome,f.start,f.attributes["PHASTCONS_SCORE"])

class cdrFile:
    def __init__(self):
        self.fileAttributes = recursiveDict()
        self.variants = set()
    
    @staticmethod
    def findNumIndividuals(filePath):
        # First need to extract the number of individuals
        numIndividuals = -1
        probeSize = 300 # we should definitely find the number of genomes in the last 300 lines of the file, but just in case we'll loop until we find it
        readWholeFile = False
        while (numIndividuals == -1):
            lastLines = tail(filePath,window=probeSize)
            if len(lastLines) != probeSize:
                readWholeFile = True    # shoot, we just read the whole file... if we don't find it, then it means this is a bad .cdr file
            
            for line in lastLines:
                if line.startswith("#"):
                    columns = line.split()
                    if columns[1] == "GENOME-COUNT":
                        return int(columns[2])
            
            if readWholeFile:
                return None
            else:
                probeSize *= 100 # Wow, we still didn't find it (this should rarely, if ever happen)... try looking at a lot more lines
    
    @staticmethod
    def parseCdrFile(fileObject,numIndividuals,functionToCall=None,callbackArgs={},mask=None,returnFileObject=True):
        if returnFileObject:
            newFileObject = cdrFile()
        
        fileAttributes = recursiveDict()
        for line in fileObject:
            if len(line) <= 1 or line.startswith("#"):
                columns = line.strip().split("\t")
                if columns[1] == "GENDER":
                    temp = columns[2].split(":")
                    fileAttributes[temp[0]] = temp[1]
                    if len(columns) >= 4:   # could potentially only have one gender
                        temp = columns[3].split(":")
                        fileAttributes[temp[0]] = temp[1]
                else:   # All the other meta lines can safely be encoded in the recursiveDict
                    fileAttributes[columns[1]] = recursiveDict(columns[2:])
                continue
            columns = line.strip().split("\t")
            chrom = columns[0]
            start = columns[1]
            if mask != None and not mask.contains(chrom,start):
                continue
            ref = columns[5].split("|")[0]
            if ref == "-":
                ref = "?"
            altList = []
            
            currentVariant = variant(chrom, start, ref, altList, name=None)
            
            adjustedPosition = False
            for c in columns[6:]:
                temp = c.split("|")
                individuals = temp[0].split(",")
                for i,v in enumerate(individuals):
                    if "-" in v:
                        temp2 = v.split("-")
                        top = int(temp2[1])
                        bottom = int(temp2[0])
                        x = top
                        while x >= bottom:
                            individuals.insert(i+1,str(x))
                            x-=1
                        individuals.remove(v)
                
                nucleotides = temp[1].split(":")
                if nucleotides[0] == "-":
                    nucleotides[0] = "?"
                if nucleotides[1] == "-":
                    nucleotides[1] = "?"
                if (nucleotides[0] == "?" or nucleotides[1] == "?") and ref != "?" and not adjustedPosition:
                    ref = "?" + ref
                    currentVariant.ref = allele(ref)
                    currentVariant.start -= 1   # temporary fix for cdr indel positions
                    adjustedPosition = True
                
                # Add any alternate nucleotide(s)
                if nucleotides[1] != ref and nucleotides[1] != "^" and nucleotides[1] not in currentVariant.alt:
                    currentVariant.alt.append(nucleotides[1])
                if nucleotides[0] != ref and nucleotides[0] != "^" and nucleotides[0] not in currentVariant.alt:
                    currentVariant.alt.append(nucleotides[0])
                
                # Now figure out the genotype
                if nucleotides[0] == "^" or nucleotides[1] == "^":
                    g = "./."
                elif nucleotides[0] == ref and nucleotides[1] == ref:
                    g = "0/0"
                else:
                    if nucleotides[0] == ref:
                        firstIndex = 0
                    else:
                        firstIndex = currentVariant.alt.index(nucleotides[0]) + 1     # array indices are 0-based...
                    if nucleotides[1] == ref:
                        secondIndex = 0
                    else:
                        secondIndex = currentVariant.alt.index(nucleotides[1]) + 1     # array indices are 0-based...
                    
                    if secondIndex < firstIndex:
                        g = "%i/%i" % (secondIndex,firstIndex)
                    else:
                        g = "%i/%i" % (firstIndex,secondIndex)
                
                # Now add the genotype to every individual
                for i in individuals:
                    currentVariant.addGenotype(i, g)
            for i in xrange(numIndividuals):
                if not currentVariant.genotypes.has_key(str(i)):
                    currentVariant.addGenotype(str(i),"0/0")    # unmentioned individuals are hom ref?
            if functionToCall != None:
                functionToCall(currentVariant, **callbackArgs)
            if returnFileObject:
                newFileObject.variants.add(currentVariant)
        if returnFileObject:
            newFileObject.fileAttributes = fileAttributes
            return newFileObject
        else:
            return fileAttributes
    
    def writeCdrFile(self):
        pass    # TODO