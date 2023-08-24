@echo off
gpg --decrypt --output "../private.yaml" --yes "../private.yaml.gpg"
