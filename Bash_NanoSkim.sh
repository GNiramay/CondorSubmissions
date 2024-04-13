#!/bin/bash
# Set up CMSSW env
# export SCRAM_ARCH=slc7_amd64_gcc700
source /cvmfs/cms.cern.ch/cmsset_default.sh
scram p CMSSW_14_0_0
cd CMSSW_14_0_0/src
cmsenv
cd -
ls -alht

# # Execute skimming script
# time python3 SkimNano.py $*

# Another attempt
time python3 SkimNano.py $1 tempOut.root
ls -alht
xrdcp tempOut.root $2
