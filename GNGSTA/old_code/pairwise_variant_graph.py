#!/usr/bin/env python
'''
Created January 2012

@author: Alex Bigelow
'''

from resources.interfaces import unixInterface, unixParameter
from resources.utils import recursiveDict, bedFile, variant, genotype, vcfFile
from resources.gephiGui import gephiController
from resources.pygephi import JSONClient
import time
import os, sys, random

########################################
# Helper classes, variables, functions #
########################################

client = None

NUM_BINS = 101;
DEFAULT_size=20

# Color scheme from colorbrewer2.org:

DEFAULT_r = 102/255.0
DEFAULT_g = 102/255.0
DEFAULT_b = 102/255.0

SEED_r = 217/255.0
SEED_g = 95/255.0
SEED_b = 2/255.0

WATCH_r = 27/255.0
WATCH_g = 158/255.0
WATCH_b = 119/255.0

FLAG_r = 231/255.0
FLAG_g = 41/255.0
FLAG_b = 138/255.0

variants = {}

class node:
    def __init__(self, name, riskAllele=None):
        self.caseIndividuals = {}
        self.backgroundIndividuals = {}
        self.maxWeight = 0.0
        self.attributes={"size":DEFAULT_size,"r":DEFAULT_r,"g":DEFAULT_g,"b":DEFAULT_b}
        self.name = name
        self.riskAllele = riskAllele
    
    def addCaseGenotypes(self, genotypes):
        self.caseIndividuals.update(genotypes)
    
    def addBackgroundGenotypes(self, genotypes):
        self.backgroundIndividuals.update(genotypes)
    
    def calculateSharedAlleleFrequency(self, candidate):
        '''
        Calculates the shared risk allele frequency
        '''
        if self.riskAllele == None:
            Tcounter = {}
            
            for i,g in self.caseIndividuals.iteritems():
                if g.isMissingData():
                    continue
                if not Tcounter.has_key(g.allele1):
                    Tcounter[g.allele1] = 1
                else:
                    Tcounter[g.allele1] += 1
                if not Tcounter.has_key(g.allele2):
                    Tcounter[g.allele2] = 1
                else:
                    Tcounter[g.allele2] += 1
            
            if len(Tcounter) == 0:
                return -2.0 # No marker case data! Undefined ... and something's wrong with the marker
            
            self.riskAllele = max(Tcounter,key=Tcounter.get)
        
        # Need to find most co-occurring allele at candidate locus
        Ccounter = {}
        
        for i,g in candidate.caseIndividuals.iteritems():
            if g.isMissingData():
                continue
            if g.allele1 == self.riskAllele:
                if not Ccounter.has_key(g.allele1):
                    Ccounter[g.allele1] = 0
                Ccounter[g.allele1] += 1
            
            if g.allele2 == self.riskAllele:
                if not Ccounter.has_key(g.allele2):
                    Ccounter[g.allele2] = 0
                Ccounter[g.allele2] += 1
        
        if len(Ccounter) == 0:
            return -1.0     # No candidate case data! Undefined...
        
        C = max(Ccounter,key=Ccounter.get)
        
        # Create a case/background individual lists - a subset of each that have data for both target and candidate
        c_prime = []
        for i,g in self.caseIndividuals.iteritems():
            if not g.isMissingData() or not candidate.caseIndividuals.has_key(i) or candidate.caseIndividuals[i].isMissingData():
                c_prime.append(i)
        
        if len(c_prime) == 0:
            return -1.0 # Undefined
        
        matches = 0
        for i in c_prime:   # count the number of matching alleles in cases
            temp = 0
            if candidate.caseIndividuals[i].allele1 == C:
                temp += 1
            if candidate.caseIndividuals[i].allele2 == C:
                temp += 1
            
            if self.caseIndividuals[i].allele1 != self.riskAllele:
                temp -= 1
            if self.caseIndividuals[i].allele2 != self.riskAllele:
                temp -= 1
            
            if temp < 0:
                temp = 0
            
            matches += temp
        
        return matches/(len(c_prime)*2.0)
            
    
    def calculateAntiLD(self, candidate):
        '''
        Calculates Anti-LD between self and other - see publication
        (self is the marker, candidate is the candidate variant)
        '''
        if self.riskAllele == None:
            Tcounter = {}
            
            for i,g in self.caseIndividuals.iteritems():
                if g.isMissingData():
                    continue
                if not Tcounter.has_key(g.allele1):
                    Tcounter[g.allele1] = 1
                else:
                    Tcounter[g.allele1] += 1
                if not Tcounter.has_key(g.allele2):
                    Tcounter[g.allele2] = 1
                else:
                    Tcounter[g.allele2] += 1
            
            if len(Tcounter) == 0:
                return -2.0 # No marker case data! Anti-LD is undefined ... and something's wrong with the marker
            
            self.riskAllele = max(Tcounter,key=Tcounter.get)
        
        # Need to find most co-occurring allele at candidate locus
        Ccounter = {}
        
        for i,g in candidate.caseIndividuals.iteritems():
            if g.isMissingData():
                continue
            if g.allele1 == self.riskAllele:
                if not Ccounter.has_key(g.allele1):
                    Ccounter[g.allele1] = 0
                Ccounter[g.allele1] += 1
            
            if g.allele2 == self.riskAllele:
                if not Ccounter.has_key(g.allele2):
                    Ccounter[g.allele2] = 0
                Ccounter[g.allele2] += 1
        
        if len(Ccounter) == 0:
            return -1.0     # No candidate case data! Anti-LD is undefined
        
        C = max(Ccounter,key=Ccounter.get)
        
        # Create a case/background individual lists - a subset of each that have data for both target and candidate, and targets are homozygous for T
        c_prime = []
        for i,g in self.caseIndividuals.iteritems():
            if g.isMissingData() or not candidate.caseIndividuals.has_key(i) or candidate.caseIndividuals[i].isMissingData():
                continue
            if g.allele1 == self.riskAllele and g.allele2 == self.riskAllele:   # TODO: in the future, we may not want to filter cases for homozygosity...
                c_prime.append(i)
        
        b_prime = []
        for i,g in self.backgroundIndividuals.iteritems():
            if g.isMissingData() or not candidate.backgroundIndividuals.has_key(i) or candidate.backgroundIndividuals[i].isMissingData():
                continue
            if g.allele1 == self.riskAllele and g.allele2 == self.riskAllele:
                b_prime.append(i)
        
        sc_total = len(c_prime)*2
        sb_total = len(b_prime)*2
        if sb_total == 0:     # No overlapping background data - this could be interesting...
            if len(candidate.backgroundIndividuals) == 0 and len(self.caseIndividuals) > 0:
                return -3.0     # Missing data entirely for candidate in background but our cases have it - could mean it's an extremely rare variant
            else:
                return -1.0     # Aw shucks... just missing data or the overlap happens to not fit. Undefined...
        if sc_total == 0:     # No overlapping case data - Anti-LD is undefined
            return -1.0
        else:
            sc_count = 0
            for i in c_prime:   # count the number of matching alleles in cases
                if candidate.caseIndividuals[i].allele1 == C:
                    sc_count += 1
                if candidate.caseIndividuals[i].allele2 == C:
                    sc_count += 1
            
            sb_count = 0
            for i in b_prime:   # count the number of matching alleles in background
                if candidate.backgroundIndividuals[i].allele1 == C:
                    sb_count += 1
                if candidate.backgroundIndividuals[i].allele2 == C:
                    sb_count += 1
            temp = sc_count*(sb_total-sb_count)/float(sc_total*sb_total)   # a little algebra to keep down the number of divides
            return temp
    
    def getWeight(self, other):
        newWeight = self.calculateSharedAlleleFrequency(other)
        # The node's maxWeight should be its strongest edge weight - this way nodes with no edges will be filtered
        #if newWeight > self.maxWeight:
        #    self.maxWeight = newWeight
        #if newWeight > other.maxWeight:
        #    other.maxWeight = newWeight
        
        return newWeight

