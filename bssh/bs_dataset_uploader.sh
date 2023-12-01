#!/bin/bash

##########################################
# Author: LeAnne Lovato
# GitHub: https://github.com/LeAnneLovato
##########################################

# required args
source=$1
project=$2
profile=$3

# exit with error
if [ "$#" -ne 3 ]; then
  echo "Missing a parameter..."
  echo "** ARG[1]: Directory for upload"
  echo "** ARG[2]: BSSH project"
  echo "** ARG[3]: BSSH config"
	exit 1
fi

# upload dataset
bs upload dataset --type common.files -p ${project} -c ${profile} --recursive --retry --verbose --no-progress-bars ${source}
