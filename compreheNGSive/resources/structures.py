from blist import sortedlist
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
        Complexity is sigma(m log^2 n) operations or sigma(m log n) comparisons, where n is the size of the whole dict and m is the number
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
        '''
        Finds the values that are within the specified ranges or exactly matching values for a set of rangeDict objects;
        vargs is any number of (rangeDict,list,set) tuples; the list is a list of (low,high)
        tuples specifying ranges to include for that particular rangeDict, and the set is a set of exact values to include
        for that particular rangeDict
        '''
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

    @staticmethod
    def countIntersection(d1, r1, v1, d2, r2, v2, limit = None):
        pass
    
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
                if isinstance(val,str):
                    val = "'%s'" % val
                raise KeyError('You can not slice when setting a value: %s] = %s' % (errorstr,str(val)))
            else:
                key = key.start
        try:
            self.myList.add((key,val))
        except TypeError:
            if isinstance(key,str):
                key = "'%s'" % key
            if isinstance(val,str):
                val = "'%s'" % val
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

if __name__ == '__main__':
    a = rangeDict()
    for k,v in [(0.0,1),(0.0,'b'),(0.0,3),(0.0,'d'),(0.0,5),(0.0,'f'),(0.0,7),(0.0,'h'),(0.0,9),(0.0,'j')]:
        a[k] = v
    print a[0.0]    
    print a[-1:1]