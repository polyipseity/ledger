@echo off
hledger --file "../index.journal" --strict check accounts assertions balancednoautoconversion commodities ordereddates parseable payees recentassertions tags uniqueleafnames
