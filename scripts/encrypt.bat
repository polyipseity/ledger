@echo off
REM Ensure exit code propagation: exits with gpg's exit code so it can be used with &&
pushd "%~dp0\.." >nul || exit /b 1
gpg --armor --encrypt --output "private.yaml.gpg" --recipient "4D3365CB145A282F!" --yes "private.yaml"
set "EXIT_CODE=%ERRORLEVEL%"
popd >nul
exit /b %EXIT_CODE%
