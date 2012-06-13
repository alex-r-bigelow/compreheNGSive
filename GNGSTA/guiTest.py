import sys
from gui.mutableSvg import mutableSvgRenderer
from gui.widgets import mutableSvgLayer, layeredWidget
from PySide.QtCore import *
from PySide.QtGui import *

class GuiTest(layeredWidget):
    def __init__(self, parent = None):
        layeredWidget.__init__(self, parent)
        
        self.setWindowTitle(self.tr("guiTest.py"))
        
        self.svgObject = mutableSvgRenderer(path='gui/svg/parallelCoordinates.svg')
        self.svgLayer = mutableSvgLayer(self.svgObject)
        self.addLayer(self.svgLayer)
    
    def sizeHint(self):
        return self.svgObject.getBoundaries().size().toSize()

if __name__ == "__main__":    
    app = QApplication(sys.argv)
    window = GuiTest()
    window.show()
    sys.exit(app.exec_())