class edge:
    def __init__(self, marker, candidate):
        self.source = marker.name
        self.target = candidate.name
        
        self.edgeWeight = marker.getWeight(candidate)
        if self.edgeWeight == -2.0:    # shoot... we're missing some critical data here
            print "ERROR: No case data for seed %s" % marker.name
            sys.exit(1)
        if self.edgeWeight == -3.0:
            pass
            #print "ATTENTION: No background data for %s; potentially rare variant!" % candidate.name
        
        if self.edgeWeight > marker.maxWeight:
            marker.maxWeight = self.edgeWeight
        if self.edgeWeight > candidate.maxWeight:
            candidate.maxWeight = self.edgeWeight
        
        self.name = self.source + "_" + self.target
        
class nodeAndEdgeBin:
    def __init__(self,threshold):
        self.nodes = []
        self.edges = []
        self.threshold = threshold
    
    def addNode(self,n):
        self.nodes.append(n)
    
    def addEdge(self,e):
        self.edges.append(e)
    
    def draw(self):
        for n in self.nodes:
            client.add_node(n.name,**n.attributes)
        for e in self.edges:
            w = e.edgeWeight
            if w == 0.0:
                w = 0.000001
            client.add_edge(e.name,e.source,e.target,directed=True,weight=w)
        client.flush()
    
    def erase(self):
        for n in self.nodes:
            client.delete_node(n.name)
        for e in self.edges:
            client.delete_edge(e.name)
        client.flush()

