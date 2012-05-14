#!/usr/bin/env python
'''
Created May 2012

@author: Alex Bigelow
'''
from resources.interfaces import unixInterface, unixParameter
from resources.utils import variant, vcfFile

####################
# Start of program #
####################

# Get command line parameters

interface = unixInterface("select_individuals",
                         "This program duplicates a .vcf file, only including a specific subset of individuals. Note: all meta data from "+
                         "the original .vcf file will be preserved; allele frequencies, etc. will probably be incorrect.",
                         requiredParameters = [unixParameter("--in",
                                                             "-i",
                                                             "file",
                                                             "Input file.",
                                                             numArgs = 1),
                                               unixParameter("--individuals",
                                                             "-p",
                                                             "string(s)",
                                                             "List of individuals to include.",
                                                             numArgs = -1),
                                               unixParameter("--out",
                                                             "-o",
                                                             "file",
                                                             "Output file.",
                                                             numArgs = 1)],
                         optionalParameters = [unixParameter("--drop_filtered",
                                                             "-d",
                                                             "boolean",
                                                             "If supplied, will ignore every line in a .vcf file that does not have "+
                                                             "\"PASS\" in its FILTER column.",
                                                             numArgs = 0),
                                               unixParameter("--sort",
                                                             "-s",
                                                             "string",
                                                             "Sort method: possible options include \"UNIX\" and \"NUMXYM\" \\n"+
                                                             "Default is no sorting - will attempt to preserve the "+
                                                             "original order, but this cannot be guaranteed.",
                                                             numArgs = 1)])

outPath = interface.getOption("--out","-o",optional=False)[0]
inPath = interface.getOption("--in","-i",optional=False)[0]
personList = interface.getOption(tag="--individuals",altTag="-p",optional=False)

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

try:
    inFile = open(inPath,'r')
except:
    interface.die("ERROR: Couldn't read %s" % inPath)
try:
    outFile = open(outPath,'w')
except:
    interface.die("ERROR: Couldn't write to %s" % outPath)

print "Loading %s..." % inPath
resultingFile = vcfFile.parseVcfFile(inFile,functionToCall=None,callbackArgs=None,individualsToExclude=[],individualsToInclude=personList,mask=None,returnFileObject=True,skipFiltered=dropVCF,skipVariantAttributes=False,skipGenotypes=False,skipGenotypeAttributes=True,includeAdditionalHeaderInfo=True,forceAlleleMatching=False)
print "Writing %s..." % outPath
resultingFile.writeVcfFile(outFile,sortMethod=sortMethod)
inFile.close()
outFile.close()