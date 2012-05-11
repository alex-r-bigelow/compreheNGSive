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
        self.idsWithValue = set(identifier)
        self.value = value
        
        self.population = 1
        self.parent = None
        self.low = value
        self.lowerChildren = None
        self.high = value
        self.higherChildren = None
    
    def addChild(self, newNode):
        if newNode.value < self.value:
            if newNode.value < self.low:
                self.low = newNode.value
            if self.lowerChildren == None:
                self.lowerChildren = newNode
            else:
                self.lowerChildren.addChild(newNode)
        elif newNode.value > self.value:
            if newNode.value > self.high:
                self.high = newNode.value
            if self.higherChildren == None:
                self.higherChildren = newNode
            else:
                self.higherChildren.addChild(newNode)
        else:
            self.idsWithValue += newNode.idsWithValue
        self.population += len(newNode.idsWithValue)
    
    def getNextNode(self):
        if self.higherChildren != None:
            return self.higherChildren
        elif self.parent != None and self.parent.value > self.value:
            return self.parent
        else:
            return None
    
    def getPreviousNode(self):
        if self.lowerChildren != None:
            return self.lowerChildren
        elif self.parent != None and self.parent.value < self.value:
            return self.parent
        else:
            return None

class RangeIterator:
    def __init__(self, start, stop):
        self.start = start
        self.stop = stop
        
        self.rootNode = None
        self.firstNode = None
        self.lastNode = None
        self.currentNode = None
        self.population = 0
    
    def __iter__(self):
        return self
    
    def __len__(self):
        return self.population
    
    def next(self):
        if self.currentNode == None:
            return None
        nextNode = self.currentNode.getNextNode()
        if nextNode == None || nextNode.value > self.stop:
            raise StopIteration
            return None
        else:
            self.currentNode = nextNode
            return self.currentNode.value
    
    def previous(self):
        if self.currentNode == None:
            return None
        previousNode = self.currentNode.getPreviousNode()
        if previousNode == None || previousNode.value < self.stop:
            raise StopIteration
            return None
        else:
            self.currentNode = previousNode
            return self.currentNode.value

class RangeTree:
    def __init__(self):
        self.root = None
        self.cacheNode = None
        self.undefinedIDs = Set()
    
    def __len__(self):
        if self.root == None:
            return 0
        else:
            return self.root.population
        
    def addPoint(self, identifier, value):
        if (value == None):
            self.undefinedIDs.add(identifier)
        else:
            newNode = RangeNode(identifier, value)
            if self.root == None:
                self.root = newNode
            else:
                self.root.addChild(newNode)
    
    def estimatePopulation(self, min, max):
        if min > max:
            print "WARNING: Attempted estimation on RangeTree with min > max!"
            return 0
        
        # To improve performance, we cache the root of the last selection or estimation; we'll probably
        # be in this neighborhood again
        temp = None
        if (self.cacheNode == None):
            temp = self.root
        else:
            temp = self.cacheNode
        
        # First just find a node in range
        while (temp != None and temp.value > max):
            temp = temp.getPreviousNode()   # move left if we need to
        while (temp != None and temp.value < min):
            temp = temp.getNextNode()   # move right if we need to
        
        # If temp is null, we know it's zero, otherwise use temp's population as our guess;
        # this estimate will always be exact or above the exact population
        if temp == None:
            return 0
        else:
            self.cacheNode = temp
            return temp.population
    
    def select(self, min, max):
        results = RangeIterator(min,max)
        if min > max:
            print "WARNING: Attempted selection on RangeTree with min > max!"
            return results
        
        # To improve performance, we cache the root of the last selection or estimation; we'll probably
        # be in this neighborhood again
        temp = None
        if (self.cacheNode == None):
            temp = self.root
        else:
            temp = self.cacheNode
        
        # First just find a node in range
        while (temp != None and temp.value > max):
            temp = temp.getPreviousNode()   # move left if we need to
        while (temp != None and temp.value < min):
            temp = temp.getNextNode()   # move right if we need to
        
        # If temp is null, we know it's zero, otherwise use temp's population as our guess;
        # this estimate will always be exact or above the exact population
        if temp == None:
            return 0
        else:
            self.cacheNode = temp
            return temp.population






