import os, tempfile
from bx.intervals.intersection import IntervalTree, Interval
from resources.structures import recursiveDict
from durus.file_storage import FileStorage
from durus.connection import Connection
from durus.persistent import Persistent

####################
# Helper constants #
####################
class genomeUtils:
    # Chromosome lengths and offsets for GRCh37 / hg19
    hg19           =   1
    hg19chrOrder   =   ["chr1",
                        "chr1_gl000191_random",
                        "chr1_gl000192_random",
                        "chr2",
                        "chr3",
                        "chr4",
                        "chr4_ctg9_hap1",
                        "chr4_gl000193_random",
                        "chr4_gl000194_random",
                        "chr5",
                        "chr6",
                        "chr6_apd_hap1",
                        "chr6_cox_hap2",
                        "chr6_dbb_hap3",
                        "chr6_mann_hap4",
                        "chr6_mcf_hap5",
                        "chr6_qbl_hap6",
                        "chr6_ssto_hap7",
                        "chr7",
                        "chr7_gl000195_random",
                        "chr8",
                        "chr8_gl000196_random",
                        "chr8_gl000197_random",
                        "chr9",
                        "chr9_gl000198_random",
                        "chr9_gl000199_random",
                        "chr9_gl000200_random",
                        "chr9_gl000201_random",
                        "chr10",
                        "chr11",
                        "chr11_gl000202_random",
                        "chr12",
                        "chr13",
                        "chr14",
                        "chr15",
                        "chr16",
                        "chr17",
                        "chr17_ctg5_hap1",
                        "chr17_gl000203_random",
                        "chr17_gl000204_random",
                        "chr17_gl000205_random",
                        "chr17_gl000206_random",
                        "chr18",
                        "chr18_gl000207_random",
                        "chr19",
                        "chr19_gl000208_random",
                        "chr19_gl000209_random",
                        "chr20",
                        "chr21",
                        "chr21_gl000210_random",
                        "chr22",
                        "chrX",
                        "chrY",
                        "chrUn_gl000211",
                        "chrUn_gl000212",
                        "chrUn_gl000213",
                        "chrUn_gl000214",
                        "chrUn_gl000215",
                        "chrUn_gl000216",
                        "chrUn_gl000217",
                        "chrUn_gl000218",
                        "chrUn_gl000219",
                        "chrUn_gl000220",
                        "chrUn_gl000221",
                        "chrUn_gl000222",
                        "chrUn_gl000223",
                        "chrUn_gl000224",
                        "chrUn_gl000225",
                        "chrUn_gl000226",
                        "chrUn_gl000227",
                        "chrUn_gl000228",
                        "chrUn_gl000229",
                        "chrUn_gl000230",
                        "chrUn_gl000231",
                        "chrUn_gl000232",
                        "chrUn_gl000233",
                        "chrUn_gl000234",
                        "chrUn_gl000235",
                        "chrUn_gl000236",
                        "chrUn_gl000237",
                        "chrUn_gl000238",
                        "chrUn_gl000239",
                        "chrUn_gl000240",
                        "chrUn_gl000241",
                        "chrUn_gl000242",
                        "chrUn_gl000243",
                        "chrUn_gl000244",
                        "chrUn_gl000245",
                        "chrUn_gl000246",
                        "chrUn_gl000247",
                        "chrUn_gl000248",
                        "chrUn_gl000249",
                        "chrM"]
    hg19chrLengths =   {"chr1":249250621,
                        "chr1_gl000191_random":106433,
                        "chr1_gl000192_random":547496,
                        "chr2":243199373,
                        "chr3":198022430,
                        "chr4":191154276,
                        "chr4_ctg9_hap1":590426,
                        "chr4_gl000193_random":189789,
                        "chr4_gl000194_random":191469,
                        "chr5":180915260,
                        "chr6":171115067,
                        "chr6_apd_hap1":4622290,
                        "chr6_cox_hap2":4795371,
                        "chr6_dbb_hap3":4610396,
                        "chr6_mann_hap4":4683263,
                        "chr6_mcf_hap5":4833398,
                        "chr6_qbl_hap6":4611984,
                        "chr6_ssto_hap7":4928567,
                        "chr7":159138663,
                        "chr7_gl000195_random":182896,
                        "chr8":146364022,
                        "chr8_gl000196_random":38914,
                        "chr8_gl000197_random":37175,
                        "chr9":141213431,
                        "chr9_gl000198_random":90085,
                        "chr9_gl000199_random":169874,
                        "chr9_gl000200_random":187035,
                        "chr9_gl000201_random":36148,
                        "chr10":135534747,
                        "chr11":135006516,
                        "chr11_gl000202_random":40103,
                        "chr12":133851895,
                        "chr13":115169878,
                        "chr14":107349540,
                        "chr15":102531392,
                        "chr16":90354753,
                        "chr17":81195210,
                        "chr17_ctg5_hap1":1680828,
                        "chr17_gl000203_random":37498,
                        "chr17_gl000204_random":81310,
                        "chr17_gl000205_random":174588,
                        "chr17_gl000206_random":41001,
                        "chr18":78077248,
                        "chr18_gl000207_random":4262,
                        "chr19":59128983,
                        "chr19_gl000208_random":92689,
                        "chr19_gl000209_random":159169,
                        "chr20":63025520,
                        "chr21":48129895,
                        "chr21_gl000210_random":27682,
                        "chr22":51304566,
                        "chrX":155270560,
                        "chrY":59373566,
                        "chrUn_gl000211":166566,
                        "chrUn_gl000212":186858,
                        "chrUn_gl000213":164239,
                        "chrUn_gl000214":137718,
                        "chrUn_gl000215":172545,
                        "chrUn_gl000216":172294,
                        "chrUn_gl000217":172149,
                        "chrUn_gl000218":161147,
                        "chrUn_gl000219":179198,
                        "chrUn_gl000220":161802,
                        "chrUn_gl000221":155397,
                        "chrUn_gl000222":186861,
                        "chrUn_gl000223":180455,
                        "chrUn_gl000224":179693,
                        "chrUn_gl000225":211173,
                        "chrUn_gl000226":15008,
                        "chrUn_gl000227":128374,
                        "chrUn_gl000228":129120,
                        "chrUn_gl000229":19913,
                        "chrUn_gl000230":43691,
                        "chrUn_gl000231":27386,
                        "chrUn_gl000232":40652,
                        "chrUn_gl000233":45941,
                        "chrUn_gl000234":40531,
                        "chrUn_gl000235":34474,
                        "chrUn_gl000236":41934,
                        "chrUn_gl000237":45867,
                        "chrUn_gl000238":39939,
                        "chrUn_gl000239":33824,
                        "chrUn_gl000240":41933,
                        "chrUn_gl000241":42152,
                        "chrUn_gl000242":43523,
                        "chrUn_gl000243":43341,
                        "chrUn_gl000244":39929,
                        "chrUn_gl000245":36651,
                        "chrUn_gl000246":38154,
                        "chrUn_gl000247":36422,
                        "chrUn_gl000248":39786,
                        "chrUn_gl000249":38502,
                        "chrM":16571}
    temp = 0
    hg19chrOffsets =    {}
    for c,p in hg19chrLengths.iteritems():
        hg19chrOffsets[c] = temp
        temp += p
    
    @staticmethod
    def standardizeChromosome(text, build):
        '''
        Forces the chromosome into "chr##" format; returns None if the chromosome is unknown
        '''
        if not text.startswith("chr"):
            if text.startswith("CHR"):
                text = text.lower()
            else:
                text = "chr" + text
        if build == genomeUtils.hg19:
            if not genomeUtils.hg19chrOffsets.has_key(text):
                text = None
        elif build == genomeUtils.hg18:
            if not genomeUtils.hg18chrOffsets.has_key(text):
                text = None
        else:
            raise Exception('Unknown build: %s' % str(build))
        return text
    
    @staticmethod
    def standardizePosition(position, build):
        '''
        If needed, converts position to the latest build (currently hg19), returns a tuple of (hg19 position, genome position)
        where genome position is the added length of all chromosomes before it. The chromosome parameter should have come
        from genomeUtils.standardizeChromosome()
        '''
        if build != genomeUtils.hg19:
            raise Exception("Only hg19 is currently supported.")
            # TODO: wrap liftover?
        return int(position)
    
    @staticmethod
    def getGlobalPosition(chromosome, position, build):
        if build != genomeUtils.hg19:
            raise Exception("Only hg19 is currently supported.")
        if position > genomeUtils.hg19chrLengths[chromosome]:
            raise Exception("You've got a genome position %s off the charts!" % str(position))
        return position+genomeUtils.hg19chrOffsets[chromosome]
    
    @staticmethod
    def getChromosomes(build):
        if build == genomeUtils.hg19:
            return genomeUtils.hg19chrOrder
        else:
            raise Exception('Unknown build: %s' % str(build))

