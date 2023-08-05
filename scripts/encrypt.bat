@echo off
gpg --output "../private.yaml.gpg" --yes --encrypt --recipient "polyipseity@gmail.com" "../private.yaml"
