import sys, math, re
from structures import recursiveDict

####################
# Helper constants #
####################
class genomeUtils:
    # Chromosome lengths for NCBI build 36 / hg18
    hg18           =   0
    hg18chrOrder   =   ["chr1",
                        "chr1_random",
                        "chr2",
                        "chr2_random",
                        "chr3",
                        "chr3_random",
                        "chr4",
                        "chr4_random",
                        "chr5",
                        "chr5_h2_hap1",
                        "chr5_random",
                        "chr6",
                        "chr6_cox_hap1",
                        "chr6_qbl_hap2",
                        "chr6_random",
                        "chr7",
                        "chr7_random",
                        "chr8",
                        "chr8_random",
                        "chr9",
                        "chr9_random",
                        "chr10",
                        "chr10_random",
                        "chr11",
                        "chr11_random",
                        "chr12",
                        "chr13",
                        "chr13_random",
                        "chr14",
                        "chr15",
                        "chr15_random",
                        "chr16",
                        "chr16_random",
                        "chr17",
                        "chr17_random",
                        "chr18",
                        "chr18_random",
                        "chr19",
                        "chr19_random",
                        "chr20",
                        "chr21",
                        "chr21_random",
                        "chr22",
                        "chr22_h2_hap1",
                        "chr22_random",
                        "chrX",
                        "chrX_random",
                        "chrY",
                        "chrM"]
    hg18chrLengths =   {"chr1":247249719,
                        "chr1_random":1663265,
                        "chr2":242951149,
                        "chr2_random":185571,
                        "chr3":199501827,
                        "chr3_random":749256,
                        "chr4":191273063,
                        "chr4_random":842648,
                        "chr5":180857866,
                        "chr5_h2_hap1":1794870,
                        "chr5_random":143687,
                        "chr6":170899992,
                        "chr6_cox_hap1":4731698,
                        "chr6_qbl_hap2":4565931,
                        "chr6_random":1875562,
                        "chr7":158821424,
                        "chr7_random":549659,
                        "chr8":146274826,
                        "chr8_random":943810,
                        "chr9":140273252,
                        "chr9_random":1146434,
                        "chr10":135374737,
                        "chr10_random":113275,
                        "chr11":134452384,
                        "chr11_random":215294,
                        "chr12":132349534,
                        "chr13":114142980,
                        "chr13_random":186858,
                        "chr14":106368585,
                        "chr15":100338915,
                        "chr15_random":784346,
                        "chr16":88827254,
                        "chr16_random":105485,
                        "chr17":78774742,
                        "chr17_random":2617613,
                        "chr18":76117153,
                        "chr18_random":4262,
                        "chr19":63811651,
                        "chr19_random":301858,
                        "chr20":62435964,
                        "chr21":46944323,
                        "chr21_random":1679693,
                        "chr22":49691432,
                        "chr22_h2_hap1":63661,
                        "chr22_random":257318,
                        "chrX":154913754,
                        "chrX_random":1719168,
                        "chrY":57772954,
                        "chrM":16571}
    temp = 0
    hg18chrOffsets =    {}
    for c,p in hg18chrLengths.iteritems():
        hg18chrOffsets[c] = temp
        temp += p
    
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
    def standardizePosition(chromosome, position, build):
        '''
        If needed, converts position to the latest build (currently hg19), returns a tuple of (hg19 position, genome position)
        where genome position is the added length of all chromosomes before it. The chromosome parameter should have come
        from genomeUtils.standardizeChromosome()
        '''
        position = int(position)
        if build == genomeUtils.hg18:
            raise Exception("hg18 is not supported yet.")
            # TODO: wrap liftover?
        return (position,position+genomeUtils.hg19chrOffsets[chromosome])

class parseException(Exception):
    pass
    
####################
# Helper functions #
####################


##################
# Helper classes #
##################

class allele:
    STRICT = 0
    FLEXIBLE = 1
    UNENFORCED = 2
    """
    Wrapper for allele text; allows different comparison approaches:

    * STRICT:
      Variants will only be considered equal if their chromosome, position,
      reference and all alternate alleles match and have the same configuration
      (e.g. REF = A, ALT = G,GT would not match
      REF = A, ALT=GT,G or REF = G, ALT=A,GT)
    * FLEXIBLE (slowest):
      Variants will be considered equal if their chromosome, position,
      at least two reference or alternate alleles match, but the REF/ALT
      configuration may differ, and allele comparisons allow regular expressions
      per python's re module syntax. In the future, this option will also
      allow flexibility in position for INDELs
    * UNENFORCED:
      Variants will be considered equal if their chromosome and position is
      the same, regardless of alleles
    """
    
    def __init__(self, text, matchMode, attemptRepairsWhenComparing):
        self.text = text
        self.matchMode
        self.attemptRepairsWhenComparing = attemptRepairsWhenComparing
    
    def __eq__(self, other):
        assert self.matchMode == other.matchMode
        if self.matchMode == self.UNENFORCED:
            return True
        elif self.matchMode == self.STRICT:
            return self.text == other.text
        elif self.text == None or other.text == None:
            return self.text == None and other.text == None
        elif re.match(self.text,other.text) != None:
            if self.attemptRepairsWhenComparing:
                # self.text has the more general regex; update to the more specific information
                self.text = other.text
            return True
        elif re.match(other.text,self.text) != None:
            if self.attemptRepairsWhenComparing:
                # other.text has the more general regex; update to the more specific information
                other.text = self.text
            return True
        return False
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __str__(self):
        return "" if self.text == None else self.text

