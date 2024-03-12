#!/bin/bash
# Script to submit jobs to skim the samples
# Example: . Skim.sh Summer20UL17 ST_s-channel_4f_hadronicDecays_TuneCP5_13TeV-amcatnlo-pythia8 ST_s-channel_4f_hadronicDecays

ProcName="Skim"
Era=$1				# Summer20UL17 etc.
Dataset=$2			# Actual name of the dataset
SamName=$3			# Corresponding sample name, that exists in XSec.py

CondFile=../ConfFiles/${ProcName}_${Dataset}.jdl
rm -f $CondFile
EvtStatRoot=../../Bkg_weights/OutHistograms/${Era}_${Dataset}.root
EvtStatKey=$( basename $EvtStatRoot)

echo "universe = vanilla">>$CondFile
echo "Executable = ../Exec/Skim.sh">>$CondFile
echo "Transfer_Input_Files = ../../Skimming/SkimAll.py , ../../Skimming/XSec.py , ${EvtStatRoot} ">>$CondFile
echo "WhenToTransferOutput = NEVER">>$CondFile
printf "Output = ../StdOut/${ProcName}_${Dataset}_%s(Cluster)_job%s(ProcId).stdout\n" $ $>>$CondFile
printf "Error = ../StdErr/${ProcName}_${Dataset}_%s(Cluster)_job%s(ProcId).stderr\n" $ $>>$CondFile
printf "Log = ../Log/${ProcName}_${Dataset}_%s(Cluster)_job%s(ProcId).log\n" $ $>>$CondFile
printf "Arguments = SkimAll.py root://cmsxrootd.fnal.gov//%s(InRootFile) ${SamName} ${Era} ${EvtStatKey} ${Era}_${Dataset}_%s(ProcId).root\n" $ $>>$CondFile
echo "Queue InRootFile from ../../Bkg_weights/FilePaths/${Era}/${Dataset}.txt" >>$CondFile

condor_submit $CondFile
# cat $CondFile
