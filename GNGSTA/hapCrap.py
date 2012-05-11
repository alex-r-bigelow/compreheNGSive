'''
Created on Mar 16, 2012

@author: Alex Bigelow
'''

from resources.interfaces import unixInterface, unixParameter
from resources.utils import vcfFile, bedFile, recursiveDict
import math, sys

unassociatedAlleles = {}

caseHaplotypes = {}
controlHaplotypes = {}
backgroundHaplotypes = {}

#caseGenotypes = {}
#controlGenotypes = {}
#backgroundGenotypes = {}

variantList = recursiveDict()

class haplotype:
    def __init__(self):
        self.variants = {}
        self.riskGenotypes = {}
    
    def add(self, allele1, allele2, variantName):
        self.variants[variantName] = (allele1,allele2)
        
    def getPseudoGenotype(self, riskAlleles):
        '''
        Returns a pseudo-genotype representing whether or not this haplotype object contains a given risk haplotype.
        In the simplest case (the risk "haplotype" only contains one variant), the genotype of the specified
        variant is returned in terms of the specified risk allele. In the event that this haplotype does
        has no data for any of the risk loci, a genotype of (None,None) is returned.
        '''
        
        # memoize to save calculating these over and over again
        genotypeName = "_".join(sorted(riskAlleles))
        if self.riskGenotypes.has_key(genotypeName):
            return self.riskGenotypes[genotypeName]
        
        numVariants = len(riskAlleles)
        allele1 = 0
        allele2 = 0
        for v,riskAllele in riskAlleles.iteritems():
            if not self.variants.has_key(v):
                self.riskGenotypes[genotypeName] = (None,None)
                return (None,None)
            if self.variants[v][0] == riskAllele:
                allele1 += 1
            if self.variants[v][1] == riskAllele:
                allele2 += 1
        if allele1 < numVariants:
            allele1 = 0
        else:
            allele1 = 1
        if allele2 < numVariants:
            allele2 = 0
        else:
            allele2 = 1
        
        self.riskGenotypes[genotypeName] = (allele1,allele2)
        return (allele1,allele2)
        
    
    def getAllele1(self):
        if self.allele1 == None:
            calculatePseudoRiskGenotype(self)

def calculateAlleleFrequencies(genotypes):
    alleleCounter = {}
    total = 0.0
    for genotype in genotypes.itervalues():
        if not genotype.allele1 == None:
            if not alleleCounter.has_key(genotype.allele1):
                alleleCounter[genotype.allele1] = 0
            alleleCounter[genotype.allele1] += 1
            total+=1.0
        if not genotype.allele2 == None:
            if not alleleCounter.has_key(genotype.allele2):
                alleleCounter[genotype.allele2] = 0
            alleleCounter[genotype.allele2] += 1
            total+=1.0
    if len(alleleCounter) == 0 or total == 0.0:
        return (None,None)
    else:
        for a in alleleCounter.iterkeys():
            alleleCounter[a] = alleleCounter[a]/total
        return (alleleCounter,str(int(total/2)))

