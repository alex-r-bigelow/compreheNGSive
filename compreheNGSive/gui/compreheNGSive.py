import os
from PySide.QtCore import QFile
from PySide.QtUiTools import QUiLoader
from PySide.QtGui import QFileDialog, QMessageBox
from dataModels.variantData import operation
from resources.genomeUtils import variantFile
from gui.parallelCoordinateWidget import parallelCoordinateWidget
from gui.scatterplotWidget import scatterplotWidget

class setupWidget:
    def __init__(self, notifyRun):
        loader = QUiLoader()
        infile = QFile("gui/ui/compreheNGSive_setup.ui")
        infile.open(QFile.ReadOnly)
        self.window = loader.load(infile, None)
        self.notifyRun = notifyRun
        
        self.vcfAttributes = None
        
        self.window.quitButton.clicked.connect(self.closeApp)
        self.window.runButton.clicked.connect(self.run)
        self.window.browseButton.clicked.connect(self.browseVcf)
        self.window.addButton.clicked.connect(self.browseFeature)
        self.window.removeButton.clicked.connect(self.removeFeature)
        self.window.loadButton.clicked.connect(self.loadFilters)
        self.window.saveButton.clicked.connect(self.saveFilters)
        
        # TODO: handle the schema view
                
        self.window.show()
    
    def closeApp(self):
        self.window.reject()
    
    def run(self):
        self.window.hide()
        vcfPath = self.window.pathBox.text()
        if not os.path.exists(vcfPath):
            QMessageBox.information(self.window,"Error","You must choose a valid variant file.",QMessageBox.Ok)
            self.window.show()
            return
        
        featurePaths = self.getFeatureList()
        for f in featurePaths:
            if not os.path.exists(f):
                QMessageBox.information(self.window,"Error","One of your feature files doesn't exist anymore. Try again.",QMessageBox.Ok)
                self.window.show()
                self.window.featureList.clear()
                return
        
        xAttribute = self.window.xAxisChooser.currentText()
        yAttribute = self.window.yAxisChooser.currentText()
        
        softFilters = None  # TODO
        forcedCategoricals = self.getForcedCategoricals()
        
        self.notifyRun(vcfPath, self.vcfAttributes, xAttribute, yAttribute, softFilters, forcedCategoricals, featurePaths)
    
    def browseVcf(self):
        newPath = QFileDialog.getOpenFileName(filter=u'VCF Files (*.vcf)')[0]
        if newPath == None or newPath == "":
            return
        self.vcfAttributes = variantFile.extractVcfFileInfo(newPath)
        allAttributes = sorted(self.vcfAttributes['variant attributes'])
        self.window.pathBox.setText(newPath)
        
        self.window.xAxisChooser.clear()
        self.window.yAxisChooser.clear()
        self.window.xAxisChooser.addItems(allAttributes)
        self.window.yAxisChooser.addItems(allAttributes)
        
        # TODO: build a default schema
        # self.window.schemaView.clear()
    
    def browseFeature(self):
        existingItems = set(self.getFeatureList())
        existingItems.update(QFileDialog.getOpenFileNames(filter=u'Feature files (*.gff3 *.bed)')[0])
        self.window.featureList.clear()
        self.window.featureList.addItems(sorted(existingItems))
    
    def removeFeature(self):
        for i in self.window.featureList.selectedItems():
            self.window.featureList.takeItem(self.window.featureList.row(i))
    
    def loadFilters(self):
        pass
    
    def saveFilters(self):
        pass
    
    def getFeatureList(self):
        i = 0
        items = []
        while i < self.window.featureList.count():
            items.append(self.window.featureList.item(i).text())
            i += 1
        return items
    
    def getForcedCategoricals(self):
        # TODO
        return set()