class nodeAndEdgeBinner:
    def __init__(self, low=0.0, high=1.0, numBins=NUM_BINS):
        self.bins = []
        self.low = low
        self.high = high
        self.numBins = numBins
        self.currentBin = numBins   # Start one above the top - this is a nonexistent bin that will never be drawn
        
        temp = low
        step = (high-low)/(numBins-1)   # We want to reserve a bin for 1.0
        for b in xrange(numBins-1):
            self.bins.append(nodeAndEdgeBin(temp))
            temp+=step
        self.bins.append(nodeAndEdgeBin(high))
        
        self.widgetCallback = None
    
    def findIndex(self, threshold):
        return int((self.numBins-1)*(threshold-self.low))
    
    def addNode(self, n):
        self.bins[self.findIndex(n.maxWeight)].addNode(n)
    
    def addEdge(self, e):
        self.bins[self.findIndex(e.edgeWeight)].addEdge(e)
    
    def setThreshold(self, threshold):
        newBin = self.findIndex(threshold)
        if newBin < self.currentBin:    # Add some nodes and edges
            #print "adding %i bins..." % (self.currentBin-newBin)
            for i in xrange(self.currentBin-1,newBin-1,-1):
                self.bins[i].draw()
                self.widgetCallback(i)
            self.currentBin = newBin
        elif newBin > self.currentBin:   # Remove some nodes and edges
            #print "removing %i bins..." % (newBin-self.currentBin)
            for i in xrange(self.currentBin,newBin):
                self.bins[i].erase()
                self.widgetCallback(i+1)
            self.currentBin = newBin
        # Do nothing; the bin hasn't changed
    
    def printHistogram(self):
        print "Threshold\tEdges\tNodes"
        for b in self.bins:
            print "%f\t%i\t%i" % (b.threshold,len(b.edges),len(b.nodes))
    
    def getHistogram(self):
        temp = {}
        for b in self.bins:
            temp[b.threshold] = (len(b.edges),len(b.nodes))
        return temp
    
    def calculateStandardDeviation(self):
        pass

def parseVariantCallback(newVariant,isCaseFile):
    newStats = variants.get(newVariant,node(newVariant.name))
    
    if isCaseFile:
        newStats.addCaseGenotypes(newVariant.genotypes)
    else:
        newStats.addBackgroundGenotypes(newVariant.genotypes)
    
    variants[newVariant] = newStats

####################
# Start of program #
####################

