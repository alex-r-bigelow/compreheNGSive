#!/bin/bash
if [ -z $1 ]
then
	VERSION=""
else
	VERSION="_"$1
fi

STARTING_DIR=$(pwd)
SCRIPT_DIR=${0%"bundle_osx.command"}

cd $SCRIPT_DIR
rm -rf dist
rm -rf build
rm -rf compreheNGSive
echo 'Running build script...'
python setup.py py2app

echo 'Moving files around...'
# move the auto-generated programs and packages around
mv dist compreheNGSive
rm -rf build
# move the svg and ui elements into the appropriate folders
cd compreheNGSive/compreheNGSive.app/Contents/Resources
touch qt.conf
mkdir gui
mkdir gui/svg
mkdir gui/ui
mv *.svg gui/svg
mv *.ui gui/ui
# copy documentation and config files
cd $STARTING_DIR
cd $SCRIPT_DIR
cp prefs.xml compreheNGSive/compreheNGSive.app/Contents/Resources
cp COPYING.txt compreheNGSive/
cp COPYING.LESSER.txt compreheNGSive/
cp README.txt compreheNGSive/

echo 'Bundling...'
hdiutil create -volname compreheNGSive -srcfolder compreheNGSive/ -ov -format UDZO compreheNGSive$VERSION.dmg
rm -rf compreheNGSive
mv compreheNGSive$VERSION.dmg $STARTING_DIR