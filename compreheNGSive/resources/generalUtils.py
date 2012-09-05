import os

def tail(fname, window):
    """
    Read last N lines from file fname.
    This function borrowed from http://code.activestate.com/recipes/577968-log-watcher-tail-f-log/ on 3 Feb 2012
    
    Author: Giampaolo Rodola' <g.rodola [AT] gmail [DOT] com>
    License: MIT
    
    Slightly tweaked from original version
    """
    f = open(fname, 'r')

    BUFSIZ = 1024
    f.seek(0, os.SEEK_END)
    fsize = f.tell()
    block = -1
    data = ""
    exit = False
    while not exit:
        step = (block * BUFSIZ)
        if abs(step) >= fsize:
            f.seek(0)
            exit = True
        else:
            f.seek(step, os.SEEK_END)
        data = f.read().strip()
        if data.count('\n') >= window:
            break
        else:
            block -= 1
    return data.splitlines()[-window:]

def fitInSevenChars(value):
    '''
    Squeeze a float into exactly 7 characters, align right
    '''
    result = "{:7G}".format(value)
    while len(result) > 7:
        if 'E' in result and result[1] != 'E':
            eind = result.find('E')
            offset = 1
            original = result
            while len(result) > 7 and result[1] != 'E':
                result = original[:eind-offset] + original[eind:]
                offset += 1
            if len(result) > 7:
                result = "INF"
        else:
            while len(result) > 7:
                result = result[:-1]
    while len(result) < 7:
        result = ' ' + result
    return result

def parameterizeArgs(args):
    results = {}
    key = None
    for i in args:
        if i.startswith("-"):
            key = i
            while key.startswith("-"):
                key = key[1:]
        else:
            if results.has_key(key):
                if not isinstance(results[key],list):
                    results[key] = [results[key]]
                results[key].append(i)
            else:
                results[key] = i
    return results