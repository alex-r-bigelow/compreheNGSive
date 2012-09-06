import sys

infile = open(sys.argv[1],'r')
outfile = open(sys.argv[2],'w')
lastLine = None
for line in infile:
    if lastLine == None:
        lastLine = line[1:].strip()
        continue
    else:
        columns = line.split()
        outfile.write("%s\t%s\t%s\t%s\n" % (columns[0],columns[1],columns[3],lastLine))
        lastLine = None
infile.close()
outfile.close()