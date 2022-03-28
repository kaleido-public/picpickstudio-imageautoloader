@echo off
set __PYTHONPATH=%PYTHONPATH%
set PYTHONPATH=%CD%\build\Debug;%PYTHONPATH%
poetry run ipython
set PYTHONPATH=%__PYTHONPATH%
