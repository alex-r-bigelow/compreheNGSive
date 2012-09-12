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

from gui.scatterplotWidget import scatterplotWidget
from gui.parallelCoordinateWidget import parallelCoordinateWidget
from dataModels.setupData import prefs
from dataModels.variantData import selectionState, operation
from PySide.QtCore import QFile, Qt
from PySide.QtGui import QFileDialog, QProgressDialog, QApplication
from PySide.QtUiTools import *
import sys

'''
Color scheme used in this app from colorbrewer2.org:

http://colorbrewer2.org/index.php?type=qualitative&scheme=Dark2&n=8
'''

def trace(frame, event, arg):
    print "%s, %s:%d" % (event, frame.f_code.co_filename, frame.f_lineno)
    return trace

class setupApp:
    def __init__(self, params):
        loader = QUiLoader()
        infile = QFile("gui/ui/Setup.ui")
        infile.open(QFile.ReadOnly)
        self.window = loader.load(infile, None)
        
        self.loadPrefs()
        
        self.window.quitButton.clicked.connect(self.closeApp)
        self.window.saveButton.clicked.connect(self.savePrefs)
        self.window.runButton.clicked.connect(self.runSV)
        
        self.splash = QProgressDialog("Loading", "Cancel", 0, 100, parent=None)
        self.splash.setWindowModality(Qt.WindowModal)
        self.splash.setAutoReset(False)
        self.splash.setAutoClose(False)
        self.splash.hide()
        self.canceled = False
        
        self.window.show()
        self.runningApp = None
    
    def loadPrefs(self):
        infile = open('prefs.xml','r')
        self.window.textEdit.setPlainText(infile.read())
        infile.close()
    
    def savePrefs(self):
        outfile=open('prefs.xml','w')
        outfile.write(self.window.textEdit.toPlainText())
        outfile.close()
    
    def showProgressWidget(self, estimate=100, message="Loading..."):
        self.splash.setLabelText(message)
        self.splash.setMaximum(estimate)
        self.splash.setValue(0)
        self.splash.show()
    
    def tickProgressWidget(self, numTicks=1, message=None):
        if self.canceled:
            return
        if message != None:
            self.splash.setLabelText(message)
        newValue = min(self.splash.maximum(),numTicks+self.splash.value())
        self.splash.setValue(newValue)
        self.canceled = self.splash.wasCanceled()
        return self.canceled
    
    def runSV(self, params='prefs.xml'):
        self.savePrefs()
        self.window.hide()
        
        appPrefs = prefs.generateFromText(self.window.textEdit.toPlainText())
        
        self.showProgressWidget(appPrefs.maxTicks, "Loading files...")
        
        self.canceled = False
        vData,fData = appPrefs.loadDataObjects(callback=self.tickProgressWidget)
        if self.canceled:
            self.splash.hide()
            self.window.show()
            return
        
        self.showProgressWidget(len(vData.axisLabels)+len(vData.statisticLabels), "Building Query Structures...")
        
        vData.freeze(startingXaxis=appPrefs.startingXaxis,startingYaxis=appPrefs.startingYaxis,callback=self.tickProgressWidget)
        if self.canceled:
            self.splash.hide()
            self.window.show()
            return
        
        self.splash.hide()
        self.runningApp = singleVariantApp(vData,fData,appPrefs.getSoftFilters(),self)
    
    def closeApp(self):
        self.window.reject()

class singleVariantApp:
    def __init__(self, vData, fData, prefilters, setupScreen):
        self.vData = vData
        self.fData = fData
        self.setupScreen = setupScreen
        
        self.selections = selectionState(self.vData, prefilters)
        self.currentOperation = operation(operation.NO_OP, self.selections, previousOp = None)
        
        self.highlightedRsNumbers = set()
        self.activeRsNumbers = self.selections.getActiveRsNumbers()
        self.activeParams = self.selections.getActiveParameters()
        
        loader = QUiLoader()
        infile = QFile("gui/ui/SingleVariant.ui")
        infile.open(QFile.ReadOnly)
        self.window = loader.load(infile, None)
        
        self.pc = parallelCoordinateWidget(data=vData,app=self,parent=self.window.pcScrollArea)
        self.window.pcScrollArea.setWidget(self.pc)
        
        self.scatter = scatterplotWidget(data=vData,app=self,parent=self.window.scatterWidget)
        
        #for i in self.activeRsNumbers:
        #    self.window.groupList.addItem(i)
        
        self.window.showMaximized()
        #self.window.show()
        #sys.settrace(trace)
    
    def newOperation(self, opCode, **kwargs):
        newOp = operation(opCode, self.selections, previousOp=self.currentOperation, **kwargs)
        if newOp.isLegal:
            self.currentOperation = newOp
            self.notifyOperation(newOp)
        return newOp.isLegal
    
    def undo(self):
        assert self.currentOperation.previousOp != None and (self.currentOperation.nextOp == None or self.currentOperation.nextOp.finished == False)
        self.currentOperation.undo()
        self.currentOperation = self.currentOperation.previousOp
        self.notifyOperation(self.currentOperation.nextOp)
    
    def redo(self):
        assert self.currentOperation.nextOp != None and self.currentOperation.nextOp.finished == False
        self.currentOperation = self.currentOperation.nextOp
        self.currentOperation.apply()
        self.notifyOperation(self.currentOperation)
    
    def notifyOperation(self, op):
        if op.opType not in operation.DOESNT_DIRTY:
            self.activeRsNumbers = self.selections.getActiveRsNumbers()
            #self.window.groupList.clear()
            #for i in self.activeRsNumbers:
            #    self.window.groupList.addItem(i)
            self.activeParams = self.selections.getActiveParameters()
            if hasattr(op,'axis'):
                self.notifySelection(op.axis)
            else:
                self.notifySelection()
        if self.multipleSelected():
            pass    # TODO: show/hide menus and stuff
        else:
            pass    # TODO: show/hide menus and stuff
    
    def multipleSelected(self):
        return len(self.selections.activeSelections) > 1
    
    def notifySelection(self, axis=None):
        self.pc.notifySelection(self.activeRsNumbers,self.activeParams,axis)
        self.scatter.notifySelection(self.activeRsNumbers,self.activeParams,axis)
    
    def notifyHighlight(self, rsNumbers):
        self.highlightedRsNumbers = set(rsNumbers)
        self.window.highlightList.clear()
        for i in self.highlightedRsNumbers:
            self.window.highlightList.addItem(i)
        self.pc.notifyHighlight(self.highlightedRsNumbers)
        self.scatter.notifyHighlight(self.highlightedRsNumbers)
    
    def notifyAxisChange(self, xAxis=True):
        self.scatter.notifyAxisChange(xAxis)

def runProgram():
    if len(sys.argv) == 2:
        params = sys.argv.pop(1)
    else:
        params = None
    app = QApplication(sys.argv)
    w = setupApp(params)
    sys.exit(app.exec_())

if __name__ == "__main__": 
    #sys.settrace(trace)
    runProgram()
    
    #import cProfile
    #cProfile.run('runProgram()')