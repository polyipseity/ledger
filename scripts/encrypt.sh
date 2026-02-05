#!/usr/bin/env sh
# This script propagates the exit code from the underlying command so it can be used with && in POSIX shells
gpg --armor --encrypt --output '../private.yaml.gpg' --recipient '4D3365CB145A282F!' --yes '../private.yaml'
