# Submit jobs for skimming hcalnano
# Syntax: . SubmitCondor_NanoSkim.sh <text file containing raw file paths> <Output file tag> <Location of the output folder>
# Example: . SubmitCondor_NanoSkim.sh FilePaths/Test_NanoSkim.txt Test root://cmseos.fnal.gov//store/user/ngogate/HCAL_DPG/PhaseScan_Skimmed/

FilePaths=$1
FileTag=$2_NanoSkim
OutFolder=$3

CondFile=ConfFiles/${FileTag}.jdl

echo "universe = vanilla"> $CondFile
echo "Executable = Bash_NanoSkim.sh">> $CondFile
echo "Transfer_Input_Files = ../SkimNano.py">> $CondFile
echo "WhenToTransferOutput = NEVER">> $CondFile
printf "Output = StdOut/${FileTag}_%s(Cluster)_job%s(ProcId).stdout\n" $ $>> $CondFile
printf "Error = StdErr/${FileTag}_%s(Cluster)_job%s(ProcId).stderr\n" $ $>> $CondFile
printf "Log = Log/${FileTag}_%s(Cluster)_job%s(ProcId).log\n" $ $>> $CondFile
# printf "Arguments = root://cmsxrootd.fnal.gov/%s(rawfile) ${OutFolder}/${FileTag}_job%s(ProcId).root\n" $ $>> $CondFile
printf "Arguments = %s(rawfile) ${OutFolder}/${FileTag}_job%s(ProcId).root\n" $ $>> $CondFile
echo "Queue rawfile from ${FilePaths}" >> $CondFile

# Submit condor job
# cat $CondFile			# Prints contents of .jdl file
condor_submit $CondFile		# submits condor jobs
