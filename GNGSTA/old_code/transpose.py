f = open('temp.csv','r')
data = {}
row = 0
maxLen = 0
for line in f:
	data[row] = line.split()
	if len(data[row]) > maxLen:
		maxLen = len(data[row])
	row += 1
f.close()

f = open('temp2.csv','w')
for r in xrange(maxLen):
	for c in xrange(len(data)):
		if len(data[c]) > r:
			f.write(data[c][r])
		f.write("\t")
	f.write("\n")
f.close()