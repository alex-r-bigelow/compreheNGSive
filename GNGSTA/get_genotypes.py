#!/usr/bin/env python
'''
Created January 2012

@author: Alex Bigelow
'''
from resources.interfaces import unixInterface, unixParameter
from resources.utils import variant, vcfFile

###############################################
# Global helper functions, classes, variables #
###############################################

def mainCallback(v,outColumns,individuals,listToKeep,forceIndividuals):
    if v.name in listToKeep:
        outColumns[v.name] = v;
        for i in v.genotypes.iterkeys():
            if len(forceIndividuals) == 0 or i in forceIndividuals:
                individuals.add(i)

####################
# Start of program #
####################

# Get command line parameters

interface = unixInterface("get_genotypes",
                         "This program extracts specific variants from a vcf file into tabular format. " +
                         "Genotypes and some basic statistics are included.",
                         requiredParameters = [unixParameter("--in",
                                                             "-i",
                                                             "file",
                                                             "Input file.",
                                                             numArgs = 1),
                                               unixParameter("--variants",
                                                             "-v",
                                                             "string(s)",
                                                             "List of variants to extract.",
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
                                               unixParameter("--individuals",
                                                             "-p",
                                                             "string(s)",
                                                             "Only include this list of column headers from the .vcf file. Allele " +
                                                             "frequencies will be recalculated.",
                                                             numArgs = -1)])

outPath = interface.getOption("--out","-o",optional=False)[0]
inPath = interface.getOption("--in","-i",optional=False)[0]
variantList = interface.getOption(tag="--variants",altTag="-v",optional=False)

dropVCF = interface.getOption(tag="--drop_filtered",altTag="-d",optional=True)
if dropVCF == None or len(dropVCF) == 0:
    dropVCF = False
else:
    dropVCF = True

individualList = interface.getOption(tag="--individuals",altTag="-p",optional=True)
if individualList == None or len(individualList) == 0:
    individualList = []
else:
    individualList = individualList

try:
    inFile = open(inPath,'r')
except:
    interface.die("ERROR: Couldn't read %s" % inPath)
try:
    outFile = open(outPath,'w')
except:
    interface.die("ERROR: Couldn't write to %s" % outPath)

listToKeep = set()
individuals = set()

outColumns = {}

print "Loading %s..." % inPath
vcfFile.parseVcfFile(inFile,functionToCall=mainCallback,callbackArgs={"listToKeep":variantList,"outColumns":outColumns,"individuals":individuals,"forceIndividuals":individualList},individualsToExclude=[],individualsToInclude=individualList,mask=None,returnFileObject=False,skipFiltered=dropVCF,skipVariantAttributes=False,skipGenotypes=False,skipGenotypeAttributes=True,includeAdditionalHeaderInfo=False,forceAlleleMatching=False)
inFile.close()

print "Recalculating Allele Frequencies..."
for v in outColumns.itervalues():
    possibleAlleles = 0.0
    minorAlleles = 0.0
    for i in individuals:
        g = v.genotypes[i]
        if g.allele1 != None:
            possibleAlleles += 1
            if g.allele1 == 1:
                minorAlleles += 1
        if g.allele2 != None:
            possibleAlleles += 1
            if g.allele2 == 1:
                minorAlleles += 1
    if possibleAlleles == 0:
        v.attributes["AF"] = "X"
    else:
        v.attributes["AF"] = "%.4f" % (minorAlleles/possibleAlleles)

print "Writing %s..." % outPath
headers = sorted(individuals)
outFile.write("rsNumber\tPosition(hg19)\tREF\tALT\tQUAL\tFILTER\tAF")
for h in headers:
    outFile.write("\t%s" % h)
outFile.write("\n")
for rsNumber,v in outColumns.iteritems():
    altAlleleString = ""
    for a in v.alt:
        altAlleleString += str(a) + ","
    outFile.write("%s\t%i\t%s\t%s\t%s\t%s\t%s" % (rsNumber,v.start,v.ref,altAlleleString[:-1],v.attributes['QUAL'],",".join(v.attributes['FILTER']),v.attributes["AF"]))
    for h in headers:
        if not v.genotypes.has_key(h):
            outFile.write("\tX")
        else:
            outFile.write("\t%s" % v.genotypes[h].text)
    outFile.write("\n")
outFile.close()