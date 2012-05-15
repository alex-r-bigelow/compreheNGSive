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
    def __init__(self, identifier, values, splitDimension):
        self.idsWithValue = set()
        self.idsWithValue.add(identifier)
        self.population = 1
        self.splitDimension = splitDimension
        self.numDimensions = len(values)
        
        self.values = values
        
        self.parent = None
        self.low = list(values)
        self.lowerChildren = None
        self.high = list(values)
        self.higherChildren = None
    
    def addChild(self, newNode):
        # TODO: update for multidimensionality
        if newNode.value < self.value:
            if newNode.value < self.low:
                self.low = newNode.value
            if self.lowerChildren == None:
                self.lowerChildren = newNode
            else:
                self.lowerChildren.addChild(newNode)
            self.population += newNode.population
        elif newNode.value > self.value:
            if newNode.value > self.high:
                self.high = newNode.value
            if self.higherChildren == None:
                self.higherChildren = newNode
            else:
                self.higherChildren.addChild(newNode)
            self.population += newNode.population
        else:
            myIds = len(self.idsWithValue)
            newNodesIds = len(newNode.idsWithValue)
            self.idsWithValue = self.idsWithValue.union(newNode.idsWithValue)
            overlap = len(self.idsWithValue) - (myIds + newNodesIds)
            self.population += newNode.population - overlap
    
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
            raise StopIteration
        nextNode = self.currentNode.getNextNode()
        if nextNode == None or nextNode.value > self.stop:
            raise StopIteration
        else:
            self.currentNode = nextNode
            return self.currentNode.value
    
class RangeTree:
    def __init__(self):
        self.root = None
        self.cacheNode = None
        self.undefinedIDs = set()
        self.min = None
        self.max = None
    
    def __len__(self):
        if self.root == None:
            return 0
        else:
            return self.root.population
        
    def add(self, identifier, value):
        if value == None:
            self.undefinedIDs.add(identifier)
        else:
            if self.min == None or value < min:
                self.min = value
            if self.max == None or value > max:
                self.max = value
            
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
        
        # Now were either in range, or we can return an empty set
        if temp == None:
            return results
        
        results.rootNode = temp
        self.cacheNode = temp
        results.population = temp.population    # Here's our starting population estimate, now shave off stuff that isn't actually in range
        
        while temp.higherChildren != None:
            if temp.higherChildren.value > max:
                results.population -= temp.higherChildren.population
                break
            else:
                temp = temp.higherChildren
        results.lastNode = temp     # oh, and by the way, we just found the last node
        temp = results.rootNode
        while temp.lowerChildren != None:
            if temp.lowerChildren.value < min:
                results.population -= temp.lowerChildren.population
                break
            else:
                temp = temp.lowerChildren
        results.firstNode = temp     # oh, and by the way, we just found the first node
        
        # Like a rental VHS, be classy and rewind to the beginning before we return it
        results.currentNode = results.firstNode
        return results
    
    def __iter__(self):
        # TODO: this is kind of inefficient... if I find myself iterating over the whole tree a lot, I should improve this
        return self.select(self.min,self.max)

class KdNode:
    def __init__(self,values,splitDimension):
        self.population = 1
        self.values = values
        self.splitDimension = splitDimension
        
        self.parent = None
        self.lows = list(values)    # clone...
        self.lowerChildren = None
        self.highs = list(values)   # clone...
        self.higherChildren = None
        