class genotype:
    """
    An object that converts the original 0/1 style text from a .vcf file to two text alleles
    
    For example, if:
    REF = A
    ALT = G,T,ATTTAG
    
    0|3 would yield a genotype object where:
    allele1 = A
    allele2 = ATTTAG
    isPhased = True
    """
    # TODO: support non-diploid genotypes (e.g. Y, other organisms...)
    def __init__(self, text, alleles, matchMode):
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
            self.allele1 = alleles[int(temp[0])]
        
        if temp[1] == ".":
            self.allele2 = None
        else:
            self.allele2 = alleles[int(temp[1])]
        
        self.attributes = {}
        self.matchMode = matchMode
    
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
    
    def __eq__(self, other):
        if other == None:
            return False
        assert self.matchMode == other.matchMode
        if self.matchMode == allele.UNENFORCED:
            return True
        elif self.matchMode == allele.STRICT:
            if self.allele1 == other.allele1 and self.allele2 == other.allele2:
                return True
            else:
                return False
        elif (self.allele1 == other.allele1 and self.allele2 == other.allele2) or (self.allele1 == other.allele2 and self.allele2 == other.allele1):
            return True
        else:
            return False
    
    def __ne__(self, other):
        return not self.__eq__(other)

class variant:
    """
    An object representing a variant (potentially with data from multiple sources)
    """
    def __init__(self, chromosome, position, matchMode, attemptRepairsWhenComparing, ref=".*", alt=".*", name=None, build=genomeUtils.hg19, attributeFilters=None):
        temp = genomeUtils.standardizeChromosome(chromosome, build)
        if temp == None:
            raise Exception('Invalid Chromosome: %s' % chromosome)
        self.chromosome = temp
        self.position,self.genomePosition = genomeUtils.standardizePosition(self.chromosome, position, build)
                
        self.matchMode = matchMode
        self.attemptRepairsWhenComparing = attemptRepairsWhenComparing
        
        if ref == ".":
            ref = None
        
        self.alleles = [allele(ref, matchMode, attemptRepairsWhenComparing)]
        if isinstance(alt,list):
            for a in alt:
                if a == ".":
                    a = None
                self.alt.append(allele(a, matchMode, attemptRepairsWhenComparing))
        else:
            if alt == ".":
                alt = None
            self.alt.append(allele(alt, matchMode, attemptRepairsWhenComparing))
        
        self.basicName = "%s_%i" % (self.chromosome,self.start)
        if name == None or name == ".":
            name = self.basicName
        self.name = name
        
        self.attributeFilters = attributeFilters
        self.poisoned = False
        
        self.twins = set()
        self.attributes = {}
        self.genotypes = {}
    
    def addGenotype(self, individual, g):
        if self.poisoned:
            return
        
        if isinstance(g,str):
            g = genotype(g, self.alleles, self.matchMode, self.attemptRepairsWhenComparing)
        
        self.genotypes[individual] = g
        
        for t in self.twins:
            if not t.genotypes.has_key(individual):
                t.addGenotype(individual, g)
            else:
                assert t.genotypes[individual] == g
    
    def setAttribute(self, key, value):
        if self.poisoned:
            return
        if self.attributeFilters != None:
            if not self.attributeFilters.has_key(key):
                return
            if not self.attributeFilters[key].isValid(value):
                self.poison()
                return
        self.attributes[key] = value
        # it's really important to share last... if one of my twins is poisoned by this value, I don't want to try to add a value to None after that
        for t in self.twins:
            if not t.attributes.has_key(key):
                t.setAttribute(key, value)
            else:
                assert t.attributes[key] == value
    
    def poison(self):
        self.poisoned = True
        self.attributes = None
        self.genotypes = None
        
        # Make sure any objects that are for the same variant get filtered as well
        for t in self.twins:
            if not t.poisoned:
                t.poison()
    
    def euthanizeTwins(self):
        """
        A little cleanup function that can be called after a
        variant is added to a set or used as a dict key (probably
        isn't a huge deal unless variant objects from many
        sources are using all your memory).
        
        The idea is if I'm hanging on to a twin that no one else
        cares about, I should break that connection and let garbage
        collection eat him up.
        
        And you thought the parent-child relationships in trees
        were messed up.
        """
        twinsToKill = set()
        for t in self.twins:
            # 1 reference from self.twins, 1 reference as parameter to getrefcount, 1 reference from the in iterator
            # If someone else cares, he's safe - I only commit these atrocities when no one else is looking
            if sys.getrefcount(t) <= 3:
                twinsToKill.add(t)
        for t in twinsToKill:
            self.twins.discard(t)
            t.twins.discard(self)
    
    def __hash__(self):
        """
        This is a funky little nuance that essentially merges variant
        objects if they are used in a set or dict (provided that
        attemptRepairsWhenComparing is on); e.g.:
        
        1) A variant is added to a set()
        2) The same variant (with data from another source, but same
        chromosome and position and maybe alleles, depending on
        matchMode) is added to the same set.
        3) The set will hash the new variant instance to the same location
        4) As they're equal, the __eq__ function will share all the info
        between both objects
        5) When __eq__ finishes (returning True), the set will recognize
        that it already has the variant object, and throw the second one
        away
        """
        if self.attemptRepairsWhenComparing:
            return hash(self.basicName)
        else:
            return hash(self)
    
    def __eq__(self, other):
        """
        We want to say two variants are equal if their chromosome and position match AND
        two matches occur (involving both reference alleles) between variant objects
        """
        if not self.attemptRepairsWhenComparing or not other.attemptRepairsWhenComparing:
            return self is other    # only do the dance if we're both in the mood
        
        if other == None:
            return False
        assert self.matchMode != other.matchMode
        if self.chromosome != other.chromosome:
            return False
        elif self.start != other.start:
            return False
        elif self.matchMode == allele.UNENFORCED:
            self.repair(other)
            return True
        elif self.matchMode == allele.STRICT:
            if len(self.alleles) != len(other.alleles):
                return False
            for i,a in enumerate(self.alleles):
                if other.alleles[i] != a:
                    return False
            self.repair(other)
            return True
        else:
            numMatches = 0
            for a in self.alleles:
                if a in other.alleles:
                    numMatches += 1
                    # even though we only care about two matches here, we'll want to check all of them in order to match/repair allele regexes
            return numMatches >= 2
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    @staticmethod
    def numXYMCompare(x, y):
        if x.chromosome == y.chromosome:
            return variant.positionCompare(x,y)
        else:
            return genomeUtils.hg19chrOrder.index(x.chromosome)-genomeUtils.hg19chrOrder.index(y.chromosome)            
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
    
    def repair(self, other):
        """
        Attempt to update self and other's information.
        Note that matching based on alleles should already have happened if it
        matters - this may change the order of other's alleles to match self. For example:
        
        self:
        REF = A    ALT = G,AA
        other:
        REF = G    ALT = A,GA
        
        will result in this configuration:
        
        self:
        REF = A    ALT = G,AA,GA
        other:
        REF = A    ALT = G,AA,GA
        
        """
        # regardless of whether we want to attempt repairs, we should be poisoned if the other is, and vice-versa
        if self.poisoned:
            if not other.poisoned:
                other.poison()
        elif other.poisoned:
            self.poison()
        # even if we've been poisoned, we might still want to update rs numbers & alleles, so keep going
        
        # attempt to update names
        newName = None
        if self.name != self.basicName:
            newName = self.name
        if other.name != other.basicName:
            newName = other.name
        if newName != None and self.name != other.name:
            return
        
        # share as many possible alleles; note that the ordering of the second variant's allele
        # order will be changed to the first
        newAlleles = list(self.alleles)
        for a in other.alleles:
            if a not in newAlleles:
                newAlleles.append(a)
        
        if not self.poisoned:
            # update attributes
            newAttributes = self.exchangeAttributes(other)
            
            # update genotypes
            newGenotypes = self.exchangeGenotypes(other)
        
        # Okay, we've made it... update everything
        if newName != None:
            self.name = newName
            other.name = newName
        
        self.alleles = newAlleles
        other.alleles = newAlleles
        
        if not self.poisoned:
            self.attributes.update(newAttributes)
            other.attributes.update(newAttributes)
            
            self.genotypes.update(newGenotypes)
            other.genotypes.update(newGenotypes)
            
            # Keep track of this guy; he and I now share everything (including attributes, genotypes, and, of course, poison)
            self.twins.add(other)
            other.twins.add(self)
    
    def exchangeAttributes(self, other):
        newAttributes = {}
        
        for k,v in other.attributes.iteritems():
            if self.attributes.has_key(k):
                assert v == self.attributes[k]
            else:
                newAttributes[k] = v
        
        for k,v in self.attributes.iteritems():
            if other.attributes.has_key(k):
                assert v == other.attributes[k]
            else:
                newAttributes[k] = v
        return newAttributes
    
    def exchangeGenotypes(self, other):
        newGenotypes = {}
        
        for k,v in other.genotypes.iteritems():
            if self.genotypes.has_key(k):
                assert v == self.genotypes[k]
            else:
                newGenotypes[k] = v
        
        for k,v in self.genotypes.iteritems():
            if other.genotypes.has_key(k):
                assert v == other.genotypes[k]
            else:
                newGenotypes[k] = v
        
        return newGenotypes
    
    def isPolymorphic(self):
        temp = genotype("./.", alleles=[], matchMode=allele.UNENFORCED, attemptRepairsWhenComparing=False)
        setFirst = False
        for g in self.genotypes.itervalues():
            if not setFirst:
                temp.allele1 = g.allele1
                temp.allele2 = g.allele2
                temp.matchMode = g.matchMode
                setFirst = True
                continue
            if temp != g:
                return True
        return False

