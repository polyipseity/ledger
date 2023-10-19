@echo off
setlocal

set "_ARGS=--strict check accounts assertions autobalanced balanced commodities ordereddates parseable payees tags"
hledger --file "../index.journal" %_ARGS%
for /d %%G in ("../*") do (
  if exist "../%%G/index.journal" (
    hledger --file "../%%G/index.journal" %_ARGS%
  )
)

endlocal
