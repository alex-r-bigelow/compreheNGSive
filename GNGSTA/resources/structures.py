import math, sys
#sys.setrecursionlimit(10000)
RECURSION_ESTIMATE = sys.getrecursionlimit() - 500  # a generous estimate about the stack frames a program will already be using before calling our structures...
                                                    # this will sort of guard against exceeding the maximum recursion depth. If this is still broken, it's likely
                                                    # only slightly broken by an already-complex program that they might need to boost the recursion limit on its own
                                                    # anyway; otherwise the programmer's doing something stupid like creating these recursive structures inside
                                                    # some kind of recursive algorithm... if that's the case, he deserves the crash

class recursiveDict(dict):
    def __init__(self, generateFrom=None):
        """
        Creates a recursiveDict; generateFrom must be iterable if not None, and the resulting recursiveDict will have
        an entry (the first element of generateFrom) pointing to a recursiveDict with an entry (the second element) pointing
        to a recursiveDict with an entry...
        The second to last element will reference the final element directly (the final element will not be embedded in a
        recursiveDict)
        """
        super(recursiveDict, self).__init__()
        if generateFrom != None:
            columns = []
            for i in generateFrom:
                columns.append(i)
            if len(columns) == 0:
                return
            elif len(columns) == 1:
                self[columns[0]] = None
            elif len(columns) == 2:
                self[columns[0]] = columns[1]
            else:
                self[columns[0]] = recursiveDict.generateFromList(columns[1:])
        
    def __missing__(self, key):
        returnValue = recursiveDict()
        self[key] = returnValue
        return returnValue
    
    @staticmethod
    def generateFromList(columns):
        temp = recursiveDict()
        if len(columns) == 0:
            return None
        elif len(columns) == 1:
            return columns[0]
        elif len(columns) == 2:
            temp[columns[0]] = columns[1]
            return temp
        else:
            temp[columns[0]] = recursiveDict.generateFromList(columns[1:])
            return temp

class countingDict(dict):
    def __missing__(self, key):
        returnValue = 0
        self[key] = returnValue
        return returnValue

class TwoNode:
    def __init__(self, identifier, value):
        self.id = identifier
        self.population = 1
        
        self.value = value
        
        self.parent = None
        self.low = value
        self.lowerChildren = None
        self.high = value
        self.higherChildren = None
        
        self.cacheNext = None
        self.cachePrevious = None
        
        self.deepChildPool = set() # resort to a presorted list of children when the recursion depth is exceeded
    
    def addChild(self, newNode, depth=0):
        self.population += newNode.population
        
        if depth > RECURSION_ESTIMATE:
            '''if len(self.deepChildPool) == 0:
                self.deepChildPool.append(newNode)
            else:
                target = len(self.deepChildPool)
                for i,n in enumerate(self.deepChildPool):
                    if n.value > newNode.value:
                        target = i
                        break
                self.deepChildPool.insert(target, newNode)'''
            self.deepChildPool.add(newNode)
            return
        
        if newNode.value < self.value:
            if newNode.value < self.low:
                self.low = newNode.value
            if self.lowerChildren == None:
                self.lowerChildren = newNode
            else:
                self.lowerChildren.addChild(newNode, depth+1)
        else:   # lump greater than OR EQUAL in the same direction
            if newNode.value > self.high:
                self.high = newNode.value
            if self.higherChildren == None:
                self.higherChildren = newNode
            else:
                self.higherChildren.addChild(newNode, depth+1)
    
    def getSubselectionNoCheck(self):
        results = set()
        results.add(self.id)
        for n in self.deepChildPool:
            results.add(n.id)
        
        if self.lowerChildren != None:
            results.update(self.lowerChildren.getSubselectionNoCheck())
        if self.higherChildren != None:
            results.update(self.higherChildren.getSubselectionNoCheck())
        return results
    
    def getSubselection(self, low, high):
        if self.high < low or self.low > high:
            return set()
        if low <= self.low and high >= self.high:   # I am strictly within the range; can add myself and everything below me without checking anymore
            return self.getSubselectionNoCheck()
        results = set()
        if self.value >= low and self.value <= high:
            results.add(self.id)
        for n in self.deepChildPool:
            if n.value >= low and n.value <= high:
                results.add(n.id)
        if self.lowerChildren != None:
            results.update(self.lowerChildren.getSubselection(low,high))
        if self.higherChildren != None:
            results.update(self.higherChildren.getSubselection(low,high))
        return results
    
    def countPopulation(self, low, high):   # if all we care about is the size of the set, we can do it a little faster
        if self.high < low or self.low > high:
            return 0
        if low <= self.low and high >= self.high:
            return self.population
        count = 0
        if self.value >= low and self.value <= high:
            count += 1
        for n in self.deepChildPool:
            if n.value >= low and n.value <= high:
                count += 1
        if self.lowerChildren != None:
            count += self.lowerChildren.countPopulation(low,high)
        if self.higherChildren != None:
            count += self.higherChildren.countPopulation(low,high)
        return count
        
    
    '''def getNextNode(self):
        if self.higherChildren != None:
            return self.higherChildren
        elif self.cacheNext != None:    # this caching behavior will always work provided you can't remove nodes
            return self.cacheNext
        else:
            temp = self.parent
            while (temp != None and temp.value < self.value):
                temp = temp.parent
            self.cacheNext = None
            return temp
    
    def getPreviousNode(self):
        if self.lowerChildren != None:
            return self.lowerChildren
        elif self.cachePrevious != None:    # this caching behavior will always work provided you can't remove nodes
            return self.cachePrevious
        else:
            temp = self.parent
            while (temp != None and temp.value > self.value):
                temp = temp.parent
            self.cachePrevious = temp
            return temp'''

