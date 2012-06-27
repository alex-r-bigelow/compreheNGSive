from widgets import mutableSvgLayer, layeredWidget

class parallelCoordinateController:
    def __init__(self, data):
        self.data = data
        self.widget = None
    
    def handleEvents(self, signals):
        if signals.has_key('switchAxes'):
            print "Switch %i and %i" % (signals['switchAxes'])
    
    def setWidget(self, widget):
        self.widget = widget
    
class parallelCoordinateWidget(layeredWidget):
    def __init__(self, controller, parent = None):
        layeredWidget.__init__(self, controller, parent)
        
        self.svgLayer = mutableSvgLayer('gui/svg/parallelCoordinates.svg',self.controller)
        w,h = self.svgLayer.size.toTuple()
        self.axes = self.controller.data.axes.keys()
        self.svgLayer.resize(QSize(len(self.axes)*w,h))
        
        first = True
        axis = self.svgLayer.svg.root.axis
        
        for i,a in enumerate(self.axes):
            if not first:
                axis = axis.clone()
                axis.translate(w*i,0)
            axis.setText(a)
        
        self.addLayer(self.svgLayer)
    
    def sizeHint(self):
        return self.svgLayer.size