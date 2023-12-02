import sys

file = sys.argv[1]
threshold = float(sys.argv[2])

with open(file, "r") as f:

    # Output header
    header = "#chrom:start-stop\tdragenCov\tsamtoolsCov\tpercentDiff\tdiff"
    print(header)

    # Read each line in the file
    for line in f:
        # Process lines
        tabs = line.split("\t")
        chrom = tabs[0]
        start = tabs[1]
        stop = tabs[2]
        dragen_cov = float(tabs[3])
        samtools_cov = float(tabs[20])
        diff = float(abs(dragen_cov - samtools_cov))

        # Calc. percent diff
        if dragen_cov + samtools_cov == 0:
            percent_diff = 0
        else:
            percent_diff = (diff / (dragen_cov + samtools_cov)) * 100
        if percent_diff > threshold:
            result = f"{chrom}:{start}-{stop}\t{dragen_cov}\t{samtools_cov}\t{percent_diff}\t{diff}"
            print(result)
