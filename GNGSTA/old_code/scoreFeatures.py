#!/usr/bin/env python
'''
Created December 2011

@author: Alex Bigelow
'''

import sys
import os
from decimal import *
from math import log

####################
# Global variables #
####################

# Modified colorblind safe color scheme from colorbrewer2.org
#featureColors = ["F5F5F5","F6E8C3","DFC27D","BF812D","8C510A","543005"]
#variantColors = ["F5F5F5","C7EAE5","80CDC1","35978F","01665E","003C30"]
#featureColors = ["245,245,245","246,232,195","223,129,125","191,129,45","140,81,10","84,48,5"]
#variantColors = ["245,245,245","199,234,229","128,205,193","53,151,143","1,102,94","0,60,48"]
featureColors = ["139,139,139","130,119,131","109,93,117","86,63,96","67,24,74","36,0,42"]
variantColors = ["139,139,139","122,135,119","94,123,90","51,98,55","9,68,31","0,38,9"]
scorelessColor = "200,200,200"
colorModes = {"PVALUE":"genome_permutation_p","RANK":"RANK","SCORE":"SCORE","CI_LOW":"genome_permutation_0.95_ci","CI_HIGH":"genome_permutation_0.95_ci"}

extraHeader = "## Added color, VAAST scores using scoreFeatures.py\n#track gffTags=on color="+scorelessColor+" midColor="+scorelessColor+" altColor="+scorelessColor+"\n"

# Default optional parameters
colorMode = "PVALUE"
featureThreshold = Decimal("-1.0")
variantThreshold = Decimal("-1.0")
includeAllFeatures = True
includeAllVariants = True


#########################
# Global helper classes #
#########################
class feature:
	maxFeatureScore = None
	minFeatureScore = None
	maxVariantScore = None
	minVariantScore = None
		
	# -Infinity indicates no score has been set, Infinity indicates the feature should be filtered from output
	def __init__(self, isVariant=False):
		self.chromosome = None
		self.source = None
		self.featureType = None
		self.start = None
		self.stop = None
		self.score = None
		self.strand = None
		self.phase = None
		self.attributes = {}
		if isVariant:
			self.setVariantScore(Decimal("-Infinity"))
		else:
			self.setFeatureScore(Decimal("-Infinity"))
	
	def overlap(self, otherFeature):
		if self.chromosome != otherFeature.chromosome:
			return False
		if self.start > otherFeature.stop:
			return False
		if otherFeature.start > self.stop:
			return False
		return True
	
	def setColor(self, isVariant=False):
		if self.colorScore == Decimal("Infinity"):
			self.attributes["color"]="EXCLUDE"
		elif self.colorScore == Decimal("-Infinity"):
			self.attributes["color"]=scorelessColor
		elif isVariant:
			if feature.minVariantScore == None or feature.maxVariantScore == None:
				self.attributes["color"]=scorelessColor
				return
			score = self.colorScore - feature.minVariantScore
			i = 0
			scoreBin = (feature.maxVariantScore-feature.minVariantScore)/5
			if scoreBin == 0:
				scoreBin = 1
			while score > i*scoreBin:
				i+=1
			if i > 5:
				i = 5
			
			self.attributes["color"]=variantColors[i]
		else:
			if feature.minFeatureScore == None or feature.maxFeatureScore == None:
				self.attributes["color"]=scorelessColor
				return
			score = self.colorScore - feature.minFeatureScore
			i = 0
			scoreBin = (feature.maxFeatureScore-feature.minFeatureScore)/5
			if scoreBin == 0:
				scoreBin = 1
			while score > i*scoreBin:
				i+=1
			# this should only happen with float round off errors:
			if i > 5:
				i = 5
						
			self.attributes["color"]=featureColors[i]
	
	def setFeatureScore(self, score):
		self.colorScore = score
		if score == Decimal("Infinity") or score == Decimal("-Infinity"):
			return
		if feature.maxFeatureScore == None or self.colorScore > feature.maxFeatureScore:
			feature.maxFeatureScore = self.colorScore
		if feature.minFeatureScore == None or self.colorScore < feature.minFeatureScore:
			feature.minFeatureScore = self.colorScore
	
	def setVariantScore(self, score):
		self.colorScore = score
		if score == Decimal("Infinity") or score == Decimal("-Infinity"):
			return
		if feature.maxVariantScore == None or self.colorScore > feature.maxVariantScore:
			feature.maxVariantScore = self.colorScore
		if feature.minVariantScore == None or self.colorScore < feature.minVariantScore:
			feature.minVariantScore = self.colorScore
	
	def parseAndSetAttributes(self, attrs):
		pairs = attrs.split(";")
		for p in pairs:
			temp = p.split("=")
			self.attributes[temp[0]] = temp[1]
	
	def getLine(self, isVariant=False):
		if self.colorScore == Decimal("Infinity"):
			return None
		if self.colorScore == Decimal("-Infinity"):
			if isVariant and not includeAllVariants:
				return None
			elif not includeAllFeatures:
				return None
		attrString = ""
		attrString+="ID="+self.attributes["ID"]+";"
		sortedByTag = sorted(self.attributes.iteritems(), key=lambda pair: pair[0])
		for k,v in sortedByTag:
			if k != "ID":
				attrString+=k+"="+v+";"
		return "%s\t%s\t%s\t%i\t%i\t%s\t%s\t%s\t%s" % (self.chromosome,self.source,self.featureType,self.start,self.stop,self.score,self.strand,self.phase,attrString[:-1])

