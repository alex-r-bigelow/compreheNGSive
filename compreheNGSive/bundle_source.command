#!/bin/bash
if [ -z $1 ]
then
	VERSION=""
else
	VERSION="_"$1
fi

STARTING_DIR=$(pwd)
SCRIPT_DIR=${0%"bundle_source.command"}

echo 'Cleaning...'
cd $SCRIPT_DIR
rm -rf dist
rm -rf build
rm Data.db*

echo 'Cloning...'
cd ..
tar -czvf $STARTING_DIR/compreheNGSive$VERSION.tar.gz compreheNGSive