class variantFile:
    def __init__(self, path):
        self.comments = []
        
        self.variantAttributes = {}
        self.variantAttributeOrder = []
        self.chrAttribute = None
        self.chrAttributeIndex = None
        self.posAttribute = None
        self.posAttributeIndex = None
        self.idAttribute = None
        self.idAttributeIndex = None
        
        self.genotypeAttributes = {}
        self.genotypeAttributeOrder = []
        
        self.path = path
        self.extension = os.path.splitext(path).lower()
        self.totalSize = os.path.getsize(path)
        self.lengthEstimate = None
        
        if self.extension == ".cvf":
            self._extractCvfFileInfo(path)
        elif self.extension == ".csv":
            self._extractCsvFileInfo(path)
        elif self.extension == ".vcf":
            self._extractVcfFileInfo(path)
        elif self.extension == ".gvf":
            self._extractGvfFileInfo(path)
    
    def __iter__(self):
        if self.extension == ".cvf":
            return self.readCvfLines()
        elif self.extension == ".csv":
            return self.readCsvLines()
        elif self.extension == ".vcf":
            return self.readVcfLines()
        elif self.extension == ".gvf":
            return self.readGvfLines()
    
    # ******** CVF format ********
    class cvfAttributeDetails:
        CHR=0
        POS=1
        ID=2
        NUMERIC=3
        CATEGORICAL=4
        MIXED=5
        IGNORE=6
        def __init__(self, columnType, low=None, high=None, values=None):
            self.columnType = columnType
            self.low = low
            self.high = high
            self.values = values
    
    def _extractCvfFileInfo(self):
        infile = open(self.path, 'r')
        readHeader = False
        headerChars = 0
        for line in infile:
            if len(line.strip()) <= 1:
                headerChars += len(line)
                continue
            elif line.startswith("##"):
                headerChars += len(line)
                self.comments.append(line[2:].strip())
            elif line.startswith("#"):
                headerChars += len(line)
                columns = line[1:-1].split('/t')
                headerName = columns[0].strip()
                if headerName == variantFile.GENOME_POSITION:
                    raise Exception("Cannot use reserved %s as column header." % variantFile.GENOME_POSITION)
                elif columns[1] == "CHR":
                    if self.chrAttribute != None:
                        raise Exception("More than one CHR column: %s and %s" % (self.chrAttribute,headerName))
                    if self.variantAttributes.has_key(headerName):
                        raise Exception("Duplicate column header: %s" % headerName)
                    self.chrAttribute = headerName
                    self.variantAttributes[headerName] = variantFile.cvfAttributeDetails(variantFile.cvfAttributeDetails.CHR)
                elif columns[1] == "POS":
                    if self.posAttribute != None:
                        raise Exception("More than one POS column: %s and %s" % (self.posAttribute,headerName))
                    if self.variantAttributes.has_key(headerName):
                        raise Exception("Duplicate column header: %s" % headerName)
                    self.posAttribute = headerName
                    self.variantAttributes[headerName] = variantFile.cvfAttributeDetails(variantFile.cvfAttributeDetails.POS)
                elif columns[1] == "ID":
                    if self.posAttribute != None:
                        raise Exception("More than one ID column: %s and %s" % (self.posAttribute,headerName))
                    if self.variantAttributes.has_key(headerName):
                        raise Exception("Duplicate column header: %s" % headerName)
                    self.posAttribute = headerName
                    self.variantAttributes[headerName] = variantFile.cvfAttributeDetails(variantFile.cvfAttributeDetails.ID)
                elif columns[1] == "IGNORE":
                    if self.variantAttributes.has_key(headerName):
                        raise Exception("Duplicate column header: %s" % headerName)
                    self.variantAttributes[headerName] = variantFile.cvfAttributeDetails(variantFile.cvfAttributeDetails.IGNORE)
                elif columns[1] == "NUMERIC":
                    if self.variantAttributes.has_key(headerName):
                        raise Exception("Duplicate column header: %s" % headerName)
                    self.variantAttributes[headerName] = variantFile.cvfAttributeDetails(variantFile.cvfAttributeDetails.NUMERIC, low=float(columns[2]), high=float(columns[3]))
                elif columns[1] == "CATEGORICAL":
                    if self.variantAttributes.has_key(headerName):
                        raise Exception("Duplicate column header: %s" % headerName)
                    self.variantAttributes[headerName] = variantFile.cvfAttributeDetails(variantFile.cvfAttributeDetails.CATEGORICAL, values=columns[2:])
                elif columns[1] == "MIXED":
                    if self.variantAttributes.has_key(headerName):
                        raise Exception("Duplicate column header: %s" % headerName)
                    self.variantAttributes[headerName] = variantFile.cvfAttributeDetails(variantFile.cvfAttributeDetails.MIXED, low=float(columns[2]), high=float(columns[3]), values=columns[4:])
                else:
                    raise Exception("Unknown .cvf column type: %s" % self.type)
                self.variantAttributes[columns[1]] = variantFile.cvfAttributeDetails(columns[2:])
                self.variantAttributeOrder.append(columns[1])
            elif not readHeader:
                headerChars += len(line)
                columns = line[:-1].split('/t')
                for i,c in enumerate(columns):
                    if not self.variantAttributes.has_key(c):
                        raise Exception("Missing meta line for column %s" % c)
                    if c == self.chrAttribute:
                        self.chrAttributeIndex = i
                    elif c == self.posAttribute:
                        self.posAttributeIndex = i
                    elif c == self.idAttribute:
                        self.idAttributeIndex = i
                for c in self.variantAttributeOrder:
                    if not c in columns:
                        raise Exception("The header %s is missing" % c)
                readHeader = True
            else:
                self.lengthEstimate = (self.totalSize-headerChars)/len(line)
                if self.chrAttribute == None or self.chrAttributeIndex == None:
                    raise Exception('Missing required CHR column')
                elif self.posAttribute == None or self.posAttributeIndex == None:
                    raise Exception('Missing required POS column')
                break
        infile.close()
    
    def readCvfLines(self):
        infile = open(self.path,'r')
        readHeader = False
        for line in infile:
            if line.startswith("#") or len(line.strip()) <= 1:
                continue
            elif not readHeader:
                readHeader = True
                continue
            else:
                columns = line[:-1].split('/t')
                if len(columns) != len(self.variantAttributeOrder):
                    raise Exception("Mismatch in number of columns:\n%s\n%s" % (str(self.variantAttributeOrder),str(columns)))
                columns[self.chrAttributeIndex] = genomeUtils.standardizeChromosome(columns[self.chrAttributeIndex], genomeUtils.hg19)
                columns[self.posAttributeIndex] = genomeUtils.standardizePosition(columns[self.posAttributeIndex], genomeUtils.hg19)
                if self.idAttributeIndex != None:
                    if columns[self.idAttributeIndex] == "." or columns[self.idAttributeIndex] == "":
                        columns[self.idAttributeIndex] = "%s_%i" % (columns[self.chrAttributeIndex],columns[self.posAttributeIndex])
                
                for i,c in enumerate(columns):
                    if i == self.chrAttributeIndex or i == self.posAttributeIndex or i == self.idAttributeIndex:
                        continue
                    if c.strip() == "":
                        columns[i] = 'Missing'
                
                #yield dict(zip(self.variantAttributeOrder,columns))
                yield (columns,genomeUtils.getGlobalPosition(columns[self.chrAttributeIndex],columns[self.posAttributeIndex],genomeUtils.hg19))
        infile.close()
    
    def composeCvfHeader(self):
        raise Exception('writing .cvf not implemented yet')
    
    def composeCvfLine(self, variant):
        raise Exception('writing .cvf not implemented yet')
    
    # ******** CSV format ********
    def _extractCsvFileInfo(self, path):
        raise Exception('.csv not supported')
    
    def readCsvLines(self):
        raise Exception('.csv not supported')
    
    def composeCsvHeader(self):
        raise Exception('.csv not supported')
    
    def composeCsvLine(self, variant):
        raise Exception('.csv not supported')
    
    # ******** VCF format ********
    def _extractVcfFileInfo(self, path):
        raise Exception('.vcf not supported')
    
    def readVcfLines(self):
        raise Exception('.vcf not supported')
    
    def composeVcfHeader(self):
        raise Exception('.vcf not supported')
    
    def composeVcfLine(self, variant):
        raise Exception('.vcf not supported')
    
    # ******** GVF format ********
    def _extractGvfFileInfo(self, path):
        raise Exception('.gvf not supported')
    
    def readGvfLines(self):
        raise Exception('.gvf not supported')
    
    def composeGvfHeader(self):
        raise Exception('.gvf not supported')
    
    def composeGvfLine(self, variant):
        raise Exception('.gvf not supported')
        

