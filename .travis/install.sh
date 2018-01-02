#!/usr/bin/env bash
set -e -x

# Install TMgen from source
git clone https://github.com/progwriter/TMgen.git
pushd TMgen
pip install -r requirements.txt
pip install -e .
popd

pip install -r requirements.txt
pip install pytest flake8
pip install -e .