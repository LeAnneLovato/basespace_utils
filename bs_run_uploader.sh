#!/bin/bash

# required args
name=$1
type=$2
runFolder=$3
config=$4

# exit with error
if [ "$#" -ne 4 ]; then
	echo "Parm 1:Name"
	echo "Parm 2: Type: HiSeq1000, HiSeq1500, HiSeq2000, HiSeq2500, HiSeq3000, HiSeq4000, HiSeqX, NovaSeq5000, NovaSeq6000, MiniSeq, MiSeq, MiSeqDx, NextSeq, NextSeqDx, iSeq100"
	echo "Parm 3: Run Folder path"
	echo "Parm 4: Config (Env)"
	exit 1
fi

bs -c ${config} upload run -n ${name} -t ${type} ${runFolder} --retry --verbose --no-progress-bars


