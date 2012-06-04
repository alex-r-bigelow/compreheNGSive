import sys
import resources.scipyPatches
from gui.svgLayer import mutableSvgRenderer
from PySide.QtCore import *
from PySide.QtGui import *

class GuiTest(QWidget):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        
        self.setWindowTitle(self.tr("guiTest.py"))
        
        self.svgObject = mutableSvgRenderer("/Users/Home/Documents/Process Book/Nicki/Sketches/SingleVariant/sketch7.svg")
        
        print self.svgObject.xmlObject
        
        self.point = self.svgObject("#numberAxis")
        parent = self.point.parent()
        self.point.attr("transform","translate(-600,200)")
        self.point2 = self.point.clone().attr("id","point2").appendTo(parent)
        self.point2.attr("transform","translate(-300,200)")
        self.point3 = self.point.clone()
        self.point4 = self.point.clone()
        
        print self.svgObject.xmlObject
        
        #print self.point.getBounds("missing")
        #print self.point2.getBounds("missing")
        #print self.point3.getBounds("missing")
        #print self.point4.getBounds("missing")
        
        #print self.svgObject.xmlObject
        
        #self.point4.setText("4","label")
        #self.point3.setText("3","label")
        #self.point2.setText("2","label")
        #self.point.setText("1","label")
        
        #print self.svgObject.xmlObject
        
        #self.point4.hideChildren("missing")
        #self.point3.hideChildren("missing")
        #self.point2.hideChildren("missing")
        #self.point.hideChildren("missing")
        
        self.drawStatic()
    
    def getBounds(self, id):
        o = self.svgObject("#%s"%id)
        b = o.boundsOnElement(id)
        if len(o.parents()) > 0:
            b = o.matrixForElement(id).mapRect(b)
        return b
    
    def drawElements(self, painter, selector):
        self.svgObject.render(painter,self.getBounds(selector))
    
    def drawStatic(self):
        self.image = QPixmap(1600,1200)
        
        painter = QPainter()
        painter.begin(self.image)
        
        #self.point.draw(painter)
        #self.point2.draw(painter)
        #self.point3.draw(painter)
        #self.point4.draw(painter)
        
        #painter.setPen(QColor.fromRgbF(0.0,0.0,0.0,0.5))
        #painter.drawRect(100,100,300,300)
        
        painter.end()
    
    def paintEvent(self, event):
        painter = QPainter()
        painter.begin(self)
        painter.drawPixmap(0, 0, self.image)
        painter.end()
    
    def sizeHint(self):
        return QSize(1800, 1200)

if __name__ == "__main__":
    from gui.widgets import rsList
    '''app = QApplication(sys.argv)
    window = rsList(SvgWrapper('/Users/Home/Documents/Process Book/Nicki/Sketches/SingleVariant/sketch7.svg'))
    window.show()
    sys.exit(app.exec_())'''
    
    app = QApplication(sys.argv)
    window = GuiTest()
    window.show()
    sys.exit(app.exec_())