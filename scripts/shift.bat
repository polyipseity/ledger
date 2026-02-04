@echo off
pushd %~dp0\..
python -m "scripts.shift" %*
popd
