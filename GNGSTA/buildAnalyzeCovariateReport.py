import os
import sys
from resources.utils import recursiveDict
from resources.utils import unixInterface, unixParameter

interface = unixInterface("buildAnalyzeCovariateReport.py",
                          "Creates a LaTeX .tex file that consolidates all the output from AnalyzeCovariates.jar into a single pdf. "+
                          "After running this program, type pdflatex <your .tex file> to generate the actual pdf.",
                         requiredParameters = [unixParameter("--dir",
                                                             "-d",
                                                             "directory",
                                                             "Root directory to iterate from. You should run AnalyzeCovariates.jar "+,
                                                             "twice (before and after TableRecalibration) - please save the results in "+
                                                             "two separate directories. For example, if the current directory is /foo "+
                                                             "and the results before recalibration are in /foo/preRecalibration and the "+
                                                             "results after recalibration are in /foo/postRecalibration, the parameter "+
                                                             "to give --dir would be \"/foo\"."
                                                             numArgs = 1),
                                               unixParameter("--out",
                                                             "-o",
                                                             "file",
                                                             "Output .tex file.",
                                                             numArgs = 1)],
                         optionalParameters = [])

analyses = recursiveDict()
runNames = ['preCalibration','postCalibration']

latexChars = ['#','$','%','^','&','_','{','}','~','\\']

def escapeLatexChars(s):
	r = ""
	for c in s:
		if c in latexChars:
			r += "\\"
		r += c
	return r

for dirname, dirnames, filenames in os.walk(interface.getOption(tag="--dir",altTag="-d",optional=False)[0]):
	#for d in dirnames:
	#	runNames.append(d)
	for f in filenames:
		pieces = f.split('.')
		if pieces[-1] == "pdf":
			if len(pieces) < 6:
				analysis = pieces[1]
				group = pieces[0]
				individual = "all"
				stat = pieces[3]
			else:
				analysis = pieces[2]
				group = pieces[0]
				individual = pieces[1]
				stat = pieces[4]
			for run in runNames:
				a = analyses[analysis]
				g = a[group]
				i = g[individual]
				s = i[stat]
				analyses[analysis][group][individual][stat][run] = recursiveDict(isLeaf=True)

outFile = open(interface.getOption(tag="--out",altTag="-o",optional=False),'w')
outFile.write("\\documentclass[12pt]{article}\n" + "\\usepackage{geometry}\n" + "\\usepackage{graphicx}\n" + "\\usepackage{float}\n" + "\\usepackage{subfig}\n" + "\\usepackage{wrapfig}\n")
for d in runNames:
	outFile.write("\\graphicspath{{./"+d+"/}}\n")
outFile.write("\\textheight = 10.5in\n" + "\\textwidth = 8in\n" + "\\topmargin = -1in\n" + "\\oddsidemargin = -0.5in\n" + "\\evensidemargin = 0in\n" + "%%% BEGIN DOCUMENT\n" + "\\begin{document}\n")
for analysis,groups in analyses.iteritems():
	outFile.write("\n\\section{"+escapeLatexChars(analysis)+"}\n")
	groupKeyList = sorted(groups.keys())
	for group in groupKeyList:
		individuals = groups[group]
		indKeyList = sorted(individuals.keys())
		for individual in indKeyList:
			stats = individuals[individual]
			statKeyList = sorted(stats.keys())
			outFile.write("\n\\subsection{"+escapeLatexChars(group)+":"+escapeLatexChars(individual)+"}\n")
			for stat in statKeyList:
				runs = stats[stat]
				outFile.write("\n\\subsubsection{"+escapeLatexChars(stat)+"}\n")
				outFile.write("\\begin{tabular}{c c}\n")
				
				rowOneText = ""
				rowTwoText = ""
				
				for run in runNames:
					groupPathString = group
					if individual != "all":
						groupPathString += "." + individual
					rowOneText += " & \\includegraphics[type=pdf,ext=.pdf,read=.pdf,width=2.5in]{%s/%s.%s.dat.%s}" % (run,groupPathString,analysis,stat)
					rowTwoText += " & " + escapeLatexChars(run)
				
				outFile.write(rowOneText[3:]+" \\\\\n")
				outFile.write(rowTwoText[3:]+" \\\\\n")
				outFile.write("\\end{tabular}\n")
outFile.write("\n\\end{document}")
outFile.close()