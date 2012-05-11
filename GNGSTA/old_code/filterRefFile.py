#!/usr/bin/env python
'''
Created December 2011

@author: Alex Bigelow
'''
import sys
import os

def die(message):
	print message
	print ""
	print "Usage:"
	print "./filterRefFile.py --out file [--filter_ffl file --filter_gff3 file --filter_bed file] [--phastcons file --sift file --cdr file --vcf file --gff3 file] {--maxFeatures int}"
	print "Exactly one of the options in each [] is required."
	sys.exit(2)

def getOption(tag):
	if tag not in sys.argv:
		return None
	tagIndex = sys.argv.index(tag)
	if tagIndex+1 == len(sys.argv):
		return None
	return sys.argv[tagIndex+1]

outFilePath = getOption("--out")
fileFormat = ""
featureFormat = ""
for tag in ["--filter_ffl","--filter_gff3","--filter_bed"]:
	featureFilePath = getOption(tag)
	if featureFilePath != None:
		featureFormat=tag[9:]
		break;
	fflFilePath = getOption("--ffl")
for tag in ["--phastcons","--sift","--cdr","--vcf","--gff3"]:
	filterFilePath = getOption(tag)
	if filterFilePath != None:
		fileFormat=tag[2:]
		break;

maxFeatures = getOption("--maxFeatures")
if maxFeatures != None:
	maxFeatures = int(maxFeatures)

if featureFilePath == None or outFilePath == None or filterFilePath == None:
	die("Missing argument(s)")



class feature:
	chromosome = ""
	start = -1
	stop = -1
	
	def __init__(self, chromosome, start, stop=-1):
		self.chromosome = chromosome
		self.start = start
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
	
outFile = open(outFilePath, 'w')
featureFile = open(featureFilePath,'r')
filterFile = open(filterFilePath, 'r')

# Build the lookup dictionary for the ffl file:
myFeatures = []

if featureFormat == "ffl":
	for line in featureFile:
		if len(line) <= 1:
			continue
		
		columns = line.split()
		chromosome = columns[0]
		startStop = columns[2].split(";")
		start = int(startStop[0])
		stop = int(startStop[1])
		
		myFeatures.append(feature(chromosome,start,stop))
elif featureFormat == "gff3":
	for line in featureFile:
		if len(line) <= 1 or line[0] == "#":
			continue
		
		columns = line.split()
		chromosome = columns[0]
		start = int(columns[3])
		stop = int(columns[4])
		
		myFeatures.append(feature(chromosome,start,stop))
elif featureFormat == "bed":
	for line in featureFile:
		if len(line) <= 1:
			continue
		
		columns = line.split()
		chromosome = columns[0]
		start = int(columns[1])
		stop = int(columns[2])
		
		myFeatures.append(feature(chromosome,start,stop))

featureFile.close()

if fileFormat=="phastcons":
	for line in filterFile:
		if len(line) <= 1:
			continue
		
		if maxFeatures != None and len(myFeatures) >= maxFeatures:
			continue
		
		columns = line.split()
		chromosome = columns[0]
		start = int(columns[1])
		# TODO: how big are the phastcons regions? What should I use for stop?
		stop = start+1
		newFeature=feature(chromosome,start,stop)
		for f in myFeatures:
			if f.overlap(newFeature):
				outFile.write(line)
				break
elif fileFormat=="sift":
	for line in filterFile:
		if len(line) <= 1:
			continue
		
		if maxFeatures != None and len(myFeatures) >= maxFeatures:
			continue
		
		columns = line.split()
		chromosome = columns[0]
		start = int(columns[1])
		# TODO: how big are the sift regions? What should I use for stop?
		stop=start+1
		newFeature=feature(chromosome,start,stop)
		for f in myFeatures:
			if f.overlap(newFeature):
				outFile.write(line)
				break
elif fileFormat=="cdr":
	for line in filterFile:
		if len(line) <= 1:
			continue
		
		if line.startswith("#"):
			outFile.write(line)
			continue
		
		if maxFeatures != None and len(myFeatures) >= maxFeatures:
			continue
		
		columns = line.split()
		chromosome = columns[0]
		start = int(columns[1])
		stop = int(columns[2])
		newFeature=feature(chromosome,start,stop)
		for f in myFeatures:
			if f.overlap(newFeature):
				outFile.write(line)
				break
elif fileFormat=="vcf":
	for line in filterFile:
		if len(line) <= 1:
			continue
		
		if line.startswith("#"):
			outFile.write(line)
			continue
		
		if maxFeatures != None and len(myFeatures) >= maxFeatures:
			continue
		columns = line.split()
		chromosome = columns[0]
		start = int(columns[1])
		length = max(len(columns[3]),len(columns[4]))
		stop = start+length
		newFeature=feature(chromosome,start,stop)
		for f in myFeatures:
			if f.overlap(newFeature):
				outFile.write(line)
				break
elif fileFormat=="gff3":
	for line in filterFile:
		if len(line) <= 1:
			continue
		
		if line.startswith("#"):
			outFile.write(line)
			continue
		
		if maxFeatures != None and len(myFeatures) >= maxFeatures:
			continue
		columns = line.split()
		chromosome = columns[0]
		start = int(columns[3])
		stop = int(columns[4])
		
		newFeature=feature(chromosome,start,stop)
		for f in myFeatures:
			if f.overlap(newFeature):
				outFile.write(line)
				break

filterFile.close()
outFile.close()

