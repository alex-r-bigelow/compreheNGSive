import sys
from copy import deepcopy
from pyquery import PyQuery as pq
from scour.scour import scourString
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtSvg import *


'''
Special extensions to the .svg standard:
Qt doesn't support anything beyond SVG Tiny (which makes sense), but for what we're doing
we need some kind of interaction mechanisms. For anything beyond extremely basic interaction,
SVG Full relies on javascript anyway - the purpose of this code is to provide a python
abstraction layer for manipulating SVG. In the future, I would probably want a more
direct jquery-like interface; this incorporates some compreheNGSive-specific stuff:

reserved classes:

.id_ - XML (and many SVG editors) enforce unique ids; for handles that this can get at,
specify a class attribute of .id_(insert your handle here) NOTE: the underscore character
"_" is also reserved and should not be used by users in class attributes except in the case of .id_
In your python code, always refer to objects by t

Each of these is mutually exclusive:
.normal - these items will be shown by default; will also be shown if deselect() is called on them or an ancestor
.highlighted - these items will only be shown if highlight() is called on them or an ancestor
.selected - these items will only be shown if select() is called on them or an ancestor

attributes:

dragDirection - can be 'x', 'y', 'none', 'both', 'inherit' (default)
                'none' is the default behavior for the root element, 'inherit' for the rest; the most precise
                draggable element (lowest child that is under the mouse and draggable) will be the one dragged,
                along with any children. An element that inherits or has not dragDirection attribute will be
                treated as part of its parent. eg:
                
                a ( )
                    b (dragDirection:'x')
                        c (dragDirection:'y')
                            d (dragDirection: 'none')
                                e (dragDirection: 'both')
                                f ( )
                            g (dragDirection:'inherit')
                        h ( )
                    i (dragDirection:'inherit')
                
                Assuming a is the root SVG element and/or no elements above a have the dragDirection attribute:
                    Attempting to drag a will have no effect
                    Attempting to drag b will move b,c,d,e,f,g and h in the x direction only
                    Attempting to drag c will move c,d,e,f and g in the y direction only
                    Attempting to drag d will have no effect
                    Attempting to drag e will move e in both directions
                    Attempting to drag f will have no effect
                    Attempting to drag g will move c,d,e,f and g in the y direction only
                    Attempting to drag h will move b,c,d,e,f,g and h in the x direction only
                    Attempting to drag i will have no effect

cursor - this exists in the full SVG spec, but here we actually use an existing SVG element in the same document
         instead; supply the id as a parameter, and that element will be used as a cursor. 'none' can also be used to
         revert to system behavior; all children will inherit the closest ancestor cursor.
'''
class SvgElement:
    def __init__(self, parent, id):
        self.parent = parent
        self.id = id
        if "_" in self.id:
            self.cloneIndex = int(self.id[self.id.rfind("_")+1:])
        else:
            self.cloneIndex = None
        self.xml = self.parent.xmlObject("#%s"%id)
        
    def updateReference(self, xmlObject):
        self.xml = xmlObject("#%s"%self.id)
    
    def draw(self, painter, xOffset=None, yOffset=None):
        '''
        If offsets are supplied, a shallow copy is drawn - mouse locations, etc. will be wrong
        '''
        self.parent.drawElement(painter,self.id,xOffset,yOffset)
    
    def clone(self, translateX=None, translateY=None):
        # find the ID index extension to use for the new clone
        newId = str(self.id)
        newIndex = 2
        while len(self.parent.xmlObject("#%s" % newId)) > 0:
            newId = "%s_%i" % (self.id,newIndex)
            newIndex += 1
        # actually clone the thing, add it to the xml document
        newXml = self.xml.clone()
        newXml.attr("id","%s"%newId)
        newXml.appendTo(self.parent.xmlObject("#%s" % self.id).parent())
        # for some reason, references to each object get jumbled in this process, and we have to find them again
        self.updateReference(self.parent.xmlObject)
        # propagate the new index extension to all the children IDs
        self.propagateIDs(newXml,newIndex-1,isRoot=True)
        
        # apply translations if relevant
        if translateX != None or translateY != None:
            if translateX == None:
                translateX = 0
            if translateY == None:
                translateY = 0
            transforms = newXml.attr("transform")
            if transforms == None:
                transforms = ""
            if "translate" in transforms:
                start = transforms.find("translate")
                temp = transforms[start+10:]
                comma = temp.find(",")
                end = temp.find(")")
                if end < comma or comma == -1:
                    if " " in temp:
                        comma = temp.find(" ")
                if end < comma or comma == -1:
                    comma = end
                    y = 0
                else:
                    y = float(temp[comma+1:end])
                x = float(temp[:comma])
                transforms = transforms[:start+10] + "%f,%f" % (translateX+x,translateY+y) + temp[end:]
            else:
                if len(transforms) > 0:
                    transforms += ";"
                transforms += "translate(%f,%f)" % (translateX,translateY)
            newXml.attr("transform",transforms)
        
        # let the svg object know that it needs to be refreshed
        self.parent.isFlattened = False
        # send back a new cloned child (we run this through the parent so it knows to propagate updates to the new clone)
        return self.parent.getElement(newId)
    
    def propagateIDs(self,xml,index,isRoot):
        if len(xml) == 0:
            return
        # apply the index
        if not isRoot:
            oldID = xml.attr("id")
            xml.attr("id","%s_%i"%(oldID,index))
            
        # apply to children
        for c in xml.children():
            self.propagateIDs(pq(c), index, False)
    
    def convertId(self, id):
        if self.cloneIndex == None:
            return id
        else:
            return "%s_%i" % (id,self.cloneIndex)
    
    def getXml(self, id):
        if id == None:
            return self.xml
        else:
            return self.xml("#%s"%self.convertId(id))
    
    def getBounds(self, id=None):
        if not self.parent.isFlattened:
            self.parent.flattenSVG()
        if id == None:
            return self.parent.getBoundaries(self.id)
        else:
            return self.parent.getBoundaries(self.convertId(id))
    
    def setAttr(self, attribute, value, id=None):
        self.parent.isFlattened = False
        return self.getXml(id).attr(attribute,value)
    
    def setText(self, value, id=None):
        return self.getXml(id).filter(".text").text(value)
    
    def getAttr(self, attribute, id=None):
        return self.getXml(id).attr(attribute)
    
    def deselect(self, id):
        self.parent.isFlattened = False
        me = self.getXml(id)
        me.children(".highlighted").attr("visibility","hidden")
        me.children(".selected").attr("visibility","hidden")
        me.children(".normal").attr("visibility","visible")
    
    def highlight(self, id):
        self.parent.isFlattened = False
        me = self.getXml(id)
        me.children(".highlighted").attr("visibility","visible")
        me.children(".selected").attr("visibility","hidden")
        me.children(".normal").attr("visibility","hidden")
    
    def select(self, id):
        self.parent.isFlattened = False
        me = self.getXml(id)
        me.children(".highlighted").attr("visibility","hidden")
        me.children(".selected").attr("visibility","visible")
        me.children(".normal").attr("visibility","hidden")
    
    def deselectAll(self, xml):
        if len(xml) == 0:
            return
        self.deselect(xml.attr('id'))
        for child in xml.children():
            self.deselectAll(pq(child))
    
    def findMousedLeaf(self, xml, x, y):
        if len(xml) == 0:
            return None
        else:
            for child in reversed(xml.children()):
                deepQuery = self.findMousedLeaf(pq(child), x, y)
                if deepQuery != None:
                    return deepQuery
            id = xml.attr('id')
            if id == None or not self.getBounds(id).contains(x,y):
                return None
            else:
                return id
                
    
    def findMousedTargets(self, xml, att, inclusive):
        if len(xml) == 0:
            return []
        attribute = xml.attr(att)
        if attribute != None and attribute.lower() != 'inherit':
            if inclusive:
                return [xml.attr('id')]
            else:
                return []
        results = []
        for c in reversed(xml.children()):
            results.extend(self.findMousedTargets(pq(c), att, False))   # exclusive when going down
        p = xml.parents()
        if len(p) > 0:
            results.extend(self.findMousedTargets(p[-1], att, True))    # inclusive when going up
        id = xml.attr('id')
        if id != None:
            results.append(id)
        return results
        
