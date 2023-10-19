#!/usr/bin/env sh

args='--strict check accounts assertions autobalanced balanced commodities ordereddates parseable payees tags'
hledger --file '../index.journal' $args
for file in ../**/index.journal; do
  hledger --file "$file" $args
done
