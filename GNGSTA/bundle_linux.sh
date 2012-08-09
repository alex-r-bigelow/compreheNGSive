#!/bin/bash
if [ $1="" ];
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
echo 'Running build script...'
python setup.py build

echo 'Moving files around...'
# move the auto-generated programs and packages around
mv dist compreheNGSive
cd build/*
cp * ../../compreheNGSive/
cd ../..
# copy the svg and ui elements manually
mkdir compreheNGSive/gui
cp -r gui/svg compreheNGSive/gui/
cp -r gui/ui compreheNGSive/gui/
rm -rf build
# copy documentation and config files
cp compreheNGSive.xml compreheNGSive/
cp COPYING.txt compreheNGSive/
cp COPYING.LESSER.txt compreheNGSive/
cp README.txt compreheNGSive/

echo 'Bundling...'
tar -czf compreheNGSive$VERSION.tar.gz compreheNGSive
rm -rf compreheNGSive
mv compreheNGSive$VERSION.tar.gz $STARTING_DIR
