set __PYTHONPATH=%PYTHONPATH%
set PYTHONPATH=%CD%\build\Debug;%PYTHONPATH%
poetry run python ./cli.py %*
set PYTHONPATH=%__PYTHONPATH%
