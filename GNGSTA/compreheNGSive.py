from gui.treeSelectionWidget import treeSelectionWidget
from gui.treeTagWidget import treeTagWidget
from gui.svApp import parallelCoordinateWidget,scatterplotWidget
from dataModels.setupData import *
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
        loader = QUiLoader()
        infile = QFile("gui/ui/loading.ui")
        infile.open(QFile.ReadOnly)
        splash = loader.load(infile,None)
        splash.show()
        # TODO: update loading screen
        vData,fData = self.svOptions.buildDataObjects()
        vData.freeze()
        splash.close()
        self.runningApp = singleVariantApp(vData,fData)
        
    def closeApp(self):
        self.window.reject()

class singleVariantApp:
    def __init__(self, vData,fData):
        loader = QUiLoader()
        infile = QFile("gui/ui/SingleVariant.ui")
        infile.open(QFile.ReadOnly)
        self.window = loader.load(infile, None)
        
        self.vData = vData
        self.fData = fData
        
        self.pc = parallelCoordinateWidget(data=vData,parent=self.window.pcScrollArea)
        self.window.pcScrollArea.setWidget(self.pc)
        
        self.scatter = scatterplotWidget(data=vData,parent=self.window.scatterWidget)
        
        self.window.show()

def runProgram():
    app = QApplication(sys.argv)
    w = setupApp()
    sys.exit(app.exec_())

if __name__ == "__main__":    
    runProgram()
    
    #import cProfile
    #cProfile.run('runProgram()')