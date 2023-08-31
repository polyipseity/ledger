#!/usr/bin/env sh
gpg --armor --encrypt --output '../private.yaml.gpg' --recipient '4D3365CB145A282F!' --yes '../private.yaml'
