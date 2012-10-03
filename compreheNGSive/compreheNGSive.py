'''
Copyright 2012 Alex Bigelow

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this program. If not, see
<http://www.gnu.org/licenses/>.
'''

'''
Color scheme used in this app from colorbrewer2.org:

http://colorbrewer2.org/index.php?type=qualitative&scheme=Dark2&n=8
'''
import sys, os
from PySide.QtCore import Qt
from PySide.QtGui import QApplication, QProgressDialog
from gui.compreheNGSive import setupWidget, appWidget
from dataModels.variantData import variantData, interactionManager
from dataModels.featureData import featureData
from resources.genomeUtils import variantFile, variantLoadingParameters, allele, valueFilter

def trace(frame, event, arg):
    print "%s, %s:%d" % (event, frame.f_code.co_filename, frame.f_lineno)
    return trace

window = None
appWindow = None
splash = None
canceled = False

class cancelButtonException(Exception):
    pass

def tick(numTicks=1, setMax=None, message=None):
    global canceled, splash
    if canceled or splash == None:
        return
    if message != None:
        splash.setLabelText(message)
    elif setMax != None:
        splash.setMaximum(setMax)
        splash.setValue(0)
    else:
        newValue = min(splash.maximum(),numTicks+splash.value())
        splash.setValue(newValue)
    canceled = splash.wasCanceled()
    if canceled:
        raise cancelButtonException()

def notifyRun(vcfPath, vcfAttributes, xAttribute, yAttribute, softFilters, forcedCategoricals, featurePaths):
    global canceled, splash, window
    splash = QProgressDialog("Loading %s" % os.path.split(vcfPath)[1], "Cancel", 0, 1000, parent=None)
    splash.setWindowModality(Qt.WindowModal)
    splash.setAutoReset(False)
    splash.setAutoClose(False)
    splash.show()
    canceled = False
    
    vData = variantData(vcfPath, vcfAttributes, forcedCategoricals)
    '''vParams = variantLoadingParameters(passFunction=vData.addVariant,
                                     rejectFunction=None,
                                     callbackArgs={},
                                     tickFunction=tick,
                                     tickInterval=0.1,
                                     individualsToInclude=[],
                                     individualAppendString="",
                                     lociToInclude=None,
                                     mask=None,
                                     invertMask=False,
                                     attributesToInclude=None,
                                     attributeAppendString="",
                                     skipGenotypeAttributes=True,
                                     returnFileObject=False,
                                     alleleMatching=allele.STRICT,
                                     attemptRepairsWhenComparing=True)
    try:
        variantFile.parseVcfFile(vcfPath, vParams)
    except cancelButtonException:
        splash.close()
        window.show()
        return'''
    
    if softFilters == None:
        softFilters = {}
        for k in vData.axisLookups.iterkeys():
            if k == xAttribute or k == yAttribute:
                if vData.axisLookups[k].hasNumeric:
                    fivePercent = 0.05*(vData.axisLookups[k].maximum-vData.axisLookups[k].minimum)
                    ranges = [(vData.axisLookups[k].maximum-fivePercent,vData.axisLookups[k].maximum)]
                else:
                    ranges = None
                values = []
            else:
                ranges = None
                values = None
            softFilters[k] = valueFilter(values=values,
                                         ranges=ranges,
                                         includeNone=True,
                                         includeBlank=True,
                                         includeInf=True,
                                         includeNaN=True,
                                         includeMissing=True,
                                         includeAlleleMasked=True,
                                         listMode=valueFilter.LIST_INCLUSIVE)
    intMan = interactionManager(vData,softFilters)
    
    # TODO
    fData = featureData(featurePaths)
    if canceled:
        splash.close()
        window.show()
        return

    splash.close()
    appWindow = appWidget(vData,fData,intMan,xAttribute,yAttribute)
    intMan.setApp(appWindow)

def runProgram():
    global window
    app = QApplication(sys.argv)
    window = setupWidget(notifyRun)
    sys.exit(app.exec_())

if __name__ == "__main__": 
    #sys.settrace(trace)
    runProgram()
    
    #import cProfile
    #cProfile.run('runProgram()',filename="compreheNGSive.profile")