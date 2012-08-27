'''
Created on Feb 1, 2012

@author: Alex Bigelow
'''

from Tkinter import Canvas,Scale,Tk
import math

WIDTH = 1000
HEIGHT = 300

BACKGROUND = "#777777"



class histogramWidget:
    BACKGROUND = "#222222"
    EDGE_HISTOGRAM_COLOR = "#999999"
    NODE_HISTOGRAM_COLOR = "#555555"
    TOOLTIP_COLOR="#FFFF55"
    
    PADDING = 8
    CENTER_WIDTH = 1
    CENTER_COLOR = "#444444"
    ZERO_GAP = 1
    UPDATE_WIDTH = 9
    UPDATE_COLOR = "#FFFFFF"
    HANDLE_WIDTH = 5
    HANDLE_COLOR = "#FFFFFF"
    HANDLE_LENGTH = (HEIGHT-2*PADDING)
    TICK_COLOR = "#FFFFFF"
    TICK_WIDTH = 10
    TICK_FACTOR = 2
    
    LOG_BASE = 10.0
    
    def __init__(self, parent, x, y, width, height, data, logScale=False, callback=None):
        self.canvas = Canvas(parent,background=histogramWidget.BACKGROUND, highlightbackground=histogramWidget.BACKGROUND,width=width,height=height)
        self.canvas.place(x=x,y=y,width=width,height=height,bordermode="inside")
        
        self.logScale = logScale
        
        self.callback = callback
        
        self.edgeBars = []
        self.nodeBars = []
        
        self.binValues = []
        self.numBins = len(data) - 1
        
        self.currentBin = self.numBins     # start the slider at the highest bin
        
        edgeRange = 0.0
        nodeRange = 0.0
        
        for values in data.itervalues():
            if values[0] > edgeRange:
                edgeRange = values[0]
            if values[1] > nodeRange:
                nodeRange = values[1]
        
        edgeRange = float(edgeRange)    # ensure that it will yield floats when used in calculations...
        nodeRange = float(nodeRange)
        
        if logScale:
            edgeRange = math.log(edgeRange,histogramWidget.LOG_BASE)
            nodeRange = math.log(nodeRange,histogramWidget.LOG_BASE)
        
        # calculate the center line - but don't draw it yet
        self.center_x = histogramWidget.PADDING
        if self.logScale:
            self.center_x += histogramWidget.TICK_WIDTH+histogramWidget.PADDING
        self.center_y = height/2
        self.center_x2 = width-histogramWidget.PADDING
        self.center_y2 = self.center_y + histogramWidget.CENTER_WIDTH
        
        # draw the histograms with background-colored baseline rectangles (these allow tooltips to work on very short bars with little area)
        self.bar_interval = float(self.center_x2 - self.center_x) / (self.numBins+1)
        bar_x = self.center_x
        edge_y2 = self.center_y-histogramWidget.PADDING
        edge_space = edge_y2-histogramWidget.PADDING
        node_y = self.center_y2+histogramWidget.PADDING
        node_space = (height-node_y)-histogramWidget.PADDING
        
        thresholds = sorted(data.iterkeys())
        for threshold in thresholds:
            self.binValues.append(threshold)
            edgeWeight = data[threshold][0]
            nodeWeight = data[threshold][1]
            if logScale:
                if edgeWeight > 0:
                    edgeWeight = math.log(edgeWeight,histogramWidget.LOG_BASE)
                else:
                    edgeWeight = 0
                if nodeWeight > 0:
                    nodeWeight = math.log(nodeWeight,histogramWidget.LOG_BASE)
                else:
                    nodeWeight = 0
            
            bar_x2 = bar_x + self.bar_interval
            
            edge_y = histogramWidget.PADDING + int(edge_space*(1.0-edgeWeight/edgeRange))
            edge = self.canvas.create_rectangle(bar_x,edge_y,bar_x2,edge_y2,fill=histogramWidget.EDGE_HISTOGRAM_COLOR,width=0)
            baseline = self.canvas.create_rectangle(bar_x,edge_y2+histogramWidget.ZERO_GAP,bar_x2,edge_y2+histogramWidget.PADDING,fill=histogramWidget.BACKGROUND,width=0)
            self.canvas.addtag_withtag("Threshold: %f" % threshold,edge)
            self.canvas.addtag_withtag("No. Edges: %i" % data[threshold][0],edge)
            self.canvas.tag_bind(edge,"<Enter>",self.updateToolTip)
            self.canvas.tag_bind(edge,"<Leave>",self.updateToolTip)
            self.edgeBars.append(edge)
            self.canvas.addtag_withtag("Threshold: %f" % threshold,baseline)
            self.canvas.addtag_withtag("No. Edges: %i" % data[threshold][0],baseline)
            self.canvas.tag_bind(baseline,"<Enter>",self.updateToolTip)
            self.canvas.tag_bind(baseline,"<Leave>",self.updateToolTip)
            
            node_y2 = node_y + int(node_space*(nodeWeight/nodeRange))
            node = self.canvas.create_rectangle(bar_x,node_y,bar_x2,node_y2,fill=histogramWidget.NODE_HISTOGRAM_COLOR,width=0)
            baseline = self.canvas.create_rectangle(bar_x,node_y-histogramWidget.PADDING,bar_x2,node_y-histogramWidget.ZERO_GAP,fill=histogramWidget.BACKGROUND,width=0)
            self.canvas.addtag_withtag("Threshold: %f" % threshold,node)
            self.canvas.addtag_withtag("No. Nodes: %i" % data[threshold][1],node)
            self.canvas.tag_bind(node,"<Enter>",self.updateToolTip)
            self.canvas.tag_bind(node,"<Leave>",self.updateToolTip)
            self.nodeBars.append(node)
            self.canvas.addtag_withtag("Threshold: %f" % threshold,baseline)
            self.canvas.addtag_withtag("No. Nodes: %i" % data[threshold][1],baseline)
            self.canvas.tag_bind(baseline,"<Enter>",self.updateToolTip)
            self.canvas.tag_bind(baseline,"<Leave>",self.updateToolTip)
            
            bar_x = bar_x2
        
        # now draw the center line
        self.centerLine = self.canvas.create_rectangle(self.center_x,self.center_y,self.center_x2,self.center_y2,fill=histogramWidget.CENTER_COLOR,width=0)
        
        # draw the tick marks if logarithmic
        if self.logScale:
            tick_x = histogramWidget.PADDING
            tick_x2 = histogramWidget.PADDING+histogramWidget.TICK_WIDTH
            
            start_y = edge_y2
            end_y = histogramWidget.PADDING
            dist = start_y-end_y
            while dist > 1:
                dist /= histogramWidget.TICK_FACTOR
                self.canvas.create_rectangle(tick_x,end_y+dist-1,tick_x2,end_y+dist,fill=histogramWidget.TICK_COLOR,width=0)
            
            start_y = node_y
            end_y = height-histogramWidget.PADDING
            dist = end_y-start_y
            while dist > 1:
                dist /= histogramWidget.TICK_FACTOR
                self.canvas.create_rectangle(tick_x,end_y-dist,tick_x2,end_y-dist+1,fill=histogramWidget.TICK_COLOR,width=0)
        
        # draw the update bar
        bar_x = self.currentBin*self.bar_interval + self.center_x
        bar_x2 = self.center_x2
        bar_y = self.center_y-histogramWidget.UPDATE_WIDTH/2
        bar_y2 = bar_y+histogramWidget.UPDATE_WIDTH
        self.updateBar = self.canvas.create_rectangle(bar_x,bar_y,bar_x2,bar_y2,fill=histogramWidget.UPDATE_COLOR,width=0)
        
        # draw the handle
        handle_x = self.currentBin*self.bar_interval-histogramWidget.HANDLE_WIDTH/2+self.center_x
        handle_x2 = handle_x+histogramWidget.HANDLE_WIDTH
        handle_y = self.center_y-histogramWidget.HANDLE_LENGTH/2
        handle_y2 = handle_y+histogramWidget.HANDLE_LENGTH
        self.handleBar = self.canvas.create_rectangle(handle_x,handle_y,handle_x2,handle_y2,fill=histogramWidget.HANDLE_COLOR,width=0)
        self.canvas.tag_bind(self.handleBar, "<Button-1>",self.adjustHandle)
        self.canvas.tag_bind(self.handleBar, "<B1-Motion>",self.adjustHandle)
        self.canvas.tag_bind(self.handleBar, "<ButtonRelease-1>",self.adjustHandle)
        parent.bind("<Left>",lambda e: self.nudgeHandle(e,-1))
        parent.bind("<Right>",lambda e: self.nudgeHandle(e,1))
        
        # init the tooltip as nothing
        self.toolTipBox = self.canvas.create_rectangle(0,0,0,0,state="hidden",fill=histogramWidget.TOOLTIP_COLOR,width=0)
        self.toolTip = self.canvas.create_text(0,0,state="hidden",anchor="nw")
        self.canvas.bind("<Enter>",self.updateToolTip)
        self.canvas.bind("<Leave>",self.updateToolTip)
    
    def adjustHandle(self, event):
        newBin = int(self.numBins*(event.x-self.center_x)/float(self.center_x2-self.center_x)+0.5)
        if newBin == self.currentBin or newBin < 0 or newBin > self.numBins:
            return
        
        self.canvas.move(self.handleBar,(newBin-self.currentBin)*self.bar_interval,0)
        self.currentBin = newBin
        if self.callback != None:
            self.callback(self.binValues[newBin])
    
    def nudgeHandle(self, event, distance):
        temp = self.currentBin+distance
        if temp < 0 or temp > self.numBins:
            return
        
        self.canvas.move(self.handleBar,distance*self.bar_interval,0)
        self.currentBin += distance
        
        if self.callback != None:
            self.callback(self.binValues[self.currentBin])
    
    def update(self, currentBins):
        currentBar = self.canvas.coords(self.updateBar)
        self.canvas.coords(self.updateBar,currentBins*self.bar_interval+self.center_x,currentBar[1],currentBar[2],currentBar[3])
    
    def updateToolTip(self, event):
        allTags = self.canvas.gettags(self.canvas.find_overlapping(event.x,event.y,event.x+1,event.y+1))
        
        if len(allTags) == 0:
            self.canvas.itemconfig(self.toolTipBox,state="hidden")
            self.canvas.itemconfig(self.toolTip,state="hidden")
            return
        
        outText = ""
        for t in allTags:
            if t == "current":
                continue
            outText += t + "\n"
        
        outText = outText[:-1]  # strip the last return
        
        self.canvas.coords(self.toolTip,event.x+20,event.y)
        self.canvas.itemconfig(self.toolTip,state="normal",text=outText,anchor="nw")
        # correct if our tooltip is off screen
        textBounds = self.canvas.bbox(self.toolTip)
        if textBounds[2] >= WIDTH-2*histogramWidget.PADDING:
            self.canvas.itemconfig(self.toolTip, anchor="ne")
            self.canvas.coords(self.toolTip,event.x-20,event.y)
            if textBounds[3] >= HEIGHT-2*histogramWidget.PADDING:
                self.canvas.itemconfig(self.toolTip, anchor="se")
        elif textBounds[3] >= HEIGHT-2*histogramWidget.PADDING:
            self.canvas.itemconfig(self.toolTip, anchor="sw")
        
        # draw the box behind it
        self.canvas.coords(self.toolTipBox,self.canvas.bbox(self.toolTip))
        self.canvas.itemconfig(self.toolTipBox, state="normal")

