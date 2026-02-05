@echo off
REM Ensure exit code propagation: exits with gpg's exit code so it can be used with &&
gpg --armor --encrypt --output "../private.yaml.gpg" --recipient "4D3365CB145A282F!" --yes "../private.yaml"
set "EXIT_CODE=%ERRORLEVEL%"
exit /b %EXIT_CODE%
