#!/bin/bash
# Script to submit jobs to count no. of bkg events with +/- genWeight
# Syntax: . EvtStat.sh <era> <Dataset name>

Era=$1
Dataset=$2
CondFile=../ConfFiles/EvtStat_${Dataset}.jdl

rm -f $CondFile

echo "universe = vanilla">>$CondFile
# echo "Executable = PythonExec.sh">>$CondFile
echo "Executable = ../Exec/EvtStat.sh">>$CondFile
echo "Transfer_Input_Files = ../../Bkg_weights/GetEvtStat.py">>$CondFile
echo "WhenToTransferOutput = NEVER">>$CondFile
printf "Output = ../StdOut/${Dataset}_%s(Cluster)_job%s(ProcId).stdout\n" $ $>>$CondFile
printf "Error = ../StdErr/${Dataset}_%s(Cluster)_job%s(ProcId).stderr\n" $ $>>$CondFile
printf "Log = ../Log/${Dataset}_%s(Cluster)_job%s(ProcId).log\n" $ $>>$CondFile
printf "Arguments = GetEvtStat.py root://cmsxrootd.fnal.gov//%s(InRootFile) ${Dataset}_%s(ProcId).root\n" $ $>>$CondFile
echo "Queue InRootFile from ../../Bkg_weights/FilePaths/${Era}/${Dataset}.txt" >>$CondFile

condor_submit $CondFile
# cat $CondFile