class appWidget:
    def __init__(self, vData, fData, intMan, startingXattribute, startingYattribute):
        loader = QUiLoader()
        infile = QFile("gui/ui/compreheNGSive.ui")
        infile.open(QFile.ReadOnly)
        self.window = loader.load(infile, None)
        
        self.resolution_threshold = 100
        
        self.vData = vData
        self.fData = fData
        self.intMan = intMan
        
        self.currentXattribute = startingXattribute
        self.currentYattribute = startingYattribute
        
        self.window.resolutionSpinBox.setMinimum(10)
        self.window.resolutionSpinBox.setMaximum(len(self.vData.data))
        self.window.resolutionSpinBox.setValue(self.resolution_threshold)
        self.window.resolutionSpinBox.valueChanged.connect(self.changeResolution)
        
        self.window.actionQuit.triggered.connect(self.window.close)
        self.window.actionExport_History.triggered.connect(self.exportHistory)
        self.window.actionExport.triggered.connect(self.exportActivePoints)
        
        self.window.actionUndo.triggered.connect(self.intMan.undo)
        self.window.actionRedo.triggered.connect(self.intMan.redo)
        
        # TODO
        
        #self.window.actionNew.triggered.connect(self.startNewSelection)
        #self.window.actionDuplicate.triggered.connect(self.duplicateActiveSelection)
        #self.window.actionDelete.triggered.connect(self.deleteActiveSelection)
        
        #self.window.actionUnion.triggered.connect(self.intMan.newOperation(operation.SELECTION_UNION,))
        #self.window.actionIntersection.triggered.connect(self.intMan.newOperation(operation.SELECTION_UNION,))
        #self.window.actionDifference.triggered.connect(self.intMan.newOperation(operation.SELECTION_UNION,))
        #self.window.actionComplement.triggered.connect(self.intMan.newOperation(operation.SELECTION_UNION,))
        
        self.pc = parallelCoordinateWidget(vData=vData,app=self,parent=self.window.pcScrollArea)
        self.window.pcScrollArea.setWidget(self.pc)
        
        self.scatter = scatterplotWidget(vData=vData,app=self,parent=self.window.scatterWidget)
        
        #self.window.showMaximized()
        self.window.show()
    
    def changeResolution(self):
        self.resolution_threshold = self.window.resolutionSpinBox.value()
    
    def exportHistory(self):
        print 'TODO: export history'
    
    def exportActivePoints(self):
        print 'TODO: export data'
    
    def notifyOperation(self, op):
        self.window.actionUndo.setDisabled(self.intMan.currentOperation.previousOp == None)
        self.window.actionRedo.setDisabled(self.intMan.currentOperation.nextOp == None)
        
        self.window.actionNew.setDisabled(True)
        self.window.actionDuplicate.setDisabled(True)  # TODO: enable if this op's opType will render a situation where an option is appropriate
        self.window.actionDelete.setDisabled(True)
        
        self.window.actionUnion.setDisabled(True)
        self.window.actionIntersection.setDisabled(True)
        self.window.actionDifference.setDisabled(True)
        self.window.actionComplement.setDisabled(True)
    
    def notifySelection(self, activePoints, activeParams):
        self.window.groupList.clear()
        for i,p in enumerate(activePoints):
            if i+1 >= self.resolution_threshold:
                self.window.groupList.addItem('... %i more not shown ...' % (len(activePoints)-i+1))
                break
            else:
                self.window.groupList.addItem(self.vData.data[str(p)].name)
        
        self.pc.notifySelection(activePoints,activeParams)
        self.scatter.notifySelection(activePoints,activeParams)
    
    def notifyHighlight(self, points):
        self.highlightedPoints = set(points)
        self.window.highlightList.clear()
        for i,p in enumerate(self.highlightedPoints):
            if i+1 >= self.resolution_threshold:
                self.window.highlightList.addItem('... %i more not shown ...' % (len(self.highlightedPoints)-i+1))
                break
            else:
                self.window.highlightList.addItem(self.vData.data[str(p)].name)
        self.pc.notifyHighlight(self.highlightedPoints)
        self.scatter.notifyHighlight(self.highlightedPoints)
    
    def notifyAxisChange(self, newAtt, xAxis=True):
        if xAxis:
            self.currentXattribute = newAtt
        else:
            self.currentYattribute = newAtt
        self.pc.notifyAxisChange()
        self.scatter.notifyAxisChange()