from layeredWidget import mutableSvgLayer, layeredWidget
from PySide.QtCore import QSize

class scatterplotWidget(layeredWidget):
    def __init__(self, data, parent = None):
        layeredWidget.__init__(self, parent)
        self.data = data
        
        self.svgLayer = mutableSvgLayer('gui/svg/scatterplot.svg',self)
        self.addLayer(self.svgLayer)
    
    def handleEvents(self, event, signals):
        pass