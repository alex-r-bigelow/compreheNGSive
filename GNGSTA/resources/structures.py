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

class RangeNode:
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
    
    def addChild(self, newNode):
        self.population += newNode.population
        
        if newNode.value < self.value:
            if newNode.value < self.low:
                self.low = newNode.value
            if self.lowerChildren == None:
                self.lowerChildren = newNode
            else:
                self.lowerChildren.addChild(newNode)
        else:   # lump greater than OR EQUAL in the same direction
            if newNode.value > self.high:
                self.high = newNode.value
            if self.higherChildren == None:
                self.higherChildren = newNode
            else:
                self.higherChildren.addChild(newNode)
    
    def getNextNode(self):
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
            return temp

class RangeIterator:
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
            return (self.currentNode.value,self.currentNode.id)
    
class RangeTree:
    def __init__(self, fromList=None):
        '''
        If a list is provided, each item should be an (id,value) tuple
        '''
        self.root = None
        self.cacheNode = None
        self.undefinedIDs = set()
        
        if fromList != None and len(fromList) > 0:
            median = len(fromList)/2
            self.root = fromList[median]
            self.addListChunk(fromList[:median])
            self.addListChunk(fromList[median+1:])
    
    def __len__(self):
        if self.root == None:
            return 0
        else:
            return self.root.population
        
    def add(self, identifier, value):
        if value == None:
            self.undefinedIDs.add(identifier)
        else:
            newNode = RangeNode(identifier, value)
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
    
    def select(self, low, high):
        results = RangeIterator(low,high)
        if low > high:
            print "WARNING: Attempted selection on RangeTree with low > high!"
            return results
        
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
            dummy = RangeNode(None,None)
            dummy.higherChildren = results.firstNode
            results.currentNode = dummy
        
        # Start our cache on the left as well
        self.cacheNode = results.firstNode
        return results
    
    def __iter__(self):
        # TODO: this is kind of inefficient... if I find myself iterating over the whole tree a lot, I should improve this
        return self.select(self.root.low,self.root.high)
