@echo off

rem Helper batch file to uninstall hippy, delete the existing build output, make
rem a new build (which includes the wheel file, license file, and sample code),
rem and install the new version of hippy

echo y | pip uninstall hippy
call build_installer.bat

set fileName=""
for /r %%i in (dist\Hippy-*) do (
  set fileName=%%i
)

echo Installing %fileName%

pip install %fileName%
