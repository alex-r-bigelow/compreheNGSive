#!/bin/bash

KGP=/raid1/sequencing/reference/background/KGP
TEMP=/export/home/alex/Desktop

for i in `ls /raid1/sequencing/reference/background/KGP/compressed_vcfs`
do
	gunzip $i
	j=${i%.gz}
	python extractGenotypes.py --vcf $j --loci $TEMP/hg19snpMap.txt --individuals $KGP/populationLists/CEU.txt --out $KGP/extracted/${j%.vcf}.csv --remove $KGP/extracted/${j%.vcf}_removed.csv
	gzip $j
done