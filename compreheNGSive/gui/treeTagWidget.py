from layeredWidget import mutableSvgLayer, layeredWidget
from PySide.QtCore import QSize

class treeTagWidget(layeredWidget):
    def __init__(self, data, parent = None):
        layeredWidget.__init__(self, parent)
        self.data = data
        
        self.svgLayer = mutableSvgLayer('gui/svg/groupTags.svg',self)
        self.addLayer(self.svgLayer)
        
        self.prototypeGroupBlock = self.svgLayer.svg.getElement('groupBlock')
        self.prototypeIndividualBlock = self.svgLayer.svg.getElement('individualBlock')
        
        self.wOffset = self.prototypeGroupBlock.background.left()
        
        self.visItems = [(True,self.prototypeGroupBlock),(False,self.prototypeIndividualBlock)]
        self.tags = {}
        
        self.updateList()
        self.peeling = None
    
    def getCurrentRows(self):
        results = []
        for g in self.data.groupOrder:
            gobj = self.data.groups[g]
            results.append((True,gobj))
            if gobj.expanded == True:
                for i,checked in gobj.nativeMembers.iteritems():
                    results.append((False,i,checked))
                for i,checked in gobj.foreignMembers.iteritems():
                    results.append((False,i,checked))
        return results
    
    def updateList(self):
        return
        rows = self.getCurrentRows()
        
        # first clone and position the elements, figure out how wide the text goes
        h = 0
        w = 0
        for i,r in enumerate(rows):
            newItem = None
            if i < len(self.visItems):
                if r[0] and not self.visItems[i][0]:    # an individual item exists, but we need a group item
                    item = self.visItems[i][1]
                    if item == self.prototypeIndividualBlock:    # we don't want to destroy our prototype... just pull it out of the list, hide it, and we'll throw it at the end later
                        self.visItems.pop(i)
                        item.hide()
                    
                    newItem = self.prototypeGroupBlock.clone()
                    self.visItems.insert(i,(True,newItem))
                    newItem.translate(0,h-newItem.top())
                    newItem.show()
                    
                    if item == self.prototypeIndividualBlock:
                        self.visItems.append((False,item))
                elif not r[0] and self.visItems[i][0]:  # a group item exists, but we need an individual one
                    item = self.visItems[i][1]
                    if item == self.prototypeGroupBlock:    # we don't want to destroy our prototype... just pull it out of the list, hide it, and we'll throw it at the end later
                        self.visItems.pop(i)
                        item.hide()
                    
                    newItem = self.prototypeIndividualBlock.clone()
                    self.visItems.insert(i,(True,newItem))
                    newItem.translate(0,h-newItem.top())
                    newItem.show()
                    
                    if item == self.prototypeGroupBlock:
                        self.visItems.append((False,item))
                else:   # already matching
                    newItem = self.visItems[i][1]
            else:
                if r[0]:
                    newItem = self.prototypeGroupBlock.clone()
                    self.visItems.append((True,newItem))
                    newItem.translate(0,h-newItem.top())
                    newItem.show()
                else:
                    newItem = self.prototypeIndividualBlock.clone()
                    self.visItems.append((False,newItem))
                    newItem.translate(0,h-newItem.top())
                    newItem.show()
            h += newItem.height()
        
        # clean up any leftovers
        indicesToRemove = []
        for i,(isgroup,item) in enumerate(self.visItems[len(rows):]):
            if isgroup:
                if item != self.prototypeGroupBlock:
                    indicesToRemove.append(i)
            else:
                if item != self.prototypeIndividualBlock:
                    indicesToRemove.append(i)
        for i in indicesToRemove:
            self.visItems[i][1].delete()
            self.visItems.pop(i)
        
        '''
        # Now figure out the details
        w = 0
        h = 0
                
        groupClones = []
        individualClones = []
        
        lastGroup = None
        
        for r in rows:
            obj = r[1]
            if r[0]: # Group
                newGroupBlock = self.prototypeGroupBlock.clone()
                newGroupBlock.moveTo(0,h)
                newGroupBlock.label.setText(obj.name)
                newGroupBlock.setAttribute('___associatedGroup',obj.name)
                lastGroup = obj.name
                offset = newGroupBlock.height()
                w = max(24 + 6*len(obj.name),w) # this is some hacking... QSvgRenderer can't properly determine the bounding box of text elements
                groupClones.append(newGroupBlock)
                
                if obj.expanded != False:
                    newGroupBlock.arrow.hide()
                if obj.expanded != True:
                    newGroupBlock.downArrow.hide()
                
                checked = obj.isChecked()
                if checked != None:
                    newGroupBlock.checkBox.dash.hide()
                if checked != True:
                    newGroupBlock.checkBox.check.hide()
            else:
                newIndividualBlock = prototypeIndividualBlock.clone()
                newIndividualBlock.moveTo(0,h)
                newIndividualBlock.label.setText(obj.name)
                assert lastGroup != None
                newIndividualBlock.setAttribute('___associatedGroup',lastGroup)
                offset = newIndividualBlock.height()
                w = max(24 + 6*len(obj.name),w) # this is some hacking... QSvgRenderer can't properly determine the bounding box of text elements
                individualClones.append(newIndividualBlock)
                
                if r[2] != True:
                    newIndividualBlock.checkBox.check.hide()
            h += offset
        
        # Apply the new widths
        for c in groupClones:
            c.background.setSize(w,c.height())
        for c in individualClones:
            c.background.setSize(w,c.height())'''
        
        self.svgLayer.resize(QSize(w+self.wOffset,h))
        
        #self.addLayer(self.svgLayer)
    
    def handleEvents(self, event, signals):
        changed = False
        if signals.has_key('groupOpened'):
            groupName = signals['groupOpened'].getAttribute('___associatedGroup')
            self.data.groups[groupName].expanded = True
            changed = True
        if signals.has_key('groupClosed'):
            groupName = signals['groupClosed'].getAttribute('___associatedGroup')
            self.data.groups[groupName].expanded = False
            changed = True
        if signals.has_key('checkClicked'):
            groupName = signals['checkClicked'].getAttribute('___associatedGroup')
            individualName = signals['checkClicked'].label.getText()
            assert self.data.groups.has_key(groupName)
            gobj = self.data.groups[groupName]
            if individualName == groupName:
                if gobj.isChecked() != False:
                    gobj.check(False)
                else:
                    gobj.check(True)
            else:
                iobj = self.data.individuals[individualName]
                assert gobj.nativeMembers.has_key(iobj) or gobj.foreignMembers.has_key(iobj)
                # TODO: if a group has two (or more) individuals of the same name, how to resolve the issue?
                if gobj.nativeMembers.has_key(iobj):
                    gobj.nativeMembers[iobj] = not gobj.nativeMembers[iobj]
                elif gobj.foreignMembers.has_key(iobj):
                    gobj.foreignMembers[iobj] = not gobj.foreignMembers[iobj]
            changed = True
        
        
        if signals.has_key('startPeel'):
            self.peeling = signals['startPeel'][0].clone()
            self.peeling.checkBox.delete()
            if hasattr(self.peeling,'downArrow') and self.peeling.downArrow != None:
                self.peeling.downArrow.delete()
            if hasattr(self.peeling,'arrow') and self.peeling.arrow != None:
                self.peeling.arrow.delete()
            self.peeling.background.setAttribute('fill-opacity',0.1)
            self.peeling.setAttribute('__eventCode',"signals['__EVENT__ABSORBED__'] = False\n"+
                                                    "signals['__LOCK__'] = True\n"+
                                                    "if 'LeftButton' not in event.buttons:\n"+
                                                    "    signals['tagDropped'] = self\n"+
                                                    "else:\n"+
                                                    "    self.translate(event.deltaX,event.deltaY)")
            #self.peeling.setAttribute('__resetCode',"self.delete()")
            self.peeling.moveTo(signals['startPeel'][1]-self.peeling.width()/2,signals['startPeel'][2]-self.peeling.height()/2)
        if signals.has_key('endPeel') and signals.has_key('tagDropped'):
            sourceName = self.peeling.label.getText()
            sourceGroupName = self.peeling.getAttribute('___associatedGroup')
            targetName = signals['endPeel'].label.getText()
            targetGroupName = signals['endPeel'].getAttribute('___associatedGroup')
            # TODO
            
            print 'endPeel'
        if signals.has_key('tagDropped'):
            if self.peeling != None:
                self.peeling.delete()
                self.peeling = None
        
        if changed:
            self.updateList()
    
    def resizeEvent(self, event):
        self.updateList()