#!/bin/bash
echo Input arguments: $*
list=$1 start=$2 n=$3; shift 3
echo python3 analysis.py "$@" $(sed -n "$((start+1)),$((start+n))p" $list)
