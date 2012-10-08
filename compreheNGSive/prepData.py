'''
Copyright 2012 Alex Bigelow

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this program. If not, see
<http://www.gnu.org/licenses/>.
'''

from gui.scatterplotWidget import scatterplotWidget
from gui.parallelCoordinateWidget import parallelCoordinateWidget
from dataModels.setupData import prefs
from dataModels.variantData import selectionState, operation
from PySide.QtCore import QFile, Qt
from PySide.QtGui import QFileDialog, QProgressDialog, QApplication
from PySide.QtUiTools import *
import sys

PREFS_FILE = 'bigPrefs.xml'

'''
Color scheme used in this app from colorbrewer2.org:

http://colorbrewer2.org/index.php?type=qualitative&scheme=Dark2&n=8
'''

def trace(frame, event, arg):
    print "%s, %s:%d" % (event, frame.f_code.co_filename, frame.f_lineno)
    return trace

class setupApp:
    def __init__(self, params):
        loader = QUiLoader()
        infile = QFile("gui/ui/Setup.ui")
        infile.open(QFile.ReadOnly)
        self.window = loader.load(infile, None)
        
        self.loadPrefs()
        
        self.window.quitButton.clicked.connect(self.closeApp)
        self.window.saveButton.clicked.connect(self.savePrefs)
        self.window.runButton.clicked.connect(self.runSV)
        
        self.splash = QProgressDialog("Loading", "Cancel", 0, 100, parent=None)
        self.splash.setWindowModality(Qt.WindowModal)
        self.splash.setAutoReset(False)
        self.splash.setAutoClose(False)
        self.splash.hide()
        self.canceled = False
        
        self.window.show()
        self.runningApp = None
    
    def loadPrefs(self):
        infile = open(PREFS_FILE,'r')
        self.window.textEdit.setPlainText(infile.read())
        infile.close()
    
    def savePrefs(self):
        outfile=open(PREFS_FILE,'w')
        outfile.write(self.window.textEdit.toPlainText())
        outfile.close()
    
    def showProgressWidget(self, estimate=100, message="Loading..."):
        self.splash.setLabelText(message)
        self.splash.setMaximum(estimate)
        self.splash.setValue(0)
        self.splash.show()
    
    def tickProgressWidget(self, numTicks=1, message=None):
        if self.canceled:
            return
        if message != None:
            self.splash.setLabelText(message)
        newValue = min(self.splash.maximum(),numTicks+self.splash.value())
        self.splash.setValue(newValue)
        self.canceled = self.splash.wasCanceled()
        return self.canceled
    
    def runSV(self, params=PREFS_FILE):
        self.savePrefs()
        self.window.hide()
        
        appPrefs = prefs.generateFromText(self.window.textEdit.toPlainText())
        
        self.showProgressWidget(appPrefs.maxTicks, "Loading files...")
        
        self.canceled = False
        vData = appPrefs.loadDataObjects(callback=self.tickProgressWidget)
        if self.canceled:
            self.splash.hide()
            self.window.show()
            return
        
        self.showProgressWidget(vData.estimateTicks(), "Writing files...")
        
        success = vData.dumpVcfFile(path='/export/home/alex/Desktop/chr3-seq.vcf',callback=self.tickProgressWidget)
        if not success:
            self.splash.hide()
            self.window.show()
            return
        
        sys.exit(0)
        # TODO write to file
    
    def closeApp(self):
        self.window.reject()

def runProgram():
    if len(sys.argv) == 2:
        params = sys.argv.pop(1)
    else:
        params = None
    app = QApplication(sys.argv)
    w = setupApp(params)
    sys.exit(app.exec_())

if __name__ == "__main__": 
    #sys.settrace(trace)
    runProgram()
    
    #import cProfile
    #cProfile.run('runProgram()')