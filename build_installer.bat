@echo off

rem Helper batch file to delete existing build output and make a new build
rem (which includes the wheel file, license file, and sample code)

set directories=(".\.cache"^
 ".\build"^
 ".\dist"^
 ".\doc"^
 ".\Hippy.egg-info"^
 ".\python\pluto\__pycache__"^
 ".\tests\__pycache__")

for %%d in %directories% do (
    echo Removing %%d
    if exist %%d rmdir /s /q %%d
)

python setup.py bdist_wheel

copy ".\LICENSE" ".\dist\"

if not exist .\dist\sample mkdir .\dist\sample
copy ".\tests\depth_camera_stream.py" ".\dist\sample\"
