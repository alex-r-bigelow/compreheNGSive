from resources.structures import recursiveDict
from pyquery import PyQuery as pq
from PySide.QtCore import QByteArray, QRectF
from PySide.QtSvg import QSvgRenderer
import sys
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
                            <g id='g' __eventCode="signals = self.yieldEventToGroupParent(event=event,signals=signals)"\>
                        <\g>
                        <g id='h'\>
                    <\g>
                    <g id='i' __eventCode="signals = self.yieldEventToGroupParent(event=event,signals=signals)"\>
                <\g>
                
                No action is the default behavior for the root element. For all others, default behavior is
                to yield the event to its closest ancestor that implements the __eventCode attribute, or
                no action if no such ancestor exists:
                "signals = self.yieldEventToGroupParent(event=event,signals=signals)"
                
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
                pass the event on to parent nodes as well as perform custom code locally, be sure to call self.yieldEventToGroupParent()
                appropriately. You can also pass messages between nodes via the signals dict, though any signals from a parent
                node that are meant for the controller should be copied by the child node from the return value of
                self.yieldEventToGroupParent() to the signals dict, or they will not be preserved. A simple way to do this is:
                
                signals.update(self.yieldEventToGroupParent(event=event,signals=signals))

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
        self.value = value
    def __str__(self):
        return repr(self.value)

