#!/usr/bin/env python
'''
Created July 2012

@author: Alex Bigelow
'''
from resources.interfaces import unixInterface, unixParameter
from resources.utils import vcfFile, bedFile

####################
# Start of program #
####################

# Get command line parameters

interface = unixInterface("vcf_to_csv",
                         "This program creates extracts the genotypes in a .vcf file into a .csv file",
                         requiredParameters = [unixParameter("--in",
                                                             "-i",
                                                             "file",
                                                             "Input .vcf file",
                                                             numArgs = 1),
                                               unixParameter("--out",
                                                             "-o",
                                                             "file",
                                                             "Output .csv file",
                                                             numArgs = 1)],
                         optionalParameters = [])

outPath = interface.getOption("--out","-o",optional=False)[0]
inPath = interface.getOption("--in","-i",optional=False)[0]
try:
    outFile = open(outPath,'w')
except:
    interface.die("ERROR: Couldn't open %s" % outPath)


try:
    inFile = open(inPath,'r')
except:
    interface.die("ERROR: Couldn't open %s" % inPath)
individuals = vcfFile.extractIndividualsInFile(inFile)
inFile.close()

outFile.write("Chromosome\tPosition\tID\t" + "\t".join(individuals) + "\n")

def parserCallback(variant):
    outLine = "%s\t%i\t%s" % (variant.chromosome,variant.start,variant.name)
    for i in individuals:
        g = variant.genotypes[i]
        if g.allele1 == None:
            a1 = "."
        elif g.allele1 == 0:
            a1 = variant.ref.text
        else:
            a1 = variant.alt[g.allele1-1].text
        slash = "|" if g.isPhased else "/"
        if g.allele2 == None:
            a2 = "."
        elif g.allele2 == 0:
            a2 = variant.ref.text
        else:
            a2 = variant.alt[g.allele1-1].text
        outLine += "\t%s%s%s" % (a1,slash,a2)
    outFile.write(outLine + "\n")

try:
    inFile = open(inPath,'r')
except:
    interface.die("ERROR: Couldn't open %s" % inPath)
vcfFile.parseVcfFile(inFile,functionToCall=parserCallback,callbackArgs={},individualsToExclude=[],mask=None,returnFileObject=False,skipFiltered=False,skipVariantAttributes=True,skipGenotypes=False,skipGenotypeAttributes=True,includeAdditionalHeaderInfo=False)
inFile.close()

outFile.close()