# compreheNGSive
compreheNGSive is an app for analyzing the end results of the next-generation sequencing pipeline. It was developed as part of a visualization design study in collaboration between the University of [Utah Division of Genetic Epidemiology](http://medicine.utah.edu/internalmedicine/geneticepidemiology/index.php) and the [Scientific Computing and Imaging Institute](http://www.sci.utah.edu/).

In order to find disease-causing genetic variants, the set of millions of variants generated from the NGS variant calling pipeline needs to be filtered down to a manageable list of interesting variants, and then explored in detail. Automated algorithms in this space are often inflexible, support only certain disease models, and tend to be particularly biased toward variants in coding regions of proteins. Complex diseases such as cancer and complex study designs are often incompatible with these algorithms.

compreheNGSive is a program that facilitates interactive, visual exploration of variants across the genome using any user-guided heuristics or user-computed annotations.

## What it can (and can't) handle
This is an early prototype! I've largely abandoned this project for the immediate future, though the odds of resurrecting it in the next few years are reasonably high. If you need a tool for whole genome-scale analysis across many attributes immediately, the best solution is probably to use the [VCF Cleaner scripts](https://github.com/yasashiku/genepi_ngs_scripts) to create .csv files. These can then be dumped into [Tableau Public](http://www.tableausoftware.com/public), which is free! If you want to play with this directly, it should be able to handle ~1 million variant .vcf files with up to 10 attributes at reasonable speeds. There is a tradeoff between data size and attributes - if you are content with looking at fewer attributes, you should be able to load more variants.

## Running compreheNGSive
No Next-Gen Sequencing app would be complete without a set of accompanying [shell scripts](https://github.com/yasashiku/genepi_ngs_scripts). I'll probably bundle these with the app in the future when the project has settled down a little. Theoretically, you should be able to run compreheNGSive with any old .vcf file, but in practice it probably won't work unless you clean it / filter it.

The first thing you should do is remove the INFO fields you know you won't use, as well as categorical INFO fields with many (> 40) possible strings. The cleanVCF.py script should make this simple. Another thing that can help performance is initial prefiltering of the .vcf file - the filterVCF.py script will let you filter with complex expressions involving Chromosome, Position, QUAL, FILTER, or any INFO column you like (a little knowledge of [Python string formatting](http://docs.python.org/2/library/stdtypes.html#string-formatting-operations) will be helpful here). As you probably want to calculate things on your own (you probably have a bunch of per-feature or per-variant data in a spreadsheet somewhere), you can bundle this info into the .vcf file as INFO fields using addBEDtoVCF.py or addCSVtoVCF.py. Finally, calcStats.py will fix allele frequencies (this fixes the often-misinterpreted REF/ALT configuration and gives you true major/minor allele frequencies) and calculates a few other basic per-population statistics.

For help with each tool, run them from the command line with the --help option. I know this documentation is probably inadequate at the moment - if you have any questions, feel free to send me an email!

## Planned Features
- Genome browser
- Pseudo-scented widget of mixed histograms and parallel coordinates
- Export selected variants as .csv files
- Export history (for data provenance, help in writing papers, etc)
- Wrap preprocessing scripts into a GUI

## License
Copyright 2012 Alex Bigelow

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.

Questions, comments, ideas, bug reports, and criticisms are more than welcome! Send an email to alex dot bigelow at utah dot edu.
