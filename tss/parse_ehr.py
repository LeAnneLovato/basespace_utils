#!/usr/bin/env python3
"""Extract info from the input EHR/ JSON file"""

##################################################################
# Author: LeAnne Lovato
# Email: llovato@illumina.com
# Extract sample and case information from the EHR JSON
# 1. Inputs: EHR JSON, output dir.
# 2. Outputs: TSS case JSON, TSS sample manifest,
# Notes:
##################################################################

import os
import json
import method_tools


def main(input_file, output_dir, config):
    """Extract info from the input EHR/ JSON file"""

    # check and format the output dir
    directory = method_tools.format_path(os.path.abspath(output_dir))

    # create logging file
    with open(directory + "parse_ehr.log", "w", encoding="UTF-8") as logfile:

        # logging
        logfile.write(f"Current Working Directory:\t{os.getcwd()}\n")
        logfile.write(f"Output Directory:\t{directory}\n")
        logfile.write(f"Log File:\t{logfile.name}\n")

        # open input
        with open(input_file, "r", encoding="UTF-8") as ehr:
            ehr_json = json.load(ehr)
            case_json = ehr_json["caseInfo"]

        # get the test
        test_name = ehr_json["quickStart"]["testName"]
        test_version = ehr_json["quickStart"]["test_version"]
        test_id, report_types = method_tools.get_test(test_name=test_name, test_version=test_version, config=config)

        case_json["testDefinitionId"] = test_id
        case_json["subjects"][0]["reportTypes"] = report_types

        # get sample
        proband = ehr_json["quickStart"]["externalSampleId"]["proband"]
        try:
            mother = ehr_json["quickStart"]["externalSampleId"]["mother"]
        except KeyError:
            pass
        try:
            father = ehr_json["quickStart"]["externalSampleId"]["father"]
        except KeyError:
            pass
        try:
            sibling = ehr_json["quickStart"]["externalSampleId"]["sibling"]
        except KeyError:
            pass

        for i in range(len(case_json["subjects"])):
            if case_json["subjects"][i]["relationshipToProband"] == "PROBAND":
                case_json["subjects"][i]["samples"][0]["externalSampleId"] = proband
            elif case_json["subjects"][i]["relationshipToProband"] == "MOTHER":
                case_json["subjects"][i]["samples"][0]["externalSampleId"] = mother
            elif case_json["subjects"][i]["relationshipToProband"] == "FATHER":
                case_json["subjects"][i]["samples"][0]["externalSampleId"] = father
            elif case_json["subjects"][i]["relationshipToProband"] == "SIBLING":
                case_json["subjects"][i]["samples"][0]["externalSampleId"] = sibling

        # write case json to file
        with open(directory + "case.json", "w", encoding="UTF-8") as case_json_file:
            case_json_file.write(json.dumps(case_json))

        # logging
        logfile.write(f"Case JSON Path:\t{os.path.abspath(case_json_file.name)}\n")
        logfile.write(f"Case JSON:\t{json.dumps(case_json)}")

    return case_json, os.path.abspath(case_json_file.name)
