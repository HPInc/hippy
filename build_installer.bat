@echo off

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

if not exist .\dist\sample mkdir .\dist\sample
copy ".\tests\depth_camera_stream.py" ".\dist\sample\"
