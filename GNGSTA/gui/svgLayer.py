import inspect
import sys
from pyquery import PyQuery as pq
from scour.scour import scourString
from PySide.QtCore import QByteArray
from PySide.QtSvg import QSvgRenderer

class functionHolder:
    def __init__(self, owner, name, superFunc, setsDirty, requiresClean):
        self.owner = owner
        self.name = name
        self.superFunc = superFunc
        self.setsDirty = setsDirty
        self.requiresClean = requiresClean
    
    def doWork(self, *args):
        if self.requiresClean:
            if self.owner.dirty:
                self.owner.clean()
                
        if self.setsDirty:
            self.owner.dirty = True
        
        return self.superFunc(*args)
        '''
        TODO: getting a subselection will return a naked PyQuery instance that won't support rendering, etc
        '''
    
class mutableSvgRenderer:
    def __init__(self, path):
        self.xmlObject = pq(filename=path)
        self.clean()
        
        # give ourselves any methods that either object has...
        # this is an ugly way of doing inheritance, but there are way too many
        # functions to override manually
        
        # use these sets to enforce which methods to use
        ignoreMethods = set(["__init__"])
        
        pyqueryDirty = set(["__add__"])
        pyqueryNeutral = set(["__str__","__call__"])
        pyqueryClean = set()
        
        qsvgDirty = set()
        qsvgNeutral = set()
        qsvgClean = set()
        
        # These sets are for internal use
        
        overlapChecker = set()
        pyqueryIgnoreMethods = ignoreMethods.union(qsvgDirty).union(qsvgNeutral).union(qsvgClean)
        qsvgIgnoreMethods = ignoreMethods.union(pyqueryDirty).union(pyqueryNeutral).union(pyqueryClean)
        
        for name,superFunc in inspect.getmembers(self.xmlObject, inspect.ismethod):
            if name in pyqueryIgnoreMethods:
                continue
            newFunction = functionHolder(self,name,superFunc,name in pyqueryDirty,name in pyqueryClean)
            overlapChecker.add(name)
            setattr(self,name,newFunction.doWork)
        
        for name,superFunc in inspect.getmembers(self.svgObject, inspect.ismethod):
            if name in qsvgIgnoreMethods:
                continue
            newFunction = functionHolder(self,name,superFunc,name in qsvgDirty,name in qsvgClean)
            if name in overlapChecker:
                print "PyQuery and QSvgRenderer have two methods of the same name (%s)!" % name
                sys.exit(1)
            overlapChecker.add(name)
            setattr(self,name,newFunction.doWork)
    
    def clean(self):
        # remove any useless cruft, flatten transformations
        scrubbedXml = scourString(str(self.xmlObject),).encode("UTF-8")
        
        # give our xml object and svg renderer the new xml
        self.xmlObject = pq(scrubbedXml)
        self.svgObject = QSvgRenderer(QByteArray(scrubbedXml))
        
        self.dirty = False