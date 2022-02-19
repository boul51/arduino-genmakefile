#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
HOOKS_DIR=$(git rev-parse --git-path hooks)

cp -v "${SCRIPT_DIR}/pre-commit" "${HOOKS_DIR}/pre-commit"
