#!/usr/bin/env python3
"""Aggregates DRAGEN *_metric.csv files in the current directory"""

import glob
import os.path
import sys

##########################################
# Author: LeAnne Lovato
# GitHub: https://github.com/LeAnneLovato
##########################################


if __name__ == "__main__":
    # list metric files in the current path
    file_list = glob.glob("*/*_metrics.csv")

    # logging
    print(f"sampleId,info,sampleName,metric,value")

    # read metric files
    for metric_file in file_list:
        with open(metric_file, "r", encoding="utf-8") as file:
            data = file.readlines()
            sample_id = os.path.basename(metric_file).split("_")[1].split("-")[0]

        # determine id metric has percent colum
        for entry in enumerate(data):
            fields = entry[1].rstrip().split(",")
            if len(fields) == 4:

                # logging
                print(f"{sample_id},{fields[0]},{fields[1]},{fields[2]} (raw),{fields[3]}")
            elif len(fields) == 5:

                # logging
                print(f"{sample_id},{fields[0]},{fields[1]},{fields[2]} (%),{fields[4]}")
            else:
                sys.exit("Error reading number of fields")
