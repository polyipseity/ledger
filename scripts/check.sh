#!/usr/bin/env sh
hledger --file '../index.journal' --strict check accounts assertions autobalanced balanced commodities ordereddates parseable payees tags
