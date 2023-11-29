#!/bin/bash

# required args
type=$1
id=$2
out=$3
config=$4

# exit with error
if [ "$#" -ne 4 ]; then
  echo "Parm 1: Type: run, appsession, appresult"
  echo "Parm 2: BS ID"
  echo "Parm 3: Output path"
  echo "Parm 4: Config file"
	exit 1
fi

# download the run, appsession, or appresult
bs ${type} download -c ${config} -i ${id} -o ${out} --retry --verbose --no-progress-bars