class gephiController:
    def __init__(self, data, appCallback=None, minValue=0.0, maxValue=1.0, logScale=False):
        self.data = data
        numBins = len(data)-1
        
        self.master = Tk()
        self.master.geometry("%dx%d%+d%+d" % (WIDTH,HEIGHT,50,50))
        self.master.resizable(False, False)
        
        self.histogram = histogramWidget(self.master,0,0,WIDTH,HEIGHT,self.data,logScale=logScale,callback=self.callApp)
        
        self.current = numBins
        self.currentValue = self.data[maxValue][0]
        
        self.appCallback = appCallback
        if self.appCallback != None:
            self.master.bind("<<appCallback>>",self.runAppCall)
        self.master.bind("<<Update>>",self.runUpdate)
    
    def mainloop(self):
        self.master.mainloop()
    
    def runUpdate(self, event):
        self.histogram.update(self.current)
    
    def runAppCall(self,event):
        self.appCallback(self.currentValue)
    
    def callApp(self, value):
        self.currentValue = value
        self.master.event_generate("<<appCallback>>",when="tail")
    
    def update(self, current):
        self.current = current
        self.master.event_generate("<<Update>>",when="tail")
    
if __name__ == "__main__":
    import time
    
    range = 101
    testData = {}
    for i in xrange(int(range)):
        testData[i/10.0] = (i,100-i)
    
    current = len(testData)-1
    
    widgetCallback = None
    
    def dummy(value):
        print value
        time.sleep(0.1)
        global widgetCallback
        if widgetCallback != None:
            widgetCallback(int(value*10.0))
    
    test = gephiController(testData,dummy,logScale=True)
    widgetCallback = test.update
    test.mainloop()