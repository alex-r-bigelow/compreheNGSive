#!/bin/bash
APPS_DIR=/raid1/sequencing/apps

NOVOALIGNCS=$APPS_DIR/alignment/novoalignCS
PICARD=$APPS_DIR/post_processing/picard-tools-1.48
GATK=$APPS_DIR/post_processing/GATK
ANNOVAR=$APPS_DIR/annotation/annovar
GNGSTA=$APPS_DIR/other/GNGSTA

REFERENCE_DIR=/raid1/sequencing/reference
REFERENCE=$REFERENCE_DIR/liverpool/hg19/all.fasta
DBSNP=$REFERENCE_DIR/background/KGP/sites.2Apr2012.vcf

ALIGNEDDATA=/raid1/alex/sequencing/casp8/data/novoalignResults
RAWDATA_DIR=/raid1/alex/sequencing/casp8/data/rawData

TMP_DIR=/raid1/alex/sequencing/casp8/scratch
REALLY_TMP_DIR=$TMP_DIR/tmp

RESULTS_DIR=/raid1/alex/sequencing/casp8/results

REGIONSFILE=/raid1/alex/sequencing/casp8/allGenes.bed

java64=/usr/local/java/jdk1.6.0_22_x64/bin/java
MEM=20

#echo ""
#echo "Run novoalignCS on all data"
#echo ""
#for f in $(ls $RAWDATA_DIR/*.csfasta)
#do
#	F=${f#$DATADIR/}
#	$NOVOALIGNCS/novoalignCS -o SAM $'@RG\tID:genepi\tPL:SOLiD\tSM:'${F%.csfasta} -r Random -k -d $REFERENCE_DIR/all.cs.nix -f $f > $TMP_DIR/${F%.csfasta}$'.sam' 2> $TMP_DIR/stats/${F%.csfasta}$'.alignment.log'
#done

#echo ""
#echo "Convert to bam, sort"
#echo ""
#for SAM in $(ls $TMP_DIR/*.sam)
#do
#	BAM=${SAM%.sam}$'.bam'
#	$java64 -Xmx$MEM\g -jar $PICARD/SortSam.jar INPUT=$SAM OUTPUT=$BAM CREATE_INDEX=true SO=coordinate COMPRESSION_LEVEL=5 MAX_RECORDS_IN_RAM=$((MEM*250000)) TMP_DIR=$REALLY_TMP_DIR
#	rm $SAM
#done
<<COMMENT_OUT
echo ""
echo "Run AddOrReplaceReadGroups - set up our data so it will be calibrated by lane down the line"
echo ""
declare -a IDs=('solid_lane1' 'solid_lane1' 'solid_lane1' 'solid_lane1' 'solid_lane1' 'solid_lane1' 'solid_lane1' 'solid_lane1' 'solid_lane2' 'solid_lane2' 'solid_lane2' 'solid_lane2' 'solid_lane2' 'solid_lane2' 'solid_lane2' 'solid_lane2' 'solid_lane3' 'solid_lane3' 'solid_lane3' 'solid_lane1' 'solid_lane1' 'solid_lane1' 'solid_lane1' 'solid_lane1' 'solid_lane2' 'solid_lane2' 'solid_lane2' 'solid_lane2' 'solid_lane2' 'solid_lane3' 'solid_lane3' 'solid_lane3' 'solid_lane3' 'solid_lane3' 'solid_lane4' 'solid_lane4' 'solid_lane3' 'solid_lane3' 'solid_lane3' 'solid_lane3' 'solid_lane4' 'solid_lane4' 'solid_lane4' 'solid_lane4' 'solid_lane4' 'solid_lane4' 'solid_lane4' 'solid_lane4' 'solid_lane4' 'solid_lane4');
for ((i=1;i<=50;i=i+1))
do
	# array index starts with 0
	j=$((i-1))
	IN=$TMP_DIR/441_$i\xF3.bam
	OUT=$TMP_DIR/441_$i\xF3.readgroups.bam
	$java64 -Xmx$MEM\g -jar $PICARD/AddOrReplaceReadGroups.jar I=$IN O=$OUT RGID=${IDs[$j]} RGLB=441_$i\x RGPL=solid RGPU=441_$i\x RGSM=441_$i\x

	# interleaving sort step
	rm $IN
	$java64 -Xmx$MEM\g -jar $PICARD/SortSam.jar INPUT=$OUT OUTPUT=$IN CREATE_INDEX=true SO=coordinate COMPRESSION_LEVEL=5 MAX_RECORDS_IN_RAM=$((MEM*250000)) TMP_DIR=$REALLY_TMP_DIR
	rm $OUT
done

