from PySide.QtGui import QScrollArea, QWidget
from gui.widgets import customSvgWidget, scatterPlot, parallelCoordinates, rsList, selectionManager, genomeBrowser
from gui.svgHelpers import SvgWrapper

class singleVariantApp(customSvgWidget):
    def __init__(self, svg, bounds = None, title = "Single Variant App", parent = None):
        customSvgWidget.__init__(self, svg, bounds, title, parent)
        
        b = svg.getElement("scatterPlot").getBounds()
        self.scatterPlot = scatterPlot(svg, bounds=b, parent=self)
        self.scatterPlot.move(b.left(),b.top())
        
        #scrollArea.setBackgroundRole(QPalette.Dark)
        #scrollArea.setWidget(QWidget(parallelCoordinates))
        
        b = svg.getElement("parallelCoordinates").getBounds()
        scrollArea = QScrollArea()
        scrollArea.setParent(self)
        scrollArea.move(b.left(),b.top())
        scrollArea.setFixedSize(b.width(),b.height())
        # The scroll bars take a little space - we're scrolling horizontally, so I shave a little off the bottom
        b.setHeight(b.height()-20)
        self.parallelCoordinates = parallelCoordinates(svg, bounds=b, parent=scrollArea)
        scrollArea.setWidget(self.parallelCoordinates)
                
        b = svg.getElement("rsList").getBounds()
        scrollArea = QScrollArea()
        scrollArea.setParent(self)
        scrollArea.move(b.left(),b.top())
        scrollArea.setFixedSize(b.width(),b.height())
        self.rsList = rsList(svg, bounds=b, parent=scrollArea)
        
        b = svg.getElement("selectionManager").getBounds()
        self.selectionManager = selectionManager(svg, bounds=b, parent=self)
        self.selectionManager.move(b.left(),b.top())
        
        b = svg.getElement("genomeBrowser").getBounds()
        self.genomeBrowser = genomeBrowser(svg, bounds=b, parent=self)
        self.genomeBrowser.move(b.left(),b.top())
    
    def bindController(self, controller):
        self.controller = controller
        
        self.scatterPlot.bindController(controller)
        self.parallelCoordinates.bindController(controller)
        self.rsList.bindController(controller)
        self.selectionManager.bindController(controller)
        self.genomeBrowser.bindController(controller)
        
##################
# Unit test code #
##################

def runProgram():
    import sys
    import operator
    from dataModels.variantData import variantData
    from controllers.singleVariantController import controller
    from resources.utils import csvVariantFile
    from PySide.QtGui import QApplication
    
    app = QApplication(sys.argv)
    
    # TODO: file handling dialog, calculate allele frequencies
    data = variantData()
    print 'Retrieving Data...'
    inFile = open('/Users/Home/Desktop/data/1000.csv')
    csvVariantFile.parseCsvVariantFile(inFile,"Chromosome","Position",refHeader="rsNumber",altHeader=None,nameHeader=None,attemptRepairsWhenComparing=True,forceAlleleMatching=True,delimiter="\t",functionToCall=data.addVariant,callbackArgs={},mask=None,returnFileObject=False)
    inFile.close()
    data.setScatterAxes("CASES Allele Frequency","CONTROLS Allele Frequency")
    
    print 'Starting GUI, Controller...'
    svg = SvgWrapper('/Users/Home/Documents/Process Book/Nicki/Sketches/SingleVariant/sketch7.svg')
    window = singleVariantApp(svg)
    window.show()
    
    c = controller(data,window)
    
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    runProgram()
    
    #import cProfile
    #cProfile.run('runProgram()')