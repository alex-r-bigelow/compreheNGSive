from layeredWidget import mutableSvgLayer, layeredWidget
from PySide.QtCore import QSize

class treeSelectionWidget(layeredWidget):
    def __init__(self, data, parent = None):
        layeredWidget.__init__(self, parent)
        self.data = data
        self.updateList()
    
    def getCurrentRows(self):
        results = []
        for f in self.data.fileOrder:
            fobj = self.data.files[f]
            results.append((f,fobj.expanded,fobj.isChecked()))
            if fobj.expanded == True:
                for att in sorted(fobj.attributes.iterkeys()):
                    results.append((att,fobj.attributes[att]))
        return results
    
    def updateList(self):
        self.clearAllLayers()
        
        rows = self.getCurrentRows()
        if len(rows) == 0:
            return
        
        self.svgLayer = mutableSvgLayer('gui/svg/fileTags.svg',self)
        w = 0
        h = 0
        
        prototypeGroupBlock = self.svgLayer.svg.getElement('groupBlock')
        prototypeIndividualBlock = self.svgLayer.svg.getElement('individualBlock')
        prototypeTag = self.svgLayer.svg.getElement('tag')
        
        groupClones = []
        individualClones = []
        
        lastFile = None
        
        for r in rows:
            if len(r) == 3: # File
                newGroupBlock = prototypeGroupBlock.clone()
                newGroupBlock.moveTo(0,h)
                newGroupBlock.label.setText(r[0])
                newGroupBlock.setAttribute('___associatedFile',r[0])
                lastFile = r[0]
                offset = newGroupBlock.height()
                w = max(24 + 6*len(r[0]),w)  # this is some hacking... QSvgRenderer can't properly determine the bounding box of text elements
                groupClones.append(newGroupBlock)
                
                if r[1] != False:
                    newGroupBlock.arrow.hide()
                if r[1] != True:
                    newGroupBlock.downArrow.hide()
                
                if r[2] != None:
                    newGroupBlock.checkBox.dash.hide()
                if r[2] != True:
                    newGroupBlock.checkBox.check.hide()
            else:
                newIndividualBlock = prototypeIndividualBlock.clone()
                newIndividualBlock.moveTo(0,h)
                newIndividualBlock.label.setText(r[0])
                assert lastFile != None
                newIndividualBlock.setAttribute('___associatedFile',lastFile)
                offset = newIndividualBlock.height()
                w = max(24 + 6*len(r[0]),w) # this is some hacking... QSvgRenderer can't properly determine the bounding box of text elements
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
            c.background.setSize(w,c.height())
        for c in individualClones:
            c.background.setSize(w,c.height())
        
        self.svgLayer.resize(QSize(w,h))
        
        self.addLayer(self.svgLayer)
    
    def handleEvents(self, signals):
        changed = False
        if signals.has_key('groupOpened'):
            fileName = signals['groupOpened'].getAttribute('___associatedFile')
            self.data.files[fileName].expanded = True
            changed = True
        if signals.has_key('groupClosed'):
            fileName = signals['groupClosed'].getAttribute('___associatedFile')
            self.data.files[fileName].expanded = False
            changed = True
        if signals.has_key('checkClicked'):
            fileName = signals['checkClicked'].getAttribute('___associatedFile')
            attName = signals['checkClicked'].label.getText()
            assert self.data.files.has_key(fileName)
            fobj = self.data.files[fileName]
            if attName == fileName:
                if fobj.isChecked() != False:
                    fobj.check(False)
                else:
                    fobj.check(True)
            else:
                assert fobj.attributes.has_key(attName)
                fobj.attributes[attName] = not fobj.attributes[attName]
            changed = True
        
        if changed:
            self.updateList()
    
    def resizeEvent(self, event):
        self.updateList()