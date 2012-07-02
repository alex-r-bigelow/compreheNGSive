from resources.structures import recursiveDict
from scour.scour import scourString
from pyquery import PyQuery as pq
from PySide.QtCore import QByteArray, QRectF
from PySide.QtSvg import QSvgRenderer
import sys, math
from copy import deepcopy

'''
Special extensions to the .svg standard:
Qt doesn't support anything beyond SVG Tiny (which makes sense), but for what we're doing
we need some kind of interaction mechanisms. For anything beyond extremely basic interaction,
SVG Full relies on javascript anyway - the purpose of this code is to provide a python
abstraction layer for manipulating SVG. In the future, I would probably want a more
direct jquery-like interface; this incorporates some compreheNGSive-specific stuff:

custom events:
                The most precise selected element will initially be be the only element that receives an event
                packet. The most precise element is the deepest child of the frontmost element in the SVG XML tree; checking
                if the mouse is in the rectangle of elements relies on the id attribute, so if your SVG is ill-formed,
                it is possible that elements will be chosen that aren't under the cursor.
                
                To implement a custom event handler, set the __eventCode attribute on any element in the SVG
                document; whether it will receive the event or not is explained as follows:
                
                <g id='a'>
                    <g id='b' __eventCode="self.applyRelativeTranslation(event.deltaX,0)">
                        <g id='c' __eventCode="self.applyRelativeTranslation(0,event.deltaY)">
                            <g id='d' __eventCode="">
                                <g id='e' __eventCode="self.applyRelativeTranslation(event.deltaX,event.deltaY)"\>
                                <g id='f'\>
                            <\g>
                            <g id='g' __eventCode="signals = self.yieldEventToGroup(event=event,signals=signals)"\>
                        <\g>
                        <g id='h'\>
                    <\g>
                    <g id='i' __eventCode="signals = self.yieldEventToGroup(event=event,signals=signals)"\>
                <\g>
                
                No action is the default behavior for the root element. For all others, default behavior is
                to yield the event to its closest ancestor that implements the __eventCode attribute, or
                no action if no such ancestor exists:
                "signals = self.yieldEventToGroup(event=event,signals=signals)"
                
                Therefore:
                
                Assuming a is the root SVG element or no elements above a have the __eventCode attribute:
                    Moving the mouse over a will have no effect
                    Moving the mouse over b will move b,c,d,e,f,g and h in the x direction only
                    Moving the mouse over c will move c,d,e,f and g in the y direction only
                    Moving the mouse over d will have no effect
                    Moving the mouse over e will move e in both directions
                    Moving the mouse over f will have no effect
                    Moving the mouse over g will move c,d,e,f and g in the y direction only
                    Moving the mouse over h will move b,c,d,e,f,g and h in the x direction only
                    Moving the mouse over i will have no effect
                
                (of course a more practical implementation would include checks to see if the mouse button was down before
                translating, which would give us simple dragging functionality - but for readability I left that out)
                
                Python implementation namespace:
                Implement custom events as if you were filling in this stub with no accessible global variables:
                
                def handleEvent(self, event, signals={'__SVG__DIRTY__':True}):
                    
                    ... your code here ...
                    
                    return signals
                
                self is a mutableSvgNode object; you can use this to query/manipulate it or other SVG elements that it can
                access via the globalSearch() and localSearch() methods.
                
                event is a QtEventPacket object; with it you can access details about the state of the user's actions in the
                last frame (e.g. which keys/mouse buttons are down, the current mouse location, and the movement of the mouse
                since the previous frame)
                
                signals is a dictionary object that you can use to pass high-level interpretations to your controller
                (e.g. signals['toy_icon_was_dragged']=(event.deltaX(),event.deltaY()) ). The final signal dict will be returned from *****TODO: fill this in*****
                There is one reserved signal: '__SVG__DIRTY__' that will be removed from the dict before it is returned from *****;
                this is used to notify the renderer that the view needs to be updated. Only set this to False if your custom code does
                not modify the appearance of the resulting SVG. You should really only bother setting this to False if you
                have a lot of minimally invasive custom code and performance is lagging.
                
                You should NOT include the return statement; whatever is in the signals dict will be returned. If you wish to
                pass the event on to parent nodes as well as perform custom code locally, be sure to call self.yieldEventToGroup()
                appropriately. You can also pass messages between nodes via the signals dict, though any signals from a parent
                node that are meant for the controller should be copied by the child node from the return value of
                self.yieldEventToGroup() to the signals dict, or they will not be preserved. A simple way to do this is:
                
                signals.update(self.yieldEventToGroup(event=event,signals=signals))

child node attributes:
                For performance reasons, it might be a good idea to store references to frequently used child elements in a
                node's attributes for easy access. To do this, begin a parameter value with "__". For example:
                
                *** TODO ***

'''