###########################
# Global helper functions #
###########################
def die(message, isError=True):
	print message
	print ""
	print "scoreFeatures.py - A program that scores a feature file based on"
	print "                   output from VAAST for visualization in IGV"
	print ""
	print "Usage:"
	print "./scoreFeatures.py --vaast file --features file"
	print "                   --feature_out file --variant_out file"
	print "                   [--feature_threshold float]"
	print "                   [--variant_threshold float]"
	print "                   [--help]"
	print ""
	print "Required Parameters:"
	print "--------------------"
	print "--vaast -s              VAAST output file to score features"
	print ".vaast file (input)"
	print ""
	print "--features -f           GFF3 file containing features to be"
	print ".gff3 file (input)      scored. This should be the same file"
	print "                        used as input to VAAST and VAT."
	print "                        NOTE: FFL support coming soon!"
	print ""
	print "--feature_out -o        GFF3 file with scored features, ready"
	print ".gff3 file (output)     for viewing in IGV."
	print ""
	print "--variant_out -v        GFF3 file with scored variants, ready"
	print ".gff3 file (output)     for viewing in IGV."
	print ""
	print "Optional Parameters:"
	print "--------------------"
	print "--feature_threshold  -t Don't include features below this"
	print "float                   threshold in the output file. If"
	print "                        negative, ALL features (including"
	print "                        unscored features in the feature file)"
	print "                        will be included."
	print "                        Default: -1.0"
	print ""
	print "--variant_threshold  -l Don't include variants below this"
	print "float                   threshold in the output file. If"
	print "                        negative, ALL variants (including"
	print "                        variants only seen in background"
	print "                        genomes) will be included."
	print "                        Default: -1.0"
	print ""
	print "--mode -m               Sets which metric to color in IGV;"
	print "string                  possible options are:"
	print "                        \"RANK\" \"SCORE\" \"PVALUE\" \"CI_LOW\" \"CI_HIGH\""
	print "                        NOTE: PVALUE and RANK will invert"
	print "                        scoring (i.e. the lowest values will"
	print "                        score the highest), as well as feature"
	print "                        threshold function (i.e. don't include"
	print "                        values ABOVE the threshold. A negative"
	print "                        threshold will still retain all"
	print "                        variants). Also, PVALUE uses a log scale"
	print "                        in the color map."
	print "                        Default: PVALUE"
	print ""
	print "--help -h               Displays this message and quits."
	if isError:
		sys.exit(2)
	else:
		sys.exit(1)

def getOption(tag, altTag, hasValue=True):
	if tag not in sys.argv:
		tag = altTag
	if tag not in sys.argv:
		return None
	if not hasValue:
		return tag
	tagIndex = sys.argv.index(tag)
	if tagIndex+1 == len(sys.argv):
		return None
	return sys.argv[tagIndex+1]

def setFeatureScore(featureObject, scoreString):
	score = Decimal(scoreString)
	if colorMode == "PVALUE":	# Log score
		score = Decimal(str(log(float(score)+0.01,10)))
	if colorMode == "PVALUE" or colorMode == "RANK":	# Golf (inverted) scoring
		score = -score
	if score >= featureThreshold:
		featureObject.setFeatureScore(score)
	elif not includeAllFeatures:
		featureObject.setFeatureScore(Decimal("Infinity"))

