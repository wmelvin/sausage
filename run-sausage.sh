#!/usr/bin/env bash

APP="./sausage.py"

function runapp
{
    "$APP" "$@"
    if [ $? -ne 0 ]; then
        exit 1
    fi
}

runapp ./README.md ./sausage.py --indent=4 --compare-cmd=bcompare
