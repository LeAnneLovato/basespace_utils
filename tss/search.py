#!/usr/bin/env python3
"""Search for TSS cases"""

##################################################################
# Author 1: Batsal Devkota
# Author Email 1: bdevkota@illumina.com
# Author 2: LeAnne Lovato
# Author Email 2: llovato@illumina.com
# Search the workgroup in config within TSS
# 1. Search 'displayId', 'externalSampleId', 'externalSampleName', 'lastname', 'mrn','status',
#    'subState','tags','testDefinitionId'
# 2. Need to provide both search term and search txt for it to display output
##################################################################

import os
import sys
import argparse
import textwrap
import requests
from requests.exceptions import HTTPError
import method_tools

HOME = os.environ["HOME"]
SEARCH_URL = "/crs/api/v2/cases/search"

""""
Name	Type 	Description
displayId 	string	Allows partial search e.g. ILM-ABC-234, ABC, 234 will include ILM-ABC-234 in result
externalSampleId	string	External SampleId of the case. Allows partial search e.g. ILM-ABC-234, ABC, 234 will include
ILM-ABC-234 in result
externalSampleName	string	Sample Name of the sample. Allows partial search e.g. ILM-ABC-234, ABC, 234 will include
ILM-ABC-234 in result
id 	string	Allows partial search of caseId e.g. dc25cd92-78e0-11e8-adc0-fa7ae01bbebc, 11e8, fa7ae01bbebc will include
dc25cd92-78e0-11e8-adc0-fa7ae01bbebc in result
lastname	string	Lastname of patient. Must be exact match
mrn 	string	MRN of patient. Must be exact match
status 	string	Case Status: Draft, New, In Progress, Complete, Canceled, Deletion
subState	string	Case SubState: MISSING_SAMPLE_INFORMATION, PROCESSING, HAS_ISSUE, AWAITING_MOLECULAR_DATA,
READY_FOR_INTERPRETATION, READY_FOR_REVIEW, REPORTS_AVAILABLE, READY_FOR_PROCESSING, QC_WARNING,
FAILED_TO_ADD_VIRTUAL_VARIANT, FAILED_TO_PROCESS_PATHOGENICITY_UPDATE, FAILED_TO_PROCESS_PHENOTYPE_OVERLAP,
DELETION_IN_PROGRESS, DELETION_HAS_ISSUE, CLOSED
tags array[string]	Tag names associated with the case. XXX NOT YET XXXX Allows partial search e.g. rug would give
result for rugd, rugd_disease etc
testDefinitionId	string	Allows partial search of testDefinitionId e.g. dc25cd92-78e0-11e8-adc0-fa7ae01bbebc, 11e8,
fa7ae01bbebc will include dc25cd92-78e0-11e8-adc0-fa7ae01bbebc in result
"""


# Search
def search(option, search_term, config_dict):
    """search for cases"""
    # print("Attempting to search for cases")

    # Get headers
    headers = method_tools.get_headers_apikey(
        config_dict["apikey"], config_dict["domain"], config_dict["wg"]
    )
    url = f"https://{config_dict['domain']}.{config_dict['url']}{SEARCH_URL}?{option}={search_term}"

    # print(f"Request URL:\t{url}")
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

    # If the response was successful, no Exception will be raised
    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # Python 3.6
        print("Exiting.")
        sys.exit()
    except Exception as err:
        print(f"Other error occurred: {err}")  # Python 3.6
        sys.exit()
    else:
        if response.json()["content"]:
            return response.json()
        print(f"Cases matching {option} {search_term} cannot be found!!")
        return response.text


def parse_search_response(search_response):
    """Parse the search response"""
    if search_response:
        for case in search_response["content"]:
            print("Case ID:", case["id"])
            print("Display ID:", case["displayId"])
            print("Status:", case["status"])
            print("Substate:", case["subState"], "\n")