def hapCallback(variant, type):
    global variantList
    
    # Grab some data from the vcf file
    variantList[variant.name]['Chromosome'] = variant.chromosome
    variantList[variant.name]['Position'] = str(variant.start)
    
    lookupArray = [variant.ref.text]
    for a in variant.alt:
        lookupArray.append(a.text)
    
    # Find the risk allele (if we haven't found it / set it yet)
    alleleFrequencies,numPeople = calculateAlleleFrequencies(variant.genotypes)
    if alleleFrequencies == None:
        minorAlleleIndex = None
        minorAllele = None
        minorAlleleFrequency = "?"
        majorAlleleIndex = None
        majorAllele = None
        majorAlleleFrequency = None
        extraAlleles = None
    else:
        if type == "background":
            if len(alleleFrequencies) <= 1:
                minorAlleleIndex = 1    # If the background is all reference, we want to grab the first ALT instead of the least frequent
                majorAlleleIndex = 0
            else:
                temp = sorted(alleleFrequencies, key=lambda k:alleleFrequencies[k])
                minorAlleleIndex = temp[0]
                majorAlleleIndex = temp[-1]
        else:
            minorAlleleIndex = 1 # this infers that the minor allele is the first ALT in the control or case file
                                 # if we didn't find it already from the background
            majorAlleleIndex = 0
        
        minorAllele = lookupArray[minorAlleleIndex]
        majorAllele = lookupArray[majorAlleleIndex]
                
        # Need to switch alleles if the minor allele was already defined
        if variantList[variant.name].has_key('Risk Allele'):
            # minor allele already set... reset ours
            minorAllele = variantList[variant.name]['Risk Allele']
            
            # reset our major allele or figure out which one to use
            if variantList[variant.name].has_key('Other Allele'):
                majorAllele = variantList[variant.name]['Other Allele']
            else:
                majorAlleleIndex = 0
                while lookupArray[majorAlleleIndex] == minorAllele:
                    majorAlleleIndex += 1
                majorAllele = lookupArray[majorAlleleIndex]
        
        # Augment/set the extra alleles
        if variantList[variant.name].has_key('Extra Alleles'):
            extraAlleles = variantList[variant.name]['Extra Alleles']
        else:
            extraAlleles = set()
        for a in lookupArray:
            if a != minorAllele and a != majorAllele:
                extraAlleles.add(a)
        
        # finally, figure out the minor allele frequency
        if minorAllele not in lookupArray:
            minorAlleleFrequency = 0.0
        else:
            minorAlleleIndex = lookupArray.index(minorAllele)
            if not alleleFrequencies.has_key(minorAlleleIndex):
                minorAlleleFrequency = 0.0
            else:
                minorAlleleFrequency = alleleFrequencies[minorAlleleIndex]
        
        # Now store everything
        variantList[variant.name]['Risk Allele'] = minorAllele
        variantList[variant.name]['Other Allele'] = majorAllele
        variantList[variant.name]['Extra Alleles'] = extraAlleles
    
    # If found, store the minor allele for unassociated SNPs
    if unassociatedAlleles.has_key(variant.name):
        unassociatedAlleles[variant.name] = minorAllele
    
    # Figure out where to store the haplotypes that we'll calculate later,
    # where to store the incoming genotypes (if we need to),
    # as well as which allele frequency it was that we just calculated
    dictToModify = None
    if type == "case":
        global caseHaplotypes
        dictToModify = caseHaplotypes
        #global caseGenotypes
        #caseGenotypes[variant.name] = variant.genotypes
        variantList[variant.name]['Case Allele Frequency'] = minorAlleleFrequency
        variantList[variant.name]['Cases Used in AF'] = numPeople
        
        # store the quality from the vcf file as well
        variantList[variant.name]['Case VCF Qual'] = variant.attributes['QUAL']
        
    elif type == "control":
        global controlHaplotypes
        dictToModify = controlHaplotypes
        #global controlGenotypes
        #controlGenotypes[variant.name] = variant.genotypes
        variantList[variant.name]['Control Allele Frequency'] = minorAlleleFrequency
        variantList[variant.name]['Controls Used in AF'] = numPeople
    else:
        global backgroundHaplotypes
        dictToModify = backgroundHaplotypes
        #global backgroundGenotypes
        #backgroundGenotypes[variant.name] = variant.genotypes
        variantList[variant.name]['Background Allele Frequency'] = minorAlleleFrequency
        variantList[variant.name]['Background Used in AF'] = numPeople
    
    # Okay, figure out and store the haplotypes (if we want to)
    if dictToModify != None:
        for individual,genotype in variant.genotypes.iteritems():
            if not dictToModify.has_key(individual):
                dictToModify[individual] = [None]
            temp = dictToModify[individual]
            lastIndex = len(temp)-1
            if temp[lastIndex] == None and genotype.isPhased:   # start a new haplotype
                temp[lastIndex] = haplotype()
            if genotype.allele1 != None and genotype.allele2 != None and len(lookupArray) > genotype.allele1 and len(lookupArray) > genotype.allele2:
                if genotype.isPhased:                             # add to existing haplotype
                    allele1 = lookupArray[genotype.allele1]
                    allele2 = lookupArray[genotype.allele2]
                    temp[lastIndex].add(allele1,allele2,variant.name)
                else:
                    # add a single "dummy haplotype" object for the current unphased genotype
                    dummy = haplotype()
                    allele1 = lookupArray[genotype.allele1]
                    allele2 = lookupArray[genotype.allele2]
                    dummy.add(allele1,allele2,variant.name)
                    temp.append(dummy)
                    temp.append(None) # add none to tell myself to start a new haplotype next time
            else:   # encountered a no-call... don't record anything, but ensure that phase is broken
                if temp[lastIndex] != None:
                    temp.append(None)