def setVariantScore(featureObject, scoreString):
	score = Decimal(scoreString)
	if score >= variantThreshold:
		featureObject.setVariantScore(score)
	elif not includeAllVariants:
		featureObject.setVariantScore(Decimal("Infinity"))

def getIDfromString(attrs):
		pairs = attrs.split(";")
		attributes = {}
		for p in pairs:
			temp = p.split("=")
			attributes[temp[0]] = temp[1]
		if not attributes.has_key("ID"):
			die("ERROR: feature has no ID")
		else:
			return attributes["ID"]

def setVariantVariables(f,chromosome,position,score,strand,details):
	f.chromosome = chromosome
	f.source = "VAAST_output"
	f.featureType = "SNP"	# TODO: this will need to change when indels are supported
	f.start = int(position)
	f.stop = int(position)
	f.score = score
	f.strand = strand
	f.phase = "."
	if f.score != ".":
		setVariantScore(f, f.score)
		f.attributes["VAAST score"] = score
	
	referenceNucleotide=details[0][0]
	if "|" in details[0]:
		referenceAminoAcid=details[0][2]
	else:
		referenceAminoAcid=None
	for genotypeGroup in details[1:]:
		sections = genotypeGroup.split("|")
		if sections[0] == "N":
			seenIn = "Targets only"
		elif sections[0] == "B":
			seenIn = "Targets and Background"
		else:
			seenIn = "Background only"
			sections.insert(0,"BO")	# the background lines don't have N or B
		nucleotideOne = sections[2][0]
		nucleotideTwo = sections[2][2]
		if referenceAminoAcid != None:
			aminoAcidOne = sections[3][0]
			aminoAcidTwo = sections[3][2]
		individuals = sections[1]
		
		nucleotideChange = "Base change %s/%s->%s/%s seen in %s" % (referenceNucleotide,referenceNucleotide,nucleotideOne,nucleotideTwo,seenIn)
		if referenceAminoAcid != None:
			aminoAcidChange = "Amino Acid change %s/%s->%s/%s seen in %s" % (referenceAminoAcid,referenceAminoAcid,aminoAcidOne,aminoAcidTwo,seenIn)
		
		if f.attributes.has_key(nucleotideChange):
			continue
		f.attributes[nucleotideChange] = individuals
		
		if referenceAminoAcid != None:
			if f.attributes.has_key(aminoAcidChange):
				continue
			f.attributes[aminoAcidChange] = individuals
		
####################
# Start of program #
####################

# Read in command line options, open files
if getOption("--help","-h",hasValue=False) != None:
		die("",isError=False)
try:
	scoreFile = open(getOption("--vaast","-s"),'r')
	inFeatureFile = open(getOption("--features","-f"),'r')
	outFeatureFile = open(getOption("--feature_out","-o"),'w')
	outVariantFile = open(getOption("--variant_out","-v"),'w')
	temp = getOption("--feature_threshold","-t")
	if temp != None:
		featureThreshold = Decimal(temp)
	temp = getOption("--variant_threshold","-l")
	if temp != None:
		variantThreshold = Decimal(temp)
	if featureThreshold < Decimal("0.0"):
		includeAllFeatures = True
	else:
		includeAllFeatures = False
	if variantThreshold < Decimal("0.0"):
		includeAllVariants = True
	else:
		includeAllVariants = False
	
	temp = getOption("--mode","-m")
	if temp != None:
		colorMode = temp
	if colorMode not in colorModes.iterkeys():
		die("Unknown --mode option: "+colorMode)
	if colorMode == "PVALUE" and not includeAllFeatures:
		featureThreshold = Decimal(str(log(float(featureThreshold)+0.01,10)))
	elif colorMode == "PVALUE":
		featureThreshold = Decimal(str(log(1.01,10)))
	if colorMode == "PVALUE" or colorMode == "RANK":
		featureThreshold = -featureThreshold
except:
	die("ERROR: Can't open file(s) or missing/incorrect arguments")

# Run through the vaast file and pull out scores that we want to keep
currentFeature = None
currentStrand = "?"
myVariants = {}
myFeatures = {}

