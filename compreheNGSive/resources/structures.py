from blist import sortedlist
from durus.persistent import Persistent
from durus.persistent_dict import PersistentDict
from durus.persistent_set import PersistentSet
from resources.duplicatebtree import BTree
import math, sys

class twinDict(dict):
    def __init__(self):
        super(twinDict, self).__init__()
        self.twins = set()
    
    def __setitem__(self, key, value):
        super(twinDict, self).__setitem__(key,value)
        for c in self.twins:
            if not c.has_key(key):
                c[key] = value
            else:
                assert c[key] == value
    
    def addTwin(self, c):
        self.twins.add(c)

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

class rangeDict:
    '''
    A structure that behaves similarly to a dict, but allows storing multiple values at single keys, and selecting ranges of keys
    via slicing. As such, much asymptotic complexity is different (this uses essentially a priority queue as a backend), and 
    behavior is subtly different from a true dict; see method descriptions for differences. One really big difference is the
    classic len(function) - in python, slicing normally uses this function to wrap negative indices. In this case, negative
    indices should be preserved, so calling len() on a rangeDict will ALWAYS return zero. To get the length, use the rangeDict.len()
    function
    '''
    class alwaysSmaller:
        def __cmp__(self, other):
            return -1
        def __lt__(self, other):
            return True
        def __le__(self, other):
            return True
        def __eq__(self, other):
            return False
        def __ne__(self, other):
            return True
        def __ge__(self, other):
            return False
        def __gt__(self, other):
            return False
    class alwaysBigger:
        def __cmp__(self, other):
            return 1
        def __lt__(self, other):
            return False
        def __le__(self, other):
            return False
        def __eq__(self, other):
            return False
        def __ne__(self, other):
            return True
        def __ge__(self, other):
            return True
        def __gt__(self, other):
            return True
    class alwaysEqual:
        def __cmp__(self, other):
            return 0
        def __lt__(self, other):
            return False
        def __le__(self, other):
            return True
        def __eq__(self, other):
            return True
        def __ne__(self, other):
            return False
        def __ge__(self, other):
            return True
        def __gt__(self, other):
            return False
    
    MIN = alwaysSmaller()
    MAX = alwaysBigger()
    EQUAL = alwaysEqual()
    
    ORDINAL = 0
    CATEGORICAL = 1
    
    def __init__(self, fromDict=None):
        self.myList = sortedlist()
        if fromDict != None:
            for k,v in fromDict:
                self[k] = v
    
    def len(self):
        return len(self.myList)
    
    def __len__(self):
        '''
        This is actually broken; see class definition note (use rangeDict.len() instead)
        '''
        return 0
        #return len(self.myList)
    
    def __getitem__(self, key):
        '''
        Allows slicing non-integer ranges (e.g. myDict['a':'b'] will give all values with keys from 'a' to 'b', inclusive).
        NON-INTUITIVE BITS DIFFERENT FROM ELSEWHERE IN PYTHON:
        - Returned ranges are inclusive (normally slicing will exclude the upper bound)
        - ALL queries will return a sorted list (there is no additional cost for the sorting; it's a natural by-product of
          the structure); if there are no values in the range of keys, the list will be empty (normally an exception
          would be raised)
        Complexity is m log^2 n operations or m log n comparisons, where n is the size of the whole dict and m is the number
        of elements between 'a' and 'b'. Note that if step
        is supplied (e.g. myDict['a':'b':4]), the step must still be an integer (e.g. every fourth value from 'a' to 'b')
        '''
        if isinstance(key,slice):
            start = key.start
            stop = key.stop
            step = key.step
        else:
            start = key
            stop = key
            step = None
        return [v for k,v in self.myList[self.myList.bisect((start,rangeDict.MIN)):self.myList.bisect_right((stop,rangeDict.MAX)):step]]
    
    def count(self, low, high=None, step=1):
        if high == None:
            high = low
        return (self.myList.bisect((high,rangeDict.MAX)) - self.myList.bisect((low,rangeDict.MIN)))/step
    
    @staticmethod
    def intersection(*vargs):
            results = set()
            first = True
            for d,r,v in vargs:
                if first:
                    for l,h in r:
                        results.update(d[l:h])
                    for l in v:
                        results.update(d[l])
                    first = False
                else:
                    valids = set()
                    for l,h in r:
                        valids.update(d[l:h])
                    for l in v:
                        valids.update(d[l])
                    results.intersection_update(valids)
                if len(results) == 0:
                    return results
            return results

    @staticmethod
    def count2D(d1,r1,v1,d2,r2,v2,limit=None):
        results = set()
        for low,high in r1:
            results.update(d1[low:high])
        for value in v1:
            results.update(d1[value])
        if len(results) == 0:
            return 0
        results2 = set()
        for low,high in r2:
            results2.update(d2[low:high])
        for value in v2:
            results2.update(d2[value])
        return len(results.intersection(results2))
    
    def __setitem__(self, key, val):
        '''
        NOTE THAT ALL KEYS AND VALUES MUST BE UNIVERSALLY COMPARABLE; e.g. you may not add a set() object as a key or value.
        '''
        if isinstance(key,slice):
            errorstr = None
            if key.stop != None:
                errorstr = "[%s:%s" % (str(key.start),str(key.stop))
            if key.step != None:
                errorstr += ":%s" % str(key.step)
            if errorstr != None:
                raise KeyError('You can not slice when setting a value: %s] = %s' % (errorstr,str(val)))
            else:
                key = key.start
        try:
            self.myList.add((key,val))
        except TypeError:
            errorstr = str("keys and values must be universally comparable: %s, %s" % (str(key), str(val)))
            raise TypeError(errorstr)
    
    def __delitem__(self, key):
        '''
        SUBTLE DICT DIFFERENCE: If the key doesn't exist, a dict will raise an error, but rangeDict will quietly do nothing. Otherwise
        it deletes all values that have the supplied key
        '''
        while self.has_key(key):
            del self.myList[self.myList.index((key,rangeDict.EQUAL))]
    
    def has_key(self, key):
        try:
            self.myList.index((key,rangeDict.EQUAL))
            return True
        except ValueError:
            return False
    
    def __repr__(self):
        outstr = "{"
        for k,v in self.myList:
            outstr += str(k) + ":" + str(v) + ","
        return outstr[:-1] + "}"