# Get command line parameters
interface = unixInterface("pairwise_variant_graph.py",
                         "This is a program that generates a meltable graph of the distributional similarity between variants.",
                         requiredParameters = [unixParameter("--cases",
                                                             "-c",
                                                             "file (or NULL_MODE)",
                                                             "Case .vcf file",
                                                             numArgs = 1),
                                               unixParameter("--background",
                                                             "-b",
                                                             "file",
                                                             "Background .vcf file",
                                                             numArgs = -1),
                                               unixParameter("--seeds",
                                                             "-s",
                                                             "string",
                                                             "Pivot variants (rs numbers or chr_pos_ref_alt).",
                                                             numArgs = -1)],
                         optionalParameters = [unixParameter("--url",
                                                             "-u",
                                                             "string",
                                                             "URL of the Gephi server. \\n Default: http://127.0.0.1:8080/workspace0",
                                                             numArgs = 1),
                                               unixParameter("--exclude",
                                                             "-e",
                                                             "string",
                                                             "Samples (column headers) from .vcf files " +
                                                             "to exclude from case and background groups.",
                                                             numArgs = -1),
                                               unixParameter("--include",
                                                             "-i",
                                                             "string",
                                                             "Samples (column headers) from .vcf files " +
                                                             "to exclusively include from case and background groups. "+
                                                             "If specified, no other individuals from cases or background "+
                                                             "will be included.",
                                                             numArgs = -1),
                                               unixParameter("--null_samples",
                                                             "-n",
                                                             "integer",
                                                             "Runs a null visualization with n randomly selected individuals "+
                                                             "from the case-background pool to use as cases. "+
                                                             "If --include or --exclude is specified, only individuals that fit "+
                                                             "those criteria will be selected.",
                                                             numArgs = 1),
                                               unixParameter("--mask",
                                                             "-m",
                                                             "file",
                                                             ".bed file containing regions of interest; variants outside of the regions will" +
                                                             "not be included.",
                                                             numArgs = 1),
                                               unixParameter("--watch",
                                                             "-w",
                                                             "string",
                                                             "Non-seed variants to highlight.",
                                                             numArgs = -1),
                                               unixParameter("--flag",
                                                             "-f",
                                                             "string",
                                                             "Non-seed variants to highlight.",
                                                             numArgs = -1)])

# Read in command line options, open and parse files
excludeList = interface.getOption(tag="--exclude",altTag="-e",optional=True)
if excludeList == None:
    excludeList = []

includeList = interface.getOption(tag="--include",altTag="-i",optional=True)
if includeList == None:
    includeList = []

seedList = interface.getOption(tag="--seeds",altTag="-s",optional=False)

watchList = interface.getOption(tag="--watch",altTag="-w",optional=True)

flagList = interface.getOption(tag="--flag",altTag="-f",optional=True)

temp = interface.getOption(tag="--null_samples",altTag="-n",optional=True)
if temp != None and len(temp) > 0:
    nullSamples = int(temp[0])
else:
    nullSamples = None

print "Loading regions..."

masks = None
maskPath = interface.getOption(tag="--mask",altTag="-m",optional=True)
if maskPath != None:
    maskFile = open(maskPath[0],'r')
    masks=bedFile.parseBedFile(maskFile)
    maskFile.close()

print "Loading cases..."

inputPath = interface.getOption(tag="--cases",altTag="-c",optional=False)
if len(inputPath) != 1:
    interface.die("Must supply exactly one cases file.")


if nullSamples != None:
    if len(includeList) == 0:
        try:
            temp = open(inputPath[0],'r')
            includeList = vcfFile.extractIndividualsInFile(temp)
            temp.close()
            tempPath = interface.getOption(tag="--background",altTag="-b",optional=False)
            temp = open(tempPath[0],'r')
            includeList = list(set(includeList) | set(vcfFile.extractIndividualsInFile(temp)))
            temp.close()
            includeList = list(set(includeList)-set(excludeList))
        except:
            interface.die("Couldn't open %s" % inputPath)
    
    nullList = includeList
    
    if len(nullList) < nullSamples:
        interface.die("More --null_samples (%i) specified than --include, --exclude, and/or the --cases and --background files allow (%i)." % (sampleSize,len(nullList)))
    
    nullList = random.sample(nullList,nullSamples)
    
    includeList = list(set(includeList)-set(nullList))

try:
    casesFile = open(inputPath[0],'r')
except:
    interface.die("Couldn't open %s" % inputPath)

if nullSamples != None:
    vcfFile.parseVcfFile(casesFile,parseVariantCallback,callbackArgs={"isCaseFile":True},returnFileObject=False,individualsToExclude=excludeList,individualsToInclude=nullList,mask=masks,skipFiltered=True,skipVariantAttributes=True,skipGenotypes=False,skipGenotypeAttributes=True,includeAdditionalHeaderInfo=False)
    casesFile.close()
    casesFile = open(inputPath[0],'r')
    vcfFile.parseVcfFile(casesFile,parseVariantCallback,callbackArgs={"isCaseFile":False},returnFileObject=False,individualsToExclude=excludeList,individualsToInclude=includeList,mask=masks,skipFiltered=True,skipVariantAttributes=True,skipGenotypes=False,skipGenotypeAttributes=True,includeAdditionalHeaderInfo=False)
