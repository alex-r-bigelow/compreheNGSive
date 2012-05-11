#!/usr/bin/env python
'''
Created December 2011

@author: Alex Bigelow
'''

import sys
import os
from gffGlobals import scorelessColor, variantColors, hg19header
from utils import recursiveDict
from collections import defaultdict

####################
# Global variables #
####################

vcfIndividuals = []
caseIndividuals = []
controlIndividuals = []
vcfFilters = {}
vcfInfo = {}
vcfFormat = {}
vcfVariants = []


# Default options:
keepFiltered = False
getGroupStats = False
getSimilarStats = False
colorMode = "QUAL"

#########################
# Global helper classes #
#########################
class variant:
	minScores = {}
	maxScores = {}
	def __init__(self, chromosome, start, stop, ref, alt, info, genotypes, rsNumber="."):
		self.chromosome = chromosome
		if "chr" in chromosome:
			self.chromosomeNumber = int(chromosome[3:])
		else:
			self.chromosomeNumber = int(chromosome)
		self.start = start
		self.stop = stop
		self.ref = ref
		self.alt = alt
		self.scores = info
		self.scores["Chromosome"] = self.chromosome
		self.scores["Start"] = self.start
		self.scores["Stop"] = self.stop
		self.scores["Reference Allele"] = self.ref
		self.scores["Alternate Allele"] = self.alt
		if rsNumber == ".":
			rsNumber = self.chromosome + "_" + str(self.start) + "_" + self.ref + "_" + self.alt
		else:
			self.scores["rs Number"] = rsNumber
		self.rsNumber = rsNumber
		self.logExtremes()
		self.genotypes = genotypes
		self.color = scorelessColor
	
	def logExtremes(self):
		for k, v in self.scores.iteritems():
			if isinstance(v, float) or isinstance(v, int):
				self.logExtreme(k, v)
			elif isinstance(v, list):
				for i in v:
					if isinstance(i, float) or isinstance(i, int):
						self.logExtreme(k, v)
					elif isinstance(i, str):
						continue
					else:
						die("Unknown data type (inside list): %s\t%s" % (k,v))
			elif isinstance(v, bool):
				self.logExtreme(k,v)
			elif isinstance(v, str):
				continue
			else:
				die("Unknown data type: %s\t%s" % (k,v))
	
	def logExtreme(self, k, v):
		if v == float("-Inf") or v == float("Inf"):
			return
		if not variant.minScores.has_key(k):
			variant.minScores[k] = v
		elif v < variant.minScores[k]:
			variant.minScores[k] = v
		if not variant.maxScores.has_key(k):
			variant.maxScores[k] = v
		elif v > variant.maxScores[k]:
			variant.maxScores[k] = v		
		
		
	def calculateGroupScores(self):
		caseAlleles = defaultdict(int)
		controlAlleles = defaultdict(int)
		totalCaseAlleles = 0.0
		totalControlAlleles = 0.0
		
		highestAllele = 0
		
		for i, g in self.genotypes.iteritems():
			if g[0] != ".":
				allele = int(g[0])
				if allele > highestAllele:
					highestAllele = allele
				if i in caseIndividuals:
					caseAlleles[allele] += 1
					totalCaseAlleles += 1
				elif i in controlIndividuals:
					controlAlleles[allele] += 1
					totalControlAlleles += 1
			if g[2] != ".":
				allele = int(g[2])
				if allele > highestAllele:
					highestAllele = allele
				if i in caseIndividuals:
					caseAlleles[allele] += 1
					totalCaseAlleles += 1
				elif i in controlIndividuals:
					controlAlleles[allele] += 1
					totalControlAlleles += 1
		
		self.scores["allele_list"] = range(highestAllele+1)
		self.scores["case_allele_count"] = []
		self.scores["control_allele_count"] = []
		self.scores["case_allele_frequency"] = []
		self.scores["control_allele_frequency"] = []
		
		numCases = float(len(caseIndividuals))
		numControls = float(len(controlIndividuals))
		
		if highestAllele == 0:
			self.scores["odds_ratio"] = 0.0
		
		for a in self.scores["allele_list"]:
			self.scores["case_allele_count"].append(caseAlleles[a])
			self.scores["control_allele_count"].append(controlAlleles[a])
			if totalCaseAlleles == 0.0:
				self.scores["case_allele_frequency"].append(0.0)
			else:
				self.scores["case_allele_frequency"].append(caseAlleles[a] / totalCaseAlleles)
			if totalControlAlleles == 0.0:
				self.scores["control_allele_frequency"].append(0.0)
			else:
				self.scores["control_allele_frequency"].append(controlAlleles[a] / totalControlAlleles)
			if a == 0:
				scoreLabel = "protective_odds_ratio" # does this make sense?
			elif a == 1:
				scoreLabel = "odds_ratio"
			elif a > 1:
				scoreLabel = "odds_ratio_for_allele_%s" % a
			
			denominator = (controlAlleles[a] * (2 * numCases - caseAlleles[a]))
			if denominator == 0:
				if caseAlleles[a] * (2 * numControls - controlAlleles[a]) == 0:
					self.scores[scoreLabel] = 0.0
				else:
					self.scores[scoreLabel] = float("Inf")
			else:
				self.scores[scoreLabel] = (caseAlleles[a] * (2 * numControls - controlAlleles[a])) / denominator
		self.logExtremes()
	
	def makeAlleleListsReadable(self):
		tempCaseCount = ""
		tempControlCount = ""
		tempCaseFreq = ""
		tempControlFreq = ""
		
		for a in self.scores["allele_list"]:
			tempCaseCount += "%s: %s," % (a,self.scores["case_allele_count"][a])
			tempControlCount += "%s: %s," % (a,self.scores["control_allele_count"][a])
			tempCaseFreq += "%s: %s," % (a,self.scores["case_allele_frequency"][a])
			tempControlFreq += "%s: %s," % (a,self.scores["control_allele_frequency"][a])
		
		self.scores["case_allele_count"] = tempCaseCount[:-1]
		self.scores["control_allele_count"] = tempControlCount[:-1]
		self.scores["case_allele_frequency"] = tempCaseFreq[:-1]
		self.scores["control_allele_frequency"] = tempControlFreq[:-1]
		
		del self.scores["allele_list"]
	
	def colorByScore(self, scoreID, columnIndex=None):
		if not self.scores.has_key(scoreID):
			print "Unknown score: %s" % scoreID
			self.color = scorelessColor
			return
		
		if isinstance(self.scores[scoreID], bool):
			if self.scores[scoreID]:
				self.color = variantColors[5]
				return
			else:
				self.color = variantColors[0]
				return
		
		if not variant.minScores.has_key(scoreID) or not variant.maxScores.has_key(scoreID):
			print "Can't color by %s, because there are no min or max values for that score." % scoreID
			self.color = scorelessColor
			return
		
		minimum = variant.minScores[scoreID]
		maximum = variant.maxScores[scoreID]
		
		if maximum == minimum:
			self.color = variantColors[0]
			return
		
		if isinstance(self.scores[scoreID], list):
			score = self.scores[scoreID][columnIndex]
		else:
			score = self.scores[scoreID]
		
		if score == float("inf"):
			self.color = variantColors[5]
			return
		
		if score == float("-inf"):
			self.color = variantColors[0]
			return
		
		if score == float("NaN"):
			self.color = scorelessColor
			return
		
		self.color = variantColors[int(5.0 * (score - minimum) / (maximum - minimum))]
	
	def getText(self):
		scoreLine = "ID="
		scoreLine+=self.rsNumber
		
		for k,v in sorted(self.scores.iteritems(), key=lambda s: s[0]):
			scoreLine += ";%s=" % k
			if isinstance(v,list):
				for i in v:
					scoreLine+="%s, " % i
				scoreLine = scoreLine[:-2]	# strip off comma and space
			else:
				scoreLine += "%s" % v
		scoreLine += ";color=%s" % self.color
		
		outLine = ""
		
		for i in [self.chromosome, "calculate_distributions", "variant", self.start, self.stop, ".", ".", ".", scoreLine]:
			outLine += "%s\t" % i
		return outLine[:-1]	# strip last tab

