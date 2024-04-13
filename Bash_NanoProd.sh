#!/bin/bash
# Set up CMSSW env
# export SCRAM_ARCH=slc7_amd64_gcc700
source /cvmfs/cms.cern.ch/cmsset_default.sh
scram p CMSSW_14_1_0_pre0
cd CMSSW_14_1_0_pre0/src
cmsenv
cd -

# # Execute hcalnano production script
# time cmsDriver.py step2  -s RAW2DIGI,RECO,USER:DPGAnalysis/HcalNanoAOD/hcalNano_cff.hcalNanoTask --conditions auto:run3_data_prompt -n -1 --era Run3 --geometry DB:Extended --datatier NANOAOD --eventcontent NANOAOD --customise_commands="process.load('DPGAnalysis.HcalNanoAOD.hcalUMNioTable_cff')\nprocess.hcalNanoTask.add(process.uMNioTable)\nprocess.hcalNanoDigiTask.add(process.uMNioTable)" --filein $1 --fileout $2

# Execute hcalnano production script
time cmsDriver.py step2  -s RAW2DIGI,RECO,USER:DPGAnalysis/HcalNanoAOD/hcalNano_cff.hcalNanoTask --conditions auto:run3_data_prompt -n -1 --era Run3 --geometry DB:Extended --datatier NANOAOD --eventcontent NANOAOD --customise_commands="process.load('DPGAnalysis.HcalNanoAOD.hcalUMNioTable_cff')\nprocess.hcalNanoTask.add(process.uMNioTable)\nprocess.hcalNanoDigiTask.add(process.uMNioTable)" --filein $1 --fileout file:TempOut.root

xrdcp TempOut.root $2
