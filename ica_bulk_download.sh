#!/bin/bash

# required args
file=$1
project=$2
target_path=$3

# exit with error
if [ "$#" -ne 3 ]; then 
	echo "Missing a parameter..."
	echo "** ARG[1]: File to read ICA paths"
	echo "** ARG[2]: ICA project ID"
	echo "** ARG[3]: Local path"
	exit 1
fi

# loop over input file
while IFS=$'\t' read -r file_id; do

	# get ICA dir name and create local dir
	name=$(echo ${file_id} | cut -d "/" -f 3 | cut -d "-" -f 1)
	echo "${name}: ${file_id}"
	if [ ! -d "${name}" ]; then
		mkdir ${name}
	fi	

	# download data
	icav2 projectdata download --project-id ${project} ${file_id} ${name}/

# close the file of ICA paths
done < ${file}

