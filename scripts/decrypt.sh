#!/usr/bin/env sh
# This script propagates the exit code from the underlying command so it can be used with && in POSIX shells
gpg --decrypt --output '../private.yaml' --yes '../private.yaml.gpg'