echo ""
echo "Mark Duplicates"
echo ""
for BAM in $(ls $TMP_DIR/*.bam)
do
	OUT=${BAM%.bam}$'.markdup.bam'
	METRICS=${BAM%.bam}$'.markdup.metrics'
	$java64 -Xmx$MEM\g -jar $PICARD/MarkDuplicates.jar INPUT=$BAM OUTPUT=$OUT METRICS_FILE=$METRICS REMOVE_DUPLICATES=false ASSUME_SORTED=true VALIDATION_STRINGENCY=LENIENT OPTICAL_DUPLICATE_PIXEL_DISTANCE=10
	
	# interleaving sort step
	rm $BAM
	rm ${BAM%.bam}$'.bai'
	mv $METRICS $TMP_DIR/stats
	$java64 -Xmx$MEM\g -jar $PICARD/SortSam.jar INPUT=$OUT OUTPUT=$BAM CREATE_INDEX=true SO=coordinate COMPRESSION_LEVEL=5 MAX_RECORDS_IN_RAM=$((MEM*250000)) TMP_DIR=$REALLY_TMP_DIR
	rm $OUT
	rm ${OUT%.bam}$'.bai'
done

echo ""
echo "Local realignment around in/dels"
echo ""
IFILES=""
#for BAM in $(ls $TMP_DIR/*.bam)
#do
#	IFILES=$IFILES$' -I '$BAM
#done
for ((i=1;i<=50;i=i+1))
do
	IFILES=$IFILES$' -I '$TMP_DIR/441_$i\xF3.bam
done

# acquire targets
#$java64 -Xmx$MEM\g -jar $GATK/GenomeAnalysisTK.jar -T RealignerTargetCreator -R $REFERENCE --known $DBSNP -L $REGIONSFILE$IFILES -o $TMP_DIR/stats/localTargets.intervals
# realign all files together, combining into one BAM file
$java64 -Xmx$MEM\g -jar $GATK/GenomeAnalysisTK.jar -T IndelRealigner -R $REFERENCE --knownAlleles $DBSNP -L $REGIONSFILE$IFILES -targetIntervals $TMP_DIR/stats/localTargets.intervals -model USE_READS --maxReadsForRealignment 900000 --out $TMP_DIR/realigned.bam
# interleaving sort step
$java64 -Xmx$MEM\g -jar $PICARD/SortSam.jar INPUT=$TMP_DIR/realigned.bam OUTPUT=$TMP_DIR/all.bam CREATE_INDEX=true SO=coordinate COMPRESSION_LEVEL=5 MAX_RECORDS_IN_RAM=$((MEM*250000)) TMP_DIR=$REALLY_TMP_DIR
rm $TMP_DIR/realigned.bam
rm $TMP_DIR/realigned.bai


echo ""
echo "Pre-recalibration CountCovariates"
echo ""
$java64 -Xmx$MEM\g -jar $GATK/GenomeAnalysisTK.jar -T CountCovariates --knownSites $DBSNP -R $REFERENCE --solid_recal_mode SET_Q_ZERO --solid_nocall_strategy PURGE_READ -l INFO -log $TMP_DIR/stats/preCalibrationCountCovariates.log -L $REGIONSFILE -I $TMP_DIR/all.bam -cov ReadGroupCovariate -cov QualityScoreCovariate -cov CycleCovariate -cov DinucCovariate -recalFile $TMP_DIR/stats/preRecalibrationFile

echo ""
echo "Pre-recalibration AnalyzeCovariates"
echo ""
mkdir $TMP_DIR/stats/analyzeCovariates
mkdir $TMP_DIR/stats/analyzeCovariates/preRecalibration
$java64 -Xmx$MEM\g -jar $GATK/AnalyzeCovariates.jar -recalFile $TMP_DIR/stats/preRecalibrationFile -outputDir $TMP_DIR/stats/analyzeCovariates/preRecalibration -log $TMP_DIR/stats/preRecalibration.log

echo ""
echo "TableRecalibration"
echo ""
$java64 -Xmx$MEM\g -jar $GATK/GenomeAnalysisTK.jar -T TableRecalibration -R $REFERENCE --solid_recal_mode SET_Q_ZERO --solid_nocall_strategy PURGE_READ -L $REGIONSFILE -l INFO -I $TMP_DIR/all.bam -recalFile $TMP_DIR/stats/preRecalibrationFile --out $TMP_DIR/all.unsorted.bam
# interleaving sort step
rm $TMP_DIR/all.bam
rm $TMP_DIR/all.bai
$java64 -Xmx$MEM\g -jar $PICARD/SortSam.jar INPUT=$TMP_DIR/all.unsorted.bam OUTPUT=$TMP_DIR/all.bam CREATE_INDEX=true SO=coordinate COMPRESSION_LEVEL=5 MAX_RECORDS_IN_RAM=$((MEM*250000)) TMP_DIR=$REALLY_TMP_DIR
rm $TMP_DIR/all.unsorted.bam
rm $TMP_DIR/all.unsorted.bai

echo ""
echo "Post-recalibration CountCovariates"
echo ""
$java64 -Xmx$MEM\g -jar $GATK/GenomeAnalysisTK.jar -T CountCovariates --knownSites $DBSNP -R $REFERENCE --solid_recal_mode SET_Q_ZERO --solid_nocall_strategy PURGE_READ -l INFO -log $TMP_DIR/stats/preCalibrationCountCovariates.log -L $REGIONSFILE -I $TMP_DIR/all.bam -cov ReadGroupCovariate -cov QualityScoreCovariate -cov CycleCovariate -cov DinucCovariate -recalFile $TMP_DIR/stats/postRecalibrationFile

echo ""
echo "Post-recalibration AnalyzeCovariates"
echo ""
mkdir $TMP_DIR/stats/analyzeCovariates/postRecalibration
$java64 -Xmx$MEM\g -jar $GATK/AnalyzeCovariates.jar -recalFile $TMP_DIR/stats/postRecalibrationFile -outputDir $TMP_DIR/stats/analyzeCovariates/postRecalibration -log $TMP_DIR/stats/postRecalibration.log
$GNGSTA/buildAnalyzeCovariateReport.py --dir $TMP_DIR/stats/analyzeCovariates --out $TMP_DIR/stats/analyzeCovariates/report.tex
pdflatex $TMP_DIR/stats/analyzeCovariates/report.tex

echo ""
echo "UnifiedGenotyper"
echo ""
$java64 -Xmx$MEM\g -jar $GATK/GenomeAnalysisTK.jar -T UnifiedGenotyper -A QualByDepth -A HaplotypeScore -A ReadPosRankSumTest -A InbreedingCoeff -A FisherStrand -out_mode EMIT_ALL_CONFIDENT_SITES --max_alternate_alleles 9 -l INFO -log $TMP_DIR/stats/indelCalls.log -R $REFERENCE --dbsnp $DBSNP -I $TMP_DIR/all.bam -o $TMP_DIR/results/indels.vcf -A DepthOfCoverage -L $REGIONSFILE -glm INDEL

$java64 -Xmx$MEM\g -jar $GATK/GenomeAnalysisTK.jar -T UnifiedGenotyper -A QualByDepth -A HaplotypeScore -A HomopolymerRun -A FisherStrand -out_mode EMIT_ALL_CONFIDENT_SITES --max_alternate_alleles 9 -l INFO -log $TMP_DIR/stats/snpCalls.log -R $REFERENCE --dbsnp $DBSNP -I $TMP_DIR/all.bam -o $TMP_DIR/results/snps.vcf -A DepthOfCoverage -L $REGIONSFILE -glm SNP

#$GNGSTA/intersect_vcf.py --in $TMP_DIR/results/indels.vcf --out $TMP_DIR/results/targetIndels.vcf --regions $REGIONSFILE --filter $DBSNP 1>$TMP_DIR/stats/indelIntersection.log 2>&1

#$GNGSTA/intersect_vcf.py --in $TMP_DIR/results/snps.vcf --out $TMP_DIR/results/targetSNPs.vcf --regions $REGIONSFILE --filter $DBSNP 1>$TMP_DIR/stats/snpIntersection.log 2>&1

echo ""
echo "VariantFiltration"
echo ""
$java64 -Xmx$MEM\g -jar $GATK/GenomeAnalysisTK.jar -T VariantFiltration -R $REFERENCE -log $TMP_DIR/stats/indelFiltering.log --variant $TMP_DIR/results/indels.vcf -o $TMP_DIR/results/filteredIndels.vcf --filterExpression "QD < 2.0" --filterName "QDFilter" --filterExpression "ReadPosRankSum < -20.0" --filterName "ReadPosRankSumFilter" --filterExpression "InbreedingCoeff < -0.8" --filterName "IBCoFilter" --filterExpression "FS > 200.0" --filterName "FSFilter"

$java64 -Xmx$MEM\g -jar $GATK/GenomeAnalysisTK.jar -T VariantFiltration -R $REFERENCE -log $TMP_DIR/stats/snpFiltering.log --mask $TMP_DIR/results/indels.vcf --variant $TMP_DIR/results/snps.vcf -o $TMP_DIR/results/filteredSNPs.vcf --filterExpression "QD < 5.0" --filterName "QDFilter" --filterExpression "HRun > 5" --filterName "HRunFilter" --filterExpression "FS > 200.0" --filterName "FSFilter"
COMMENT_OUT
echo ""
echo "Merging SNP and Indel vcf files..."
echo ""

$GNGSTA/combine_vcf.py -i $TMP_DIR/results/filteredIndels.vcf $TMP_DIR/results/filteredSNPs.vcf -o $TMP_DIR/results/combined.vcf -d 1>$TMP_DIR/stats/vcfCombine.log 2>&1

echo ""
echo "ReadBackedPhasingWalker"
echo ""

$java64 -Xmx$MEM\g -jar $GATK/GenomeAnalysisTK.jar -T ReadBackedPhasing -R $REFERENCE -I $TMP_DIR/all.bam --variant $TMP_DIR/results/combined.vcf -L $REGIONSFILE -o $RESULTS_DIR/all.vcf 1>$TMP_DIR/stats/phasing.log 2>&1