class feature(Interval):
    def __init__(self, chromosome, start, end=None, name=None, build=genomeUtils.hg19, strand=None, attributes={}):
        '''
        Create a genome feature that spans [start,stop) of chromosome in build (using 0-based BED coordinates)
        '''
        temp = genomeUtils.standardizeChromosome(chromosome,build)
        if temp == None:
            raise Exception('Invalid Chromosome: %s' % chromosome)
        chromosome = temp
        
        start,self.genomeStart = genomeUtils.standardizePosition(chromosome, start, build)
        if end == None:    # assume that the size is only 1 bp
            end = start+1
            self.genomeEnd = self.genomeStart+1
        else:
            end,self.genomeEnd = genomeUtils.standardizePosition(chromosome, end, build)
        
        self.hashCode = "%s_%i_%i" % (chromosome,start,end)
        
        if name==None:
            self.name = self.hashCode
        else:
            self.name = name
        
        self.build = build
        self.strand = strand
        self.attributes = attributes
        
        Interval.__init__(self, start=start, end=end, value=self.attributes, chrom=chromosome, strand=strand)
        
        # I use these objects for nested structures such as exons inside a gene, etc
        self.queryObjects = set()
        self.children = set()
    
    def applyMask(self,mask):
        collisions = mask.chromosomes[self.chrom].find(self.start,self.end)
        if len(collisions) == 0:
            return [self]
        else:
            newBounds = [(self.start,self.end)]
            for c in collisions:
                for i,(s,e) in enumerate(newBounds):
                    if s >= e:  # ignore stuff that's size zero or less 
                        continue
                    if s < c.end and c.start < e:   # guarantees overlap
                        if e > c.end:   # we have a bit of me at the top surviving beyond this collision
                            if s < c.start: # is there a piece at the bottom too (e.g. am i splitting into two pieces)?
                                newBounds.append((e,max(c.end)))
                            else:   # otherwise just modify in place
                                newBounds[i] = (e,max(c.end))
                        if s < c.start: # just a piece at the bottom surviving
                            newBounds[i] = (s,min(e,c.start))
            results = []
            for s,e in sorted(newBounds):
                if s >= e:
                    continue
                results.append(feature(chromosome=self.chrom, start=s, end=e, name=self.name, build=self.build, strand=self.strand, attributes=self.attributes))
            return results
    
    def contains(self, chromosome, position):
        return self.chrom == chromosome and position >= self.start and position < self.end
    
    def overlaps(self, otherFeature):
        return self.chrom == otherFeature and not self.start < otherFeature.end and otherFeature.start < self.end
    
    def addChild(self, c):
        assert c.chrom == self.chrom
        if c in self.children:
            return
        self.children.add(c)
        for q in self.queryObjects:
            q.addFeature(c)
    
    @staticmethod
    def numXYMCompare(x, y):
        if x.chrom == y.chrom:
            return feature.positionCompare(x,y)
        else:
            return genomeUtils.hg19chrOrder.index(x.chrom)-genomeUtils.hg19chrOrder.index(y.chrom)
    @staticmethod
    def unixCompare(x, y):
        if x.chrom == y.chrom:
            return feature.positionCompare(x,y)
        if x.chrom > y.chrom:
            return 1;
        else:
            return -1
    @staticmethod
    def positionCompare(x,y):
        return x.start-y.start
    
    def __hash__(self):
        return self.genomeStart + self.genomeStop
    
    def __eq__(self, other):
        if self.hashCode == other.hashCode:
            return True
        else:
            return False
    
    def __ne__(self, other):
        return not self.__eq__(other)

