#!/bin/bash

# required args
file=$1
project=$2
ica_path=$3

# exit with error
if [ "$#" -ne 3 ]; then 
	echo "Missing a paramerter..."
	echo "** ARG[1]: File to read local paths"
	echo "** ARG[2]: ICA project ID"
	echo "** ARG[3]: ICA path"
	exit 1
fi

# loop over input file
while IFS=$'\t' read -r local_path; do

	# get sample dir for ICA
	sample=$(basename ${local_path} | cut -d "." -f 1)
	clean_path=$(echo ${ica_path} | sed 's/\/$//g')
	target_path=${clean_path}/${sample}/
	echo "${sample}	${target_path}"	

	# upload data
	icav2 projectdata upload --project-id ${project} ${local_path} ${target_path}

# close file of ICA paths
done < ${file}

