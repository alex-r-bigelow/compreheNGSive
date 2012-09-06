#!/bin/bash

KGP=/raid1/sequencing/reference/background/KGP
TEMP=/export/home/alex/Desktop

python mapToBed.py $TEMP/HDJ-3-SNP_Map.txt $TEMP/hg18snpMap.bed
/raid1/sequencing/apps/other/ucsc/liftOver $TEMP/hg18snpMap.bed /raid1/sequencing/apps/other/ucsc/chainFiles/hg18ToHg19.over.chain $TEMP/hg19snpMap.bed $TEMP/liftover_removed.txt
python bedToLoci.py $TEMP/hg19snpMap.bed $KGP/extracted/hg19snpMap.csv
python liftoverFailReformat.py $TEMP/liftover_removed.txt $KGP/extracted/liftover_removed.csv

for i in `ls /raid1/sequencing/reference/background/KGP/compressed_vcfs/*.gz`
do
	gunzip $i
	j=${i%.gz}
	python extractGenotypes.py --vcf $j --loci $KGP/extracted/hg19snpMap.csv --individuals $KGP/populationLists/CEU.txt --out $KGP/extracted/${j%.phase1_release_v3.20101123.snps_indels_svs.genotypes.vcf}.csv --remove $KGP/extracted/${j%.phase1_release_v3.20101123.snps_indels_svs.genotypes.vcf}_removed.csv
	gzip $j
done