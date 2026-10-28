
################## USER DEFINED
# Formant: <text file storing root file paths> <no. of jobs to submit> <analysis script arguments>
SAMPLES = [
    {"filelist": "FilePaths/test_signal.txt", "nfiles": 5,  "args": "--sample signal"},
    {"filelist": "FilePaths/test_bkg.txt",    "nfiles": 10, "args": "--sample bkg"},
    {"filelist": "FilePaths/test_data.txt",   "nfiles": 20, "args": "--sample data --lumi 59.8"},
]

JOBTXT = "test.txt"
CondConfig = "test.jdl"
BatchName = 'test'
Exec = 'Exec/test.sh'
TransferFiles = ''

##################

# Include above mentioned text files to the transfer file list
PutComma = (TransferFiles != '')
for ss in SAMPLES:
    if PutComma:
        TransferFiles += ' , ' + ss["filelist"]
    else:
        TransferFiles += ss["filelist"]
        PutComma = True

# Create text file for jobs submission. Generally, don't have to touch.
with open('JobInfo/'+JOBTXT, "w") as out:
    for s in SAMPLES:
        total = len(open(s["filelist"]).read().split())
        for start in range(0, total, s["nfiles"]):
            out.write(f'{s["filelist"].split("/")[-1]} {start} {s["nfiles"]} {s["args"]}\n')

# A generic config template. Make chages whenever needed.
with open('ConfFiles/'+CondConfig, "w") as f:
    f.write(f'''batch_name = {BatchName}
JobTag = $(batch_name)_$(Cluster)_job$(ProcId)
universe = vanilla
Executable = {Exec}
WhenToTransferOutput = ON_EXIT
request_cpus = 1
# request_memory = 5000
Output = StdOut/$(JobTag).stdout
Error = StdErr/$(JobTag).stderr
Log = Log/$(JobTag).log
Transfer_Input_Files = {TransferFiles}

Arguments = $(AnaScript).py --nthreads $(request_cpus) $(line) -e $(Run2Lumi)
Queue Arguments from JobInfo/{JOBTXT}
''')