def recordAlleles(t1,c1,counters):
    if t1 == 1:
        counters['x1'] += 1
        if c1 == 1:
            counters['x1y1'] += 1
            counters['y1'] += 1
        else:
            counters['x1y0'] += 1
            counters['y0'] += 1
    else:
        counters['x0'] += 1
        if c1 == 1:
            counters['x0y1'] += 1
            counters['y1'] += 1
        else:
            counters['x0y0'] += 1
            counters['y0'] += 1

def calculateCorrelation(target,candidate):
    global backgroundHaplotypes
    straight = {'x1y1':0,'x1y0':0,'x0y1':0,'x0y0':0,'x1':0,'y1':0,'x0':0,'y0':0}
    semiHap = {'x1y1':0,'x1y0':0,'x0y1':0,'x0y0':0,'x1':0,'y1':0,'x0':0,'y0':0}
    enfHap = {'x1y1':0,'x1y0':0,'x0y1':0,'x0y0':0,'x1':0,'y1':0,'x0':0,'y0':0}
    
    for i,haps in backgroundHaplotypes.iteritems():
        target1 = None
        target2 = None
        candidate1 = None
        candidate2 = None
        recordedAllStats = False
        for h in haps:
            t1,t2 = h.getPseudoGenotype(target)
            c1,c2 = h.getPseudoGenotype(candidate)
            if t1 != None and t2 != None and target1 == None and target2 == None:
                target1 = t1
                target2 = t2
            if c1 != None and c2 != None and candidate1 == None and candidate2 == None:
                candidate1 = c1
                candidate2 = c2
            if t1 != None and t2 != None and c1 != None and c2 != None and not recordedAllStats:
                # phase is unbroken between them... record all the stats!
                recordAlleles(t1,c1,straight)
                recordAlleles(t2,c2,straight)
                recordAlleles(t1,c1,semiHap)
                recordAlleles(t2,c2,semiHap)
                recordAlleles(t1,c1,enfHap)
                recordAlleles(t2,c2,enfHap)
                recordedAllStats = True
                
        if not recordedAllStats:
            # okay, we never saw the two variants on the same haplotype... do we even have data for both?
            if target1 == None or target2 == None or candidate1 == None or candidate2 == None:
                continue
            
            # okay, we have data - is at least one genotype homozygous?
            if target1 == target2 or candidate1 == candidate2:
                recordAlleles(t1,c1,semiHap)
                recordAlleles(t2,c2,semiHap)
            # and we always record the straight correlation, provided we have data
            recordAlleles(t1,c1,straight)
            recordAlleles(t2,c2,straight)
    temp = straight['x0']*straight['y0']*straight['x1']*straight['y1']
    if temp > 0:
        straightCorr = abs((straight['x1y1']*straight['x0y0']-straight['x1y0']*straight['x0y1'])/pow(temp,0.5))
    else:
        straightCorr = float("NaN")
    
    temp = semiHap['x0']*semiHap['y0']*semiHap['x1']*semiHap['y1']
    if temp > 0:
        semiHapCorr = abs((semiHap['x1y1']*semiHap['x0y0']-semiHap['x1y0']*semiHap['x0y1'])/pow(temp,0.5))
    else:
        semiHapCorr = float("NaN")
    
    temp = enfHap['x0']*enfHap['y0']*enfHap['x1']*enfHap['y1']
    if temp > 0:
        enfHapCorr = abs((enfHap['x1y1']*enfHap['x0y0']-enfHap['x1y0']*enfHap['x0y1'])/pow(temp,0.5))
    else:
        enfHapCorr = float("NaN")
    return (straightCorr,semiHapCorr,enfHapCorr)

