#!/bin/bash

# required cmd line inputs
project=$1
bs_id=$2
file=$3
icaPath=$4

# exit with error
if [ $# -lt 3 ]; then
  echo "Missing a parameter ..."
  echo "** ARG[1]: ICAv2 project ID"
  echo "** ARG[2]: BSSH project ID"
  echo "** ARG[3]: File with local data paths"
  echo "** ARG[4]: ICA path"
	exit 1
fi

# create a basemount instance
basemount --unmount BaseSpace/
basemount BaseSpace/
bsshPath="./BaseSpace/.ResourceById/AppSession/${bs_id}"

# loop over local data paths
while IFS=$'\t' read -r folder; do
	sample=$(basename $folder | cut -d "_" -f 2 | cut -d "-" -f 1)
	echo "Processing... ${sample}"
	prefix=$(basename $folder | cut -d "." -f 3)

	# upload select DRAGEN output files: bam, vcfs
	# uploads to a sample dir within the ICA path provided
	icav2 projectdata upload ${bsshPath}/${folder}/Files/${prefix}.bam ${icaPath}/${sample}/ --project-id ${project}
	icav2 projectdata upload ${bsshPath}/${folder}/Files/${prefix}.bam.md5sum ${icaPath}/${sample}/ --project-id ${project}
	icav2 projectdata upload ${bsshPath}/${folder}/Files/${prefix}.bai ${icaPath}/${sample}/ --project-id ${project}
	icav2 projectdata upload ${bsshPath}/${folder}/Files/${prefix}.hard-filtered.gvcf.gz ${icaPath}/${sample}/ --project-id ${project}
	icav2 projectdata upload ${bsshPath}/${folder}/Files/${prefix}.hard-filtered.gvcf.gz.tbi ${icaPath}/${sample}/ --project-id ${project}
	icav2 projectdata upload ${bsshPath}/${folder}/Files/${prefix}.hard-filtered.vcf.gz ${icaPath}/${sample}/ --project-id ${project}
	icav2 projectdata upload ${bsshPath}/${folder}/Files/${prefix}.hard-filtered.vcf.gz.tbi ${icaPath}/${sample}/ --project-id ${project}
	icav2 projectdata upload ${bsshPath}/${folder}/Files/${prefix}.sv.vcf.gz ${icaPath}/${sample}/ --project-id ${project}
	icav2 projectdata upload ${bsshPath}/${folder}/Files/${prefix}.sv.vcf.gz.tbi ${icaPath}/${sample}/ --project-id ${project}
	icav2 projectdata upload ${bsshPath}/${folder}/Files/${prefix}.cnv.vcf.gz ${icaPath}/${sample}/ --project-id ${project}
	icav2 projectdata upload ${bsshPath}/${folder}/Files/${prefix}.cnv.vcf.gz ${icaPath}/${sample}/ --project-id ${project}

	# create a list of csv files
	ls ${bsshPath}/${folder}/Files/ | grep ".csv" > ${sample}_csvList.txt
	csv=${sample}_csvList.txt

	# upload all csv (metric) files
	while IFS=$'\t' read -r csv; do
		icav2 projectdata upload ${bsshPath}/${folder}/Files/${csv} ${icaPath}/${sample}/ --project-id ${project}

	# close the csv list
	done < ${csv}
	rm ${sample}_csvList.txt

# close file of local data paths
done < ${file}