class mutableSvgNode:
    nodeLookup = {}
    queryObject = None
    active = set()
    reset = set()
    lock = None
    
    def __init__(self, document, xmlElement, parent=None, groupParent=None, cloneNumber=0):
        self.document = document
        self.xmlElement = xmlElement
        mutableSvgNode.nodeLookup[self.xmlElement] = self
        
        self.parent = parent
        self.groupParent = groupParent
        self.cloneNumber = cloneNumber
        self.callsGroupParent = False
        self.children = []
        
        self.attributes = xmlElement.attrib
        self.parseTransforms(self.attributes.get('transform',""))
        
        # Events
        if self.attributes.has_key('__eventCode'):
            self.eventCode = self.attributes['__eventCode']
            self.eventProgram = self.compileCode(self.eventCode)
            self.attributes['__eventCode'] = "_COMPILED__"
        else:
            self.eventProgram = None
            self.eventCode = None
        
        # Resets
        if self.attributes.has_key('__resetCode'):
            if self.eventProgram == None:
                raise SvgMapException("Node %s\nhas __resetCode without __eventCode" % (str(self)))
            self.resetCode = self.attributes['__resetCode']
            self.resetProgram = self.compileCode(self.resetCode)
            self.attributes['__resetCode'] = "_COMPILED__"
        else:
            self.resetProgram = None
            self.resetCode = None
        
        # Preserve drag
        if self.attributes.has_key('__preserveDrag'):
            if self.eventProgram == None:
                raise SvgMapException("Node %s\nhas __preserveDrag without __eventCode" % (str(self)))
            self.preserveDrag = self.attributes['__preserveDrag'].strip().lower() == 'true'
        else:
            # default: inherit from groupParent
            if self.groupParent != None:
                self.preserveDrag = self.groupParent.preserveDrag
            else:
                self.preserveDrag = False   # ...or don't preserve if root
        
        self.resetAttributes = {}
        for k,v in self.attributes.iteritems():
            self.resetAttributes[k] = v # I would just do self.attributes.copy(), but self.attributes is actually not a normal dict
        
        # Custom references
        self.needs = {}
        for a,v in self.attributes.iteritems():
            if a == '__parentProperty':
                if self.parent == None or not self.parent.fillNeed(v,self):
                    raise SvgMapException("Node %s\nhas a __parentProperty that filled no requirements" % (str(self)))
            elif v.startswith("__"):
                if a == 'self' or a == 'event' or a == 'signals' or hasattr(self,a):
                    raise SvgMapException("Node %s defines a reserved custom attribute %s" % (str(self),a))
                self.needs[a] = v
        
        # Custom init code
        if self.attributes.has_key('__initCode'):
            self.initCode = self.attributes['__initCode']
            self.initProgram = self.compileCode(self.initCode)
            self.attributes['__initCode'] = "_COMPILED__"
            customNameSpace = {'self':self}
            exec self.initProgram in {},customNameSpace
        else:
            self.initProgram = None
            self.initCode = None
    
    # ****** TODO: make these private! ********
    
    def compileCode(self, code):
        if 'self.yieldEventToGroupParent' in code:
            self.callsGroupParent = True
        else:
            self.callsGroupParent = False
        code = code.split("\\n ")
        code = "\n".join(code)
        
        return compile(code,'<string>','exec')
    
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
                    raise SvgMapException("Two child nodes (\n%s\nand\n%s\n) attempted to fill the same attribute %s with __parentProperty: %s" % (str(obj),str(self.needs[a]),a,v))
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
    
    def yieldEventToGroupParent(self,event,signals={},isBase=False):
        if self.groupParent != None:
            return self.groupParent.handleEvent(event,signals,isBase)
        else:
            return signals
    
    def handleEvent(self,event,signals={},isBase=False):
        if self.eventProgram != None:
            if isBase:
                if self.preserveDrag and 'LeftButton' in event.buttons:
                    mutableSvgNode.lock = self
                else:
                    mutableSvgNode.lock = None
            
            if self.resetProgram != None:
                mutableSvgNode.active.add(self)
                mutableSvgNode.reset.add(self)
            
            if not signals.has_key('__SVG__DIRTY__'):
                oldDirtiness = True
            else:
                oldDirtiness = signals['__SVG__DIRTY__']
            
            signals['__SVG__DIRTY__'] = True
            self.handleCustomEvent(event,signals)
            
            if signals.get('__SVG__DIRTY__',True) == False and not oldDirtiness:  # Allow it to stay clean only if it came in clean and the custom code explicitly marked it as untouched
                signals['__SVG__DIRTY__'] = False
            else:
                signals['__SVG__DIRTY__'] = True
            
            return signals
        else:
            return self.yieldEventToGroupParent(event,signals,isBase)   # default behavior is to yield to any groupParent's event handler - this is overridden if a node defines the __eventCode attribute
    
    def handleCustomEvent(self,event,signals={'__SVG__DIRTY__':True}):
        customNameSpace = {'self':self,
                           'event':event,
                           'signals':signals}
        exec self.eventProgram in {},customNameSpace
        return customNameSpace['signals']
    
    def handleReset(self,event,signals={'__SVG__DIRTY__':True}):
        customNameSpace = {'self':self,
                           'event':event,
                           'signals':signals}
        exec self.resetProgram in {},customNameSpace
        return customNameSpace['signals']
    
    def getRect(self):
        id = self.attributes.get('id',None)
        temp = self.parent
        while id == None and temp != None:
            id = temp.attributes.get('id',None)
            temp = temp.parent
        return self.document.getBoundaries(id)
    
    # ****** TODO: these are my API... rename them? ******
    
    def yieldEvent(self, event, signals={}):
        return self.yieldEventToGroupParent(event, signals, False)
    
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
        for x in mutableSvgNode.queryObject(queryString):
            results.append(mutableSvgNode.nodeLookup[x])
        return results
    
    def localSearch(self, queryString):
        results = []
        for x in mutableSvgNode.queryObject(self.xmlElement).find(queryString):
            results.append(mutableSvgNode.nodeLookup[x])
        return results
    
    def parseTransforms(self, string):
        self.transforms = [1.0,0.0,0.0,1.0,0.0,0.0] # identity matrix
        for t in string.split():
            key,p,rightChunk = t.partition("(")
            values = rightChunk[:rightChunk.rfind(")")].split(",")
            if key == 'matrix':
                self.matrix(float(values[0]),float(values[1]),float(values[2]),float(values[3]),float(values[4]),float(values[5]),applyImmediately=False)
            elif key == 'translate':
                self.translate(float(values[0]),float(values[1]),applyImmediately=False)
            # TODO: add other transforms
    
    def applyTransforms(self):
        self.attributes['transform'] = 'matrix(%f,%f,%f,%f,%f,%f)' % (self.transforms[0],self.transforms[1],self.transforms[2],self.transforms[3],self.transforms[4],self.transforms[5])
    
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
    
    def drag(self, deltaX, deltaY, left, top, right, bottom):
        self.translate(deltaX,deltaY)
        self.document.forceFreeze()
        if not QRectF(left,top,right-left,bottom-top).contains(self.getRect()):
            self.translate(-deltaX,-deltaY)
    
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
        twin = deepcopy(self.xmlElement)
        newCloneNumber = self.cloneNumber + 1
        for node in twin.iter():
            if node.attrib.has_key('id'):
                if newCloneNumber == 1:
                    node.attrib['id'] += "_%i" % newCloneNumber
                else:
                    temp = twin.attrib['id']
                    node.attrib['id'] = temp[:temp.rfind("_")] + "_%i" % newCloneNumber
        
        self.xmlElement.getparent().append(twin)
        print 'added'
        return mutableSvgNode(self.document,twin,self.parent,self.groupParent,newCloneNumber)
    
    def setAttribute(self, att, value, force=True):
        if not self.attributes.has_key(att):
            success = self.setCSS(att,value,force=False)
        else:
            success = False
        
        if not success and force:
            self.attributes[att] = str(value)
            success = True
        
        if success:
            if att == 'transform':
                self.parseTransforms[self.attributes['transform']]
            elif att == "__eventCode":
                self.eventCode = self.attributes['__eventCode']
                self.eventProgram = self.compileCode(self.eventCode)
                self.attributes['__eventCode'] = "_COMPILED__"
            elif att == '__resetCode':
                self.resetCode = self.attributes['__resetCode']
                self.resetProgram = self.compileCode(self.resetCode)
                self.attributes['__resetCode'] = "_COMPILED__"
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
        if att == '__eventCode':
            return self.eventCode
        elif att == '__resetCode':
            return self.resetCode
        else:
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
    def __init__(self, path):
        self.queryObject = pq(filename=path)
        mutableSvgNode.queryObject = self.queryObject
        
        self.isFrozen = False
        self.freeze()
        
        self.root = self.buildTree(self.queryObject.root.getroot(),parent=None,groupParent=None)
        self.root.verify()
        
        self.lastTarget = None
    
    def buildTree(self, xmlObject,parent=None,groupParent=None):
        newNode = mutableSvgNode(self,xmlObject,parent,groupParent)
        for child in xmlObject.getchildren():
            if newNode.eventProgram != None:
                groupParent = newNode
            else:
                groupParent = newNode.groupParent
            newChild = self.buildTree(child, newNode, groupParent)
            newNode.addChild(newChild)
        return newNode
    
    def freeze(self):
        if self.isFrozen:
            return
        self.renderer = QSvgRenderer(QByteArray(str(self.queryObject)))
        self.isFrozen = True
    
    def forceFreeze(self):
        self.isFrozen = False
        self.freeze()
    
    def thaw(self):
        self.isFrozen = False
    
    def handleFrame(self, userState, node=None):
        if node == None:
            if mutableSvgNode.lock != None:   # We're in dragging mode - we don't care what's moused over, just fire the event on the base element that was active before
                results = mutableSvgNode.lock.handleEvent(userState,{'__SVG__DIRTY__':True},isBase=True)
                # By definition, only an element and the group parents it calls will be in the active set; we only need to fire the event on
                # the base event receiver, and everything else will be handled.
            else:
                mutableSvgNode.active = set()   # empty out the active set... afterward, anything that's in reset that isn't in active will need to have reset called
                results = self.handleFrame(userState, self.root)
                
                if results == None:
                    results = {'__SVG__DIRTY__':False}    # If at the highest level we were still out of bounds, there's no signal,
                                                          # and things got dirty only if there's a reset; we'll find out if that
                                                          # happened next
                # Run any resets...
                needReset = mutableSvgNode.reset.difference(mutableSvgNode.active)
                for n in needReset:
                    temp = results.get('__SVG__DIRTY__',True)
                    results['__SVG__DIRTY__'] = True
                    n.handleReset(userState,results)
                    mutableSvgNode.reset.discard(n)
                    results['__SVG__DIRTY__'] = results['__SVG__DIRTY__'] or temp  # again, we want to let it be clean only if every call explicitly marks it clean
            
            # Okay, we're finally done - we need to check if something dirtified the SVG:
            if results.get('__SVG__DIRTY__',True):
                self.thaw()
            # Clean up our little internal flag
            if results.has_key('__SVG__DIRTY__'):
                del results['__SVG__DIRTY__']
            return results
        else:
            id = node.attributes.get('id',None)
            if id != None:
                inBounds = self.eventInElement(userState,id)
            else:
                inBounds = True # If there's no id, we'll have to check the children...
                                # If there's no id there, we'll have to assume the frontmost, deepest child is in bounds.
                                # This isn't ideal, but the SVG is screwed up so this is the best we can do
            
            results = None
            
            if inBounds:
                for child in reversed(node.children):   # DFS, using the frontmost elements first
                    results = self.handleFrame(userState, child)
                    if results != None:
                        break
                
                if results == None:# Okay, no child gave me answers... so I'm the base node that gets the event
                    results = node.handleEvent(userState,signals={'__SVG__DIRTY__':False},isBase=True) # we'll start by assuming it's clean; provided no custom code touches the appearance, this will come back intact
                
                return results
            else:
                # We're out of bounds; let our caller know we couldn't find anything in range
                return None
    
    def getBoundaries(self, id=None):
        if id == None:
            id = self.root.attributes['id']
        b = self.renderer.boundsOnElement(id)
        if self.renderer.elementExists(id):
            b = self.renderer.matrixForElement(id).mapRect(b)
        return b
    
    def eventInElement(self, event, id):
        self.freeze()
        if self.renderer.elementExists(id):
            return self.getBoundaries(id).contains(event.x,event.y)
        else:
            return True # If we have an element with no id or that's un-renderable, we have to assume that we're in bounds
    
    def render(self, painter, queryString=None):
        self.freeze()
        if queryString == None:
            self.renderer.render(painter)
        else:
            id = self.queryObject(queryString).attr('id')
            if id == None:
                self.renderer.render(painter)
            else:
                self.renderer.render(painter,id,self.getBoundaries(id))
    
    
    
    
    
    
    