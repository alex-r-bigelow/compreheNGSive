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
    from resources.genomeUtils import genomeUtils, allele, variant, variantFile, featureFile, variantLoadingParameters, featureLoadingParameters, valueFilter
    from resources.structures import countingDict
    
    #  END LOCAL IMPORTS  #
    #######################
    
    sys.path[0] = _original_dir

##################
# BEGIN APP CODE #

def performGroupCalculations(variantObject, groupDict, basisGroup, mode=1, vcfOverride=False):
        if variantObject == None or variantObject.poisoned:
            return
        
        # First find all the target alleles
        targetAlleles = {}
        if vcfOverride:
            alleles = variantObject.alleles
        else:
            # First see if we can find a major allele with the people in basisGroup
            alleleCounts = countingDict()
            for i in groupDict[basisGroup]:
                if variantObject.genotypes.has_key(i):
                    allele1 = variantObject.genotypes[i].allele1
                    allele2 = variantObject.genotypes[i].allele2
                    if allele1.text != None:
                        alleleCounts[allele1] += 1
                    if allele2.text != None:
                        alleleCounts[allele2] += 1
            alleles = [x[0] for x in sorted(alleleCounts.iteritems(), key=lambda x: x[1])]
        
        if mode > 0:
            mode -= 1   # we're in 0-based coordinates, but -1 is still the same
        if mode >= len(alleles) or mode < -len(alleles):
            targetAllele = None
        else:
            targetAllele = variantObject.alleles[mode]
        
        for groupID,samples in groupDict.iteritems():
            if targetAllele == None:
                variantObject.setAttribute(groupID + " AF","Masked")    # the original group didn't have the allele, so we're masked
                continue
            
            allCount = 0
            targetCount = 0
            
            for i in samples:
                if variantObject.genotypes.has_key(i):
                    allele1 = variantObject.genotypes[i].allele1
                    allele2 = variantObject.genotypes[i].allele2
                    if allele1 != None:
                        allCount += 1
                        if allele1 == targetAllele:
                            targetCount += 1
                    if allele2 != None:
                        allCount += 1
                        if allele2 == targetAllele:
                            targetCount += 1
            if allCount == 0:
                variantObject.setAttribute(groupID,None)    # We had no data for this variant, so this thing is undefined
            else:
                variantObject.setAttribute(groupID,float(targetCount)/allCount)

def tick(*args,**kwargs):
    print ".",