class categoricalIndex(Persistent):
    def __init__(self, name, low, high, legalValues):
        self.name = name
        self.data = PersistentDict()
        for l in legalValues:
            self.data[l] = PersistentSet()
    
    def __getitem__(self, keys):
        if isinstance(keys,slice):
            raise Exception('A categorical index cannot be sliced.')
        elif isinstance(keys,set):
            keys = list(keys)
        elif not isinstance(keys,list):
            keys = [keys]
        
        # start with the smallest set
        smallestSize=sys.maxint
        smallestKey=None
        for k in keys:
            if len(self.data[k]) < smallestSize:
                smallestSize = len(self.data[k])
            smallestKey = k
        if smallestKey == None:
            return set()
        
        results = set(self.data[smallestKey])
        for k in keys:
            if k == smallestKey:
                continue
            results.intersection_update(self.data[k])
        return results
    
    def __setitem__(self, key, value):
        if not self.data.has_key(key):
            raise Exception('Unknown categorical key: %s' % key)
        else:
            self.data[key].add(value)
    
    def count(self, keys):
        if isinstance(keys,slice):
            raise Exception('A categorical index cannot be sliced.')
        elif isinstance(keys,set):
            keys = list(keys)
        elif not isinstance(keys,list):
            keys = [keys]
        
        count = 0
        for k in keys:
            count += len(self.data[k])
        return count
    
    def has_key(self, key):
        return self.data.has_key(key)

