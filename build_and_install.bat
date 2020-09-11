@echo off

echo y | pip uninstall hippy
call build_installer.bat

set fileName=""
for /r %%i in (dist\Hippy-*) do (
  set fileName=%%i
)

echo Installing %fileName%

pip install %fileName%
