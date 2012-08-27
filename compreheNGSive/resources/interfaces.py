'''
Created January 2012

@author: Alex Bigelow
'''

import sys
from collections import defaultdict

CONSOLE_WIDTH=77

class unixParameter:
    def __init__(self, tag, altTag, inputType, description, numArgs = 1):
        self.tag = tag
        self.altTag = altTag
        self.inputType = inputType
        self.description = description
        self.numArgs = numArgs

class unixInterface:
    """
    
    """
    def __init__(self, programName, programDescription, requiredParameters = [], optionalParameters = []):
        self.programName = programName
        self.programDescription = programDescription
        self.requiredParameters = requiredParameters
        self.optionalParameters = optionalParameters
        self.initOptions()
    
    def initOptions(self):
        if "--help" in sys.argv or "-h" in sys.argv:
            self.die(isError=False)
        self.args = defaultdict(list)
        currentArg = None
        for a in sys.argv[1:]:
            if a.startswith("-") and currentArg != None and len(self.args[currentArg]) == 0:
                self.args[currentArg].append(currentArg) # case where there were 0 parameters for the last argument (argument is a flag)
            
            if a.startswith("-"):
                if "=" in a:
                    temp = a.split("=")
                    currentArg = temp[0]
                    self.args[currentArg].append(temp[1])
                else:
                    currentArg = a
            else:
                if currentArg == None:
                    self.args["no_arg"].append(a)
                else:
                    self.args[currentArg].append(a)
        # case where the last argument given was a flag
        if currentArg != None and len(self.args[currentArg]) == 0:
            self.args[currentArg].append(currentArg)
    
    def getOption(self, tag, altTag=None, optional=True):
        if self.args.has_key(tag):
            return self.args[tag]
        elif altTag != None and self.args.has_key(altTag):
            return self.args[altTag]
        elif optional:
            return None
        else:
            self.die("ERROR: Missing required parameter: %s" % tag)
    
    def alignRight(self, text):
        words = text.split()
        outText = ""
        maxLength = 2*CONSOLE_WIDTH/3
        leftPadding = ''.rjust(CONSOLE_WIDTH/3)
        lineLength = 0
        currentLine = ""
        currentWord = ""
        for w in words:
            currentWord = w
            lineLength += len(w) + 1
            if currentWord == "\\n":
                outText += leftPadding + currentLine + "\n"
                lineLength = 0
                currentLine = ""
                currentWord = ""
            elif lineLength - 1 > maxLength:
                outText += leftPadding + currentLine + "\n"
                lineLength = len(currentWord) + 1
                currentLine = currentWord + " "
                currentWord = ""
            elif lineLength - 1 == maxLength:
                outText += leftPadding + currentLine + currentWord + "\n"
                lineLength = 0
                currentLine = ""
                currentWord = ""
            else:
                currentLine += currentWord + " "
                currentWord = ""
        if currentLine != "":
            outText += leftPadding + currentLine + "\n"
        return outText
        
    def die(self, message="", isError=True):
        if len(message) > 0:
            message += "\n"
        
        message += self.programName + ":\n"
        message += self.alignRight(self.programDescription) + "\n"
        
        message += ("Usage:\n" +
                    "\n" +
                    "python " + self.programName + ".py\n")
        for p in self.requiredParameters:
            message += ''.rjust(CONSOLE_WIDTH/3) + p.tag
            numArgs = p.numArgs
            if numArgs < 0:
                numArgs = 2
            for i in xrange(numArgs):
                message += " " + p.inputType
            if p.numArgs < 0:
                message += " ..."
            message += "\n"
        for p in self.optionalParameters:
            message += '['.rjust(CONSOLE_WIDTH/3) + p.tag
            if numArgs < 0:
                numArgs = 2
            for i in xrange(numArgs):
                message += " " + p.inputType
            if p.numArgs < 0:
                message += " ..."
            message += "]\n"
        
        message += ("\n" +
                    "Required Parameters:\n" +
                    "--------------------\n")
        for p in self.requiredParameters:
            message += (p.tag + "\n" +
                        p.altTag + "\n" +
                        self.alignRight(p.description) + "\n")
        message += ("\n" +
                    "Optional Parameters:\n" +
                    "--------------------\n")
        for p in self.optionalParameters:
            message += (p.tag + "\n" +
                        p.altTag + "\n" +
                        self.alignRight(p.description) + "\n")
        message += ("--help\n"+
                    "-h\n"+
                    self.alignRight("Displays this message.") + "\n")
        print message
        if isError:
            sys.exit(1)
        else:
            sys.exit(2)