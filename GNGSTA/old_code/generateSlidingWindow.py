#!/usr/bin/env python
'''
Created December 2011

@author: Alex Bigelow
'''

import sys
import os
from gffGlobals import hg19header

####################
# Global variables #
####################

truncateLastWindow = False

#########################
# Global helper classes #
#########################
class region:
	def __init__(self, chromosome, start, stop, region_name=None):
		self.chromosome = chromosome
		self.start = start
		self.stop = stop
		self.region_name=region_name
	
	def generateWindowList(self, windowSize, interleave):
		returnList = []
		# +1, -1 converts BED to GFF3 coordinates, except for interleave+1
		i = self.start+1
		while i+windowSize-1 < self.stop:
			returnList.append(window(self.chromosome,i,i+windowSize-1,self.region_name))
			i+=windowSize/(interleave+1)	# +1: translates number of overlaps to distance
		# Final window:
		if i < self.stop:
			returnList.append(window(self.chromosome,i,i+windowSize-1,self.region_name,windowEnd=self.stop))
		return returnList

class window:
	myNames = {}
	def __init__(self, chromosome, start, stop, window_name=None, windowEnd=None):
		self.chromosome = chromosome
		if "chr" in chromosome:
			self.chromosomeNumber = int(chromosome[3:])
		else:
			self.chromosomeNumber = int(chromosome)
		self.start = start
		self.stop = stop
		if window_name==None:
			window_name = "Window"
		if window.myNames.has_key(window_name):
			window.myNames[window_name] += 1
		else:
			window.myNames[window_name] = 1
		self.window_name = window_name + ".%i" % window.myNames[window_name]
		if truncateLastWindow and windowEnd != None and windowEnd < self.stop:
			self.stop = windowEnd
	
	def getText(self):
		outLinePlus = ""
		for i in [self.chromosome,"sliding_window","window",self.start,self.stop,".","+",".","ID="+self.window_name+"+"]:
			outLinePlus += "%s\t" % i
		outLineMinus = ""
		for i in [self.chromosome,"sliding_window","window",self.start,self.stop,".","-",".","ID="+self.window_name+"-"]:
			outLineMinus += "%s\t" % i
		return (outLinePlus[:-1],outLineMinus[:-1])	# strip last tab

###########################
# Global helper functions #
###########################
def die(message, isError=True):
	print message
	print ""
	print "generateSlidingWindow.py - Generates features in .gff3"
	print "                           format for use in VAAST as a"
	print "                           sliding window"
	print ""
	print "                           NOTE: when using features"
	print "                           generated by this program, you"
	print "                           should include these parameters"
	print "                           when running VAAST:"
	print ""
	print "                           --all_variants"
	print "                           --parent_feature window"
	print ""
	print "Usage:"
	print "./generateSlidingWindow.py --regions file"
	print "                           --out file"
	print "                           --windowSize int"
	print "                           --interleave int"
	print "                          [--truncateLastWindow]"
	print "                          [--help]"
	print ""
	print "Required Parameters:"
	print "--------------------"
	print "--regions -r            File containing regions that the"
	print ".bed file (input)       windows will span."
	print ""
	print "--out -o                Place to write output features;"
	print ".gff3 file (output)     the format will be gff3."
	print ""
	print "--windowSize -w         Size of each window in bp."
	print "int                     Windows follow the GFF3 1-based"
	print "                        coordinates (not the BED 0-base)"
	print ""
	print "--interleave -i         Number of windows that can overlap;"
	print "int                     this determines the spacing of"
	print "                        windows. For example:"
	print ""
	print "                        -w 100 -i 0"
	print "                        over a BED region from 0 to 1999"
	print "                        the resulting GFF3 windows will be:"
	print "                        1-100,101-200,201-300..."
	print ""
	print "                        -w 100 -i 1"
	print "                        over the same region would yield:"
	print "                        1-100,51-150,101-200,151-250..."
	print ""
	print "Optional Parameters:"
	print "--------------------"
	print "--truncateLastWindow -t If the length of a region is not"
	print "                        evenly divisible by windowSize,"
	print "                        truncate the last window to fit."
	print "                        Default: no truncation (the last"
	print "                        window will go a little beyond the"
	print "                        region."
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

####################
# Start of program #
####################

# Read in command line options, open files
if getOption("--help","-h",hasValue=False) != None:
		die("",isError=False)
try:
	regionFile = open(getOption("--regions","-r"),'r')
	outFile = open(getOption("--out","-o"),'w')
	windowSize = int(getOption("--windowSize","-w"))
	interleave = int(getOption("--interleave","-i"))
	if getOption("--truncateLastWindow","-t",hasValue=False) != None:
		truncateLastWindow = True
	if windowSize <= 0:
		die("ERROR: windowSize must be > 1 bp")
	if interleave < 0:
		die("ERROR: interleave must be >= 0")
except:
	die("ERROR: Can't open file(s) or missing/incorrect arguments")

# Build list of regions
myRegions = []
for line in regionFile:
	if len(line) <= 1 or not line.startswith("chr"):
		continue
	columns = line.split()
	if len(columns) < 3:
		die("ERROR: ill-formed or corrupt BED file")
	myRegions.append(region(columns[0],int(columns[1]),int(columns[2])))
regionFile.close()

# Generate the windows
myWindows = []
for r in myRegions:
	myWindows.extend(r.generateWindowList(windowSize,interleave))

# Output the gff3 file
outFile.write(hg19header)	#TODO: add other headers, or an option to provide a custom one
sortedByPosition = sorted(myWindows, key=lambda w: w.start)
sortedByChromosome = sorted(sortedByPosition, key=lambda w: w.chromosomeNumber)
for w in sortedByChromosome:
	plusText,minusText = w.getText()
	outFile.write(plusText + "\n")
	outFile.write(minusText + "\n")
outFile.close()