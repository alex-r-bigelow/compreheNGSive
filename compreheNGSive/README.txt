compreheNGSive is an app for analyzing the end results of the next-generation sequencing pipeline (a better description coming soon...).

RELEASE NOTES
-------------

v0.1:
There are two ways of running the program; if you just want to load an existing .vcf file and/or related .csv files, you can just double-click the app, and load the files using the dialog. Note that none of the options in the dialog other than selecting files work yet.
The other way is from the command line; edit compreheNGSive.xml to your liking (hopefully it's pretty straightforward from the existing example, but feel free to ask about it if you have questions!), and type:

open -a compreheNGSive.app compreheNGSive.xml
(Mac OS X)

compreheNGSive.exe compreheNGSive.xml
(Windows)

./compreheNGSive compreheNGSive.xml

Features not yet implemented:

    Genome browser
    Rs # List
    Interactive opening screen (we're still mulling nuances of picking minor alleles - for now, the program assumes that the major allele is in the REF column of the .vcf file, and the minor allele is the first ALT allele)

LICENSE
-------
Copyright 2012 Alex Bigelow

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.

Questions, comments, ideas, bug reports, and criticisms are more than welcome! Send an email to alex.bigelow@utah.edu.
