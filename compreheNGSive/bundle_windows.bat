echo off

if "%1"=="" (set VERSION=) else set VERSION=_%1
echo %VERSION%

echo 'Cleaning...'
rd /S /Q dist
rd /S /Q build
rd /S /Q compreheNGSive
echo 'Running build script...'
python setup.py py2exe

echo 'Moving files around...'
:: move the auto-generated programs and packages around
ren dist compreheNGSive
rd /S /Q build

:: copy documentation and config files
copy prefs.xml compreheNGSive
copy COPYING.txt compreheNGSive
copy COPYING.LESSER.txt compreheNGSive
copy README.txt compreheNGSive

::echo 'Bundling...'
cd compreheNGSive
7z.exe a ../compreheNGSive%VERSION%.zip *
cd ..
rd /S /Q compreheNGSive