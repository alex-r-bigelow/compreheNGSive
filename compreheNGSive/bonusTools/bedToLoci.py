import sys

infile = open(sys.argv[1],'r')
outfile = open(sys.argv[2],'w')
for line in infile:
    columns = line.split()
    outfile.write("%s %s %s\n" % (columns[0],columns[1],columns[3]))
infile.close()
outfile.close()