inputBed=$1
inputBAM=$2

if [ "$#" -ne 2 ]; then
	echo "Parameters:"
	echo "(1) DRAGEN BED Coverage Report"
	echo "(2) BAM file"
	exit 1
fi

file=$(basename ${inputBed})
samtools bedcov ${inpubasetBed} ${inputBam} > ${file}.bedcov

