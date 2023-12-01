#!/bin/bash

##########################################
# Author: LeAnne Lovato
# GitHub: https://github.com/LeAnneLovato
##########################################

# required args
type=$1
id=$2
ext=$3
profile=$4

# exit with error
if [ "$#" -ne 4 ]; then
  echo "Missing a parameter(s)..."
  echo "** ARG[1]: type case-sensitive 1) appsession or 2) appresult"
  echo "** ARG[1]: Appsession or Appresult ID"
  echo "** ARG[3]: Extension to download: bam, hard-filtered.gvcf.gz, hard-filtered.vcf.gz, metrics.csv"
  echo "** ARG[4]: BSSH config"
	exit 1
fi

# logging
echo "Type: ${type}"
echo "${type}: ${id}"
echo "BSSH config: ${profile}"
echo "File Extension to download: *${ext}"

# appsession
if [ "${type}" == "appsession" ]; then
	bs download appsession -i ${id} --exclude '*' --include "*${ext}" --retry --verbose --no-progress-bars

# appresult
elif [ "${type}" == "appresult" ]; then
	bs download appresult -c ${profile} -i ${id} --exclude '*' --include "*${ext}" --retry --verbose --no-progress-bars

# exit
else
	echo "Error determining type. Only 'appsession' or 'appresult' are allowed."
	exit 1
fi
