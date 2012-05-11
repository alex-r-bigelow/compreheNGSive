#!/bin/bash
NOVOALIGNCS=/gen21/alex/Apps/SequencePipeline/novoalignCS
PICARD=/gen21/alex/Apps/SequencePipeline/picard-tools-1.48
GATK=/gen21/alex/Apps/SequencePipeline/GATK/dist
#YINGREF=/gen21/alex/pipelineFiles/referenceSequence/ying_reference
WEIYUREF=/gen21/alex/pipelineFiles/referenceSequence/wei_yu_reference
RODBIND=/gen21/alex/pipelineFiles/rodBinding
#YINGDATA=/gen21/alex/pipelineFiles/filesFromYing/post_novoalignCS
DATADIR=/export/home/alex/pipelineFiles/rawData
TMPDIR=/gen21/alex/pipelineFiles/scratch
REALLYTMPDIR=$TMPDIR/tmp
REGIONSFILE=/gen21/alex/pipelineFiles/genes_new.bed
java64=/usr/local/java/jdk1.6.0_22_x64/bin/java
MEM=20

echo "Alex's pipeline v1.2 - novoalign phase"
#echo ""
#echo "Index the reference genome - this only needs to be done once"
#echo ""
#$NOVOALIGNCS/novoindex -c $WEIYUREF/all.cs.nix $WEIYUREF/all.fasta

echo ""
echo "Run novoalignCS on all data"
echo ""
for f in $(ls $DATADIR/*.csfasta)
do
	F=${f#$DATADIR/}
	$NOVOALIGNCS/novoalignCS -o SAM $'@RG\tID:genepi\tPL:SOLiD\tSM:'${F%.csfasta} -r Random -k -d $WEIYUREF/all.cs.nix -f $f > $TMPDIR/${F%.csfasta}$'.sam' 2> $TMPDIR/${F%.csfasta}$'.log'
done