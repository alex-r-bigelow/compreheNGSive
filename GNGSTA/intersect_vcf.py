#!/usr/bin/env python
'''
Created January 2012

@author: Alex Bigelow
'''
from resources.interfaces import unixInterface, unixParameter
from resources.utils import vcfFile, bedFile

###############################################
# Global helper functions, classes, variables #
###############################################

def filterCallback(variant,listToKeep):
    listToKeep.add(variant)

def mainCallback(variant,resultingVCF,listToKeep,strict):
    if variant in listToKeep or (not strict and variant.isPolymorphic()):
        resultingVCF.addVariant(variant)

####################
# Start of program #
####################

# Get command line parameters

interface = unixInterface("intersect_vcf.py",
                         "This program only includes variants from a .vcf file that are seen in one or more other .vcf files",
                         requiredParameters = [unixParameter("--filter",
                                                             "-f",
                                                             "file",
                                                             "Input .vcf file(s) to filter with; these are only used to list variants "+
                                                             "that we want to include in the resulting file. The only information that these "+
                                                             "could contribute to --out that might not be found in --in are "+
                                                             "updates to rs numbers and additional possible ALT alleles; no information about "+
                                                             "variants not found in the --in file will be included.",
                                                             numArgs = -1),
                                               unixParameter("--in",
                                                             "-i",
                                                             "file",
                                                             "Input .vcf file to filter.",
                                                             numArgs = 1),
                                               unixParameter("--out",
                                                             "-o",
                                                             "file",
                                                             "Output .vcf file.",
                                                             numArgs = 1)],
                         optionalParameters = [unixParameter("--regions",
                                                             "-r",
                                                             "file",
                                                             ".bed file containing regions on which to operate; if included, all variants " +
                                                             "not found in these regions will be discarded.",
                                                             numArgs = 1),
                                               unixParameter("--strict",
                                                             "-s",
                                                             "boolean",
                                                             "In addition to variants listed, default behavior is to include any site that " +
                                                             "is polymorphic in --in, even if it wasn't listed in any --filter. Include this " +
                                                             "option to disable this functionality.",
                                                             numArgs = 1)])

outPath = interface.getOption("--out","-o",optional=False)[0]
inPath = interface.getOption("--in","-i",optional=False)[0]
filterPaths = interface.getOption("--filter","-f",optional=False)
maskPath = interface.getOption("--regions","-r",optional=True)
strict = interface.getOption("--strict","-s",optional=True)
if strict == None or len(strict) == 0:
    strict = False
else:
    strict = True

if maskPath == None or len(maskPath) != 1:
    mask = None
else:
    mask = bedFile.parseBedFile(open(maskPath[0],'r'),functionToCall=None,callbackArgs={},mask=None,returnFileObject=True)

try:
    inFile = open(inPath,'r')
    outFile = open(outPath,'w')
except:
    interface.die("ERROR: Couldn't open %s" % outPath)

listToKeep = set()

for p in filterPaths:
    print "Loading %s..." % p
    try:
        filterFile = open(p,'r')
    except:
        interface.die("ERROR: Couldn't open %s" % p)
    vcfFile.parseVcfFile(filterFile,functionToCall=filterCallback,callbackArgs={"listToKeep":listToKeep},individualsToExclude=[],mask=mask,returnFileObject=False,skipFiltered=False,skipVariantAttributes=True,skipGenotypes=True,skipGenotypeAttributes=True,includeAdditionalHeaderInfo=False)
    filterFile.close()

resultingVCF = vcfFile()
fileAttributes = vcfFile.parseVcfFile(inFile,functionToCall=mainCallback,callbackArgs={"resultingVCF":resultingVCF,"listToKeep":listToKeep,"strict":strict},individualsToExclude=[],mask=mask,returnFileObject=False,skipFiltered=False,skipVariantAttributes=False,skipGenotypes=False,skipGenotypeAttributes=False,includeAdditionalHeaderInfo=True)
inFile.close()

resultingVCF.addAttributes(fileAttributes)
resultingVCF.writeVcfFile(outFile,sortMethod="NUMXYM")

outFile.close()