for line in scoreFile:
	if len(line) <= 1 or line.startswith("##"):
		continue
	if line.startswith(">"):
		columns = line.split()
		currentFeature = columns[0][1:]
	elif line.startswith("chr"):
		currentStrand = line.split()[1]
	elif line.startswith("BR") and includeAllVariants:
		columns = line[:-1].split()
		currentVariant = columns[1]
		if not myVariants.has_key(currentVariant):
			myVariants[currentVariant] = feature(isVariant=True)
		myVariants[currentVariant].attributes["ID"] = currentVariant
		temp = currentVariant.split("@")
		setVariantVariables(myVariants[currentVariant],chromosome=temp[1],position=temp[0],score=".",strand=currentStrand,details=columns[2:])
	elif line.startswith("TU") or line.startswith("TR"):
		columns = line[:-1].split()
		currentVariant = columns[2]
		if not myVariants.has_key(currentVariant):
			myVariants[currentVariant] = feature(isVariant=True)
		myVariants[currentVariant].attributes["ID"] = currentVariant
		temp = currentVariant.split("@")
		setVariantVariables(myVariants[currentVariant],chromosome=temp[1],position=temp[0],score=columns[1],strand=currentStrand,details=columns[3:])
	else:
		for modeTag,scoreTag in colorModes.iteritems():
			if line.startswith(scoreTag):
				scoreString = line[:-1].split(":")[1]
				
				# Add the feature if we haven't yet
				if not myFeatures.has_key(currentFeature):
					if currentFeature == None:
						die("ERROR: vaast file is ill-formed or corrupted.")
					myFeatures[currentFeature]=feature()
					myFeatures[currentFeature].attributes["ID"] = currentFeature
				
				# Add the score as an attribute
				myFeatures[currentFeature].attributes[scoreTag] = scoreString
				
				# If the score happens to be the one we're coloring features by, set the color
				if colorMode.startswith("CI") and "," in scoreString:
					scoreStrings = scoreString.split(",")
					if colorMode == "CI_LOW":
						setFeatureScore(myFeatures[currentFeature],scoreStrings[0])
					elif colorMode == "CI_HIGH":
						setFeatureScore(myFeatures[currentFeature],scoreStrings[1])
				elif colorMode == modeTag:
					setFeatureScore(myFeatures[currentFeature],scoreString)
scoreFile.close()


# Now run through the feature file, get all the other details we need about (maybe only scored)
# features and variants, and output them as we find them - this will preserve the sort order of
# the original gff3 file as well
finishedHeader = False
for line in inFeatureFile:
	if len(line) <= 1:
		continue
	if line.startswith("#"):
		outFeatureFile.write(line)
		outVariantFile.write(line)
	elif line.startswith("chr"):
		if not finishedHeader:
			outFeatureFile.write(extraHeader)
			outFeatureFile.write("## colorMode=%s\n" % colorMode)
			outVariantFile.write(extraHeader)
			finishedHeader = True
		columns = line[:-1].split("\t")
		if len(columns) != 9:
			if len(line.split()) == 0:
				continue
			else:
				die("ERROR: gff3 file is ill-formed or corrupted.")
		
		# Okay, we've dealt with all the header stuff and error checking; now write the actual row
		currentFeature=getIDfromString(columns[8])
		if not myFeatures.has_key(currentFeature):
			if not includeAllFeatures:
				continue
			myFeatures[currentFeature]=feature()
		f = myFeatures[currentFeature]
		f.chromosome=columns[0]
		f.source=columns[1]
		f.featureType=columns[2]
		f.start=int(columns[3])
		f.stop=int(columns[4])
		f.score=columns[5]
		f.strand=columns[6]
		f.phase=columns[7]
		f.parseAndSetAttributes(columns[8])
		# Before we actually print it, we need to normalize the color
		f.setColor()
		outString = f.getLine()
		if outString != None:
			outFeatureFile.write(outString + "\n")
inFeatureFile.close()
outFeatureFile.close()

sortedByPosition = sorted(myVariants.itervalues(), key=lambda v: v.start)
sortedByChromosome = sorted(sortedByPosition, key=lambda v: v.chromosome)
# TODO: this will probably do a unix sort of chromosomes...

for variant in sortedByChromosome:
	# Normalize the color
	variant.setColor(isVariant=True)
	outString = variant.getLine(isVariant=True)
	if outString != None:
		outVariantFile.write(outString + "\n")

outVariantFile.close()