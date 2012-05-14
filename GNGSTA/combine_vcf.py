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

def parserCallback(variant,resultingVCF):
    resultingVCF.addVariant(variant)

####################
# Start of program #
####################

# Get command line parameters

interface = unixInterface("combine_vcf",
                         "This program combines vcf files generated from the same sequencing data set (e.g. if indels and snps were called separately...).",
                         requiredParameters = [unixParameter("--in",
                                                             "-i",
                                                             "file",
                                                             "Input .vcf file(s).",
                                                             numArgs = -1),
                                               unixParameter("--out",
                                                             "-o",
                                                             "file",
                                                             "Output .vcf file.",
                                                             numArgs = 1)],
                         optionalParameters = [unixParameter("--regions",
                                                             "-r",
                                                             "file",
                                                             ".bed file containing regions to extract. If not " +
                                                             "used, all regions will be included.",
                                                             numArgs = 1),
                                               unixParameter("--genotypes",
                                                             "-g",
                                                             "boolean",
                                                             "Set this flag to only include genotypes (will ignore " +
                                                             "data in the INFO and FORMAT fields.",
                                                             numArgs = 0),
                                               unixParameter("--variants_only",
                                                             "-v",
                                                             "boolean",
                                                             "Set this flag to only include variants (for use with reference " +
                                                             "variant lists, etc, that have no genotypes).",
                                                             numArgs = 0),
                                               unixParameter("--drop_filtered",
                                                             "-d",
                                                             "boolean",
                                                             "Set this flag to only include variants that have \"PASS\" in the FILTER column.",
                                                             numArgs = 0)])

outPath = interface.getOption("--out","-o",optional=False)[0]
inPaths = interface.getOption("--in","-i",optional=False)
maskPath = interface.getOption("--regions","-r",optional=True)
temp = interface.getOption("--genotypes","-g",optional=True)
skipDetails = (temp != None and len(temp) > 0)
temp = interface.getOption("--variants_only","-v",optional=True)
skipAllDetails = (temp != None and len(temp) > 0)
if skipAllDetails:
    skipDetails = True
temp = interface.getOption("--drop_filtered","-d",optional=True)
dropFiltered = (temp != None and len(temp) > 0)

if maskPath == None or len(maskPath) != 1:
    mask = None
else:
    mask = bedFile.parseBedFile(open(maskPath[0],'r'),functionToCall=None,callbackArgs={},mask=None,returnFileObject=True)

try:
    outFile = open(outPath,'w')
except:
    interface.die("ERROR: Couldn't open %s" % outPath)

resultingVCF = vcfFile()

for p in inPaths:
    print "Loading %s..." % p
    try:
        inFile = open(p,'r')
    except:
        interface.die("ERROR: Couldn't open %s" % p)
    newAttributes = vcfFile.parseVcfFile(inFile,functionToCall=parserCallback,callbackArgs={"resultingVCF":resultingVCF},individualsToExclude=[],mask=mask,returnFileObject=False,skipFiltered=dropFiltered,skipVariantAttributes=skipDetails,skipGenotypes=skipAllDetails,skipGenotypeAttributes=skipDetails,includeAdditionalHeaderInfo=True)
    resultingVCF.addAttributes(newAttributes)
    inFile.close()

resultingVCF.writeVcfFile(outFile,sortMethod="NUMXYM")
outFile.close()