def runApp(mask="",m="",vcf="",v="",out="",o="",csv="",c=""):
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
    
    variants = {}
    fileAttributes = variantFile.extractVcfFileInfo(vcf)
    
    def addVariant(v):
        variants[v.genomePosition] = v
    
    params = variantLoadingParameters(build=genomeUtils.hg19,
                                     passFunction=addVariant,
                                     rejectFunction=None,
                                     callbackArgs={},
                                     tickFunction=tick,
                                     tickInterval=10,
                                     individualsToInclude=None,
                                     individualAppendString="",
                                     lociToInclude=None,
                                     mask=None,  #features.regions,
                                     invertMask=False,  #True
                                     attributesToInclude=None,
                                     attributeAppendString="",
                                     skipGenotypeAttributes=True,   # TODO: there's actually a bug here (you should turn this back off
                                     returnFileObject=False,
                                     alleleMatching=allele.UNENFORCED,
                                     attemptRepairsWhenComparing=True)
    print "parsing vcf file",
    variantFile.parseVcfFile(vcf, params)
    print ""
    # TODO: throw this bit out
    print "swapping attributes"
    for v in variants.itervalues():
        newName = v.attributes.get('RSID',v.name)
        if v.attributes.has_key('RSID'):
            newName = v.attributes['RSID']
            del v.attributes['RSID']
        else:
            newName = v.name
        if isinstance(newName,list):
            newName = newName[1]
        #if newName.startswith('dbsnp'):
        #    newName = newName.split(':')[1]
        if newName == '.':
            newName = v.basicName
        v.name = newName
    print "calculating frequencies",
    tickInterval = len(variants) / 10
    i = 0
    nextTick = tickInterval
    groupDict = {   "CASES3":set(["T2DG0300147", "T2DG0300160", "T2DG0300135", "T2DG0300133", "T2DG0300143"]),
                    "CASES6":set(["T2DG0600449", "T2DG0600426", "T2DG0600428", "T2DG0600470", "T2DG0600442", "T2DG0600431"]),
                    "CASES20":set(["T2DG2000900", "T2DG2000901", "T2DG2000904", "T2DG2000928"]),
                    "CASES21":set(["T2DG2100946", "T2DG2100955", "T2DG2100967", "T2DG2100966"]),
                    "CONTROLS_IND_EXTREME":set(["T2DG0200013", "T2DG0200027", "T2DG0500309", "T2DG0701163", "T2DG0701156", "T2DG0800488", "T2DG0901234", "T2DG1000568", "T2DG1000570", "T2DG1101324", "T2DG1600768", "T2DG2701070", "T2DG4701118", "T2DG0200068", "T2DG0200071", "T2DG0400250", "T2DG0500349", "T2DG0500339", "T2DG0701179", "T2DG0800504", "T2DG0800564", "T2DG0901289", "T2DG0901275", "T2DG1000595", "T2DG1101348", "T2DG1600785", "T2DG1700875", "T2DG2701094", "T2DG4701124"]),
                    "CONTROL_Normal_nonind":set(["T2DG0200098", "T2DG0200076", "T2DG0200104", "T2DG0200065", "T2DG0400287", "T2DG0400260", "T2DG0400280", "T2DG0400288", "T2DG0400267", "T2DG0400269", "T2DG0400279", "T2DG0400256", "T2DG0400273", "T2DG0500370", "T2DG0500367", "T2DG0500353", "T2DG0500383", "T2DG0500362", "T2DG0500364", "T2DG0500379", "T2DG0500351", "T2DG0500381", "T2DG0500385", "T2DG0500357", "T2DG0701225", "T2DG0701227", "T2DG0701194", "T2DG0701196", "T2DG0701195", "T2DG0701211", "T2DG0701222", "T2DG0701220", "T2DG0701204", "T2DG0701208", "T2DG0701192", "T2DG0701191", "T2DG0701198", "T2DG0701181", "T2DG0701174", "T2DG0800561", "T2DG0800542", "T2DG0800563", "T2DG0800547", "T2DG0800559", "T2DG0901306", "T2DG0901296", "T2DG0901285", "T2DG0901284", "T2DG0901269", "T2DG0901295", "T2DG0901299", "T2DG0901279", "T2DG0901307", "T2DG1000637", "T2DG1000629", "T2DG1000630", "T2DG1000614", "T2DG1000612", "T2DG1000613", "T2DG1000631", "T2DG1000591", "T2DG1000620", "T2DG1000640", "T2DG1000606", "T2DG1000636", "T2DG1000638", "T2DG1000627", "T2DG1101369", "T2DG1101381", "T2DG1101383", "T2DG1101377", "T2DG1101354", "T2DG1101356", "T2DG1600793", "T2DG1600811", "T2DG1600816", "T2DG1600810", "T2DG1700872", "T2DG1700869", "T2DG1700876", "T2DG1700867", "T2DG2701096", "T2DG2701093", "T2DG4701139", "T2DG4701129"]),
                    "CONTROLS_PreHypertension_ind":set(["T2DG0200073", "T2DG0200031", "T2DG0200040", "T2DG0200032", "T2DG0200042", "T2DG0200047", "T2DG0200070", "T2DG0200078", "T2DG0200096", "T2DG0200063", "T2DG0200077", "T2DG0200057", "T2DG0200086", "T2DG0200041", "T2DG0400234", "T2DG0400243", "T2DG0400257", "T2DG0400261", "T2DG0400264", "T2DG0400241", "T2DG0400237", "T2DG0400238", "T2DG0400258", "T2DG0400295", "T2DG0400254", "T2DG0400262", "T2DG0500334", "T2DG0500346", "T2DG0500358", "T2DG0500371", "T2DG0500389", "T2DG0500332", "T2DG0500352", "T2DG0500375", "T2DG0500347", "T2DG0500388", "T2DG0500373", "T2DG0701188", "T2DG0701219", "T2DG0701203", "T2DG0701199", "T2DG0701216", "T2DG0701217", "T2DG0701214", "T2DG0800541", "T2DG0800520", "T2DG0800552", "T2DG0800529", "T2DG0800514", "T2DG0800502", "T2DG0800505", "T2DG0800509", "T2DG0901305", "T2DG0901287", "T2DG0901267", "T2DG0901271", "T2DG0901270", "T2DG0901308", "T2DG0901288", "T2DG0901298", "T2DG0901278", "T2DG0901272", "T2DG0901263", "T2DG1000599", "T2DG1000618", "T2DG1000597", "T2DG1000611", "T2DG1000616", "T2DG1000592", "T2DG1000598", "T2DG1000604", "T2DG1000642", "T2DG1000639", "T2DG1000607", "T2DG1101365", "T2DG1101366", "T2DG1101382", "T2DG1101388", "T2DG1101389", "T2DG1101372", "T2DG1101384", "T2DG1101385", "T2DG1101338", "T2DG1101341", "T2DG1101343", "T2DG1101387", "T2DG1101390", "T2DG1101344", "T2DG1101342", "T2DG1600812", "T2DG1600819", "T2DG1600805", "T2DG1600804", "T2DG1600807", "T2DG1600799", "T2DG1700861", "T2DG1700846", "T2DG1700854", "T2DG1700853", "T2DG1700868", "T2DG1700870", "T2DG2701110", "T2DG2701085", "T2DG2701088", "T2DG2701111", "T2DG2701107", "T2DG2701091", "T2DG4701130", "T2DG4701122", "T2DG4701133", "T2DG4701127", "T2DG4701128", "T2DG0200006", "T2DG0200008", "T2DG0200012", "T2DG0200009", "T2DG0200018", "T2DG0200023", "T2DG0200007", "T2DG0400219", "T2DG0500318", "T2DG0500327", "T2DG0500310", "T2DG0500312", "T2DG0500313", "T2DG0701164", "T2DG0701143", "T2DG0800490", "T2DG0800498", "T2DG0901251", "T2DG1000567", "T2DG1000582", "T2DG1000586", "T2DG1000565", "T2DG1000566", "T2DG1000569", "T2DG1101320", "T2DG1101330", "T2DG1600767", "T2DG1600773", "T2DG1600778", "T2DG1600771", "T2DG1700824", "T2DG1700836", "T2DG2701073", "T2DG2701079"]),
                    "CONTROLS_ALL":set(["T2DG0200013", "T2DG0200027", "T2DG0500309", "T2DG0701163", "T2DG0701156", "T2DG0800488", "T2DG0901234", "T2DG1000568", "T2DG1000570", "T2DG1101324", "T2DG1600768", "T2DG2701070", "T2DG4701118", "T2DG0200068", "T2DG0200071", "T2DG0400250", "T2DG0500349", "T2DG0500339", "T2DG0701179", "T2DG0800504", "T2DG0800564", "T2DG0901289", "T2DG0901275", "T2DG1000595", "T2DG1101348", "T2DG1600785", "T2DG1700875", "T2DG2701094", "T2DG4701124", "T2DG0200098", "T2DG0200076", "T2DG0200104", "T2DG0200065", "T2DG0400287", "T2DG0400260", "T2DG0400280", "T2DG0400288", "T2DG0400267", "T2DG0400269", "T2DG0400279", "T2DG0400256", "T2DG0400273", "T2DG0500370", "T2DG0500367", "T2DG0500353", "T2DG0500383", "T2DG0500362", "T2DG0500364", "T2DG0500379", "T2DG0500351", "T2DG0500381", "T2DG0500385", "T2DG0500357", "T2DG0701225", "T2DG0701227", "T2DG0701194", "T2DG0701196", "T2DG0701195", "T2DG0701211", "T2DG0701222", "T2DG0701220", "T2DG0701204", "T2DG0701208", "T2DG0701192", "T2DG0701191", "T2DG0701198", "T2DG0701181", "T2DG0701174", "T2DG0800561", "T2DG0800542", "T2DG0800563", "T2DG0800547", "T2DG0800559", "T2DG0901306", "T2DG0901296", "T2DG0901285", "T2DG0901284", "T2DG0901269", "T2DG0901295", "T2DG0901299", "T2DG0901279", "T2DG0901307", "T2DG1000637", "T2DG1000629", "T2DG1000630", "T2DG1000614", "T2DG1000612", "T2DG1000613", "T2DG1000631", "T2DG1000591", "T2DG1000620", "T2DG1000640", "T2DG1000606", "T2DG1000636", "T2DG1000638", "T2DG1000627", "T2DG1101369", "T2DG1101381", "T2DG1101383", "T2DG1101377", "T2DG1101354", "T2DG1101356", "T2DG1600793", "T2DG1600811", "T2DG1600816", "T2DG1600810", "T2DG1700872", "T2DG1700869", "T2DG1700876", "T2DG1700867", "T2DG2701096", "T2DG2701093", "T2DG4701139", "T2DG4701129", "T2DG0200073", "T2DG0200031", "T2DG0200040", "T2DG0200032", "T2DG0200042", "T2DG0200047", "T2DG0200070", "T2DG0200078", "T2DG0200096", "T2DG0200063", "T2DG0200077", "T2DG0200057", "T2DG0200086", "T2DG0200041", "T2DG0400234", "T2DG0400243", "T2DG0400257", "T2DG0400261", "T2DG0400264", "T2DG0400241", "T2DG0400237", "T2DG0400238", "T2DG0400258", "T2DG0400295", "T2DG0400254", "T2DG0400262", "T2DG0500334", "T2DG0500346", "T2DG0500358", "T2DG0500371", "T2DG0500389", "T2DG0500332", "T2DG0500352", "T2DG0500375", "T2DG0500347", "T2DG0500388", "T2DG0500373", "T2DG0701188", "T2DG0701219", "T2DG0701203", "T2DG0701199", "T2DG0701216", "T2DG0701217", "T2DG0701214", "T2DG0800541", "T2DG0800520", "T2DG0800552", "T2DG0800529", "T2DG0800514", "T2DG0800502", "T2DG0800505", "T2DG0800509", "T2DG0901305", "T2DG0901287", "T2DG0901267", "T2DG0901271", "T2DG0901270", "T2DG0901308", "T2DG0901288", "T2DG0901298", "T2DG0901278", "T2DG0901272", "T2DG0901263", "T2DG1000599", "T2DG1000618", "T2DG1000597", "T2DG1000611", "T2DG1000616", "T2DG1000592", "T2DG1000598", "T2DG1000604", "T2DG1000642", "T2DG1000639", "T2DG1000607", "T2DG1101365", "T2DG1101366", "T2DG1101382", "T2DG1101388", "T2DG1101389", "T2DG1101372", "T2DG1101384", "T2DG1101385", "T2DG1101338", "T2DG1101341", "T2DG1101343", "T2DG1101387", "T2DG1101390", "T2DG1101344", "T2DG1101342", "T2DG1600812", "T2DG1600819", "T2DG1600805", "T2DG1600804", "T2DG1600807", "T2DG1600799", "T2DG1700861", "T2DG1700846", "T2DG1700854", "T2DG1700853", "T2DG1700868", "T2DG1700870", "T2DG2701110", "T2DG2701085", "T2DG2701088", "T2DG2701111", "T2DG2701107", "T2DG2701091", "T2DG4701130", "T2DG4701122", "T2DG4701133", "T2DG4701127", "T2DG4701128", "T2DG0200006", "T2DG0200008", "T2DG0200012", "T2DG0200009", "T2DG0200018", "T2DG0200023", "T2DG0200007", "T2DG0400219", "T2DG0500318", "T2DG0500327", "T2DG0500310", "T2DG0500312", "T2DG0500313", "T2DG0701164", "T2DG0701143", "T2DG0800490", "T2DG0800498", "T2DG0901251", "T2DG1000567", "T2DG1000582", "T2DG1000586", "T2DG1000565", "T2DG1000566", "T2DG1000569", "T2DG1101320", "T2DG1101330", "T2DG1600767", "T2DG1600773", "T2DG1600778", "T2DG1600771", "T2DG1700824", "T2DG1700836", "T2DG2701073", "T2DG2701079"])}
    for v in variants.itervalues():
        performGroupCalculations(v,groupDict,"CONTROLS_IND_EXTREME",mode=-1)
        i += 1
        if i > nextTick:
            nextTick += tickInterval
            print ".",
    print ""
    
    
    del fileAttributes['INDIVIDUALS']
    del fileAttributes['INFO']['RSID']
    for k in groupDict.iterkeys():
        fileAttributes['INFO'][k] = {"ID":k,"Number":1,"Type":"Float","Description":"%s Allele frequency"%k}
    
    
    print "loading .csv file",
    acceptAllFilter = valueFilter()
    csvDict = {"SIFT_score":acceptAllFilter,
               "LRT_score":acceptAllFilter,
               "MutationTaster_pred":acceptAllFilter,
               "phyloP":acceptAllFilter,
               "SLR_test_statistic":acceptAllFilter,
               "LRT_pred":acceptAllFilter,
               "MutationTaster_score":acceptAllFilter,
               "MutationTaster_pred":acceptAllFilter,
               "GERP++_NR":acceptAllFilter,
               "GERP++_RS":acceptAllFilter,
               "phyloP":acceptAllFilter,
               "29way_logOdds":acceptAllFilter,
               "LRT_Omega":acceptAllFilter,
               "1000Gp1_AF":acceptAllFilter}
    for k in csvDict.iterkeys():
        fileAttributes['INFO'][k] = {"ID":k,"Number":1,"Type":"Float","Description":k}
    
    def tryRepair(v):
        if variants.has_key(v.genomePosition):
            for key,value in v.attributes.iteritems():
                variants[v.genomePosition].setAttribute(key,value)
    params = variantLoadingParameters(build=genomeUtils.hg19,
                                      passFunction=tryRepair,
                                      rejectFunction=None,
                                      callbackArgs={},
                                      tickFunction=tick,
                                      tickInterval=10,
                                      individualsToInclude=None,
                                      individualAppendString="",
                                      lociToInclude=None,
                                      mask=None,    #features.regions,
                                      invertMask=False, #True,
                                      attributesToInclude=csvDict,
                                      attributeAppendString="",
                                      skipGenotypeAttributes=True,
                                      returnFileObject=False,
                                      alleleMatching=allele.UNENFORCED,
                                      attemptRepairsWhenComparing=True)
    variantFile.parseCsvFile(csv,params)
    print ""
    
    print "writing file..."
    temp = variantFile(fileAttributes)
    temp.variants = variants.values()
    temp.writeVcfFile(out, sortMethod="NUMXYM", includeScriptLine=True)
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
                    ("csv","c","path to .csv file"),
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
