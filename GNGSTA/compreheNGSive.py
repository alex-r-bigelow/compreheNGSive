from gui.treeSelectionWidget import treeSelectionWidget
from gui.treeTagWidget import treeTagWidget
from gui.scatterplotWidget import scatterplotWidget
from gui.parallelCoordinateWidget import parallelCoordinateWidget
from dataModels.setupData import *
from dataModels.variantData import selectionState, operation
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import *
import sys, os

'''
Link to the color scheme used in this app:

http://colorbrewer2.org/index.php?type=qualitative&scheme=Dark2&n=8
'''

class setupApp:
    def __init__(self):
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
        
        ##########
        self.runningApp = None
        self.window.show()
    
    def addFiles(self):
        newPaths = QFileDialog.getOpenFileNames(filter='Variant, attribute, and/or feature files (*.vcf *.gvf *.csv *.tsv *.bed *.gff3)')
        for path in newPaths[0]:
            self.svOptions.addFile(path)
        self.selectionView.updateList()
        self.tagView.updateList()
    
    def updateGroupButtons(self):
        text = self.window.groupLineEdit.text()
        
        if len(text) == 0:
            self.window.createNewGroupButton.setText("Create New Group")
            self.window.createNewGroupButton.setEnabled(False)
        elif self.svOptions.hasGroup(text):
            self.window.createNewGroupButton.setText("Remove Group")
            self.window.createNewGroupButton.setEnabled(True)
        else:
            self.window.createNewGroupButton.setText("Create New Group")
            self.window.createNewGroupButton.setEnabled(True)
    
    def addGroup(self):
        text = self.window.groupLineEdit.text()
        if self.svOptions.hasGroup(text):
            self.svOptions.removeGroup(text)
        else:
            self.svOptions.addGroup(text)
        self.tagView.updateList()
        self.updateGroupButtons()
        
    def runSV(self):
        self.window.hide()
        
        splash = QProgressDialog("Loading", "Cancel", 0, 100, parent=None)
        splash.setWindowModality(Qt.WindowModal)
        splash.setAutoClose(False)
        splash.setAutoReset(False)
        
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
            self.runningApp = singleVariantApp(vData,fData,splash,self)
        
    def closeApp(self):
        self.window.reject()

class singleVariantApp:
    def __init__(self, vData,fData,progressWidget,setupScreen):
        progressWidget.reset()
        progressWidget.setMinimum(0)
        progressWidget.setMaximum(3000)
        progressWidget.show()
        
        progressWidget.setLabelText('Moving data around, Loading UI')
        self.setupScreen = setupScreen
        
        self.vData = vData
        self.fData = fData
        self.selections = selectionState(self.vData)
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
        #self.window.showMaximized()
        self.window.show()
    
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
        if op.type not in operation.DOESNT_DIRTY:
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
        self.highlightedRsNumbers = rsNumbers
        self.pc.notifyHighlight(rsNumbers)
        self.scatter.notifyHighlight(rsNumbers)
    
    def notifyAxisChange(self, xAxis=True):
        self.scatter.notifyAxisChange(xAxis)

def runProgram():
    app = QApplication(sys.argv)
    w = setupApp()
    sys.exit(app.exec_())

if __name__ == "__main__":    
    runProgram()
    
    #import cProfile
    #cProfile.run('runProgram()')