'''
TODO:
render function
__revertCode attribute
clone function
'''

class SvgMapException(Exception):
    def __init__(self, value):
        self.value = "\n" + value
    def __str__(self):
        return self.value

class mutableSvgNode:
    def __init__(self, document, controller, xmlElement, parent=None, isClone=False):
        self.document = document
        self.controller = controller
        self.xmlElement = xmlElement
        self.document.nodeLookup[self.xmlElement] = self
        
        self.parent = parent
        self.children = []
        
        self.isClone = isClone
        if isClone:
            self.document.numClones += 1
        
        self.attributes = xmlElement.attrib
        self.originalVisibility = None
        self.parseTransforms(self.attributes.get('transform',""))
        
        # Events
        if self.attributes.has_key('__eventCode'):
            self.eventProgram = self.compileCode(self.attributes['__eventCode'],isEvent=True)
        else:
            self.eventProgram = None
        
        # Resets
        if self.attributes.has_key('__resetCode'):
            if self.eventProgram == None:
                raise SvgMapException("Node %s\nhas __resetCode without __eventCode" % (str(self)))
            self.resetProgram = self.compileCode(self.attributes['__resetCode'])
        else:
            self.resetProgram = None
        
        self.resetAttributes = {}
        for k,v in self.attributes.iteritems():
            self.resetAttributes[k] = v # I would just do self.attributes.copy(), but self.attributes is actually not a normal dict
        
        # Custom references
        self.needs = {}
        for a,v in self.attributes.iteritems():
            if a == '__parentProperty':
                if self.parent == None or not self.parent.fillNeed(v,self):
                    raise SvgMapException("Node %s\nhas a __parentProperty %s that filled no requirements" % (str(self),v))
            elif a == '__childProperty':
                if self.document.childProperites.has_key(v):
                    raise SvgMapException("Two parent nodes:\n(%s and %s)\nattempted to fill the same __childProperty: %s" % (str(self),str(self.document.childProperites[v]),v))
                self.document.childProperites[v] = self
            elif a == '__globalProperty':
                if self.document.globalProperties.has_key(v):
                    raise SvgMapException("Two nodes:\n(%s and %s)\nattempted to fill the same __globalProperty: %s" % (str(self),str(self.document.globalProperties[v]),v))
                self.document.globalProperties[v] = self
            elif v.startswith("__"):
                if hasattr(self,a):
                    raise SvgMapException("Node %s attempts to overwrite a reserved or existing property %s" % (str(self),a))
                if self.document.childProperites.has_key(v):
                    self.needs[a] = self.document.childProperites[v]
                    setattr(self,a,self.document.childProperites[v])
                else:
                    self.needs[a] = v
        
        # run custom init code
        if self.attributes.has_key('__initCode'):
            self.initProgram = self.compileCode(self.attributes['__initCode'])
            customNameSpace = {'self':self}
            exec self.initProgram in {},customNameSpace
        else:
            self.initProgram = None
    
    # ****** TODO: make these private! ********
    
    def compileCode(self, code, isEvent=False):
        if isEvent:
            if 'self.yieldEvent' in code:
                self.callsGroupRoot = True
            else:
                self.callsGroupRoot = False
        temp = code.split("\\n ")
        temp = "\n".join(temp)
        
        return compile(temp,'<string>','exec')
    
    def addChild(self, c):
        self.children.append(c)
    
    def __str__(self):
        tag = self.xmlElement.tag
        if "{" in tag and "}" in tag:
            tag = tag[tag.find("}")+1:]
        html = "<%s" % tag
        if self.attributes.has_key('id'):
            html += " id='%s'" % self.attributes['id']
        if self.attributes.has_key('class'):
            html += " class='%s'" % self.attributes['class']
        html += ">...</%s>" % tag
        return html
    
    def fillNeed(self,value,obj):
        if self.parent != None:
            success = self.parent.fillNeed(value,obj)
        else:
            success = False
        
        for a,v in self.attributes.iteritems():
            if v == value:
                if not isinstance(self.needs[a],str):
                    raise SvgMapException("Two nodes:\n(%s and %s)\nattempted to fill the same attribute:\n(%s of node %s)\nwith __parentProperty or __childProperty:\n%s" % (str(obj),str(self.needs[a]),a,str(self),v))
                self.needs[a] = obj
                setattr(self,a,obj)
                success = True
        
        return success
    
    def verify(self):
        for v in self.needs.itervalues():
            if isinstance(v,str):
                raise SvgMapException("No child has a __parentProperty that maps to the %s requirement of node:\n%s" % (v,str(self)))
        for c in self.children:
            c.verify()
    
    def runCustomEvent(self,event,signals):
        inDirty = signals.get('__SVG__DIRTY__',True)
        signals['__SVG__DIRTY__'] = True
        signals['__EVENT__ABSORBED__'] = True
        customNameSpace = {'self':self,
                           'event':event,
                           'signals':signals}
        exec self.eventProgram in {},customNameSpace
        signals = customNameSpace['signals']
        signals['__SVG__DIRTY__'] = inDirty or signals.get('__SVG__DIRTY__',True)
        signals['__EVENT__ABSORBED__'] = signals.get('__EVENT__ABSORBED__',True)
        return signals
    
    def runReset(self,event,signals):
        inDirty = signals.get('__SVG__DIRTY__',True)
        signals['__SVG__DIRTY__'] = True
        signals['__EVENT__ABSORBED__'] = True
        customNameSpace = {'self':self,
                           'event':event,
                           'signals':signals}
        exec self.resetProgram in {},customNameSpace
        signals = customNameSpace['signals']
        signals['__SVG__DIRTY__'] = inDirty or signals.get('__SVG__DIRTY__',True)
        signals['__EVENT__ABSORBED__'] = signals.get('__EVENT__ABSORBED__',True)
        return signals
    
    def getRect(self):
        id = self.attributes.get('id',None)
        temp = self.parent
        while id == None and temp != None:
            id = temp.attributes.get('id',None)
            temp = temp.parent
        return self.document.getBoundaries(id)
    
    def setSizeZero(self):
        if self.originalVisibility == None:
            self.originalVisibility = self.getAttribute('visibility')
            if self.originalVisibility == None:
                self.originalVisibility = 'visible'
        self.hide()
    
    def unsetSizeZero(self):
        if self.originalVisibility != None:
            self.setAttribute('visibility', self.originalVisibility, True)
        self.originalVisibility = None
    
    # ****** TODO: these are my API... rename them? ******
        
    def resetAllAttributes(self):
        newKeys = set()
        for k in self.attributes.iterkeys():
            if self.resetAttributes.has_key(k):
                self.attributes[k] = self.resetAttributes[k]
            else:
                newKeys.add(k)
        for k in newKeys:
            del self.attributes[k]
    
    def getRoot(self):
        temp = self
        while temp.parent != None:
            temp = temp.parent
        return temp
    
    def globalSearch(self, queryString):
        results = []
        for x in self.document.queryObject(queryString):
            results.append(self.document.nodeLookup[x])
        return results
    
    def localSearch(self, queryString):
        results = []
        for x in self.document.queryObject(self.xmlElement).find(queryString):
            results.append(self.document.nodeLookup[x])
        return results
    
    def parseTransforms(self, string):
        self.transforms = [1.0,0.0,0.0,1.0,0.0,0.0] # identity matrix
        transformList = string.split(")")
        for t in transformList:
            key,p,values = t.partition("(")
            if "," in values:
                values = values.split(",")
            else:
                values = values.split()
            if key == 'matrix':
                self.matrix(float(values[0]),float(values[1]),float(values[2]),float(values[3]),float(values[4]),float(values[5]),applyImmediately=False)
            elif key == 'translate':
                if len(values) == 1:
                    values.append(0)
                self.translate(float(values[0]),float(values[1]),applyImmediately=False)
            elif key == 'scale':
                if len(values) == 1:
                    values.append(values[0])
                self.scale(float(values[0]),float(values[1]),applyImmediately=False)
            elif key == 'rotate':
                while len(values) < 3:
                    values.append(0)
                self.rotate(float(values[0]),float(values[1]),float(values[2]),applyImmediately=False)
            # TODO: add other transforms
    
    def applyTransforms(self):
        self.attributes['transform'] = 'matrix(%f,%f,%f,%f,%f,%f)' % (self.transforms[0],self.transforms[1],self.transforms[2],self.transforms[3],self.transforms[4],self.transforms[5])
        self.document.forceFreeze()
    
    def matrix(self,a,b,c,d,e,f,applyImmediately=True):
        # Per SVG spec, flatten by multiplying the new matrix to the left of the existing one
        temp = list(self.transforms) # copy
        self.transforms[0] = a*temp[0] + c*temp[1] # + e*0.0
        self.transforms[2] = a*temp[2] + c*temp[3] # + e*0.0
        self.transforms[4] = a*temp[4] + c*temp[5] + e # *1.0
        
        self.transforms[1] = b*temp[0] + d*temp[1] # + e*0.0
        self.transforms[3] = b*temp[2] + d*temp[3] # + e*0.0
        self.transforms[5] = b*temp[4] + d*temp[5] + f # *1.0
        
        if applyImmediately:
            self.applyTransforms()
    
    def translate(self, deltaX, deltaY, applyImmediately=True):
        self.transforms[4] += deltaX
        self.transforms[5] += deltaY
        if applyImmediately:
            self.applyTransforms()
    
    def moveTo(self, x, y):
        l,t,r,b = self.getBounds()
        deltaX = x-l
        deltaY = y-t
        self.translate(deltaX, deltaY)
    
    def translateLimit(self, deltaX, deltaY, left, top, right, bottom):
        self.translate(deltaX,deltaY)
        self.document.forceFreeze()
        if not QRectF(left,top,right-left,bottom-top).contains(self.getRect()):
            self.translate(-deltaX,-deltaY)
    
    def scale(self, xFactor, yFactor, applyImmediately=True):
        self.transforms[0] *= xFactor
        self.transforms[3] *= yFactor
        if applyImmediately:
            self.applyTransforms()
    
    def stretch(self, fromLeft, fromTop, fromRight, fromBottom):
        l,t,r,b = self.getBounds()
        width = float(r-l)
        height = float(b-t)
        xGrowth = fromLeft + fromRight
        yGrowth = fromTop + fromBottom
        
        xFactor = None
        yFactor = None
        if width + xGrowth <= 0:
            self.setSizeZero()
            xFactor = 1.0
        elif self.originalVisibility != None:
            self.unsetSizeZero()
        if height + yGrowth <= 0:
            self.setSizeZero()
            yFactor = 1.0
        elif self.originalVisibility != None and xFactor == None:
            self.unsetSizeZero()
        
        if xFactor == None:
            xFactor = (xGrowth + width)/width
        if yFactor == None:
            yFactor = (yGrowth + height)/height
        self.scale(xFactor,yFactor)
        self.moveTo(l-fromLeft, t-fromTop)
    
    def setSize(self, width, height):
        l,t,r,b = self.getBounds()
        self.stretch(0, 0, width-(r-l), height-(b-t))
    
    def rotate(self, degrees, offsetX=0, offsetY=0, applyImmediately=True):
        '''
        #print "1 %s %s %s" % (self.attributes.get('id','noid'),str(self.transforms),str(self.getBounds()))
        b = self.getRect()
        offsetX += b.left()+b.width()/2
        offsetY += b.top()+b.height()/2
        self.translate(-offsetX, -offsetY, applyImmediately)
        #print "2 %s %s %s" % (self.attributes.get('id','noid'),str(self.transforms),str(self.getBounds()))
        r = math.radians(degrees)
        c = math.cos(r)
        s = math.sin(r)
        self.matrix(c,s,-s,c,0,0, applyImmediately)
        # Qt does some funky messing with coordinates right here... rotate doesn't work yet!
        #print "3 %s %s %s" % (self.attributes.get('id','noid'),str(self.transforms),str(self.getBounds()))
        self.translate(offsetX, offsetY, applyImmediately)
        #print "4 %s %s %s" % (self.attributes.get('id','noid'),str(self.transforms),str(self.getBounds()))
        '''
    
    def hide(self):
        self.setAttribute('visibility', 'hidden', True)
    
    def show(self):
        if self.originalVisibility != None:
            self.originalVisibility = 'visible'
        else:
            self.setAttribute('visibility', 'visible', True)
    
    def getBounds(self):
        b = self.getRect()
        tl = b.topLeft()
        br = b.bottomRight()
        return (tl.x(),tl.y(),br.x(),br.y())
    
    def intersects(self, other):
        return self.getRect().intersects(other.getRect())
    
    def top(self):
        return self.getRect().top()
    
    def left(self):
        return self.getRect().left()
    
    def right(self):
        return self.getRect().right()
    
    def bottom(self):
        return self.getRect().bottom()
    
    def width(self):
        return self.getRect().width()
    
    def height(self):
        return self.getRect().height()
    
    def contains(self,other):
        return self.getRect().contains(other.getRect())
    
    def contains(self,x,y):
        return self.getRect().contains(x,y)
    
    def clone(self):
        if self.parent == None:
            raise SvgMapException("Attempted to clone parentless node: %s\n(probably the root, which is not allowed)" % str(self))
        twin = deepcopy(self.xmlElement)
        for node in twin.iter():
            appendText = "_%i" % self.document.numClones
            if node.attrib.has_key('__globalProperty'):
                del node.attrib['__globalProperty']
            for att in node.attrib.iterkeys():
                if att == 'id' or att == '__parentProperty' or att == '__childProperty' or node.attrib[att].startswith("__"):
                    if not self.isClone:
                        node.attrib[att] += appendText
                    else:
                        temp = node.attrib[att]
                        node.attrib[att] = temp[:temp.rfind("_")] + appendText
                            
        self.xmlElement.getparent().append(twin)
        result = self.document.buildTree(twin,self.parent,buildClones=True)
        self.parent.addChild(result)
        self.document.forceFreeze()
        return result
    
    def delete(self):
        # remove ourself completely from the SVG
        if self.parent != None:
            self.parent.children.remove(self)
        self.xmlElement.getparent().remove(self.xmlElement)
        self.document.reset.discard(self)
        self.document.active.discard(self)
        self.document.forceFreeze()
    
    def setText(self, text):
        self.xmlElement.text = text
        self.document.forceFreeze()
    
    def getText(self):
        return self.xmlElement.text
    
    def setAttribute(self, att, value, force=True):
        if not self.attributes.has_key(att):
            success = self.setCSS(att,value,force=False)
        else:
            self.attributes[att] = str(value)
            success = True
        
        if not success and force:
            self.attributes[att] = str(value)
            success = True
        
        if success:
            if att == 'transform':
                self.parseTransforms[self.attributes['transform']]
            elif att == "__eventCode":
                if self.attributes['__eventCode'] == "":
                    del self.attributes['__eventCode']
                    self.eventProgram = None
                    self.callsGroupRoot = False
                else:
                    self.eventProgram = self.compileCode(self.attributes['__eventCode'],isEvent=True)
            elif att == '__resetCode':
                if self.attributes['__resetCode'] == "":
                    del self.attributes['__resetCode']
                    self.resetProgram = None
                else:
                    self.resetProgram = self.compileCode(self.attributes['__resetCode'])
            # elif att == '__initCode': only clones of me could ever experience this... and they'll recompile it on their own anyway. don't bother compiling
            elif att in self.needs.iterkeys():
                raise SvgMapException("TODO: I have not yet implemented resetting of custom attributes...")
        return success     
    
    def setCSS(self, att, value, force=True):
        if not self.attributes.has_key('style'):
            if force:
                self.attributes['style'] = "%s:'%s'" % (att,str(value))
                return True
            else:
                return False
        else:
            css = self.attributes['style']
            result = ""
            att = att.strip().lower()
            setValue = False
            for pair in css.split(";"):
                pair = pair.split(":")
                a = pair[0].strip().lower()
                v = pair[1].strip().lower()
                
                a = a.strip().lower()
                if a == att:
                    result += "%s:%s;" % (a,str(value))
                    setValue = True
                else:
                    result += "%s:%s;" % (a,v)
            if setValue:
                self.attributes['style'] = result[:-1]
                return True
            elif force:
                self.attributes['style'] = result + "%s:%s" % (att,v)
                return True
            else:
                return False
    
    def getAttribute(self, att):
        value = self.attributes.get(att,self.getCSS(att))
        if value == None:
            return None
        try:
            value = int(value)
        except ValueError:
            try:
                value = float(value)
            except ValueError:
                pass
        return value
    
    def getCSS(self, att):
        css = self.attributes.get('style',None)
        att = att.strip().lower() + ":"
        if css == None or att not in css:
            return None
        else:
            part = css[css.find(att)+len(att):]
            endPoint = part.find(";")
            if endPoint == -1:
                endPoint = len(part)-1
            value = part[:endPoint]
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass
            return value

