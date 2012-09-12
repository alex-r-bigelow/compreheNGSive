#!/bin/bash

KGP=/raid1/sequencing/reference/background/KGP
TEMP=/export/home/alex/Desktop

#python mapToBed.py $TEMP/HDJ-3-SNP_Map.txt $TEMP/hg18snpMap.bed
#/raid1/sequencing/apps/other/ucsc/liftOver $TEMP/hg18snpMap.bed /raid1/sequencing/apps/other/ucsc/chainFiles/hg18ToHg19.over.chain $TEMP/hg19snpMap.bed $TEMP/liftover_removed.txt
#python bedToLoci.py $TEMP/hg19snpMap.bed $KGP/extracted/hg19snpMap.csv
#python liftoverFailReformat.py $TEMP/liftover_removed.txt $KGP/extracted/liftover_removed.csv

f=""
for i in `ls /raid1/sequencing/reference/background/KGP/compressed_vcfs/*.gz`
do
	f="$f $i"
	echo Decompressing $i
	#gunzip $i
done
echo Extracting genotypes...
echo "python extractGenotypes.py --vcf $f --loci $KGP/extracted/hg19snpMap.csv --individuals $KGP/populationLists/CEU_2.txt --out $KGP/extracted/results.csv --remove $KGP/extracted/extraction_removed.csv"
for i in `ls /raid1/sequencing/reference/background/KGP/compressed_vcfs/*.vcf`
do
	echo Recompressing $i
	#gzip $i
done