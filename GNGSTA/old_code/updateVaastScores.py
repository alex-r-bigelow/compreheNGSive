#!/usr/bin/env python
'''
Created December 2011

@author: Alex Bigelow
'''

import sys
import os
from gffGlobals import colorModes
from utils import recursiveDict

###########################
# Global helper functions #
###########################
def die(message, isError=True):
	print message
	print ""
	print "updateVaastScores.py - Creates an updated .vaast score file"
	print "                       from two .vaast score files; one"
	print "                       one should contain results from a run"
	print "                       with a high threshold, and the other"
	print "                       should contain results from a run on"
	print "                       a filtered feature set and a lower"
	print "                       threshold."
	print ""
	print "Usage:"
	print "./updateVaastScores.py --original file"
	print "                       --update file"
	print "                       --out file"
	print "                      [--help]"
	print ""
	print "Required Parameters:"
	print "--------------------"
	print "--origianl -s          .vaast score file (high threshold, many"
	print ".vaast file (input)    features)"
	print ""
	print "--update -u            .vaast score file (lower threshold,"
	print ".vaast file (input)    fewer features"
	print ""
	print "--out -o               .vaast score file containing all"
	print ".vaast file (output)   features from --original, but with"
	print "                       updated scores from --update"
	print ""
	print "Optional Parameters:"
	print "--------------------"
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

####################
# Start of program #
####################

legalExtensions = [".vaast",".simple"]

# Read in command line options, open files
if getOption("--help","-h",numValues=0) != None:
		die("",isError=False)
try:
	firstPath = getOption("--original","-s")
	firstType = os.path.splitext(firstPath)[1]
	if firstType not in legalExtensions:
		die("Illegal file extension: %s" % firstType)
	firstFile = open(firstPath,'r')
	
	secondPath = getOption("--update","-u")
	secondType = os.path.splitext(secondPath)[1]
	if secondType not in legalExtensions:
		die("Illegal file extension: %s" % secondType)
	secondFile = open(secondPath,'r')
	
	outPath = getOption("--out","-o")
	outType = os.path.splitext(outPath)[1]
	if outType not in legalExtensions:
		die("Illegal file extension: %s" % outType)
	if outType != secondType or secondType != firstType:
		die("All files must have same extension.")
	outFile = open(outPath,'w')
except:
	die("ERROR: Can't open file(s) or missing/incorrect arguments")

if firstType == ".vaast":
	# Run through the second vaast file and pull out features and scores that we'll want to update with
	currentFeature = None
	myFeatures = recursiveDict()
	
	for line in secondFile:
		if len(line) <= 1:
			continue
		elif line.startswith(">"):
			currentFeature = line
		else:
			for scoreTag in colorModes.itervalues():
				if line.startswith(scoreTag):
					if currentFeature == None:
						die("ERROR: Update file improperly formed or corrupted.")
					myFeatures[currentFeature][scoreTag] = line
	secondFile.close()
	
	# Now run through the first vaast file, swapping in lines that should be swapped in
	currentFeature = None
	
	for line in firstFile:
		if line.startswith(">"):
			currentFeature = line
		
		addedNewLine = False
		if myFeatures.has_key(currentFeature):
			for scoreTag in colorModes.itervalues():
				if line.startswith(scoreTag):
					outFile.write(myFeatures[currentFeature][scoreTag])
					addedNewLine = True
					break
		
		if not addedNewLine:
			outFile.write(line)
	secondFile.close()
	outFile.close()
elif firstType == ".simple":
	# Run through the second simple file and pull out features and scores that we'll want to update with
	currentFeature = None
	myFeatures = recursiveDict()
	
	for line in secondFile:
		if len(line) <= 1:
			continue
		else:
			columns = line.split()
			currentFeature = columns[1]
			rank = columns[0]
			myFeatures[currentFeature]["line"] = line
			myFeatures[currentFeature]["rank"] = rank
	secondFile.close()
	
	# Now run through the first vaast file, swapping in lines that should be swapped in
	currentFeature = None
	
	for line in firstFile:
		if line.startswith(">"):
			currentFeature = line
		else:
			columns = line.split()
			currentFeature = columns[1]
			if not myFeatures.has_key(currentFeature):
				outFile.write(line)
			else:
				rank = columns[0]
				if rank != myFeatures[currentFeature]["rank"]:
					outFile.write(rank + "," + myFeatures[currentFeature]["line"])
				else:
					outFile.write(myFeatures[currentFeature]["line"])
	secondFile.close()
	outFile.close()