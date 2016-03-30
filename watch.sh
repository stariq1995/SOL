#!/usr/bin/env bash

platform=$(uname -s)
if [ $platform == "Darwin" ]; then
    if [[ "$(which fswatch)" == *"not found"* ]]; then
        echo "Error: You need fswatch for this to work"
        exit 1
    fi
    pip install -e .
    fswatch -or -l 1 $(find src -name '*.pyx') | while read num; do echo $num; pip install -e . ; done
else
    echo "Sorry, have not implemented this for your OS"
    exit 1
fi

