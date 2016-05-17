#!/usr/bin/env bash

echo <<EOF
deb http://downloads.skewed.de/apt/trusty trusty universe
deb-src http://downloads.skewed.de/apt/trusty trusty universe
EOF
>> /etc/apt/sources.list
add-apt-repository ppa:ubuntu-toolchain-r/test
apt-key add 98507F25
apt-get -q update
apt-get install -y python python-graph-tool