###########################
# Global helper functions #
###########################
def die(message, isError=True):
	print message
	print ""
	print "calculateDistributions.py - Calculates raw distribution"
	print "                            metrics across individuals in a"
	print "                            .vcf file(s) for visualization."
	print ""
	print "Usage:"
	print "./calculateDistributions.py --in file [file file file ...]"
	print "                            --out file"
	print "                           [--keepFiltered]"
	print ""
	print "Required Parameters:"
	print "--------------------"
	print "--in -i                 Input vcf file(s). Note: filenames"
	print ".vcf file(s) (input)    cannot start with a \"-\" character."
	print ""
	print "--out -o                Output gff3 file"
	print ".gff3 file (output)"
	print ""
	print "Optional Parameters:"
	print "--------------------"
	print "--keepFiltered -k       Keep filtered variants from .vcf"
	print "                        file. Default: remove filtered"
	print ""
	print "--groups -g             Input tab-delimited file for"
	print "file (input)            defining groups for calculations."
	print "                        The first row contains the labels"
	print "                        of each case (each label must match"
	print "                        a header in the .vcf file), and the"
	print "                        second row contains the labels of"
	print "                        each control."
	print ""
	print "--similar -s            Input tab-delimited file containing"
	print "file (input)            variants for which to calculate"
	print "                        distributional sharing statistics."
	print "                        Each variant should be identified"
	print "                        by its rs number (or, in the case"
	print "                        of an unknown variant, it may be"
	print "                        identified by combining the CHROM,"
	print "                        POS, REF, and ALT columns separated"
	print "                        by underscore characters)."
	print ""
	print "                        This provides only one statistic if"
	print "                        used without the --groups option."
	print ""
	print "--color -c              Select the statistic to color"
	print "                        variants by; when using the --groups"
	print "                        option, default is \"odds_ratio\";"
	print "                        otherwise default is \"QUAL\"."
	print ""
	print "                        Possible options include:"
	print "                        -------------------------"
	print "                        Any INFO field in the VCF file"
	print "                        QUAL"
	print ""
	print "                        Additionally, if the --groups option"
	print "                        is supplied, the following may be"
	print "                        used:"
	print "                        ------------------------------------"
	print "                        odds_ratio"
	print "                        protective_odds_ratio"
	print "                        odds_ratio_for_allele_<n>"
	print "                        case_allele_count"
	print "                        case_allele_frequency"
	print "                        control_allele_count"
	print "                        control_allele_frequency"
	print ""
	print "                        If the --similar option is supplied:"
	print "                        ------------------------------------"
	print "                        Sharing_<rs number>"
	print ""
	print "                        If the --similar AND --groups"
	print "                        parameters are supplied:"
	print "                        -----------------------------"
	print "                        LD_<rs number>"
	print "                        Case_Control_Sharing_<rs number>"
	print ""
	print "--help -h               Displays this message and quits."
	if isError:
		sys.exit(2)
	else:
		sys.exit(1)

