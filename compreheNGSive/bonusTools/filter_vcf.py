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
    from resources.genomeUtils import genomeUtils, allele, variant, variantFile, featureFile, variantLoadingParameters, featureLoadingParameters
    
    #  END LOCAL IMPORTS  #
    #######################
    
    sys.path[0] = _original_dir

##################
# BEGIN APP CODE #

def tick(*args,**kwargs):
    print ".",

def runApp(mask="",m="",vcf="",v="",out="",o=""):
    print "loading features",
    params = featureLoadingParameters(build=genomeUtils.hg19,
                                     passFunction=None,
                                     rejectFunction=None,
                                     callbackArgs={},
                                     tickFunction=tick,
                                     tickInterval=10,
                                     mask=None,
                                     attributesToInclude={},
                                     returnFileObject=True)
    features = featureFile.parseBedFile(mask, params)
    print ""
    
    params = variantLoadingParameters(build=genomeUtils.hg19,
                                     passFunction=None,
                                     rejectFunction=None,
                                     callbackArgs={},
                                     tickFunction=tick,
                                     tickInterval=10,
                                     individualsToInclude=None,
                                     individualAppendString="",
                                     lociToInclude=None,
                                     mask=features.regions,
                                     attributesToInclude=None,
                                     attributeAppendString="",
                                     skipGenotypeAttributes=False,
                                     returnFileObject=True,
                                     alleleMatching=allele.STRICT,
                                     attemptRepairsWhenComparing=True)
    print "parsing variants",
    newFile = variantFile.parseVcfFile(vcf, params)
    print ""
    print "writing file..."
    newFile.writeVcfFile(out, sortMethod="NUMXYM", includeScriptLine=True)
    print ""
    print "done"
    

#  END APP CODE  #
##################

if __name__ == '__main__':
    '''
    Here are rules for me, as I don't enforce them; each argument triple is in the form (long,short,description), and the combined set
    of all long and short flags across both requiredArgs and optionalArgs can have no duplicates and "h" and "help" are reserved. If
    the user uses one tag, both will be populated by the time runApp() is called.
    '''
    
    ########################
    # BEGIN APP PARAMETERS #
    
    requiredArgs = [("vcf","v","path to .vcf file"),
                    ("out","o","path to write .vcf file"),
                    ("mask","m","path to .bed file")]
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