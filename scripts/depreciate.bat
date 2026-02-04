@echo off
pushd %~dp0\..
python -m "scripts.depreciate" %*
popd