'''class TwoIterator:
    def __init__(self, start, stop):
        self.start = start
        self.stop = stop
        
        self.rootNode = None
        self.firstNode = None
        self.lastNode = None
        self.currentNode = None
        self.populationEstimate = 0
    
    def __iter__(self):
        return self
    
    def next(self):
        if self.currentNode == None:
            raise StopIteration
        nextNode = self.currentNode.getNextNode()
        if nextNode == None or nextNode.value > self.stop:
            raise StopIteration
        else:
            self.currentNode = nextNode
            return (self.currentNode.value,self.currentNode.id)'''
    
class TwoTree:
    def __init__(self, fromList=None):
        '''
        If a list is provided, each item should be an (id,value) tuple
        '''
        self.root = None
        self.cacheNode = self.root
        self.maskedIDs = set()
        self.undefinedIDs = set()
        self.missingIDs = set()
        
        if fromList != None and len(fromList) > 0:
            median = len(fromList)/2
            self.add(fromList[median][0],fromList[median][1])
            self.addListChunk(fromList[:median])
            self.addListChunk(fromList[median+1:])
    
    def __len__(self):
        if self.root == None:
            return 0
        else:
            return self.root.population
        
    def add(self, identifier, value):
        # nan indicates that a variant has been masked because of how the minor allele was defined
        # inf indicates values that are undefined
        # None indicates values that are missing
        if value == None:
            self.missingIDs.add(identifier)
        elif math.isinf(value):
            self.undefinedIDs.add(identifier)
        elif math.isnan(value):
            self.maskedIDs.add(identifier)
        else:
            newNode = TwoNode(identifier, value)
            if self.root == None:
                self.root = newNode
            else:
                self.root.addChild(newNode)
    
    def addListChunk(self, data):
        if len(data) == 0:
            return
        median = len(data)/2
        self.add(data[median][0],data[median][1])
        self.addListChunk(data[:median])
        self.addListChunk(data[median+1:])
    
    def select(self, low=None, high=None, includeMasked=False, includeUndefined=False, includeMissing=False):
        results = set()
        if low != None and high != None:
            if low > high:
                temp = high
                high = low
                low = temp
            
            if self.root != None:
                results.update(self.root.getSubselection(low, high))
        
        if includeMasked:
            results.update(self.maskedIDs)
        if includeUndefined:
            results.update(self.undefinedIDs)
        if includeMissing:
            results.update(self.missingIDs)
        
        return results
    
    def countPopulation(self, low=None, high=None, includeMasked=False, includeUndefined=False, includeMissing=False):
        count = 0
        if low != None and high != None:
            if low > high:
                temp = high
                high = low
                low = temp
            
            if self.root != None:
                count += self.root.countPopulation(low, high)
        
        if includeMasked:
            count += len(self.maskedIDs)
        if includeUndefined:
            count += len(self.undefinedIDs)
        if includeMissing:
            count += len(self.missingIDs)
        
        return count
    
    '''def select(self, low, high):
        results = TwoIterator(low,high)
        if low > high:
            temp = high
            high = low
            low = temp
        
        # To improve performance, we cache the pointer that we used for the last selection or estimation; if we
        # query again in the same neighborhood, we'll want to start someplace similar
        if (self.cacheNode == None):
            self.cacheNode = self.root
        
        # Find the leftmost node in range...
        while (self.cacheNode != None and self.cacheNode.value < low):
            self.cacheNode = self.cacheNode.getNextNode()   # move right if we need to
        if self.cacheNode == None:
            return results
        
        while (True):
            temp = self.cacheNode.getPreviousNode()    # move left as much as we need to
            if temp == None or temp.value < low:
                break
            self.cacheNode = temp
        
        # if our leftmost point doesn't fit the high bound, we have an empty set
        if self.cacheNode.value > high:
            return results
        
        # okay, our selection isn't empty
        results.firstNode = self.cacheNode
        
        # iterate right, keeping track of populations. The highest pop is the root of our subtree
        results.rootNode = self.cacheNode
        highestPop = self.cacheNode.population
        while (True):
            temp = self.cacheNode.getNextNode()
            if temp == None or temp.value > high:
                break
            self.cacheNode = temp
            if self.cacheNode.population > highestPop:
                results.rootNode = self.cacheNode
                highestPop = self.cacheNode.population
        
        # we've made it to the rightmost point
        results.lastNode = self.cacheNode
        
        # Here's our starting population estimate, now shave off stuff that isn't actually in range
        results.populationEstimate = results.rootNode.population
        
        # Like a rental VHS, be classy and rewind to the beginning before we return it - we need to start by pointing to the node BEFORE the first node
        results.currentNode = results.firstNode.getPreviousNode()
        if results.currentNode == None:
            dummy = TwoNode(None,None)
            dummy.higherChildren = results.firstNode
            results.currentNode = dummy
        
        # Start our cache on the left as well
        self.cacheNode = results.firstNode
        return results
    
    def __iter__(self):
        # TODO: this is kind of inefficient... if I find myself iterating over the whole tree a lot, I should improve this
        return self.select(self.root.low,self.root.high)'''