def calculateCorrelations(target,altName=None):
    global variantList
    if altName == None:
        targetName = "_".join(sorted(target))
    else:
        targetName = altName
    print "...Correlations to %s" % targetName
    
    for v in variantList.iterkeys():
        straight,semiHap,enfHap = calculateCorrelation(target,{v:variantList[v]['Risk Allele']})
        variantList[v][targetName+"_straight"] = straight
        variantList[v][targetName+"_semiHap"] = semiHap
        variantList[v][targetName+"_enfHap"] = enfHap

def getHaplotypeFrequency(target,population):
    # debugging stuff: delete when finished:
    global backgroundHaplotypes
    global caseHaplotypes
    global controlHaplotypes
    # end debugging
    possible = 0
    seen = 0
    for i,haps in population.iteritems():
        for h in haps:
            if h == None:
                #if population == caseHaplotypes
                continue
            t1, t2 = h.getPseudoGenotype(target)
            if t1 == None or t2 == None:
                continue
            possible += 2
            seen += t1
            seen += t2
    if possible == 0:
        return float("NaN")
    else:
        return float(seen)/float(possible)

if __name__ == "__main__":
    interface = unixInterface("hapCrap.py",
                              "This program uses a risk haplotype and unassociated variants to prioritize candidate variants.",
                              requiredParameters = [unixParameter("--unassociated",
                                                                  "-u",
                                                                  "string(s)",
                                                                  "Variants (rs numbers) that are known to be unassociated, with their \"risk\" "+
                                                                  "alleles. If rs123 and rs456 are unassociated variants, and their risk alleles "+
                                                                  "respectively T and AGGGC (say rs456 is an insertion), then you should type:\\n"+
                                                                  "rs123,T rs456,AGGGC",
                                                                  numArgs = -1),
                                                    unixParameter("--hap",
                                                                  "-h",
                                                                  "string,string pairs",
                                                                  "Variants (rs numbers) and risk alleles that are on the risk haplotype. " +
                                                                  "If rs123 and rs456 are the risk haplotype and their risk alleles are " +
                                                                  "respectively T and AGGGC (say rs456 is an insertion), then you should " +
                                                                  "type:\\n rs123,T rs456,AGGGC",
                                                                  numArgs = -1),
                                                    unixParameter("--case_file",
                                                                  "-a",
                                                                  "file(s)",
                                                                  "Phased VCF file(s) containing case data.",
                                                                  numArgs = -1),
                                                    unixParameter("--background_file(s)",
                                                                  "-b",
                                                                  "file(s)",
                                                                  "Phased VCF file(s) containing background data.",
                                                                  numArgs = -1),
                                                    unixParameter("--control_file",
                                                                  "-c",
                                                                  "file(s)",
                                                                  "Phased VCF file(s) containing control data.",
                                                                  numArgs = -1),
                                                    unixParameter("--out",
                                                                  "-o",
                                                                  "file",
                                                                  "Output .tsv file",
                                                                  numArgs = 1)],
                              optionalParameters = [unixParameter("--include_cases",
                                                                  "-A",
                                                                  "string(s)",
                                                                  "Use only individuals with these labels (in the .vcf file) as cases.",
                                                                  numArgs = -1),
                                                    unixParameter("--include_background",
                                                                  "-B",
                                                                  "string(s)",
                                                                  "Use only individuals with these labels (in the .vcf file) as background.",
                                                                  numArgs = -1),
                                                    unixParameter("--include_controls",
                                                                  "-C",
                                                                  "string(s)",
                                                                  "Use only individuals with these labels (in the .vcf file) as controls.",
                                                                  numArgs = -1),
                                                    unixParameter("--mask",
                                                                  "-m",
                                                                  "file",
                                                                  "Only look at this region of the genome.",
                                                                  numArgs = -1)])
    
    unassociatedList = interface.getOption(tag="--unassociated", altTag="-u", optional=False)
    hapList = interface.getOption(tag="--hap", altTag="-h", optional=False)
    
    for c in unassociatedList:
        unassociatedAlleles[c] = None
    
    riskHaplotype = {}
    for h in hapList:
        temp = h.split(",")
        riskHaplotype[temp[0]] = temp[1]
    
    riskName = "risk_haplotype"
    
    case_files = interface.getOption(tag="--case_file", altTag="-a", optional=False)
    case_headers = interface.getOption(tag="--include_cases", altTag="-A", optional=True)
    if case_headers == None:
        case_headers = []
    
    background_files = interface.getOption(tag="--background_file", altTag="-b", optional=False)
    background_headers = interface.getOption(tag="--include_background", altTag="-B", optional=True)
    if background_headers == None:
        background_headers = []
    
    control_files = interface.getOption(tag="--control_file", altTag="-c", optional=False)
    control_headers = interface.getOption(tag="--include_controls", altTag="-C", optional=True)
    if control_headers == None:
        control_headers = []
    
    masks = None
    maskPath = interface.getOption(tag="--mask",altTag="-m",optional=True)
    if maskPath != None:
        maskFile = open(maskPath[0],'r')
        masks=bedFile.parseBedFile(maskFile)
        maskFile.close()
    
    outPath = interface.getOption(tag="--out",altTag="-o",optional=False)[0]
        
    # NOTE: The order in which we load files is important (the first minor allele found is declared
    # to be the "risk" allele) - we also want to enforce the haplotype alleles as the minor alleles
    # before we do anything else
    for rsNo,allele in riskHaplotype.iteritems():
        variantList[rsNo]['Risk Allele'] = allele
    
    print "Loading Background..."
    for f in background_files:
        inFile = open(f,'r')
        vcfFile.parseVcfFile(inFile,functionToCall=hapCallback,callbackArgs={'type':'background'},individualsToInclude=background_headers,mask=masks,returnFileObject=False,skipFiltered=True,skipVariantAttributes=False,skipGenotypes=False,skipGenotypeAttributes=True,includeAdditionalHeaderInfo=False)
        inFile.close()
    
    numBackgroundDeterminedAlleles = len(variantList)
    print "...Number of minor alleles determined from background: %i" % numBackgroundDeterminedAlleles
    
    print "Loading Controls..."
    for f in control_files:
        inFile = open(f,'r')
        vcfFile.parseVcfFile(inFile,functionToCall=hapCallback,callbackArgs={'type':'control'},individualsToInclude=control_headers,mask=masks,returnFileObject=False,skipFiltered=True,skipVariantAttributes=False,skipGenotypes=False,skipGenotypeAttributes=True,includeAdditionalHeaderInfo=False)
        inFile.close()
    
    numControlDeterminedAlleles = len(variantList) - numBackgroundDeterminedAlleles
    print "...Number of minor alleles determined from controls: %i" % numControlDeterminedAlleles
    
    print "Loading Cases..."
    for f in case_files:
        inFile = open(f,'r')
        vcfFile.parseVcfFile(inFile,functionToCall=hapCallback,callbackArgs={'type':'case'},individualsToInclude=case_headers,mask=masks,returnFileObject=False,skipFiltered=True,skipVariantAttributes=False,skipGenotypes=False,skipGenotypeAttributes=True,includeAdditionalHeaderInfo=False)
        inFile.close()
    
    numCaseDeterminedAlleles = len(variantList) - (numControlDeterminedAlleles+numBackgroundDeterminedAlleles)
    print "...Number of minor alleles determined from cases: %i" % numCaseDeterminedAlleles
    
    print "The risk haplotype was seen in:"
    backgroundHapFreq = getHaplotypeFrequency(riskHaplotype,backgroundHaplotypes)
    if backgroundHapFreq != None:
        print "...%.2f%% of the background alleles" % (backgroundHapFreq * 100.0)
    controlHapFreq = getHaplotypeFrequency(riskHaplotype,controlHaplotypes)
    if controlHapFreq != None:
        print "...%.2f%% of the control alleles" % (controlHapFreq * 100.0)
    caseHapFreq = getHaplotypeFrequency(riskHaplotype,caseHaplotypes)
    if caseHapFreq != None:
        print "...%.2f%% of the case alleles" % (caseHapFreq * 100.0)
        
    unseenUnassociated = []
    for k in unassociatedList:
        if unassociatedAlleles[k] == None:
            unseenUnassociated.append(k)
            del unassociatedAlleles[k]
    
    if len(unseenUnassociated) > 0:
        print "Unassociated SNPs not seen in background, controls, or cases: %s" % str(unseenUnassociated)
        print "Unassociated SNPs that will be used: %s" % str(list(set(unassociatedList)-set(unseenUnassociated)))
    
    print "Calculating..."
    calculateCorrelations(riskHaplotype,altName=riskName)
    for c,a in unassociatedAlleles.iteritems():
        calculateCorrelations({c:a})
    
    print "Finding max unassociated SNPs..."
    for v in variantList.iterkeys():
        max_straight = float("NaN")
        max_semiHap = float("NaN")
        max_enfHap = float("NaN")
        
        for c in unassociatedAlleles.iterkeys():
            straightLabel = "%s_straight" % c
            semiHapLabel = "%s_semiHap" % c
            enfHapLabel = "%s_enfHap" % c
            if variantList[v].has_key(straightLabel):
                if not math.isnan(variantList[v][straightLabel]):
                    if not math.isnan(max_straight):
                        if variantList[v][straightLabel] > max_straight:
                            max_straight = variantList[v][straightLabel]
                    else:
                        max_straight = variantList[v][straightLabel]
                del variantList[v][straightLabel]
            if variantList[v].has_key(semiHapLabel):
                if not math.isnan(variantList[v][semiHapLabel]):
                    if not math.isnan(max_semiHap):
                        if variantList[v][semiHapLabel] > max_semiHap:
                            max_semiHap = variantList[v][semiHapLabel]
                    else:
                        max_semiHap = variantList[v][semiHapLabel]
                del variantList[v][semiHapLabel]
            if variantList[v].has_key(enfHapLabel):
                if not math.isnan(variantList[v][enfHapLabel]):
                    if not math.isnan(max_enfHap):
                        if variantList[v][enfHapLabel] > max_enfHap:
                            max_enfHap = variantList[v][enfHapLabel]
                    else:
                        max_enfHap = variantList[v][enfHapLabel]
                del variantList[v][enfHapLabel]
        variantList[v]["Max_Unassociated_SNP_straight"] = max_straight
        variantList[v]["Max_Unassociated_SNP_semiHap"] = max_semiHap
        variantList[v]["Max_Unassociated_SNP_enfHap"] = max_enfHap
    
    print "Dumping output..."
    # TODO: calculate case-normalized AFs for cases, controls, background, as well as variation from hap allele freq
    headerList = ['Name','Chromosome','Position','Risk Allele','Other Allele','Extra Alleles','Case VCF Qual','Case Allele Frequency','Cases Used in AF','Control Allele Frequency','Controls Used in AF','Background Allele Frequency','Background Used in AF']
    headerList.append("%s_straight" % riskName)
    headerList.append("%s_semiHap" % riskName)
    headerList.append("%s_enfHap" % riskName)
    
    headerList.append("Max_Unassociated_SNP_straight")
    headerList.append("Max_Unassociated_SNP_semiHap")
    headerList.append("Max_Unassociated_SNP_enfHap")
    
    
    # Temporary: dump to json bits
    '''
    import json
    filesizeIncrement = 1000
    numVariants = 0
    numFiles = 0
    currentVariants = {}
    for v in variantList.iterkeys():
        currentVariants[v] = {}
        hasNoControls = (not variantList[v].has_key("Controls Used in AF") or variantList[v]["Controls Used in AF"] == "?" or variantList[v]["Controls Used in AF"] == "x")
        hasNoCases = (not variantList[v].has_key("Cases Used in AF") or variantList[v]["Controls Used in AF"] == "?" or variantList[v]["Controls Used in AF"] == "x")
        hasNoBackground = (not variantList[v].has_key("Background Used in AF") or variantList[v]["Controls Used in AF"] == "?" or variantList[v]["Controls Used in AF"] == "x")
        if hasNoControls and hasNoBackground:
            continue
        if hasNoCases and hasNoBackground:
            continue
        for h in headerList[1:]:
            if not variantList[v].has_key(h):
                currentVariants[v][h]="?"
            elif isinstance(variantList[v][h],float):
                if math.isnan(variantList[v][h]) or math.isinf(variantList[v][h]):
                    currentVariants[v][h] = "x"
                else:
                    currentVariants[v][h] = variantList[v][h]
            elif isinstance(variantList[v][h],set):
                currentVariants[v][h] = list(variantList[v][h])
            else:
                currentVariants[v][h] = variantList[v][h]
        numVariants += 1
        if numVariants > filesizeIncrement:
            temp = open('/export/home/alex/Desktop/dataBits/hapCrap.%i.json' % numFiles, 'w')
            temp.write(json.dumps(currentVariants, allow_nan=False))
            temp.close()
            currentVariants = {}
            numFiles += 1
            numVariants = 0
    
    temp = open('/export/home/alex/Desktop/dataBits/hapCrap.%i.json' % numFiles, 'w')
    temp.write(json.dumps(currentVariants, allow_nan=False))
    temp.close()
    currentVariants = {}
    numFiles += 1
    # end temporary
    '''
    
    
    outFile = open(outPath,'w')
    outLine = ""
    for h in headerList:
        outLine += "%s\t" % h
    outFile.write(outLine[:-1] + "\n")
    
    for v in variantList.iterkeys():
        outFile.write(v)
        for h in headerList[1:]:
            if not variantList[v].has_key(h):
                if h == "Cases Used in AF" or h == "Controls Used in AF" or h == "Background Used in AF":
                    outFile.write("\t0")
                else:
                    outFile.write("\t?")
            elif isinstance(variantList[v][h],float):
                if math.isnan(variantList[v][h]):
                    outFile.write("\tx")
                else:
                    outFile.write("\t%.8f" % variantList[v][h])
            elif isinstance(variantList[v][h],set) or isinstance(variantList[v][h],list):
                if len(variantList[v][h]) == 0:
                    outFile.write("\tx")
                else:
                    outFile.write("\t%s" % ",".join(variantList[v][h]))
            else:
                outFile.write("\t%s" % variantList[v][h])
        outFile.write("\n")
        
    outFile.close()
    print "Finished. '?' indicates missing data, 'x' indicates data that could not be calculated (e.g. division by 0)."