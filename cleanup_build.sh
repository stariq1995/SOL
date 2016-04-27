#! /bin/sh
rm -r build
find ./src -name '*.c' -exec rm {} \;
find ./src -name '*.so' -exec rm {} \;