class SvgWrapper:
    def __init__(self, path):
        self.xmlObject = pq(filename=path)
        
        cleanedXml = scourString(str(self.xmlObject),).encode("UTF-8")
        self.xmlObject = pq(cleanedXml)
        
        self.children = {}
        self.root = self.getElement(self.xmlObject.attr("id"))
        self.flattenSVG()
        self.deselectAll()
        
        self.mouseDown = False
        self.targetElements = []
    
    def flattenSVG(self):
        # scrub any useless cruft, flatten transformations
        #newXml = scourString(str(self.xmlObject),).encode("UTF-8")
        newXml = str(self.xmlObject)
        #print newXml
        
        # give our xml object and svg renderer the new xml
        #self.xmlObject = pq(newXml)
        self.svgObject = QSvgRenderer(QByteArray(newXml))
        
        #self.svgObject = QSvgRenderer(QByteArray(str(self.xmlObject)),self.parent)
        # sweet - we're done
        self.isFlattened = True
        
        for d in self.children.itervalues():
            d.updateReference(self.xmlObject)
    
    def drawSVG(self, painter):
        if not self.isFlattened:
            self.flattenSVG()
        self.svgObject.render(painter,QRect(QPoint(0,0),self.svgObject.defaultSize()))
    
    def getBoundaries(self, id):
        b = self.svgObject.boundsOnElement(id)
        if self.svgObject.elementExists(id):
            m = self.svgObject.matrixForElement(id)
            b = m.mapRect(b)
        return b
    
    def drawElement(self, painter, id, xOffset=None, yOffset=None):
        if not self.isFlattened:
            self.flattenSVG()
        bounds = self.getBoundaries(id)
        if xOffset != None and yOffset != None:
            bounds.moveTo(xOffset,yOffset)
        self.svgObject.render(painter,id,bounds)
    
    def getElement(self, id):
        if self.children.has_key(id):
            return self.children[id]
        temp = SvgElement(self,id)
        self.children[id] = temp
        return temp
    
    def getBounds(self, id=None):
        return self.root.getBounds(id)
    
    def setAttr(self, attribute, value, id=None):
        return self.root.setAttr(attribute, value, id)
    
    def setText(self, value, id=None):
        return self.root.setText(value, id)
    
    def getAttr(self, attribute, id=None):
        return self.root.getAttr(self, attribute, id)
    
    def highlight(self, id):
        return self.root.highlight(id)
    
    def deselect(self, id):
        return self.root.deselect(id)
    
    def select(self, id):
        return self.root.select(id)
    
    def deselectAll(self):
        self.root.deselectAll(pq(self.root.xml))
    
    def findMousedLeaf(self, x, y):
        return self.root.findMousedLeaf(self.xmlObject, x, y)
    
    def findMousedTargets(self, x, y, att):
        '''
        Returns a list of all affected elements in the manner described in the opening comment sorted from top to bottom and then back to front
        '''
        leaf = self.findMousedLeaf(x, y)
        return self.root.findMousedTargets(self.xmlObject(leaf),att,inclusive=True)    # inclusive if leaf happens to have the tag - it will be the only one
    
    def mouseMoveEvent(self, event):
        if self.mouseDown:
            return None
        else:
            for id in self.targetElements:
                self.deselect(id)
            self.targetElements = self.findMousedTargets(event.x(), event.y(), 'highlightChildren')
            print self.targetElements
            for id in self.targetElements:
                self.highlight(id)
            # TODO: cursors
            return "changesHappened"
    
    def mousePressEvent(self, event):
        return None
    
    def mouseReleaseEvent(self, event):
        return None