class numericIndex(Persistent):
    '''
    Essentially an extension of durus.btree.BTree that accepts duplicate keys (via chaining)
    '''
    def __init__(self, name, low, high, legalValues):
        self.name = name
        
        self.minimum = low
        self.maximum = high
        
        self.data = BTree()
    
    def __getItem__(self, key):
        return self.data.get(key,[])
    
    def __setItem__(self, key, value):
        if self.minimum == None or key < self.minimum:
            self.minimum = key
        if self.maximum == None or key > self.maximum:
            self.maximum = key
        self.data[key] = value
    
    def count(self, low, high):
        return self.data.count_range(low,high,closed_start=True,closed_end=True)
    
    def has_key(self, key):
        return self.data.has_key(key)
    
    def findNaturalMinAndMax(self):
        if self.minimum == self.maximum:
            self.minimum = 0
            if self.maximum == 0:
                self.minimum = -1
                self.maximum = 1
                self._p_note_change()
                return
        elif self.minimum > self.maximum:
            temp = self.maximum
            self.maximum = self.minimum
            self.minimum = temp
        
        span = self.maximum - self.minimum
        
        if self.maximum > 0:
            nearestTenMax = 10**math.ceil(math.log10(self.maximum))
        elif self.maximum == 0:
            nearestTenMax = 0
        else:
            nearestTenMax = -10**math.floor(math.log10(-self.maximum))
        
        if self.minimum > 0:
            nearestTenMin = 10**math.floor(math.log10(self.minimum))
        elif self.minimum == 0:
            nearestTenMin = 0
        else:
            nearestTenMin = -10**math.ceil(math.log10(-self.minimum))
        
        # prefer nearestTenMax if the gap between it and self.maximum is less than 25% the span of the data
        if abs(nearestTenMax - self.maximum) < 0.25*span:
            self.maximum = nearestTenMax
        
        # prefer zero if the gap between it and self.minimum is less than 50% the span of the data, then 25% for nearestTenMin
        if self.minimum > 0 and self.minimum < 0.5*span:
            self.minimum = 0
        elif abs(self.minimum - nearestTenMin) < 0.25*span:
            self.minimum = nearestTenMin
        self._p_note_change()
    
class mixedIndex(Persistent):
    def __init__(self, name, low, high, legalValues):
        self.numerics = numericIndex(name, low, high)
        self.categoricals = numericIndex(name, legalValues)
    
    def __getItem__(self, keys):
        if isinstance(keys,slice):
            return self.numerics.__getItem__(keys)
        elif isinstance(keys,set):
            keys = list(keys)
        elif not isinstance(keys,list):
            keys = [keys]
        
        results = []
        catKeys = set()
        for k in keys:
            if self.categoricals.has_key(k):
                catKeys.add(k)
            else:
                results.extend(self.numerics.__getItem__(k))
        results.extend(self.categoricals.__getItem__(catKeys))
        return results
    
    def __setItem__(self, key, value):
        if self.categoricals.has_key(key):
            self.categoricals[key] = value
        else:
            self.numerics[key] = value
    
    def count(self, low=None, high=None, keys=[]):
        count = self.categoricals.count(keys)
        if low != None:
            count += self.numerics.count(low,high)
        return count
    
    def has_key(self, key):
        return self.categoricals.has_key(key) or self.numerics.has_key(key)

if __name__ == '__main__':
    a = rangeDict()
    for k,v in [(0.1,1),(1.0,'b'),(2.3,3),(0.3,'d'),(0.7,5),(0.0,'f'),(3.0,7),(2.0,'h'),(1.0,9),(0.0,'j')]:
        a[k] = v
    b = rangeDict()
    for k,v in [(5.5,1),(5.5,'b'),(5.5,3),(5.5,'d'),(5.5,5),(5.5,'f'),(5.0,7),(5.0,'h'),(5.0,9),(5.0,'j')]:
        b[k] = v
    print a[0.0]
    print b[5.0]
    print rangeDict.intersection((a,[],set([0.0])),(b,[(5.0,5.0)],set()))