import numpy as np
from scipy import spatial

'''
Monkey patch that adds query types to scipy.spatial's KDTree; to use, simply

import resources.scipyPatches
'''

def query_rectangle(self, low, high):
    low = np.array(low, copy=False)
    high = np.array(high, copy=False)
    
    if low.shape[-1] != self.m or high.shape[-1] != self.m:
        raise ValueError("Searching for a %d-dimensional or %d-dimensional point in a " \
                         "%d-dimensional KDTree" % (low.shape[-1], high.shape[-1], self.m))
    
    for i in xrange(self.m):
        if low[i] > high[i]:
            temp = high[i]
            high[i] = low[i]
            low[i] = temp
    
    def traverse(node):
        if isinstance(node, spatial.KDTree.leafnode):
            results = []
            for i in node.idx:
                temp = self.data[i]
                if np.all(temp >= low) and np.all(temp <= high):
                    results.append(i)
            return results
        elif node.split < low[node.split_dim]:
            return traverse(node.greater)
        elif node.split > high[node.split_dim]:
            return traverse(node.less)
        else:
            return traverse(node.greater) + traverse(node.less)
    
    return traverse(self.tree)
spatial.KDTree.query_rectangle = query_rectangle