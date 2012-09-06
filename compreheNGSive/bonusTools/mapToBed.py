import sys

infile = open(sys.argv[1],'r')
outfile = open(sys.argv[2],'w')
isFirst = True
for line in infile:
    if isFirst:
        isFirst = False
        continue
    columns = line.split()
    outfile.write("chr%s %s %i %s\n" % (columns[2],columns[3],int(columns[3])+1,columns[1]))
infile.close()
outfile.close()
