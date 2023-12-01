#!/usr/bin/env python3
"""Delete case ID or list of case IDs"""

#######################################################################################
# Author: LeAnne Lovato
# Email: llovato@illumina.com
# Delete cases
# 1. Provide a list of caseIDs
# 2. Delete the case
#######################################################################################

import os
import sys
import argparse
import pandas as pd
import method_tools
import case_mgt_v2

HOME = os.environ["HOME"]


# get args
def get_args():
    """Get input arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-g",
        "--case_guid",
        help="Case GUID (example: 3796601f-9ee9-45c9-80ae-e2f5aee5d2f3, "
        "https://tss-test.trusight.illumina.com/cmp/cases/case/"
        "3796601f-9ee9-45c9-80ae-e2f5aee5d2f3)",
        type=str,
        default=None,
    )
    parser.add_argument(
        "-i",
        "--input_file",
        help="Input file with case GUIDs are required (example: "
        "3796601f-9ee9-45c9-80ae-e2f5aee5d2f3, "
        "https://tss-test.trusight.illumina.com/cmp/cases/case/"
        "3796601f-9ee9-45c9-80ae-e2f5aee5d2f3)",
        type=str,
        default=None,
    )
    parser.add_argument(
        "-o", "--output_dir", help="Path to write CSV log file", type=str, required=True
    )
    parser.add_argument(
        "-c",
        "--config_file",
        help="Provide a TSS CLI config file. Default ~/.illumina/uploader-config.json",
        type=str,
        default=f"{HOME}/.illumina/uploader-config.json",
    )
    args = parser.parse_args()
    return args


# main runs automatically
if __name__ == "__main__":
    # get args
    arguments = get_args()

    # check and format the output dir
    directory = method_tools.format_path(arguments.output_dir)

    # get the config file and create request header
    config = method_tools.parse_config(arguments.config_file)

    # logging
    print(f"Current Working Directory:\t{os.getcwd()}")
    print(f"Output Directory:\t{directory}")
    print(f"Config File:\t{arguments.config_file}")

    # single sample mode
    if arguments.case_guid and not arguments.input_file:
        # logging
        print("Running Single Case Mode:\n")

        # create data frame
        df = pd.DataFrame(data={"sampleId": [arguments.case_guid]})

    # batch Mode
    elif arguments.input_file and not arguments.case_guid:
        # logging
        print("Running Batch Case Mode:")
        print(f"Input File:\t{os.path.abspath(arguments.input_file)}")

        # create data frame
        df = pd.read_csv(arguments.input_file)

    # exit when args are conflicting
    else:
        print("Exiting...")
        print("Expected Options (1) or (2):")
        print("(1) -g/ --caseGuid")
        print("(2) -i/ --input")
        sys.exit()

    # loop over input
    for index, row in df.iterrows():
        # case GUID
        case_id = row[0]
        print(f"Deleting Case GUID:\t{case_id}")
        case_mgt_v2.delete_case(case_id, config)
