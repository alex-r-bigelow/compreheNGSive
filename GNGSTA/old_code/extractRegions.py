#!/usr/bin/env python
'''
Created December 2011

@author: Alex Bigelow
'''
import sys
import os
from decimal import *

def die(message):
	print message
	print ""
	print "Usage:"
	print "./extractRegions.py --vaast file --threshold float [--ffl file] [--gff3 file] --out outFile"
	print "Exactly one of the options in brackets is required."
	sys.exit(2)

def getOption(tag):
	if tag not in sys.argv:
		return None
	tagIndex = sys.argv.index(tag)
	if tagIndex+1 == len(sys.argv):
		return None
	return sys.argv[tagIndex+1]
#try:
featurePath = getOption("--gff3")
isFFL = False
if featurePath == None:
	featurePath = getOption("--ffl")
	isFFL = True
	if featurePath == None:
		die("Must supply either a gff3 or ffl file")
featureFile = open(featurePath,'r')
outFile = open(getOption("--out"),'w')
inFile = open(getOption("--vaast"),'r')
threshold = Decimal(getOption("--threshold"))
#except:
#	die("Error reading file(s) and/or missing/incorrect arguments")

class feature:
	def __init__(self, chromosome, start, stop=-1, score = -1.0, parentID="", fullText=""):
		self.chromosome = chromosome
		self.chromosomeNumber = int(chromosome[3:])
		self.start = start
		self.score = score
		self.parentID = parentID
		self.fullText = fullText
		
		if stop == -1:
			self.stop = self.start
		else:
			self.stop = stop
	
	def overlap(self, otherFeature):
		if self.chromosome != otherFeature.chromosome:
			return False
		if self.start > otherFeature.stop:
			return False
		if otherFeature.start > self.stop:
			return False
		return True
	
	def setScore(self, score):
		self.score = score
	
# Build the lookup dictionary for the ffl or gff3 file:
myFeatures = {}

def getParentScore(featureID):
	currentScore = myFeatures[featureID].score
	currentFeature = myFeatures[featureID]
	while currentScore == -1.0:
		if currentFeature.parentID == "" or not myFeatures.has_key(currentFeature.parentID):
			return -1.0
		else:
			currentFeature = myFeatures[currentFeature.parentID]
			currentScore = currentFeature.score
	return currentScore


if not isFFL:
	headerText = ""
	for line in featureFile:
		if len(line) <= 1:
			continue
		if line.startswith("#"):
			headerText += line
		elif line.startswith("chr"):
			columns = line[:-1].split("\t")
			attributes = {}
			details = columns[8].split(";")
			for d in details:
				temp = d.split("=")
				attributes[temp[0]]=temp[1]
			featureID = attributes["ID"]
			if attributes.has_key("Parent"):
				parentID = attributes["Parent"]
			else:
				parentID = ""
			myFeatures[featureID] = feature(columns[0], int(columns[3]), stop=int(columns[4]), parentID=parentID, fullText=line)
	featureFile.close()
	
	for line in inFile:
		if len(line) <= 1:
			continue
		if line.startswith(">"):
			columns = line[:-1].split()
			currentFeature = columns[0][1:]
		elif line.startswith("genome_permutation_p"):
			columns = line.split(":")
			pValue = Decimal(columns[1])
			if pValue <= threshold and currentFeature != None:
				myFeatures[currentFeature].setScore(pValue)
	inFile.close()
	
	outLines = ""
	sortedByPosition = sorted(myFeatures.iteritems(), key=lambda f: f[1].start)
	sortedByChromosome = sorted(sortedByPosition, key=lambda f: f[1].chromosomeNumber)
	for featureID,f in sortedByChromosome:
		if getParentScore(featureID) == -1.0:
			continue
		else:
			outLines += f.fullText
	
	if len(outLines) > 0:
		outFile.write(headerText)
		outFile.write(outLines)
	
	outFile.close()
else:
	featureFile.close()
	# TODO: I do a manual cheating way of building the ffl straight from the vaast file... maybe I should fix this?
	currentFeature = None
	currentChr = None
	currentStart = None
	currentStop = None
	currentStrand = None
	for line in inFile:
		if len(line) <= 1:
			continue
		if line.startswith(">"):
			columns = line.split()
			currentFeature = columns[0][1:]
			currentChr = None
			currentStart = None
			currentStop = None
			currentStrand = None
		elif line.startswith("chr"):
			columns = line.split()
			for i in xrange(2,len(columns)):
				details = columns[i].split(";")
				start = int(details[0])
				stop = int(details[1])
				if currentStart == None or start < currentStart:
					currentStart = start
				if currentStop == None or stop > currentStop:
					currentStop = stop
				currentStrand = details[2]
				currentChr = details[3]
		elif line.startswith("genome_permutation_p"):
			columns = line.split(":")
			pValue = Decimal(columns[1])
			if pValue <= threshold and currentFeature != None and currentChr != None and currentStart != None and currentStop != None and currentStrand != None:
				outFile.write("%s\t%s\t%i;%i\t%s\n" % (currentChr,currentStrand,currentStart,currentStop,currentFeature))
				currentFeature = None
				currentChr = None
				currentStart = None
				currentStop = None
				currentStrand = None
	outFile.close()
	inFile.close()