class FourNode:
    def __init__(self, identifier, x,y):
        self.id = identifier
        self.population = 1
        
        self.x = x
        self.y = y
        
        self.parent = None
        
        self.lowerChildren = None
        self.higherXChildren = None
        self.higherYChildren = None
        self.higherChildren = None
        
        self.lowX = x
        self.highX = x
        self.lowY = y
        self.highY = y
        
        self.deepChildPool = set() # resort to unsorted set of children when the recursion depth is exceeded
    
    def addChild(self, newNode, depth=0):
        self.population += newNode.population
        
        if depth > RECURSION_ESTIMATE:
            self.deepChildPool.add(newNode)
            return
        
        if newNode.x < self.x:
            if newNode.x < self.lowX:
                self.lowX = newNode.x
            
            if newNode.y < self.y:
                if newNode.y < self.lowY:
                    self.lowY = newNode.y
                
                if self.lowerChildren == None:
                    self.lowerChildren = newNode
                else:
                    self.lowerChildren.addChild(newNode,depth+1)
            else:   # lump greater than OR EQUAL in the same direction
                if newNode.y > self.highY:
                    self.highY = newNode.y
                
                if self.higherYChildren == None:
                    self.higherYChildren = newNode
                else:
                    self.higherYChildren.addChild(newNode,depth+1)
        else:   # lump greater than OR EQUAL in the same direction
            if newNode.x > self.highX:
                self.highX = newNode.x
            
            if newNode.y < self.y:
                if newNode.y < self.lowY:
                    self.lowY = newNode.y
                
                if self.higherXChildren == None:
                    self.higherXChildren = newNode
                else:
                    self.higherXChildren.addChild(newNode,depth+1)
            else:   # lump greater than OR EQUAL in the same direction
                if newNode.y > self.highY:
                    self.highY = newNode.y
                
                if self.higherChildren == None:
                    self.higherChildren = newNode
                else:
                    self.higherChildren.addChild(newNode,depth+1)
    
    def getSubselectionNoCheck(self):
        results = set()
        results.add(self.id)
        for n in self.deepChildPool:
            results.add(n.id)
        if self.lowerChildren != None:
            results.update(self.lowerChildren.getSubselectionNoCheck())
        if self.higherXChildren != None:
            results.update(self.higherXChildren.getSubselectionNoCheck())
        if self.higherYChildren != None:
            results.update(self.higherYChildren.getSubselectionNoCheck())
        if self.higherChildren != None:
            results.update(self.higherChildren.getSubselectionNoCheck())
        return results
    
    def getSubselection(self, lowX, lowY, highX, highY):
        if self.highX < lowX or self.lowX > highX or self.highY < lowY or self.lowY > highY:
            return set()
        if lowX <= self.lowX and highX >= self.highX and lowY <= self.lowY and highY >= self.highY:   # I am strictly within the range; can add myself and everything below me without checking anymore
            return self.getSubselectionNoCheck()
        results = set()
        if self.x >= lowX and self.x <= highX and self.y >= lowY and self.y <= highY:
            results.add(self.id)
        for n in self.deepChildPool:
            if n.x >= lowX and n.x <= highX and n.y >= lowY and n.y <= highY:
                results.add(n.id)
        if self.lowerChildren != None:
            results.update(self.lowerChildren.getSubselection(lowX,lowY,highX,highY))
        if self.higherXChildren != None:
            results.update(self.higherXChildren.getSubselection(lowX,lowY,highX,highY))
        if self.higherYChildren != None:
            results.update(self.higherYChildren.getSubselection(lowX,lowY,highX,highY))
        if self.higherChildren != None:
            results.update(self.higherChildren.getSubselection(lowX,lowY,highX,highY))
        return results
    
    def countPopulation(self, lowX, lowY, highX, highY):   # if all we care about is the size of the set, we can do it a little faster
        if self.highX < lowX or self.lowX > highX or self.highY < lowY or self.lowY > highY:
            return 0
        if lowX <= self.lowX and highX >= self.highX and lowY <= self.lowY and highY >= self.highY:   # I am strictly within the range; can add myself and everything below me without checking anymore
            return self.population
        count = 0
        if self.x >= lowX and self.x <= highX and self.y >= lowY and self.y <= highY:
            count += 1
        for n in self.deepChildPool:
            if n.x >= lowX and n.x <= highX and n.y >= lowY and n.y <= highY:
                count += 1
        if self.lowerChildren != None:
            count += self.lowerChildren.countPopulation(lowX,lowY,highX,highY)
        if self.higherXChildren != None:
            count += self.higherXChildren.countPopulation(lowX,lowY,highX,highY)
        if self.higherYChildren != None:
            count += self.higherYChildren.countPopulation(lowX,lowY,highX,highY)
        if self.higherChildren != None:
            count += self.higherChildren.countPopulation(lowX,lowY,highX,highY)
        return count
    
