#!/usr/bin/env python
'''
Created April 2012

@author: Alex Bigelow
'''
from resources.interfaces import unixInterface, unixParameter

####################
# Start of program #
####################

# Get command line parameters

interface = unixInterface("addChr.py",
                         "Adds \"chr\" to the beginning of every non-blank line that doesn't start with \"#\".",
                         requiredParameters = [unixParameter("--in",
                                                             "-i",
                                                             "file",
                                                             "Input .vcf file.",
                                                             numArgs = 1),
                                               unixParameter("--out",
                                                             "-o",
                                                             "file",
                                                             "Output .vcf file.",
                                                             numArgs = 1)],
                         optionalParameters = [])

outPath = interface.getOption("--out","-o",optional=False)[0]
inPath = interface.getOption("--in","-i",optional=False)[0]

try:
    inFile = open(inPath,'r')
    outFile = open(outPath,'w')
except:
    interface.die("ERROR: Couldn't open %s" % outPath)

for line in inFile:
    if len(line) <= 1 or line.startswith("#"):
        outFile.write(line)
    else:
        outFile.write("chr" + line)

inFile.close()
outFile.close()