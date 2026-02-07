@echo off
REM Ensure exit code propagation: exits with gpg's exit code so it can be used with &&
pushd "%~dp0\.." >nul || exit /b 1
gpg --decrypt --output "private.yaml" --yes "private.yaml.gpg"
set "EXIT_CODE=%ERRORLEVEL%"
popd >nul
exit /b %EXIT_CODE%
