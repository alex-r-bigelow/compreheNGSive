#!/bin/bash
if [ -z $1 ]
then
	VERSION=""
else
	VERSION="_"$1
fi

STARTING_DIR=$(pwd)

SCRIPT_DIR=$(readlink -f $0)
SCRIPT_DIR=${SCRIPT_DIR%"bundle_linux.sh"}
cd $SCRIPT_DIR
rm -rf dist
rm -rf build
rm -rf compreheNGSive
rm Data.db*
echo 'Running build script...'
python setup.py build

echo 'Moving files around...'
# move the auto-generated programs and packages around
mv dist compreheNGSive
# copy the svg and ui elements manually
cp -r gui compreheNGSive/gui
cp -r dataModels compreheNGSive/dataModels
cp -r resources compreheNGSive/resources
cp -r bonusTools compreheNGSive/bonusTools
rm -rf build
# copy documentation and config files
cp COPYING.txt compreheNGSive/
cp COPYING.LESSER.txt compreheNGSive/
cp README.txt compreheNGSive/

echo 'Bundling...'
tar -czf compreheNGSive$VERSION.tar.gz compreheNGSive
mv compreheNGSive$VERSION.tar.gz $STARTING_DIR
