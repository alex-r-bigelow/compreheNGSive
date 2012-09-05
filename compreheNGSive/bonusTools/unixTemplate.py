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
    from resources.genomeUtils import allele, variant, variantFile, variantLoadingParameters
    
    #  END LOCAL IMPORTS  #
    #######################
    
    sys.path[0] = _original_dir

##################
# BEGIN APP CODE #

def runApp(loci="",l="",vcf="",v="",individuals="",i="",out="",o=""):
    individualList = []
    infile = open(individuals,'r')
    for line in infile:
        individualList.append(line.strip())
    infile.close()
    
    loci = set()
    firstLine = True
    infile = open(loci,'r')
    for line in infile:
        if firstLine:
            firstLine = False
            continue
        columns = line.split()
        loci.add(variant(self, chromosome=columns[1], position=columns[2], matchMode=allele.FLEXIBLE, attemptRepairsWhenComparing=True, ref=".*", alt=".*", name=columns[0], build=genomeUtils.hg19, attributeFilters=None))
    infile.close()
    
    # we only care about genotypes; all other details don't matter. I won't even bother returning a file object because the variants in loci will be updated.
    parseParameters = variantLoadingParameters(  individualsToInclude=individualList,
                                                 lociToInclude=loci,
                                                 attributesToInclude={},
                                                 skipGenotypeAttributes=True)
    
    variantFile.parseVcfFile(vcf,parseParameters)
    
    outfile = open(out,'w')
    outfile.write("rs#\tbp")
    for i in individualsToInclude:
        outfile.write("\t%s" % i)
    outfile.write("\n")
    
    for v in sorted(loci, key=lambda x:x.position):
        outfile.write("%s\t%i" % (v.name,v.position))
        for i in individualsToInclude:
            outfile.write("\t%s" % str(v.genotypes[i]))
        outfile.write("\n")
    outfile.close()
    

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
    
    requiredArgs = [("loci","l","path to .tsv file containing loci to extract with one header. Columns should be:\n"+
                                "rs Number    Chromosome    Position"),
                    ("vcf","v","path to .vcf file"),
                    ("individuals","i","path to .txt file containing a list (one per line) of individuals to include from the .vcf file."),
                    ("out","o","path to write .tsv file with columns:\n"+
                               "rs Number    Position    <person 1> Genotype    ...")]
    optionalArgs = []
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