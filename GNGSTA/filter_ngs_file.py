#!/usr/bin/env python
'''
Created January 2012

@author: Alex Bigelow
'''
from resources.interfaces import unixInterface, unixParameter
from resources.utils import bedFile, vcfFile, phastconsFile, gff3File
import os

####################
# Start of program #
####################

# Get command line parameters

interface = unixInterface("filter_ngs_file",
                         "This program filters any of:  \\n .vcf .cdr .gff3 .bed .txt(phastcons) \\n" +
                         "to only contain items that are contained in/overlapped by regions specified in a bed file. " +
                         "The type will automatically be determined from the file extension.",
                         requiredParameters = [unixParameter("--in",
                                                             "-i",
                                                             "file",
                                                             "Input file.",
                                                             numArgs = 1),
                                               unixParameter("--filter",
                                                             "-f",
                                                             "file",
                                                             "Bed file containing regions with which to filter.",
                                                             numArgs = 1),
                                               unixParameter("--out",
                                                             "-o",
                                                             "file",
                                                             "Output file.",
                                                             numArgs = 1)],
                         optionalParameters = [unixParameter("--sort",
                                                             "-s",
                                                             "string",
                                                             "Sort method: possible options include \"UNIX\" and \"NUMXYM\" \\n"+
                                                             "Default is no sorting - will attempt to preserve the "+
                                                             "original order, but this cannot be guaranteed.",
                                                             numArgs = 1),
                                               unixParameter("--drop_filtered",
                                                             "-d",
                                                             "boolean",
                                                             "If supplied, will ignore every line in a .vcf file that does not have "+
                                                             "\"PASS\" in its FILTER column.",
                                                             numArgs = 0)])

outPath = interface.getOption("--out","-o",optional=False)[0]
inPath = interface.getOption("--in","-i",optional=False)[0]
bedPath = interface.getOption(tag="--filter",altTag="-f",optional=False)[0]

sortMethod = interface.getOption(tag="--sort",altTag="-s",optional=True)
if sortMethod != None and len(sortMethod) > 0:
    sortMethod = sortMethod[0]
else:
    sortMethod = None

dropVCF = interface.getOption(tag="--drop_filtered",altTag="-d",optional=True)
if dropVCF == None or len(dropVCF) == 0:
    dropVCF = False
else:
    dropVCF = True

fileType = os.path.splitext(inPath)[1]
if os.path.splitext(outPath)[1] != fileType:
    interface.die("ERROR: Input/output files must have the same extension.")

try:
    regionFile = open(bedPath,'r')
except:
    interface.die("ERROR: Couldn't open %s" % bedPath)
regions = bedFile.parseBedFile(regionFile)
regionFile.close()

try:
    outFile = open(outPath,'w')
except:
    interface.die("ERROR: Couldn't open %s" % outPath)

try:
    inFile = open(inPath,'r')
except:
    interface.die("ERROR: Couldn't open %s" % inPath)

########################
# Back to main program #
########################

# TODO: I can speed this up by writing lines as I get them instead of storing everything in a file object...
if fileType == ".vcf":
    temp = vcfFile.parseVcfFile(inFile,functionToCall=None,callbackArgs={},individualsToExclude=[],individualsToInclude=[],mask=regions,returnFileObject=True,skipFiltered=dropVCF,skipVariantAttributes=False,skipGenotypes=False,skipGenotypeAttributes=False,includeAdditionalHeaderInfo=False)
    temp.writeVcfFile(outFile,sortMethod=sortMethod)
elif fileType == ".gff3":
    temp = gff3File.parseGff3File(inFile,functionToCall=None,callbackArgs={},columnsToExclude=[],mask=regions,returnFileObject=True)
    temp.writeGff3File(outFile, sortMethod=sortMethod)
elif fileType == ".cdr":
    print "WARNING: CDR not implemented yet! Will generate empty file."
elif fileType == ".txt":    # For now, assume phastcons...
    temp = phastconsFile.parsePhastconsFile(inFile,functionToCall=None,callbackArgs={},mask=regions,returnFileObject=True)
    temp.writePhastconsFile(outFile, sortMethod=sortMethod)
elif fileType == ".bed":
    temp = bedFile.parseBedFile(fileObject,functionToCall=None,callbackArgs={},mask=regions,returnFileObject=True)
    temp.writeBedFile(outFile, sortMethod=sortMethod)
else:
    interface.die("ERROR: Unsupported file type: %s" % fileType)

outFile.close()
inFile.close()