#!/bin/bash

KGP=/raid1/sequencing/reference/background/KGP
TEMP=/export/home/alex/Desktop

python mapToBed.py $KGP/extracted/popInference/snpMap_hg18.csv $TEMP/hg18snpMap.bed
/raid1/sequencing/apps/other/ucsc/liftOver $TEMP/hg18snpMap.bed /raid1/sequencing/apps/other/ucsc/chainFiles/hg18ToHg19.over.chain $TEMP/hg19snpMap.bed $TEMP/liftover_removed.txt
python bedToLoci.py $TEMP/hg19snpMap.bed $KGP/extracted/popInference/snpMap_hg19.csv
python liftoverFailReformat.py $TEMP/liftover_removed.txt $KGP/extracted/popInference/liftover_removed.csv

f=""
for i in `ls /raid1/sequencing/reference/background/KGP/compressed_vcfs/ALL.chr*.vcf`
do
	f="$f ${i}"
done
echo Extracting CEU...
python extractGenotypes.py --vcf $f --loci $KGP/extracted/popInference/snpMap_hg19.csv --individuals $KGP/populationLists/CEU.txt --out $KGP/extracted/popInference/CEU_results.csv --remove $KGP/extracted/popInference/CEU_removed.csv
echo Extracting JPT...
python extractGenotypes.py --vcf $f --loci $KGP/extracted/popInference/snpMap_hg19.csv --individuals $KGP/populationLists/JPT.txt --out $KGP/extracted/popInference/JPT_results.csv --remove $KGP/extracted/popInference/JPT_removed.csv
echo Extracting CHB...
python extractGenotypes.py --vcf $f --loci $KGP/extracted/popInference/snpMap_hg19.csv --individuals $KGP/populationLists/CHB.txt --out $KGP/extracted/popInference/CHB_results.csv --remove $KGP/extracted/popInference/CHB_removed.csv
echo Extracting YRI...
python extractGenotypes.py --vcf $f --loci $KGP/extracted/popInference/snpMap_hg19.csv --individuals $KGP/populationLists/YRI.txt --out $KGP/extracted/popInference/YRI_results.csv --remove $KGP/extracted/popInference/YRI_removed.csv
echo Done