#!/usr/bin/env python3
"""Extract indications form an existing case"""

##################################################################
# Author: LeAnne Lovato
# Email: llovato@illumina.com
# Get indications from a case
##################################################################

import json
import argparse
import method_tools
import case_mgt_v2


def get_args():
    """Get command line arguments"""
    parser = argparse.ArgumentParser(description="Extract indications from a case")

    # required for all pipelines
    parser.add_argument(
        "-c", "--config_file", help="Path to a TSS config file", type=str, required=True
    )
    parser.add_argument("-i", "--id", help="Enter a case GUID", type=str, required=True)

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    # Get user input
    arguments = get_args()
    case_id = arguments.id
    config_file = arguments.config_file

    # Parse config file
    config = method_tools.parse_config(config_file)

    # Get case
    case_response = case_mgt_v2.get_case(case_id, config)
    case_subjects = case_response["caseSubjects"]

    # Loop over case response
    for subject in case_subjects:
        relationship = subject["relationshipToProband"]
        indications = subject["phenotypes"]
        print(f"\n{relationship} indication(s):")

        print(json.dumps(indications))
