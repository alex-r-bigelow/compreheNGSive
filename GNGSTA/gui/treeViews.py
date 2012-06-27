from widgets import mutableSvgLayer, layeredWidget
from PySide.QtCore import QSize

class treeTagController:
    def __init__(self, data):
        self.data = data
        self.widget = None
    
    def handleEvents(self, signals):
        pass
    
    def setWidget(self, widget):
        self.widget = widget
    
    def updateList(self):
        self.widget.updateList()

class treeTagWidget(layeredWidget):
    def __init__(self, controller, parent = None):
        layeredWidget.__init__(self, controller, parent)
        
        self.svgLayer = mutableSvgLayer('gui/svg/groupTags.svg',self.controller)
        self.updateList()
        
        self.addLayer(self.svgLayer)
    
    def updateList(self):
        ''''w,h = self.size().toTuple()
        # TODO: w = max(w,)
        h = 20
        self.svgLayer.resize(QSize(w,h))'''
    
    def resizeEvent(self, event):
        self.updateList()

class treeSelectionItem:
    def __init__(self, text, isChild=False):
        self.text = text
        self.isChild=isChild
        self.isVisible=not isChild
        self.isChecked = True

class treeSelectionController:
    def __init__(self, data):
        self.data = data
        self.widget = None
        
        self.expanded = {}
    
    def handleEvents(self, signals):
        if signals.has_key('groupOpened'):
            print signals['groupOpened'].label.getText() + " opened"
        if signals.has_key('groupClosed'):
            print signals['groupClosed'].label.getText() + " closed"
        if signals.has_key('checkClicked'):
            signals['checkClicked'].check.hide()
        
    def setWidget(self, widget):
        self.widget = widget
    
    def updateList(self):
        for f,fobj in self.data.files.iteritems():
            if not self.expanded.has_key(f):
                if fobj.checkable:
                    self.expanded[f] = False
                else:
                    self.expanded[f] = None
        self.widget.updateList()
    
    def getCurrentRows(self):
        results = []
        for f in self.data.fileOrder:
            fobj = self.data.files[f]
            results.append((f,self.expanded[f],fobj.isChecked()))
            if self.expanded[f]:
                for att in sorted(fobj.attributes.iterkeys()):
                    results.append((att,fobj.attributes[att]))
        return results

class treeSelectionWidget(layeredWidget):
    def __init__(self, controller, parent = None):
        layeredWidget.__init__(self, controller, parent)
        self.updateList()
    
    def updateList(self):
        rows = self.controller.getCurrentRows()
        if len(rows) == 0:
            self.clearAllLayers()
            return
        
        self.svgLayer = mutableSvgLayer('gui/svg/groupTags.svg',self.controller)
        w = 0
        h = 0
        
        prototypeGroupBlock = self.svgLayer.svg.getElement('groupBlock')
        prototypeIndividualBlock = self.svgLayer.svg.getElement('individualBlock')
        prototypeTag = self.svgLayer.svg.getElement('tag')
        
        groupClones = []
        individualClones = []
        
        for r in rows:
            if len(r) == 3: # File
                newGroupBlock = prototypeGroupBlock.clone()
                newGroupBlock.moveTo(0,h)
                newGroupBlock.label.setText(r[0])
                offset = newGroupBlock.height()
                w = max(newGroupBlock.label.left() + 10*len(r[0]),w)
                groupClones.append(newGroupBlock)
                
                if r[1]:
                    newGroupBlock.arrow.hide()
                else:
                    newGroupBlock.downArrow.hide()
                
                if r[2] != None:
                    newGroupBlock.checkBox.dash.hide()
                if r[2] != True:
                    newGroupBlock.checkBox.check.hide()
            else:
                newIndividualBlock = prototypeIndividualBlock.clone()
                newIndividualBlock.moveTo(newIndividualBlock.arrow.right(),h)
                newIndividualBlock.label.setText(r[0])
                offset = newIndividualBlock.height()
                w = max(newIndividualBlock.label.left() + 10*len(r[0]),w)
                individualClones.append(newIndividualBlock)
                
                if r[1] != True:
                    newIndividualBlock.checkBox.check.hide()
            h += offset
        
        # kill off the prototypes
        prototypeGroupBlock.delete()
        prototypeIndividualBlock.delete()
        prototypeTag.delete()
        
        # Apply the new widths
        for c in groupClones:
            c.background.setSize(w-c.checkBox.width(),c.height())
        for c in individualClones:
            c.background.setSize(w-c.checkBox.width(),c.height())
        
        self.svgLayer.resize(QSize(w,h))
        
        self.setLayer(self.svgLayer)
    
    def resizeEvent(self, event):
        self.updateList()