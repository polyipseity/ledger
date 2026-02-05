@echo off
REM Lint and fix all Markdown files using pnpm
REM Ensure exit code propagation: exits with pnpm's exit code so it can be used with &&
pnpm run markdownlint:fix
set "EXIT_CODE=%ERRORLEVEL%"
exit /b %EXIT_CODE%
