#!/bin/bash

# required args
project=$1
config=$2
READ1_FASTQ=$3
READ2_FASTQ=$4

# exit with error
if [ "$#" -ne 4 ]; then
  echo "Missing a parameter..."
  echo "** ARG[1]: BSSH project"
  echo "** ARG[2]: BSSH config"
  echo "** ARG[3]: Read 1 file"
  echo "** ARG[4]: Read 2 file"
	exit 1
fi

# upload FASTQ files
bs upload dataset --config -c ${config} --project ${project} "${READ1_FASTQ}" "${READ2_FASTQ}"