if __name__ == "__main__":
    # Create the parser
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    # Add an argument
    parser.add_argument(
        "-c", "--configFile", help="Path to a TSS config file", type=str, required=False
    )
    parser.add_argument(
        "-s",
        "--searchTerm",
        help="search term for specific name",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-n",
        "--searchName",
        choices=[
            "displayId",
            "externalSampleId",
            "externalSampleName",
            "id",
            "mrn",
            "status",
            "subState",
            "tags",
            "testDefinitionId",
        ],
        help=textwrap.dedent(
            """
        displayId [string]\tAllows partial search e.g. ILM-ABC-234, ABC, 234 will include ILM-ABC-234 in result
        externalSampleId [string]\tExternal SampleId of the case. Must be exact match
        externalSampleName [string]\tSample Name of the sample. Must be exact match
        id [string]\tAllows partial search of caseId e.g. dc25cd92-78e0-11e8-adc0-fa7ae01bbebc, 11e8,
        \t\tfa7ae01bbebc will include dc25cd92-78e0-11e8-adc0-fa7ae01bbebc in result
        mrn [string]\tMRN of patient. Must be exact match
        status [string]\tCase Status: Draft, New, In Progress, Complete, Canceled, Deletion
        subState [string]\tCase SubState: MISSING_SAMPLE_INFORMATION, PROCESSING, HAS_ISSUE, AWAITING_MOLECULAR_DATA,
        \t\tREADY_FOR_INTERPRETATION, READY_FOR_REVIEW, REPORTS_AVAILABLE, READY_FOR_PROCESSING, QC_WARNING,
        \t\tFAILED_TO_ADD_VIRTUAL_VARIANT, FAILED_TO_PROCESS_PATHOGENICITY_UPDATE, FAILED_TO_PROCESS_PHENOTYPE_OVERLAP,
        \t\tDELETION_IN_PROGRESS, DELETION_HAS_ISSUE, CLOSED
        tags [array (string)]\tTag names associated with the case. Must be exact match. Can enter a single tag
        \t\t(--s "exome") or a comma-separated list (--s "exome,GRCh38")
        testDefinitionId [string]\tAllows partial search of testDefinitionId e.g.
        \t\tdc25cd92-78e0-11e8-adc0-fa7ae01bbebc, 11e8, fa7ae01bbebc will include dc25cd92-78e0-11e8-adc0-fa7ae01bbebc
        \t\tin result)"""
        ),
        required=True,
    )

    # Parse the argument
    args = parser.parse_args()

    # Get config_file
    # default config file path
    configFile = args.configFile or HOME + "/.illumina/uploader-config.json"
    config = method_tools.parse_config(configFile)

    # Search by search term #
    term = args.searchTerm
    name = args.searchName

    # searching by tags array
    if name == "tags":
        # strip any whitespace around items in the tags array
        tags = [entry.strip() for entry in term.split(",")]
        TAGS_TERMS = "&tags=".join(tags)

        # perform search
        search_results = search(name, TAGS_TERMS, config)
        parse_search_response(search_results)

    # searching by any other type of search term
    else:
        # check that status is valid
        if name == "status":
            if term not in [
                "Draft",
                "New",
                "In Progress",
                "Complete",
                "Canceled",
                "Deletion",
            ]:
                print(
                    "Invalid status; must be one of 'Draft', 'New', 'In Progress', 'Complete', 'Canceled', 'Deletion'"
                )
                sys.exit()

        # check that subState is valid
        if name == "subState":
            if term not in [
                "MISSING_SAMPLE_INFORMATION",
                "PROCESSING",
                "HAS_ISSUE",
                "AWAITING_MOLECULAR_DATA",
                "READY_FOR_INTERPRETATION",
                "READY_FOR_REVIEW",
                "REPORTS_AVAILABLE",
                "READY_FOR_PROCESSING",
                "QC_WARNING",
                "FAILED_TO_ADD_VIRTUAL_VARIANT",
                "FAILED_TO_PROCESS_PATHOGENICITY_UPDATE",
                "FAILED_TO_PROCESS_PHENOTYPE_OVERLAP",
                "DELETION_IN_PROGRESS",
                "DELETION_HAS_ISSUE",
                "CLOSED",
            ]:
                print(
                    "Invalid subState: must be one of 'MISSING_SAMPLE_INFORMATION', 'PROCESSING', 'HAS_ISSUE', '"
                    "AWAITING_MOLECULAR_DATA', 'READY_FOR_INTERPRETATION', 'READY_FOR_REVIEW','REPORTS_AVAILABLE', "
                    "'READY_FOR_PROCESSING', 'QC_WARNING', 'FAILED_TO_ADD_VIRTUAL_VARIANT', "
                    "'FAILED_TO_PROCESS_PATHOGENICITY_UPDATE', 'FAILED_TO_PROCESS_PHENOTYPE_OVERLAP', "
                    "'DELETION_IN_PROGRESS', 'DELETION_HAS_ISSUE', 'CLOSED'"
                )
                sys.exit()

        # perform search
        search_results = search(name, term, config)
        parse_search_response(search_results)
