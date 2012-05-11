#!/bin/bash
ANNOVAR=/gen21/alex/Apps/SequencePipeline/annovar
PIPELINEFILES=/gen21/alex/pipelineFiles
VCFCONCAT=/gen21/alex/Apps/SequencePipeline/vcftools_0.1.6/bin/vcf-concat
export PERL5LIB=/gen21/alex/Apps/SequencePipeline/vcftools_0.1.6/perl

# My files
$VCFCONCAT $PIPELINEFILES/filesIMade/filteredSNPs.vcf $PIPELINEFILES/filesIMade/filteredIndels.vcf > $PIPELINEFILES/filesIMade/merged.vcf
$ANNOVAR/convert2annovar.pl $PIPELINEFILES/filesIMade/merged.vcf -format vcf4 -filter PASS > $PIPELINEFILES/filesIMade/merged.annovar
$ANNOVAR/annotate_variation.pl --buildver hg19 -geneanno $PIPELINEFILES/filesIMade/merged.annovar $ANNOVAR/humandb/

# Wei-Yu's files
$VCFCONCAT $PIPELINEFILES/filesFromWeiYu/snps.filtered*.vcf $PIPELINEFILES/filesFromWeiYu/indels.filtered*.vcf > $PIPELINEFILES/filesFromWeiYu/merged.vcf
$ANNOVAR/convert2annovar.pl $PIPELINEFILES/filesFromWeiYu/merged.vcf -format vcf4 -filter PASS > $PIPELINEFILES/filesFromWeiYu/merged.annovar
$ANNOVAR/annotate_variation.pl --buildver hg19 -geneanno $PIPELINEFILES/filesFromWeiYu/merged.annovar $ANNOVAR/humandb/