def getOption(tag, altTag, numValues=1):
	if tag not in sys.argv:
		tag = altTag
	if tag not in sys.argv:
		return None
	if numValues == 0:
		return tag
	tagIndex = sys.argv.index(tag)
	if tagIndex + numValues >= len(sys.argv):
		return None
	if numValues == 1:
		return sys.argv[tagIndex + 1]
	elif numValues > 1:
		return sys.argv[tagIndex + 1:tagIndex + 1 + numValues]
	elif numValues == -1:
		i = tagIndex + 1
		returnList = []
		while i < len(sys.argv) and not sys.argv[i].startswith("-"):
			returnList.append(sys.argv[i])
			i += 1
		return returnList

def parseHeader(line):
	attributes = {}
	attrString = line[line.find("<") + 1:line.rfind(">")]
	attrList = attrString.split(",")
	for pair in attrList:
		temp = pair.split("=")
		k = temp[0]
		v = temp[1]
		attributes[k] = v
	return attributes

def parseGenotypes(columns):
		genotypes = {}
		for i, c in enumerate(columns):
			genotypes[vcfIndividuals[i]] = c[0:3]
		return genotypes

def parseInfo(attrString):
	attributes = {}
	attrList = attrString.split(";")
	for pair in attrList:
		if "=" not in pair:
			attributes[pair] = True
		else:
			temp = pair.split("=")
			if "," not in temp[1]:
				try:
					attributes[temp[0]] = float(temp[1])
				except ValueError:
					attributes[temp[0]] = temp[1]
			else:
				results = []
				try:
					for t in temp[1].split(","):
						results.append(float(t))
					attributes = results
				except ValueError:
					attributes[temp[0]] = temp[1].split(",")
	return attributes