class mutableSvgRenderer:
    def __init__(self, path, controller):
        self.controller = controller
        
        self.nodeLookup = {}
        self.queryObject = None
        self.active = set()
        self.reset = set()
        self.locks = set()
        self.childProperites = {}
        self.globalProperties = {}
        self.numClones = 0
        
        self.queryObject = pq(filename=path)
        #cleanedXml = scourString(str(self.queryObject),).encode("UTF-8")
        #self.queryObject = pq(cleanedXml)
        
        self.isFrozen = False
        
        self.root = self.buildTree(self.queryObject.root.getroot(),parent=None)
        self.root.verify()
        
        self.freeze()
        
        self.lastTarget = None
    
    def buildTree(self, xmlObject,parent=None,buildClones=False):
        newNode = mutableSvgNode(self,self.controller,xmlObject,parent,isClone=buildClones)
        
        for child in xmlObject.getchildren():
            newChild = self.buildTree(child, newNode)
            newNode.addChild(newChild)
        return newNode
    
    def getElement(self, key):
        return self.globalProperties[key]
    
    def freeze(self):
        if self.isFrozen:
            return
        self.renderer = QSvgRenderer(QByteArray(str(self.queryObject)))
        if self.root != None:
            b = self.getBoundaries()
            self.renderer.setViewBox(b)
            self.root.setAttribute('width', b.width())
            self.root.setAttribute('height', b.height())
        self.isFrozen = True
    
    def forceFreeze(self):
        self.isFrozen = False
        self.freeze()
    
    def thaw(self):
        self.isFrozen = False
    
    def handleFrame(self, userState, node=None, results={'__EVENT__ABSORBED__':False,'__SVG__DIRTY__':False}, runLocks=False):
        if node == None:
            self.reset = set(self.active)
            self.active = set()   # empty out the active set... afterward, anything that's in reset that isn't in active will need to have reset called
            
            # First run on all locked nodes
            for n in self.locks:
                temp = results.get('__SVG__DIRTY__',True)
                if n.eventProgram != None:
                    results['__SVG__DIRTY__'] = True
                    results = self.handleFrame(userState, n, results, runLocks=True)
                results['__SVG__DIRTY__'] = results['__SVG__DIRTY__'] or temp
            
            if not results.get('__EVENT__ABSORBED__',True):
                results = self.handleFrame(userState, self.root, results)
            
            # Run any resets...
            needReset = self.reset.difference(self.active)
            needReset = needReset.difference(self.locks)
            for n in needReset:
                temp = results.get('__SVG__DIRTY__',True)
                if n.resetProgram != None:
                    results['__SVG__DIRTY__'] = True
                    n.runReset(userState,results)
                self.reset.discard(n)
                results['__SVG__DIRTY__'] = results['__SVG__DIRTY__'] or temp  # again, we want to let it be clean only if every call explicitly marks it clean
            
            # Okay, we're finally done - we need to check if something dirtified the SVG:
            if results.get('__SVG__DIRTY__',True):
                self.thaw()
            # Clean up our little internal flags
            if results.has_key('__SVG__DIRTY__'):
                del results['__SVG__DIRTY__']
            return results
        else:
            if results.get('__EVENT__ABSORBED__',True):
                return results
            id = node.attributes.get('id',None)
            if id != None:
                inBounds = self.eventInElement(userState,id)
            else:
                inBounds = True # If there's no id, we'll have to check the children...
                                # If there's no id there, we'll have to assume the frontmost, deepest child is in bounds.
                                # This isn't ideal, but the SVG is screwed up so this is the best we can do
            if inBounds or runLocks:
                for child in reversed(node.children):   # DFS, using the frontmost elements first
                    if not runLocks and child in self.locks:
                        continue
                    results = self.handleFrame(userState, child, results)
                    if results.get('__EVENT__ABSORBED__',True) == True:
                        break
                
                # Okay, no child has absorbed the event yet... so I actually get to call my event if I'm visible and I have one
                if node.eventProgram != None and node.getAttribute('visibility') != 'hidden' and results.get('__EVENT__ABSORBED__',True) == False:
                    results = node.runCustomEvent(userState,signals=results) # we'll start by assuming it's clean; provided no custom code touches the appearance, this will come back intact
                    self.active.add(node)
                    if results.get('__LOCK__',False):
                        self.locks.add(node)
                    else:
                        self.locks.discard(node)
                    if results.has_key('__LOCK__'):
                        del results['__LOCK__']
            return results
    
    def getBoundaries(self, id=None):
        if id == None:
            id = self.root.attributes['id']
        b = self.renderer.boundsOnElement(id)
        if self.renderer.elementExists(id):
            m = self.renderer.matrixForElement(id)
            #print "id: %s b: %s m: %s" % (id,b,m)
            b = m.mapRect(b)
        return b
    
    def getVisibleBoundaries(self, id=None):
        objBounds = self.getBoundaries(id)
        viewBounds = self.renderer.viewBoxF()
        objBounds.setLeft(max(objBounds.left(),viewBounds.left()))
        objBounds.setTop(max(objBounds.top(),viewBounds.top()))
        objBounds.setRight(min(objBounds.right(),viewBounds.right()))
        objBounds.setBottom(min(objBounds.bottom(),viewBounds.bottom()))
        return objBounds
        
    def eventInElement(self, event, id):
        self.freeze()
        if self.renderer.elementExists(id):
            return self.getBoundaries(id).contains(event.x,event.y)
        else:
            return True # If we have an element with no id or that's un-renderable, we have to assume that we're in bounds
    
    def render(self, painter, queryString=None):
        self.freeze()
        if queryString == None:
            self.renderer.render(painter,self.renderer.viewBox())
        else:
            id = self.queryObject(queryString).attr('id')
            if id == None:
                self.renderer.render(painter,self.renderer.viewBox())
            else:
                self.renderer.render(painter,id,self.getVisibleBoundaries(id))
    
    def defaultSize(self):
        self.forceFreeze()
        return self.renderer.defaultSize()
    
    
    
    
    
    