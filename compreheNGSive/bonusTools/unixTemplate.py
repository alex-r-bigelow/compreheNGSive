#!/usr/bin/env python
import sys, os
if __name__ == '__main__':
    # this is an ugly hack to be able to store these scripts in a subdirectory; as a side effect you need to add all your local imports as marked
    _original_dir = sys.path[0]
    _root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    sys.path[0] = _root_dir
    
    #######################
    # BEGIN LOCAL IMPORTS #
    
    from resources.generalUtils import parameterizeArgs
    from resources.genomeUtils import genomeUtils, allele, variant, variantFile, variantLoadingParameters
    
    #  END LOCAL IMPORTS  #
    #######################
    
    sys.path[0] = _original_dir

##################
# BEGIN APP CODE #
def tick():
    print ".",

def runApp(loci="",l="",vcf="",v="",individuals="",i="",out="",o=""):
    if individuals != None:
        print "Parsing individual list..."
        individualList = []
        infile = open(individuals,'r')
        for line in infile:
            individualList.append(line.strip())
        infile.close()
        
    else:
        individualList = None
    
    lociToKeep = set()
    if loci != None:
        print "Parsing loci list..."
        firstLine = True
        infile = open(loci,'r')
        for line in infile:
            if firstLine:
                firstLine = False
                continue
            columns = line.split()
            lociToKeep.add(variant(chromosome=columns[0], position=columns[1], matchMode=allele.FLEXIBLE, attemptRepairsWhenComparing=True, ref=".*", alt=".*", name=columns[2], build=genomeUtils.hg19, attributeFilters=None))
        infile.close()
    
    print "Parsing .vcf file..."
    # we only care about genotypes; we throw out all other details.
    parseParameters = variantLoadingParameters(  passFunction=lambda v: lociToKeep.add(v),
                                                 tickFunction=tick,
                                                 tickInterval=5,
                                                 individualsToInclude=individualList,
                                                 lociToInclude=lociToKeep,
                                                 attributesToInclude={},
                                                 skipGenotypeAttributes=True)
    
    variantFile.parseVcfFile(vcf,parseParameters)
    
    print "Writing results..."
    outfile = open(out,'w')
    outfile.write("rs Number\tChromosome\tPosition")
    for i in individualList:
        outfile.write("\t%s" % i)
    outfile.write("\n")
    
    for v in sorted(lociToKeep, key=lambda x:x.position):
        outfile.write("%s\t%i" % (v.name,v.position))
        for i in individualList:
            outfile.write("\t%s" % str(v.genotypes[i]))
        outfile.write("\n")
    outfile.close()
    print "Done."
    

#  END APP CODE  #
##################

if __name__ == '__main__':
    '''
    Here are rules for me, as I don't enforce them; each argument triple is in the form (long,short,description), and the combined set
    of all long and short flags across both requiredArgs and optionalArgs can have no duplicates. If the user uses one tag, both will be
    populated by the time runApp() is called.
    '''
    
    ########################
    # BEGIN APP PARAMETERS #
    
    requiredArgs = [("vcf","v","path to .vcf file"),
                    ("out","o","path to write .csv file with columns:\n"+
                               "Chromosome    Position    Rs#    <person 1> Genotype    ...")]
    optionalArgs = [("loci","l","path to .csv file containing loci to extract with one header. Columns should be:\n"+
                                "Chromosome    Position    Rs#\n"+
                                "Default is to include all loci."),
                    ("individuals","i","path to .txt file containing a list (one per line) of individuals to include from the .vcf file.\n"+
                                        "Default is to include all individuals. Point this to an empty file to exclude all individuals.")]
    appDescription = ""
    
    #  END APP PARAMETERS  #
    ########################
    
    def run(help=None, h=None, **vargs):
        for double,single,desc in requiredArgs:
            if not vargs.has_key(double) and not vargs.has_key(single):
                print "Required argument(s) missing."
                print ""
                print "Usage: python %s [arguments; see below]" % sys.argv[0]
                help = 'help'
                break
            elif vargs.has_key(double):
                vargs[single] = vargs[double]
            elif vargs.has_key(single):
                vargs[double] = vargs[single]
        
        for double,single,desc in optionalArgs:
            if vargs.has_key(double):
                vargs[single] = vargs[double]
            elif vargs.has_key(single):
                vargs[double] = vargs[single]
            else:
                vargs[double] = None
                vargs[single] = None
        
        if help != None or h != None:
            print appDescription
            print ""
            if len(requiredArgs) > 0:
                print "Required arguments:"
                print "-------------------"
                for double,single,desc in requiredArgs:
                    print "-%s or --%s:" % (single,double)
                    print desc
                    print ""
            if len(optionalArgs) > 0:
                print "Optional arguments:"
                print "-------------------"
                for double,single,desc in optionalArgs:
                    print "-%s or --%s:" % (single,double)
                    print desc
                    print ""
            sys.exit(0)
        
        #######################################################
        # BEGIN APP-SPECIFIC PARAMETER CHECKING, MANIPULATION #
        
        #  END APP-SPECIFIC PARAMETER CHECKING, MANIPULATION  #
        #######################################################
        
        runApp(**vargs)
    
    run(**parameterizeArgs(sys.argv[1:]))