class featureSet():
    def __init__(self, build=genomeUtils.hg19):
        self.chromosomes = {}
        for c in genomeUtils.getChromosomes(build):
            self.chromosomes[c] = IntervalTree()
    
    def addFeature(self, f):
        self.chromosomes[f.chrom].insert_interval(f)
        for c in f.children:
            self.chromosomes[f.chrom].insert_interval(c)
    
    def contains(self, chromosome, position):
        temp = self.chromosomes[chromosome].find(position,position+1)
        return len(temp) > 0

class featureLoadingParameters:
    """
        An object for specifying what we care about when parsing a .bed or .gff3 feature file
    """
    def __init__(self,
                 build=genomeUtils.hg19,
                 passFunction=None,
                 rejectFunction=None,
                 callbackArgs={},
                 tickFunction=None,
                 tickInterval=10,
                 mask=None,
                 attributesToInclude={},
                 returnFileObject=False):
        """
        :param passFunction:
            function or None
            
            This function will be called for every feature that passes all criteria,
            with the feature as the first argument and callbackArgs as **kwargs
            
        :param rejectFunction:
            function or None
            
            This function will be called for every feature that fails at least one
            criteria or is masked, with the feature as the first argument and callbackArgs as **kwargs
        
        :param tickFunction:
            function or None
            
            This function will be called approximately every tickInterval percent of the way through the file;
            this is useful for progress bars, etc. As this relies on an estimate, it is certainly possible to have
            more or less ticks than expected; for example, if tickInterval is 5 (i.e. 5%), there could be 21 or 19
            (or even more or less) total calls to tickFunction(). There would be approximately 20 total calls, but
            this is an estimate.
            
        :param mask:
            featureSet or None
            
            Only include features outside the masked regions. If a feature is partially in and out of the mask, it
            will be clipped. Set to None to include features anywhere.
            
        :param attributesToInclude:
            dict {string:valueFilter} or None
            
            This should be a dict containing strings mapped to valueFilter
            objects (where the string matches a column name per the appropriate specification:
            .bed: "name", "score", "strand" ... (see http://genome.ucsc.edu/FAQ/FAQformat.html#format1)
            .gff3: "seqid", "source", "type" ... or any key in the "attribute" column (see http://www.sequenceontology.org/gff3.shtml)
            Note that only attributes specified here will be extracted from the file. Set to None to extract all attributes.
        """
        self.build=build
        self.passFunction=passFunction
        self.rejectFunction=rejectFunction
        self.callbackArgs=callbackArgs
        self.tickFunction=tickFunction
        self.tickInterval=tickInterval
        self.mask=mask
        self.attributesToInclude=attributesToInclude
        self.returnFileObject=returnFileObject

