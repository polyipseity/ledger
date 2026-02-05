@echo off
REM Ensure exit code propagation: exits with gpg's exit code so it can be used with &&
gpg --decrypt --output "../private.yaml" --yes "../private.yaml.gpg"
set "EXIT_CODE=%ERRORLEVEL%"
exit /b %EXIT_CODE%
