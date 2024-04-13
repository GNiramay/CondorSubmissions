# Submit jobs for making hcalnano
# Syntax: . SubmitCondor_NanoProd.sh <text file containing raw file paths> <Output file tag> <Location of the output folder>
# Example: . SubmitCondor_NanoProd.sh FilePaths/Test_NanoProd.txt Test root://cmseos.fnal.gov//store/user/ngogate/HCAL_DPG/PhaseScan_Nano/

FilePaths=$1
FileTag=$2_NanoProd
OutFolder=$3

CondFile=ConfFiles/${FileTag}_NanoProd.jdl

echo "universe = vanilla"> $CondFile
echo "Executable = Bash_NanoProd.sh">> $CondFile
echo "Transfer_Input_Files = ../step2_RAW2DIGI_RECO_USER.py">> $CondFile
echo "WhenToTransferOutput = NEVER">> $CondFile
printf "Output = StdOut/${FileTag}_%s(Cluster)_job%s(ProcId).stdout\n" $ $>> $CondFile
printf "Error = StdErr/${FileTag}_%s(Cluster)_job%s(ProcId).stderr\n" $ $>> $CondFile
printf "Log = Log/${FileTag}_%s(Cluster)_job%s(ProcId).log\n" $ $>> $CondFile
printf "Arguments = root://cmsxrootd.fnal.gov/%s(rawfile) ${OutFolder}/${FileTag}_job%s(ProcId).root\n" $ $>> $CondFile
echo "Queue rawfile from ${FilePaths}" >> $CondFile

# Submit condor job
# cat $CondFile			# Prints contents of .jdl file
condor_submit $CondFile		# submits condor jobs