class valueFilter:
    """
    Applies a filter (categorical, numeric, and/or allow/exclude special values)
    to any attribute from a .csv or .vcf file. These modes can be mixed, and
    can be lists; e.g. using both:
    
    values=['PASS','FSFilter']
    ranges=[(0.0,0.25),(0.75,1.0)]
    
    at the same time is okay. Of course, lists are not necessary; these are also
    legitimate parameters:
    
    values='PASS'
    ranges=(0.0,0.25)
    
    Incoming values to isValid will be compared
    against the appropriate criteria. isValid also attempts to handle nested values;
    e.g. some variants have multiple alternate alleles, and consequently there
    are occasional multiple
    values in the AF INFO field. This class assumes that the same filter applies
    to all values equally (otherwise you really should be splitting them up into
    separate attributes anyway, right?). In the event a value is in fact a list,
    if listMode is LIST_INCLUSIVE, it will allow the value if at least one of
    its values fits the criteria of the filter. If listMode is LIST_EXCLUSIVE,
    it will fail a value if even one of the list fails.
    """
    
    LIST_INCLUSIVE = 0
    LIST_EXCLUSIVE = 1
    def __init__(self, values=None, ranges=None, includeNone=True, includeInf=True, includeNaN=True, includeInvalid=True, listMode=LIST_INCLUSIVE):
        self.values = values
        self.multiValue = isinstance(self.values,list)
        self.ranges = ranges
        self.multiRange = isinstance(self.ranges,list)
        self.includeAllValid = values == None and ranges == None
        self.includeNone = includeNone
        self.includeInf = includeInf
        self.includeNaN = includeNaN
        self.includeInvalid = includeInvalid
        self.listMode = listMode
    
    def isValid(self, value):
        # this is an ugly hack to allow lists and sets, but not try to iterate over strings
        if not hasattr(value,'__iter__'):
            value = [value]
        
        if self.listMode == valueFilter.LIST_INCLUSIVE:
            for v in value:
                if self._isValid(v):
                    return True
            return False
        else:
            for v in value:
                if not self._isValid(v):
                    return False
            return True
    
    def _isValid(self, value):
        if value == None:
            return self.includeNone
        try:
            value = float(value)
            if math.isnan(value):
                return self.includeNaN
            elif math.isinf(value):
                return self.includeInf
            else:
                if self.includeAllValid:
                    return True
                elif self.multiRange:
                    for low,high in self.ranges:
                        if value >= low and value <= high:
                            return True
                    return False
                else:
                    return value >= self.ranges[0] and value <= self.ranges[1]
        except ValueError:
            if self.includeAllValid:
                return True
            elif self.multiValue:
                return value in self.values
            else:
                return value == self.values

