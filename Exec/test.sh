#!/bin/bash
echo Input arguments: $*
read list start n args <<< "$(sed -n "$(($1 + 1))p" jobs.txt)"
files=$(sed -n "${start},$((start + n - 1))p" $list)
echo python3 analysis.py $args $files
