from gui.parallelCoordinates import parallelCoordinateWidget, parallelCoordinateController
from gui.treeViews import treeTagController, treeTagWidget, treeSelectionController, treeSelectionWidget
from dataModels.qtModels import *
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtUiTools import *
import sys, os

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
        
        self.selectionController = treeSelectionController(self.svOptions)
        #self.tagController = treeTagController(self.svOptions)
        self.window.svFileScrollArea.setWidget(treeSelectionWidget(controller=self.selectionController,parent=self.window.svFileScrollArea))
        #self.window.svGroupScrollArea.setWidget(treeTagWidget(controller=self.tagController,parent=self.window.svGroupScrollArea))
        ##########
        # Events #
        ##########
        
        # connecting events: SV
        self.window.runSVbutton.clicked.connect(self.runSV)
        self.window.addFilesButton.clicked.connect(self.loadFiles)
        self.window.groupLineEdit.textChanged.connect(self.updateGroupButtons)
        self.window.createNewGroupButton.clicked.connect(self.addGroup)
        
        # connecting events: OR
        self.window.runORbutton.clicked.connect(self.runOR)
        
        # connecting events: AND
        self.window.runANDbutton.clicked.connect(self.runAND)
        
        # other events:
        self.window.Quit.clicked.connect(self.closeApp)
        self.window.Quit_2.clicked.connect(self.closeApp)
        self.window.Quit_3.clicked.connect(self.closeApp)
        
        ##########
        self.runningApp = None
        self.window.show()
    
    def loadFiles(self):
        newPaths = QFileDialog.getOpenFileNames(filter='Variant, attribute, and/or feature files (*.vcf *.gvf *.csv *.tsv *.bed *.gff3)')
        for path in newPaths[0]:
            self.svOptions.loadFile(path)
        self.selectionController.updateList()
        #self.tagController.updateList()
    
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
        self.tagController.updateList()
        self.updateGroupButtons()
        
    def runSV(self):
        self.window.hide()
        # TODO: recalculate Allele Frequencies
        self.runningApp = singleVariantApp(self.svOptions)
    
    def runOR(self):
        pass
    
    def runAND(self):
        pass
    
    def closeApp(self):
        self.window.reject()

class singleVariantApp:
    def __init__(self, options):
        loader = QUiLoader()
        infile = QFile("gui/ui/SingleVariant.ui")
        infile.open(QFile.ReadOnly)
        self.window = loader.load(infile, None)
        self.pcController = parallelCoordinateController(options.vData)
        self.window.pcScrollArea.setWidget(parallelCoordinateWidget(controller=self.pcController,parent=self.window.pcScrollArea))
        self.window.show()

def runProgram():
    app = QApplication(sys.argv)
    w = setupApp()
    sys.exit(app.exec_())

if __name__ == "__main__":    
    runProgram()
    
    #import cProfile
    #cProfile.run('runProgram()')