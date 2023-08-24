@echo off
gpg --encrypt --output "../private.yaml.gpg" --recipient "polyipseity@gmail.com" --yes "../private.yaml"