def parseVariant(line):
	columns = line.split()
	start = int(columns[1])
	stop = start + len(columns[3]) - 1
	info = parseInfo(columns[7])
	filterString = columns[6]
	if not keepFiltered and filterString != "PASS":
		return None
	else:
		info["FILTERs"] = columns[6].split(";")
	info["QUAL"] = float(columns[5])
	return variant(chromosome=columns[0], start=start, stop=stop, ref=columns[3], alt=columns[4], info=info, genotypes=parseGenotypes(columns[9:]), rsNumber=columns[2])
	
	

####################
# Start of program #
####################

# Read in command line options, open files
if getOption("--help", "-h", numValues=0) != None:
		die("", isError=False)
try:
	inFilePaths = getOption("--in", "-i", numValues= -1)
	inFiles = []
	for f in inFilePaths:
		inFiles.append(open(f, 'r'))
	outFile = open(getOption("--out", "-o"), 'w')
	groupPath = getOption("--groups", "-g")
	if groupPath != None:
		groupFile = open(groupPath)
		getGroupStats = True
		colorMode = "odds_ratio"
	similarPath = getOption("--similar","-s")
	if similarPath != None:
		similarFile = open(similarPath)
		getSimilarStats = True
	tempColorMode = getOption("--color", "-c")
	if tempColorMode != None:
		colorMode = tempColorMode
	if getOption("--keepFiltered", "-k") != None:
		keepFiltered = True
except:
	die("ERROR: Can't open file(s) or missing/incorrect arguments")

# Read in vcf files
for inFile in inFiles:
	for regLine in inFile:
	    if len(regLine) <= 1:
	        # ignore blank lines
	        continue
	    line = regLine.strip()
	    if line[0:2] == "##":
	        # Meta info
	        if line.startswith("##filter"):
	        	attributes = parseHeader(line)
	        	vcfFilters[attributes["ID"]] = attributes
	        elif line.startswith("##info"):
	            attributes = parseHeader(line)
	            vcfInfo[attributes["ID"]] = attributes
	        elif line.startswith("##format"):
	            attributes = parseHeader(line)
	            vcfFormat[attributes["ID"]] = attributes
	        else:
	            # Must be some detail like ##UnifiedGenotyper=....
	            pass
	    elif line[0] == "#":
	        # column headers - get individuals from this
	        columns = line.split()
	        columnsToIgnore = ['#chrom', 'pos', 'id', 'ref', 'alt', 'qual', 'filter', 'info', 'format']
	        for c in columns:
	            if c.lower() in columnsToIgnore:
	                continue
	            vcfIndividuals.append(c)
	    else:
	        # actual data - a row is a variant
	        newVariant = parseVariant(regLine)
	        if newVariant != None:
	        	vcfVariants.append(newVariant)
	inFile.close()

# Read in the groups file
if getGroupStats:
	caseIndividuals = groupFile.readline().split()
	controlIndividuals = groupFile.readline().split()
	for c in caseIndividuals:
		if c not in vcfIndividuals:
			die("Individual not in .vcf file: %s" % c)
	for c in controlIndividuals:
		if c not in vcfIndividuals:
			die("Individual not in .vcf file: %s" % c)
	groupFile.close()
	for v in vcfVariants:
		v.calculateGroupScores()

# TODO: read in similar file, run its calculations

# Output the gff3 file
outFile.write(hg19header)	#TODO: add other headers, or an option to provide a custom one

sortedByPosition = sorted(vcfVariants, key=lambda v: v.start)
sortedByChromosome = sorted(sortedByPosition, key=lambda v: v.chromosomeNumber)

for v in sortedByChromosome:
	v.colorByScore(colorMode)
	v.makeAlleleListsReadable()
	outFile.write(v.getText() + "\n")
outFile.close()

