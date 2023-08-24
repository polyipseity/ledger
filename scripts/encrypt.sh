#!/usr/bin/env sh
gpg --armor --encrypt --output '../private.yaml.gpg' --recipient 'polyipseity@gmail.com' --yes '../private.yaml'
