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

from gui.treeSelectionWidget import treeSelectionWidget
from gui.treeTagWidget import treeTagWidget
from gui.scatterplotWidget import scatterplotWidget
from gui.parallelCoordinateWidget import parallelCoordinateWidget
from dataModels.setupData import svOptionsModel
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
    def __init__(self, params=None):
        if params != None:
            self.runSV(params)
        else:
            loader = QUiLoader()
            infile = QFile("gui/ui/Setup.ui")
            infile.open(QFile.ReadOnly)
            self.window = loader.load(infile, None)
            ########
            
            ########
            # Data #
            ########
            
            # data model for setup
            self.svOptions = svOptionsModel()
            
            self.selectionView = treeSelectionWidget(data=self.svOptions, parent=self.window.svFileScrollArea)
            self.window.svFileScrollArea.setWidget(self.selectionView)
            self.tagView = treeTagWidget(data=self.svOptions, parent=self.window.svGroupScrollArea)
            self.window.svGroupScrollArea.setWidget(self.tagView)
            ##########
            # Events #
            ##########
            
            # connecting events
            self.window.runSVbutton.clicked.connect(self.runSV)
            self.window.addFilesButton.clicked.connect(self.addFiles)
            self.window.groupLineEdit.textChanged.connect(self.updateGroupButtons)
            self.window.createNewGroupButton.clicked.connect(self.addGroup)
            self.window.Quit.clicked.connect(self.closeApp)
            self.window.fallbackRadioButtons.buttonReleased.connect(self.toggleAltEnabled)
            
            ##########
            self.runningApp = None
            self.window.show()
    
    def addFiles(self):
        newPaths = QFileDialog.getOpenFileNames(filter='Variant, attribute, and/or feature files (*.vcf *.gvf *.csv *.tsv *.bed *.gff3)')
        for path in newPaths[0]:
            newFile = self.svOptions.addFile(path)
            #if newGroup != None:
            #    self.window.alleleComboBox.addItem(newGroup)
        self.selectionView.updateList()
        self.tagView.updateList()
    
    def updateGroupButtons(self):
        text = self.window.groupLineEdit.text()
        
        if len(text) == 0 or text == "None":
            self.window.createNewGroupButton.setText("Create New Group")
            self.window.createNewGroupButton.setEnabled(False)
        elif self.svOptions.hasGroup(text):
            self.window.createNewGroupButton.setText("Remove Group")
            if self.svOptions.groups[text].userDefined:
                self.window.createNewGroupButton.setEnabled(True)
            else:
                self.window.createNewGroupButton.setEnabled(False)
        else:
            self.window.createNewGroupButton.setText("Create New Group")
            self.window.createNewGroupButton.setEnabled(True)
    
    def addGroup(self):
        text = self.window.groupLineEdit.text()
        if self.svOptions.hasGroup(text):
            #self.window.alleleComboBox.removeItem(self.svOptions.groupOrder.index(text)+1)
            self.svOptions.removeGroup(text)
        else:
            #self.window.alleleComboBox.addItem(text)
            self.svOptions.addGroup(text)
        self.tagView.updateList()
        self.updateGroupButtons()
    
    def toggleAltEnabled(self):
        self.window.altSpinBox.setEnabled(self.window.fallbackRadioButtons.checkedButton() == self.window.altRadioButton)
        
    def runSV(self, params=None):
        if params != None:
            splash = QProgressDialog("Loading", "Cancel", 0, 100, parent=None)
            splash.setWindowModality(Qt.WindowModal)
            splash.setAutoClose(False)
            splash.setAutoReset(False)
            
            self.svOptions = svOptionsModel(params)
            results = self.svOptions.buildDataObjects(splash)
            
            if results == False:
                splash.close()
                sys.exit(0)
            else:
                vData = results[0]
                fData = results[1]
            
            results = vData.freeze(startingXaxis=self.svOptions.startingXattribute,startingYaxis=self.svOptions.startingYattribute,progressWidget=splash)
            
            if results == False:
                splash.close()
                sys.exit(0)
            else:
                self.runningApp = singleVariantApp(vData,fData,self.svOptions.prefilters,splash,self)
        else:
            self.window.hide()
            
            splash = QProgressDialog("Loading", "Cancel", 0, 100, parent=None)
            splash.setWindowModality(Qt.WindowModal)
            splash.setAutoClose(False)
            splash.setAutoReset(False)
            
            # TODO: set parameters...
            results = self.svOptions.buildDataObjects(splash)
            
            if results == False:
                splash.close()
                self.window.show()
                return
            else:
                vData = results[0]
                fData = results[1]
            
            results = vData.freeze(progressWidget=splash)
            
            if results == False:
                splash.close()
                self.window.show()
                return
            else:
                self.runningApp = singleVariantApp(vData,fData,self.svOptions.prefilters,splash,self)
        
    def closeApp(self):
        self.window.reject()

class singleVariantApp:
    def __init__(self, vData,fData,prefilters,progressWidget,setupScreen):
        progressWidget.reset()
        progressWidget.setMinimum(0)
        progressWidget.setMaximum(3000)
        progressWidget.show()
        
        progressWidget.setLabelText('Moving data around, Loading UI')
        self.setupScreen = setupScreen
        
        self.vData = vData
        self.fData = fData
        self.selections = selectionState(self.vData, prefilters)
        self.currentOperation = operation(operation.NO_OP, self.selections, previousOp = None)
        
        self.highlightedRsNumbers = set()
        self.activeRsNumbers = self.selections.getActiveRsNumbers()
        self.activeParams = self.selections.getActiveParameters()
        
        loader = QUiLoader()
        infile = QFile("gui/ui/SingleVariant.ui")
        infile.open(QFile.ReadOnly)
        self.window = loader.load(infile, None)
        
        if progressWidget.wasCanceled():
            self.close()
            self.setupScreen.show()
            return
        progressWidget.setValue(1000)
        progressWidget.setLabelText('Drawing Parallel Coordinates')
        
        self.pc = parallelCoordinateWidget(data=vData,app=self,parent=self.window.pcScrollArea)
        self.window.pcScrollArea.setWidget(self.pc)
        
        if progressWidget.wasCanceled():
            self.close()
            self.setupScreen.show()
            return
        progressWidget.setValue(2000)
        progressWidget.setLabelText('Drawing Scatterplot')
        self.scatter = scatterplotWidget(data=vData,app=self,parent=self.window.scatterWidget)
        
        progressWidget.close()
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