class FourTree:
    def __init__(self, fromList=None):
        '''
        If a list is provided, each item should be an (id,x,y) tuple
        '''
        self.root = None                    # points that are defined & unmasked in both dimensions
        self.cacheNode = None
        
        exceptionTypes = ["Value","Null","Masked","Missing"]
        exceptionTempList = []
        self.exceptionGroups = {}
        for t in exceptionTypes:
            exceptionTempList.append("x" + t)
        for x in exceptionTempList:
            for y in exceptionTypes:
                if x == "xValue":
                    if y == "Value":
                        continue    # if x and y have values, we want to store them in self.root
                    else:
                        self.exceptionGroups[x + "_y" + y] = TwoTree()  # x has a value but y doesn't
                else:
                    if y == "Value":
                        self.exceptionGroups[x + "_yValue"] = TwoTree() # y has a value but x doesn't
                    else:
                        self.exceptionGroups[x + "_y" + y] = set()  # neither have values... a set will do the job
        
        if fromList != None and len(fromList) > 0:
            median = len(fromList)/2
            self.add(fromList[median][0],fromList[median][1],fromList[median][2])
            self.addListChunk(fromList[:median])
            self.addListChunk(fromList[median+1:])
    
    def __len__(self):
        if self.root == None:
            return 0
        else:
            return self.root.population
        
    def add(self, identifier, x, y):
        # nan indicates that a variant has been masked because of how the minor allele was defined
        # inf indicates values that are undefined
        # None indicates values that are missing
        
        xIndex = None
        if x == None:
            xIndex = "xMissing"
        elif math.isnan(x):
            xIndex = "xMasked"
        elif math.isinf(x):
            xIndex = "xNull"
        
        yIndex = None
        if y == None:
            yIndex = "yMissing"
        elif math.isnan(y):
            yIndex = "yMasked"
        elif math.isinf(y):
            yIndex = "yNull"
        
        if xIndex == None and yIndex == None:
            newNode = FourNode(identifier,x,y)
            if self.root == None:
                self.root = newNode
            else:
                self.root.addChild(newNode)
        elif xIndex == None:
            self.exceptionGroups["xValue_"+yIndex].add(identifier,x)
        elif yIndex == None:
            self.exceptionGroups[xIndex+"_yValue"].add(identifier,y)
        else:
            self.exceptionGroups[xIndex+"_"+yIndex].add(identifier)
    
    def addListChunk(self, data):
        if len(data) == 0:
            return
        median = len(data)/2
        self.add(data[median][0],data[median][1],data[median][2])
        self.addListChunk(data[:median])
        self.addListChunk(data[median+1:])
    
    def select(self, lowX=None, lowY=None, highX=None, highY=None, includeMaskedX=False, includeMaskedY=False, includeUndefinedX=False, includeUndefinedY=False, includeMissingX=False, includeMissingY=False):
        results = set()
        if lowX != None and lowY != None and highX != None and highY != None:
            if lowX > highX:
                temp = highX
                highX = lowX
                lowX = temp
            if lowY > highY:
                temp = highY
                highY = lowY
                lowY = temp
            
            if self.root != None:
                results.update(self.root.getSubselection(lowX, lowY, highX, highY))
        
        xExceptionIndices = ["xValues"]
        yExceptionIndices = ["yValues"]
        
        if includeMaskedX:
            xExceptionIndices.append("xMasked")
        if includeUndefinedX:
            xExceptionIndices.append("xNull")
        if includeMissingX:
            xExceptionIndices.append("xMissing")
        
        if includeMaskedY:
            yExceptionIndices.append("yMasked")
        if includeUndefinedY:
            yExceptionIndices.append("yNull")
        if includeMissingY:
            yExceptionIndices.append("yMissing")
        
        for x in xExceptionIndices:
            for y in yExceptionIndices:
                if x == "xValues":
                    if y == "yValues":
                        continue    # both have values - this will come from earlier selection from self.root
                    elif lowX != None and highX != None:
                        results.update(self.exceptionGroups["xValues_"+y].select(lowX,highX))
                else:
                    if y == "yValues":
                        if lowY != None and highY != None:
                            results.update(self.exceptionGroups[x+"_yValues"].select(lowY,highY))
                    else:
                        results.update(self.exceptionGroups[x+"_"+y])
        
        return results
    
    def countPopulation(self, lowX=None, lowY=None, highX=None, highY=None, includeMasked=False, includeUndefined=False, includeMissing=False):
        count = 0
        if lowX != None and lowY != None and highX != None and highY != None:
            if lowX > highX:
                temp = highX
                highX = lowX
                lowX = temp
            if lowY > highY:
                temp = highY
                highY = lowY
                lowY = temp
            
            if self.root != None:
                count += self.root.countPopulation(lowX, lowY, highX, highY)
        
        if not includeMasked and not includeUndefined and not includeMissing:   # this is probably the most common scenario... save some time
            return count
        
        xExceptionIndices = ["xValues"]
        yExceptionIndices = ["yValues"]
        
        if includeMaskedX:
            xExceptionIndices.append("xMasked")
        if includeUndefinedX:
            xExceptionIndices.append("xNull")
        if includeMissingX:
            xExceptionIndices.append("xMissing")
        
        if includeMaskedY:
            yExceptionIndices.append("yMasked")
        if includeUndefinedY:
            yExceptionIndices.append("yNull")
        if includeMissingY:
            yExceptionIndices.append("yMissing")
        
        for x in xExceptionIndices:
            for y in yExceptionIndices:
                if x == "xValues":
                    if y == "yValues":
                        continue    # both have values - this will come from earlier selection from self.root
                    elif lowX != None and highX != None:
                        count += self.exceptionGroups["xValues_"+y].countPopulation(lowX,highX)
                else:
                    if y == "yValues":
                        if lowY != None and highY != None:
                            count += self.exceptionGroups[x+"_yValues"].countPopulation(lowY,highY)
                    else:
                        count += len(self.exceptionGroups[x+"_"+y])
        
        return count