#!/usr/bin/env bash

platform=$(uname -s)
if [ ${platform} == "Darwin" ]; then
    if [[ "$(which fswatch)" == *"not found"* ]]; then
        echo "Error: You need fswatch for this to work"
        exit 1
    fi
    python setup.py build_ext --inplace
    echo 'done'
    fswatch -or -l 1 $(find src \( -name '*.pyx' -or -name '*.pxd' \) ) | while read num; do echo ${num}; python setup.py build_ext --inplace; echo 'done' ; done
else
    echo "Sorry, have not implemented this for your OS"
    exit 1
fi

