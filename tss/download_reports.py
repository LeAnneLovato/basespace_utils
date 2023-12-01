#!/usr/bin/env python3
"""Download TSS reports"""

###################################################################################################################
# Author: LeAnne Lovato
# Email: llovato@illumina.com
# Download report(s) for each case subject
# 1. Provide a list of caseIDs
# 2. Get the case
# 3. Extract the reportTypeId
# 4. Download reports for successfully processed cases: PDF (In Progress or Complete cases), JSON (Complete cases)
# 5. Create a pre case subject text file from the JSON report
###################################################################################################################

import os
import sys
import argparse
import json
import requests
from requests.exceptions import HTTPError
import method_tools


# get args
def get_args():
    """Get command line args"""

    parser = argparse.ArgumentParser(description="Download JSON and PDF Reports from TSS")
    parser.add_argument("-o","--output_dir",
        help="Path to save output log. Please specify a directory with no escapes or spaces in the name.",
        type=str,
        required=True,
    )
    parser.add_argument("-c", "--config_file",
        help="Path to JSON config file",
        type=str,
        required=True
    )
    parser.add_argument("-i", "--case_id",
        help="TSS case GUID",
        type=str,
        required=True
    )
    args = parser.parse_args()
    return args


# try API call (general)
def call_api(url, header):
    """Call DRS"""

    response = None
    try:
        response = requests.get(url, headers=header, timeout=30)
        response.raise_for_status()
    except HTTPError as http_err:
        print(f"[Error] HTTP error occurred: {http_err}")
    else:
        pass
    return response


# get case API call
def get_case(config_file, case_id, logfile):
    """Get the case"""

    # get request header from config_file fields
    config = method_tools.parse_config(config_file)
    header = method_tools.get_headers_apikey(
        config["apikey"], config["domain"], config["wg"]
    )

    logfile.write(f"\n\nget_case server response for case {case_id}:\n")

    # get case URL
    get_case_url = (
        f"https://{config['domain']}.{config['url']}/crs/api/v1/cases/{case_id}?directIdentifiers=false"
    )
    response = call_api(get_case_url, header)
    if response:
        logfile.write(response.text)
    return response.json()


# get pdf report API call
def get_pdf_report(config_file, case_id, subject_report_id, logfile):
    """Create a PDF report"""

    # get request header from config_file fields
    config = method_tools.parse_config(config_file)
    header = method_tools.get_headers_apikey(
        config["apikey"], config["domain"], config["wg"]
    )
    logfile.write(
        f"\n\nget_pdf_report server response for case {case_id}, report ID {subject_report_id}:\n"
    )

    # get reports URL
    get_report_url = (f"https://{config['domain']}.{config['url']}/drs/v1/draftreport/case/"
                      f"{case_id}/reports/{subject_report_id}/pdf")
    response = call_api(get_report_url, header)
    if response:
        logfile.write(str(response))

    return response


# get json report API call
def get_json_report(config_file, case_id, logfile):
    """Get the JSON report"""

    # get request header from config_file fields
    config = method_tools.parse_config(config_file)
    header = method_tools.get_headers_apikey(
        config["apikey"], config["domain"], config["wg"]
    )
    logfile.write(f"\n\nget_json_report server response for case {case_id}:\n")

    # get reports URL
    get_report_url = (
        f"https://{config['domain']}.{config['url']}:443/drs/v1/draftreport/case/{case_id}/json"
    )
    response = call_api(get_report_url, header)
    if response:
        logfile.write(response.text)
        return response.json()

    return None


# main runs automatically
if __name__ == "__main__":

    arguments = get_args()

    # check and format the output dir
    directory = method_tools.format_path(arguments.output_dir)

    # create output CSV: sampleID, JSON file path
    # create logfile in which to record API call responses
    with open(directory + "download_reports.log", "w", encoding="UTF-8") as log:

        # logging
        log.write(f"Current Working Directory:\t{os.getcwd()}")
        log.write(f"\nOutput Directory:\t{os.path.abspath(directory)}")
        log.write(f"\nConfig File:\t{os.path.abspath(arguments.config_file)}")

        # get case info
        case_payload = get_case(arguments.config_file, arguments.case_id, log)
        if case_payload is None:
            error = f"[ERROR] Case {arguments.case_id} does not exist; see log file for details."
            log.write(error)
            sys.exit()

        case_subjects = case_payload["caseSubjects"]
        display_id = case_payload["displayId"]
        case_status = case_payload["status"]
        case_substate = case_payload["subState"]
        activation_state = case_payload["activationState"]

        # logging
        log.write(f"Case ID:\t{arguments.case_id}")
        log.write(f"Case Display ID:\t{display_id}")
        log.write(f"Case Status:\t{case_status} - {case_substate}")
        log.write(f"Case Activation Status:\t{activation_state}")

        # check if case has been successfully processed
        if activation_state is None or activation_state == "INACTIVE":
            error = (
                f"[ERROR] Reports cannot be downloaded for an unprocessed, processing, or inactive case ; "
                f"please check case ID {arguments.case_id}"
            )
            log.write(f"{arguments.case_id},,{error}\n")
            sys.exit()

        # loop over case subjects
        for subject in case_subjects:
            # find the proband; script only supports pushing variants to report for proband
            if subject["relationshipToProband"] == "PROBAND":
                report_types = subject["reportTypes"]
                relationship = subject["relationshipToProband"]
                samples = subject["samples"]

                # find the active sample
                ACTIVE_ID = ""
                for sample in samples:
                    if sample["status"] == "ACTIVE":
                        ACTIVE_ID = sample["externalSampleId"]

                # logging
                log.write(f"Case Subject:\t{relationship}")
                log.write(f"Active Sample:\t{ACTIVE_ID}")

                # check if report(s) exist
                if report_types:

                    # loop over reports
                    for individual_report_id in report_types:
                        individual_report_id = individual_report_id["id"]

                        # download the latest PDF report
                        log.write(
                            f"Downloading PDF report(s):\t{relationship, individual_report_id}"
                        )
                        pdf_content = get_pdf_report(
                            arguments.config_file, arguments.case_id, individual_report_id, log)
                        if pdf_content:

                            # set report name
                            pdf_name = (
                                f"{display_id}_{relationship}_"
                                f"{ACTIVE_ID}_{individual_report_id}_latest.pdf"
                            )
                            with open(directory + pdf_name, "wb", encoding="UTF-8") as pdf_report:

                                # write content to report
                                pdf_report.write(pdf_content.content)
                                log.write(f"PDF Path:\t{os.path.abspath(pdf_report.name)}")
                        else:
                            error = (
                                f"[ERROR] Could not download PDF reports for the {relationship}; see log "
                                "file for details."
                            )
                            log.write(error)

                        # download the latest JSON report
                        log.write(
                            f"Downloading JSON report(s):\t{relationship, individual_report_id}"
                        )
                        json_response = get_json_report(arguments.config_file, arguments.case_id, log)

                        if json_response:
                            json_content = json_response["response"]

                            # set report name
                            with open(directory + f"{display_id}_latest.json", "w", encoding="UTF-8") as json_report:
                                json.dump(json_content, json_report, indent=2)
                                log.write(f"JSON Path:\t{os.path.abspath(json_report.name)}")
                        else:
                            error = (
                                f"[ERROR] Could not download json reports for the {relationship}; "
                                f"see log file for details."
                            )
                            log.write(error)
                else:
                    error = (
                        f"[ERROR] Report(s) do not exist for the {relationship}; "
                        "see log file for details."
                    )
                    log.write(error)
