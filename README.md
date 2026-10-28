# CondorSubmissions
A generic repository to store all the condor related programs

## Installation
```bash
git clone git@github.com:GNiramay/CondorSubmissions.git
cd CondorSubmissions/
. firsttime.sh
```

## Test an example
```bash
python3 test.py
condor_Submit ConfFiles/test.jdl
```

## Example code explanation
1. `test.py`: A simple python script that creates condor submission file as well as a text file that stores what each job is supposed to do.
	1.  `SAMPLES` list allows submitting different kinds of jobs with a single config file. It specifies where the root file paths are stored, how many files to process per job and what arguments to pass to the analysis script during execution.
	2. Lines `10-14` specify the file to store the information needed in each job, condor config file name, batch name for bookkeeping, executable to use and any extra files to transfer to the condor node.
	3. Lines `19-25` ensure that the text files storing root file paths get transferred to the condor node
	4. Line `35` onwards is a code to create the condor config file. This is also a place to explore.
2. `Exec/test.sh`: An example executable that shows how to execute a typical job. It passes the specified arguments to the analysis script along with all the root files that need to be processed.
3. `CleanIt.sh`: Deletes condor output, error, log files.

## Ideal workflow
1. Store the root file paths in new files in the folder `FilePaths`
2. Create a new executable in `Exec` according to your needs; motived from `Exec/test.sh`.
	1. Set GRID certificate proxy
	2. setup CMSSW
	3. Instead of passing all the root file paths to the analysis script, loop over them.
	4. Might want to xrdcp the root files before processing.
3. Copy `test.py` to a new file and modify the file according to your needs.