class featureFile:
    def __init__(self, fileAttributes):
        self.regions = featureSet()
        self.fileAttributes = None
    
    @staticmethod
    def extractBedFileInfo(path):
        fileAttributes = recursiveDict()
        fileAttributes['browser'] = []
        fileAttributes['track'] = {}
        
        infile = open(path,'r')
        for line in infile:
            line = line.strip()
            if len(line) <= 1 or line.startswith('#'):
                continue
            lowerLine = line.lower()
            if lowerLine.startswith('browser'):
                fileAttributes['browser'].append(line[8:].split())
            elif lowerLine.startswith('track'):
                for c in line.split():
                    if c == 'track':
                        continue
                    temp = c.split('=')
                    fileAttributes['track'][temp[0]] = temp[1]
            else:
                break   # we're in to real data now
        infile.close()
        return fileAttributes
    
    @staticmethod
    def parseBedFile(path,parameters):
        fileAttributes = featureFile.extractBedFileInfo(path)
        
        if parameters.returnFileObject:
            newFileObject = featureFile(fileAttributes)
            newFileObject.fileAttributes = fileAttributes
        
        bedColumns = ['thickStart','thickEnd','itemRgb','blockCount','blockSizes','blockStarts']
        if fileAttributes['track'].get('type',None) == 'bedDetail':
            bedColumns.append('ID')
            bedColumns.append('description')
        
        fileObject = open(path,'r')
        for line in fileObject:
            lowerLine = line.lower().strip()
            if len(lowerLine) <= 1 or lowerLine.startswith('#') or lowerLine.startswith('browser') or lowerLine.startswith('track'):
                continue
            
            columns = line.split()
            
            if len(columns) <= 3:
                name = None
            else:
                name = columns[3]
            
            if len(columns) <= 4:
                attributes = {'score':1000}
            else:
                attributes = {'score':int(columns[4])}
            
            if len(columns) <= 5:
                strand = None
            else:
                strand = columns[5]
            
            for i,header in enumerate(bedColumns):
                if i >= len(columns):
                    break
                attributes[header] = columns[i]
            
            poisoned = False
            if parameters.attributesToInclude != None:
                attsToDel = set()
                for att,val in attributes.iteritems():
                    if not parameters.attributesToInclude.has_key(att):
                        attsToDel.add(att)
                    else:
                        if not parameters.attributesToInclude[att].isValid(val):
                            poisoned = True
                for att in attsToDel:
                    del attributes[att]
            
            tempFeature = feature(chromosome=columns[0], start=columns[1], end=columns[2], name=name, build=parameters.build, strand=strand, attributes=attributes)
            
            if parameters.mask != None:
                newFeatures = tempFeature.applyMask(parameters.mask)
            else:
                newFeatures = [tempFeature]
            
            if poisoned and parameters.rejectFunction != None:
                for f in newFeatures:
                    parameters.rejectFunction(f)
            elif not poisoned and parameters.passFunction != None:
                for f in newFeatures:
                    parameters.passFunction(f)
            if not poisoned and parameters.returnFileObject:
                for f in newFeatures:
                    newFileObject.regions.addFeature(f)
        fileObject.close()
        
        if parameters.returnFileObject:
            return newFileObject
        else:
            return