else:
    vcfFile.parseVcfFile(casesFile,parseVariantCallback,callbackArgs={"isCaseFile":True},returnFileObject=False,individualsToExclude=excludeList,individualsToInclude=includeList,mask=masks,skipFiltered=True,skipVariantAttributes=True,skipGenotypes=False,skipGenotypeAttributes=True,includeAdditionalHeaderInfo=False)

print "Loading background..."

inputPath = interface.getOption(tag="--background",altTag="-b",optional=False)
if len(inputPath) != 1:
    interface.die("Must supply exactly one cases file.")
try:
    backgroundFile = open(inputPath[0],'r')
except:
    interface.die("Couldn't open %s" % inputPath)

if nullSamples != None:
    vcfFile.parseVcfFile(backgroundFile,parseVariantCallback,callbackArgs={"isCaseFile":True},returnFileObject=False,individualsToExclude=excludeList,individualsToInclude=nullList,mask=masks,skipFiltered=True,skipVariantAttributes=True,skipGenotypes=False,skipGenotypeAttributes=True,includeAdditionalHeaderInfo=False)
    backgroundFile.close()
    backgroundFile = open(inputPath[0],'r')
    vcfFile.parseVcfFile(backgroundFile,parseVariantCallback,callbackArgs={"isCaseFile":False},returnFileObject=False,individualsToExclude=excludeList,individualsToInclude=includeList,mask=masks,skipFiltered=True,skipVariantAttributes=True,skipGenotypes=False,skipGenotypeAttributes=True,includeAdditionalHeaderInfo=False)
else:
    vcfFile.parseVcfFile(backgroundFile,parseVariantCallback,callbackArgs={"isCaseFile":False},returnFileObject=False,individualsToExclude=excludeList,individualsToInclude=includeList,mask=masks,skipFiltered=True,skipVariantAttributes=True,skipGenotypes=False,skipGenotypeAttributes=True,includeAdditionalHeaderInfo=False)

print "Calculating edge weights:"
nodesAndEdges = nodeAndEdgeBinner()

# Find the seed nodes
print "...Finding seeds"

seedNodes = []
for n in variants.itervalues():
    if n.name in seedList:
        n.attributes["r"] = SEED_r
        n.attributes["g"] = SEED_g
        n.attributes["b"] = SEED_b
        n.attributes["label"] = n.name
        seedNodes.append(n)

# Calculate edges between seeds and non-seeds
print "...Calculating edges between seeds and non-seeds"
for n in variants.itervalues():
    if n.name in seedList:
        continue
    for s in seedNodes:
        newEdge = edge(s,n)
        if newEdge.edgeWeight >= 0.0:
            nodesAndEdges.addEdge(newEdge)

# Calculate edges between seeds
print "...Calculating edges between seeds"
#print "   Edge Name:\tForwardALD:\tBackwardALD:\tALD:"
for n in seedNodes:
    for s in seedNodes:
        if n.name == s.name:
            continue
        newEdge = edge(s,n)
        if newEdge.edgeWeight >= 0.0:
            nodesAndEdges.addEdge(newEdge)

# Finally add all the nodes, highlighting watch ones if relevant
print "...Adding data, coloring watch nodes"
for n in variants.itervalues():
    if watchList != None and n.name in watchList:
        n.attributes["r"] = WATCH_r
        n.attributes["g"] = WATCH_g
        n.attributes["b"] = WATCH_b
        n.attributes["Label"] = n.name
    if flagList != None and n.name in flagList:
        n.attributes["r"] = FLAG_r
        n.attributes["g"] = FLAG_g
        n.attributes["b"] = FLAG_b
        n.attributes["Label"] = n.name
    nodesAndEdges.addNode(n)

print "Starting server..."

gephi_url = interface.getOption(tag="--url",altTag="-u",optional=True)
if gephi_url == None:
    gephi_url = "http://127.0.0.1:8080/workspace0"
else:
    gephi_url = gephi_url[0]


# TODO: reverse the gephi server/client deal...
client = JSONClient(gephi_url)

print "Starting GUI..."

gui = gephiController(nodesAndEdges.getHistogram(),nodesAndEdges.setThreshold,logScale=True)
nodesAndEdges.widgetCallback = gui.update
gui.mainloop()
    