class variantLoadingParameters:
    """
        An object for specifying what we care about when parsing a .vcf or .csv variant file
    """
    def __init__(self,
                 build=genomeUtils.hg19,
                 passFunction=None,
                 rejectFunction=None,
                 callbackArgs={},
                 individualsToInclude=[],
                 lociToInclude=None,
                 mask=None,
                 attributesToInclude=None,
                 skipGenotypeAttributes=False,
                 returnFileObject=False,
                 alleleMatching=allele.FLEXIBLE,
                 attemptRepairsWhenComparing=True):
        """
        :param passFunction:
            function
            
            This function will be called for every variant that passes all criteria,
            with the variant as the first argument and callbackArgs as **vargs
            
        :param rejectFunction:
            function
            
            This function will be called for every variant that fails at least one
            criteria or is masked, with the variant as the first argument and callbackArgs as **vargs
            
        :param individualsToInclude:
            list or None
            
            This should be a list containing the column headers corresponding
            to (and in the order of) individuals whose genotypes will be included. Note that if
            this is empty, no genotype information will be loaded. To include all individuals,
            set this to None.
            
        :param lociToInclude:
            set or None
            
            Only variants in this set will be included. Set this to None to include all loci.
            
        :param mask:
            genomeMask or None
            
            Only include variants outside the masked regions. Set to None to include variants anywhere.
            
        :param attributesToInclude:
            dict {string:valueFilter} or None
            
            This should be a dict containing strings mapped to valueFilter
            objects (where the string matches a column header in a .csv
            variant file, or "QUAL", "FILTER", or an INFO header from a
            .vcf file). Note that only attributes specified here will
            be extracted from the file. Set to None to extract all attributes.
            
        :param alleleMatching:
            One of allele.STRICT, allele.FLEXIBLE, or allele.UNENFORCED
            
            All variants generated will have this allele matching property; you should use the
            same mode for every variant in your program.
            
        :param attemptRepairsWhenComparing:
            bool
            
            Once two variants are identified as equal, enabling this option will
            attempt to make the objects equal (as if they had been merged into
            a single instance - even future updates to one will update the other).
            This can fail if there is conflicting data (leaving the variants separate
            objects without this dynamic updating, even though they will still be
            considered equivalent). Another nuance is that the order of REF/ALT
            allele configurations can not be guaranteed if variants from two
            .vcf files are compared but these orders differ.
        """
        self.passFunction = passFunction
        self.rejectFunction = rejectFunction
        self.callbackArgs = callbackArgs
        self.individualsToInclude = individualsToInclude
        self.lociToInclude = lociToInclude
        self.mask = mask
        self.attributesToInclude = attributesToInclude
        self.skipGenotypeAttributes = skipGenotypeAttributes
        self.returnFileObject = returnFileObject
        self.alleleMatching = alleleMatching
        self.attemptRepairsWhenComparing = attemptRepairsWhenComparing

class variantFile:
    def __init__(self):
        self.fileAttributes = None
        self.variants = set()
    
    def addVariant(self, v):
        self.variants.add(v)
        # after we've tried to add it
        v.euthanizeTwins()
    
    @staticmethod
    def extractVcfFileInfo(path):
        def parseVcfHeader(text):
            tempDict = {}
            lowerText = text.lower()
            for key in ["ID=","Type=","Number=","length="]: # TODO: there are more keys for contig... I'll need to revise anyway to better comply with the VCFv4.1 spec
                if key.lower() in lowerText:
                    temp = text[lowerText.find(key.lower()) + len(key):]
                    endClip = temp.find(",")
                    if endClip == -1:
                        endClip = temp.find("/")
                        if endClip == -1:
                            endClip = temp.find(">")
                            if endClip == -1:
                                endClip = len(temp)
                    temp = temp[:endClip]
                    tempDict[key[:-1]] = temp
            if 'description=' in lowerText:
                tempDict["Description"] = text.split("\"")[1]
            return tempDict
    
        fileAttributes = recursiveDict()
        fileAttributes['variant attributes'] = set(['FILTER','QUAL'])
        fileAttributes['genotype attributes'] = set()
        
        fileObj = open(path,'r')
        for line in fileObj:
            line = line.strip()
            if len(line) <= 1:
                continue
            elif line[0:2] == "##":
                line = line[2:]
                if line.startswith("FILTER"):
                    headerData = parseVcfHeader(line[8:-1])
                    fileAttributes["FILTER"][headerData["ID"]] = headerData
                elif line.startswith("INFO"):
                    headerData = parseVcfHeader(line[6:-1])
                    fileAttributes["INFO"][headerData["ID"]] = headerData
                    fileAttributes['variant attributes'].add(headerData["ID"])
                elif line.startswith("FORMAT"):
                    headerData = parseVcfHeader(line[8:-1])
                    fileAttributes["FORMAT"][headerData["ID"]] = headerData
                    fileAttributes['genotype attributes'].add(headerData["ID"])
                elif line.lower().startswith("fileformat"):
                    fileAttributes['file format'] = line[line.find("=")+1:]
                elif line.lower().startswith("contig"):
                    headerData = parseVcfHeader(line[8:-1])
                    fileAttributes['contig'][headerData["ID"]] = headerData
                else:
                    idstr = line[:line.find("=")]
                    value = line[line.find("=")+1:]
                    fileAttributes['file attributes'][idstr] = value
            elif line[0] == "#":
                # column headers - get individuals from this
                columns = line.split()
                fileAttributes["INDIVIDUALS"] = columns[9:]
            else:
                # reached real data; we're done
                break
        fileObj.close()
        # Set some defaults if they were missing
        if not fileAttributes.has_key("fileformat"):
            fileAttributes["fileformat"] = "VCFv4.1"
        if not fileAttributes.has_key("INFO"):
            fileAttributes["INFO"] = {}
        if not fileAttributes.has_key("FORMAT"):
            fileAttributes["FORMAT"] = {}
        if not fileAttributes.has_key("FILTER"):
            fileAttributes["FILTER"] = {}
        if not fileAttributes.has_key("contig"):
            fileAttributes["contig"] = {}
        return fileAttributes
        
    @staticmethod
    def parseVcfFile(path,parameters):
        fileAttributes = variantFile.extractVcfFileInfo(path)
        fileAttributes['loading parameters'] = parameters
        
        if parameters.returnFileObject:
            fileObject = variantFile(fileAttributes)
        
        inFile = open(path,'r')
        
        for line in inFile:
            line = line.strip()
            if len(line) <= 1 or line.startswith('#'):
                continue    # skip header and blank lines
            
            columns = line.split("\t")
            
            # Grab the basics (CHROM, POS, ID, REF, ALT)
            rsNumber=columns[2]
            if rsNumber == ".":
                rsNumber = None
            newVariant = variant(chromosome=columns[0],
                                 position=columns[1],
                                 matchMode=parameters.alleleMatching,
                                 attemptRepairsWhenComparing=parameters.attemptRepairsWhenComparing,
                                 ref=columns[3],
                                 alt=columns[4].split(","),
                                 name=rsNumber,
                                 build=parameters.build,
                                 attributeFilters=parameters.attributesToInclude)
            
            if parameters.lociToInclude != None and newVariant not in parameters.lociToInclude:
                newVariant.poison()
            if parameters.mask != None and parameters.mask.contains(newVariant):
                newVariant.poison()
            
            if not newVariant.poisoned: # don't bother loading anything else if we know we don't need to
                # Handle QUAL, FILTER, and INFO
                if paramters.attributesToInclude == None or parameters.attributesToInclude.has_key("QUAL"):
                    newVariant.setAttribute("QUAL", columns[5])
                if paramters.attributesToInclude == None or parameters.attributesToInclude.has_key("FILTER"):
                    filters = columns[6].split(';')
                    if len(filters) == 1:
                        filters = filters[0]
                    newVariant.setAttribute("FILTER", filters)
                
                # Add the INFO fields
                infoChunks = columns[7].split(";")
                for chunk in infoChunks:
                    if "=" in chunk:
                        temp = chunk.split("=")
                        key = temp[0]
                        value = temp[1]
                        if "," in value:
                            value = value.split(',')
                        if paramters.attributesToInclude == None or parameters.attributesToInclude.has_key(key):
                            newVariant.setAttribute(key,value)
                    else:
                        if paramters.attributesToInclude == None or parameters.attributesToInclude.has_key(chunk):
                            newVariant.setAttribute(chunk,chunk)
                
                # Now for genotypes - first let's figure out the columns we care about
                if (parameters.individualsToInclude == None or len(parameters.individualsToInclude) > 0) and fileAttributes.has_key("INDIVIDUALS"):
                    formatPattern = columns[8].split(":")
                    if len(formatPattern) > 0:
                        if formatPattern[0] != "GT":
                            raise parseException("Bad .vcf file (GT FORMAT field must exist and must be first):\n%s" % line)
                    for i,p in enumerate(fileAttributes["INDIVIDUALS"]):
                        if parameters.individualsToInclude != None and p not in parameters.individualsToInclude:
                            continue
                        temp = columns[9+i].split(":")
                        if len(temp) > len(formatPattern) and temp[0] != "./." and temp[0] != ".|.":
                            raise parseException("Bad .vcf file (too many values in FORMAT column):\n%s" % line)
                        
                        newGenotype = genotype(text=temp[0],
                                               alleles=newVariant.alleles,
                                               matchMode=parameters.alleleMatching)
                        if not parameters.skipGenotypeAttributes:
                            for i,a in enumerate(formatPattern):
                                if a == "GT":
                                    if temp[i] == "./." or temp[i] == ".|.":
                                        break
                                    continue
                                # It is possible to list FORMAT columns that only some individuals have data - I assume, however, that this must always be the last column?
                                if i < len(temp) and temp[i] != ".":
                                    newGenotype.attributes[a] = temp[i]
                        newVariant.addGenotype(p, newGenotype)
            
            # We've built the variant object... call the appropriate function if we need to
            if not newVariant.poisoned and parameters.passFunction != None:
                parameters.passFunction(newVariant,**parameters.callbackArgs)
            elif newVariant.poisoned and parameters.rejectFunction != None:
                parameters.rejectFunction(newVariant,**parameters.callbackArgs)
            
            # If we're storing this thing in a file, do that now
            if parameters.returnFileObject and not newVariant.poisoned:
                fileObject.addVariant(newVariant)
        inFile.close()
        
        # finally set the file attributes to match our parameters (you can get the original
        # details via an independent call to extractVcfFileInfo)
        if parameters.individualsToInclude != None:
            fileAttributes["INDIVIDUALS"] = parameters.individualsToInclude
        if parameters.attributesToInclude != None:
            attrsToDelete = fileAttributes['variant attributes'].difference(parameters.attributesToInclude.iterkeys())
            for a in attrsToDelete:
                fileAttributes['variant attributes'].discard(a)
                if a == "FILTER":
                    fileAttributes["FILTER"] = {}
                elif a != "QUAL":
                    del fileAttributes["INFO"][a]
        if parameters.skipGenotypeAttributes:
            fileAttributes["FORMAT"] = {}
            fileAttributes['genotype attributes'] = set()
        
        if parameters.returnFileObject:
            fileObject.fileAttributes = fileAttributes
            return fileObject
        else:
            return
    
    def writeVcfFile(self, path, sortMethod=None, includeScriptLine=True):
        if includeScriptLine:
            scriptNumber = 0
            while fileAttributes['file attributes'].has_key("compreheNGSive script %i" % scriptNumber):
                scriptNumber += 1
            fileAttributes['file attributes']["compreheNGSive script %i" % scriptNumber] = '"' + " ".join(sys.argv) + '"'
        
        if sortMethod == "UNIX":
            variantList = sorted(self.variants, cmp=variant.unixCompare)
        elif sortMethod == "NUMXYM":
            variantList = sorted(self.variants, cmp=variant.numXYMCompare)
        else:
            variantList = list(self.variants)
        
        fileObject=open(path,'w')
        fileObject.write(variantFile.composeVcfHeader(self.fileAttributes) + "\n")
        
        for v in variantList:
            fileObject.write(variantFile.composeVcfLine(v, self.fileAttributes) + "\n")
        fileObject.close()
    
    @staticmethod
    def composeVcfHeader(fileAttributes):
        outString = ""
        outString += "##fileformat=VCFv4.1\n"   # % fileAttributes.get("file format",'VCFv4.1')
        
        for k in ["FILTER","INFO","FORMAT",'file attributes',"contig"]: # TODO: rearrange?
            if k == 'file attributes':
                for k2,v2 in fileAttributes['file attributes'].iteritems():
                    outString += "##%s=%s\n" % (k,v)
            else:   #if k == "INFO" or k == "FORMAT" or k == "FILTER" or k == "contig":
                for idstr,values in fileAttributes[k].iteritems():
                    outString += "##%s=<ID=%s" % (k,idstr)
                    for k2 in ["Number","Type","length"]:
                        if values.has_key(k2):
                            outString += ",%s=%s" % (k2,values[k2])
                    for k2,v2 in values.iteritems():
                        if k2 == "ID" or k2 == "Number" or k2 == "Type":
                            continue
                        if k2 == "Description":
                            outString += ",%s=\"%s\"" % (k2,v2)
                        else:
                            outString += ",%s=%s" % (k2,v2)
                    outString += ">\n"
        outString += "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT"
        
        if fileAttributes.has_key("INDIVIDUALS"):
            outString += "\t" + "\t".join(fileAttributes["INDIVIDUALS"])
        return outString
    
    @staticmethod
    def composeVcfLine(v,fileAttributes):
        outString = ""
        rsNumber = v.name
        if v.basicName == v.name:
            rsNumber = "."
        # basics
        outString += "%s\t%i\t%s\t%s\t%s"%(v.chromosome,v.start,rsNumber,str(v.ref),",".join([str(a) for a in v.alt]))
        
        # variant attributes
        info = ""
        for k,val in v.attributes.iteritems():
            if k == "QUAL" or k == "FILTER":
                continue
            info += "%s=%s;" % (k,val)
        info = info[:-1]    # strip last semicolon
        outString += "\t%s\t%s\t%s"%(v.attributes["QUAL"],";".join(v.attributes["FILTER"]),info)
        
        # We'll stick on the genotypes after we've seen all the possible format fields
        if fileAttributes.has_key("INDIVIDUALS"):
            # genotypes - the VCF spec requires that every column must have the same fields for a variant; find all fields that exist
            formatList = ["GT"]
            for g in v.genotypes.itervalues():
                for k in g.attributes.iterkeys():
                    if k not in formatList:
                        formatList.append(k)
            outString += "\t%s" % ":".join(formatList)
            
            for i in fileAttributes["INDIVIDUALS"]:
                outString += "\t"
                outString += str(v.alleles.index(v.genotypes[i].allele1))
                if v.genotypes[i].isPhased:
                    outString += "|"
                else:
                    outString += "/"
                outString += str(v.alleles.index(v.genotypes[i].allele2))
                for k in formatList:
                    outString += ":%s" % (v.genotypes[i].attributes.get(k,""))
        return outString

class csvVariantFile:
    # TODO: migrate this stuff to variantFile
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

#################################################
# Feature-level helper classes and file formats #
#################################################
'''
# TODO: probably find a better way to organize these structures using bx.intervals.intersection import Interval, IntervalTree

class feature:
    def __init__(self, chromosome, start, stop=None, name=None, attemptRepairsWhenComparing=True, build=genomeUtils.hg19):
        temp = standardizeChromosome(chromosome)
        if temp == None:
            raise Exception('Invalid Chromosome: %s' % chromosome)
        self.chromosome = temp
        self.start,self.genomeStart = genomeUtils.standardizePosition(self.chromosome, start, build)
        if stop == None:
            self.stop = self.start+1
            self.genomeStop = self.genomeStart+1
        else:
            self.stop,self.genomeStop = genomeUtils.standardizePosition(self.chromosome, stop, build)
        self.basicName = "%s_%i_%i" % (self.chromosome,self.start,self.stop)
        if name==None:
            self.name = self.basicName
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
        if x.chromosome == y.chromosome:
            return feature.positionCompare(x,y)
        else:
            return genomeUtils.hg19chrOrder.index(x.chromosome)-genomeUtils.hg19chrOrder.index(y.chromosome)
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
        return self.genomeStart + self.genomeStop
    
    def __eq__(self, other):
        if self.basicName == other.basicName:
            self.repair(other)
            return True
        else:
            return False
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def repair(self, other):
        if self.attemptRepairsWhenComparing and other.attemptRepairsWhenComparing:
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

class genomeMask:
    INDEL_STRICT = 0  # if either endpoint of an indel is in the mask, it fails
    INDEL_LOOSE = 1 # if either endpoint is NOT in the mask, it passes
    def __init__(self, regions, invert=False):
        self.indelMode = indelMode
        
        self.regions = defaultdict(list)   # {chromosome:[feature (sorted by start)]}
        for f in regions:
            self.regions[f.chromosome].append(f)
        for featureList in self.regions.itervalues():
            featureList.sort(key=lambda x:x.value)
        
        if invert:
            temp = self.regions
            self.regions = defaultdict(list)
            for chromosome,size in genomeUtils.hg19chrLengths.iteritems():
                newFeature = feature(chromosome,start=0,stop=size)
                self.regions[newFeature.chromosome].append(newFeature)
            self.subtract(temp)
    
    def subtract(self, otherMask):
        newRegions = defaultdict(list)
        for chr,features in self.regions.iteritems():
            otherFeatures = otherMask.get(chr,[])
            newFeatures = []
            
            myIndex = 0
            otherIndex = 0
            while myIndex < len(features):  # while there's something to subtract from...
                if otherIndex < len(otherFeatures): # anything left to subtract?
                    if otherFeatures[otherIndex].stop < features[myIndex].start: # we know that the lists are sorted, so nothing overlaps... look at the next feature
                        otherIndex += 1
                        continue
                    else: # okay, something overlapped...
                        if otherFeatures[otherIndex].start > features[myIndex].start: # do we need to add a bottom piece of me to the list?
                            newFeatures.append(feature(chr,start=features[myIndex].start,stop=otherFeatures[otherIndex].start-1))
                        if otherFeatures[otherIndex].stop < features[myIndex].stop: # is there anything left of me?
                            features[myIndex].start = otherFeatures[otherIndex.stop] + 1    # look at the slimmer version of me next time around, and we know we've finished with the other piece
                            features[myIndex].genomeStart = otherFeatures[otherIndex.genomeStop] + 1
                            otherIndex += 1
                            continue
                        else: # nothing left of of me to take (but there could be more of the other piece that affects something else)
                            myIndex += 1
                            continue
                else: # nothing left to subtract from me, so I can add myself and move on
                    newFeatures.append(features[myIndex])
                    myIndex += 1
            # The way we did that, newFeatures will already be sorted
            newRegions[chr] = newFeatures
        self.regions = newRegions
    
    # TODO: need a method that query whether a variant/feature intersects, and how much is left if it's a feature...
    # from bx.intervals.intersection import Interval, IntervalTree might help a little (may need the flattening pattern though)

class featureLoadingParameters:
    """
        An object for specifying what we care about when parsing a .bed or .gff3 feature file
    """
    def __init__(self,
                 build=genomeUtils.hg19,
                 passFunction=None,
                 rejectFunction=None,
                 callbackArgs={},
                 mask=None,
                 attributesToInclude={},
                 returnFileObject=False,
                 attemptRepairsWhenComparing=True):
        """
        :param passFunction:
            This function will be called for every variant that passes all criteria,
            with the variant as the first argument and callbackArgs as **vargs
        :param rejectFunction:
            This function will be called for every variant that fails at least one
            criteria or is masked, with the variant as the first argument and callbackArgs as **vargs
        :param mask:
            If not none, this should be a genomeMask object; any part of any features
            that overlaps the mask will be clipped (or if a feature is entirely in the
            mask, it will be rejected)
        :param attributesToInclude:
            This should be a dict containing strings mapped to valueFilter
            objects (where the string matches a column header in a .csv
            variant file, or "QUAL", "FILTER", or an INFO header from a
            .vcf file). Note that only attributes specified here will
            be extracted from the file.
        :param attemptRepairsWhenComparing:
            Once two variants are identified as equal, enabling this option will
            attempt to merge the information into a single variant object. Usually
            this is straightforward, but fails when REF/ALT allele configurations
            are reversed (to do this correctly, it would involve identifying which
            allele is the true REF, and reversing genotypes).
        """
        self.passFunction = passFunction
        self.rejectFunction = rejectFunction
        self.callbackArgs = callbackArgs
        self.mask = mask
        self.attributesToInclude = attributesToInclude
        self.returnFileObject = returnFileObject
        self.attemptRepairsWhenComparing = attemptRepairsWhenComparing

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
    def parseBedFile(path,featureParameters):
        if returnFileObject:
            newFileObject = bedFile()
        fileObject = open(path,'r')
        for line in fileObject:
            columns = line.split()
            if len(columns) < 3:
                name = None
            else:
                name = columns[3]
            newRegion = feature(columns[0], int(columns[1])+1, stop=int(columns[2]), name=name, featureParameters.attemptRepairsWhenComparing, featureParameters.build)   # the +1 converts from BED coordinates
            if mask != None and not mask.overlap(newRegion):
                continue
            if functionToCall != None:
                functionToCall(newRegion,**callbackArgs)
            if returnFileObject:
                newFileObject.regions.append(newRegion)
        fileObject.close()
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
'''