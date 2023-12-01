#!/usr/bin/env python3
"""Post, Get Details, Get pre-signed URL(s), Update, QC Modify, QC Override, and Delete Case(s)"""

##################################################################
# Author 1: Batsal Devkota
# Author Email 1: bdevkota@illumina.com
# Author 2: LeAnne Lovato
# Author Email 2: llovato@illumina.com
# Case management in TSS
# 1. Posts (submits) and processes the cases
# 2. Update the status of the case
# 3. Delete case
# 4. Get presigned url for any file of interest, for easy exploration/sharing
# 5. Get details for a case
##################################################################

import os
import sys
import json
import argparse
import requests
from requests.exceptions import HTTPError
import method_tools

HOME = os.environ["HOME"]
CASE_SEARCH_URL = "/crs/api/v2/cases/search"


# Create Sample Dict
def read_case_csv(input_csv):
    """Read the input CSV and check the header"""

    with open(input_csv, "r", encoding="utf-8") as input_file:
        header = input_file.readline().lstrip("#").strip().split(",")  # read header

        # Commenting out and using familyID as default display ID
        # display_id_option = input("Do you want to use family_id as Case Display ID? (yes/no)")

        try:
            # Required items 0-5
            # Optional items - add any items below 6-13
            header_index = {
                "FamilyID": header.index("FamilyID"),
                "SampleID": header.index("SampleID"),
                "RelationshipToProband": header.index("RelationshipToProband"),
                "Affected": header.index("Affected"),
                "Sex": header.index("Sex"),
                "TestID": header.index("TestID"),
                "FirstName": header.index("FirstName"),
                "MiddleName": header.index("MiddleName"),
                "LastName": header.index("LastName"),
                "DOB": header.index("DOB"),
                "MRN": header.index("MRN"),
                "ReportID": header.index("ReportID"),
                "Indications": header.index("Indications"),
                "Tags": header.index("Tags"),
            }
        except ValueError:
            print(
                "Please provide an input csv with proper header. See resources/case folder for an example."
            )
            sys.exit()

        # create samples list
        file_lines = input_file.readlines()
        case_subjects = []
        for line in file_lines:
            if line.startswith(",") or line.isspace():
                pass
            else:
                case_subjects.append(line.strip())

    # create dict of samples
    sample_dict = {}
    for individual in case_subjects:
        subject_data = individual.split(",")
        family_id = subject_data[header_index["FamilyID"]]

        # create list for indications and tags
        indications = method_tools.indications_to_json(
            "code", subject_data[header_index["Indications"]]
        )  # optional
        tags = subject_data[header_index["Tags"]].strip().split(";")  # optional

        # pass parameters for sample as dictionary. All the samples within a family will be under familyID key.
        try:
            sample_dict[family_id].append(
                [
                    subject_data[header_index["SampleID"]],
                    subject_data[header_index["RelationshipToProband"]].upper(),
                    subject_data[header_index["FirstName"]] or "",  # optional
                    subject_data[header_index["MiddleName"]] or "",  # optional
                    subject_data[header_index["LastName"]] or "",  # optional
                    subject_data[header_index["MRN"]] or "",  # optional
                    subject_data[header_index["Sex"]],
                    subject_data[header_index["DOB"]] or "",  # optional
                    [subject_data[header_index["ReportID"]].strip()]
                    if subject_data[header_index["ReportID"]].strip()
                    else [],
                    indications if indications else [],
                    subject_data[header_index["Affected"]].strip(),
                    tags if tags else [],
                    subject_data[header_index["TestID"]],
                    family_id[0:12],  # take only the first 12 characters.
                ]
            )
        except KeyError:
            sample_dict[family_id] = [
                [
                    subject_data[header_index["SampleID"]],
                    subject_data[header_index["RelationshipToProband"]].upper(),
                    subject_data[header_index["FirstName"]] or "",  # optional
                    subject_data[header_index["MiddleName"]] or "",  # optional
                    subject_data[header_index["LastName"]] or "",  # optional
                    subject_data[header_index["MRN"]] or "",  # optional
                    subject_data[header_index["Sex"]],
                    subject_data[header_index["DOB"]] or "",  # optional
                    [subject_data[header_index["ReportID"]].strip()]
                    if subject_data[header_index["ReportID"]].strip()
                    else [],
                    indications if indications else [],
                    subject_data[header_index["Affected"]].strip(),
                    tags if tags else [],
                    subject_data[header_index["TestID"]],
                    family_id[0:12],  # take only the first 12 characters.
                ]
            ]

    return sample_dict


# Get Payload
def get_payload(sample_dict):
    """Create sample_dic={sample_id, firstname, lastname, mrn, sex, dob, reportid, json_indication}"""
    test_id = None
    tags = None
    display_id = None

    allsubjects = []
    for sample in enumerate(sample_dict):
        # Convert None values to empty strings
        test_id = sample[1][12]
        tags = sample[1][11]
        display_id = sample[1][13]

        subject = {
            "dateOfBirth": sample[1][7],
            "firstName": sample[1][2],
            "lastName": sample[1][3],
            "middleName": sample[1][4],
            "gender": sample[1][6],
            "mrn": sample[1][5],
            "isAffected": sample[1][10],
            "relationshipToProband": None,
            "phenotypes": sample[1][9],
            "reportTypes": sample[1][8],
            "samples": [{"externalSampleId": sample[1][0]}],
            "previousTestHistory": "",
            "medicalHistory": "",
            "familyHistory": "",
            "customPhenotypes": "",
            "hasResearchConsent": "NO",
            "allowDnaStorage": "NO",
        }
        allsubjects.append(subject)

        # Check relationship
        # for relationship "Other", otherRelationshipToProband is mandatory, relationship provided after
        if sample[1][1].startswith("O") or sample[1][1].startswith("o"):
            otherinfo = sample[1][1].split(";")
            subject.update({"relationshipToProband": otherinfo[0]})
            subject.update({"otherRelationshipToProband": otherinfo[1]})
        else:
            subject.update({"relationshipToProband": sample[1][1]})

    # Create case payload dict
    payload = {
        "subjects": allsubjects,
        "testDefinitionId": test_id,
        "tags": tags,
        "displayId": display_id,
        "phi": {"summary": ""},
    }
    return payload


# Post Case
def post_case(payload, config, output_dir):
    """Post a case"""

    # Change relationshipToProband to uppercase to fix Emedgene issue
    for i in range(len(payload["subjects"])):
        payload["subjects"][i]["relationshipToProband"] = payload["subjects"][i][
            "relationshipToProband"
        ].upper()

    directory = method_tools.format_path(os.path.abspath(output_dir))
    with open(directory + "post_case.log", "w", encoding="utf-8") as logfile:
        # Request inputs
        response = None
        url_post = f"https://{config['domain']}.{config['url']}/crs/api/v1/cases?forceOverwrite=false"

        headers = method_tools.get_headers_apikey(
            config["apikey"], config["domain"], config["wg"]
        )

        print("Attempting to POST case.")
        logfile.write("Attempting to post case...")

        print(f"Request URL:\t{url_post}")
        logfile.write(f"\nRequest URL:\t{url_post}")

        print(f"Payload:\t{json.dumps(payload)}")
        logfile.write(f"\nPayload:\t{json.dumps(payload)}")

        # Post case
        logfile.write("\n\npost_case server response:\n")
        try:
            response = requests.post(
                url_post, headers=headers, data=json.dumps(payload), timeout=30
            )

            # If the response was successful, no Exception will be raised
            response.raise_for_status()

        # Error posting case
        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            logfile.write(f"HTTP error occurred: {http_err}\n")

            # calls error messaging function in method tools
            if response.text:
                method_tools.error_messaging(response.text)
                logfile.write(response.text)
            print(
                "Exiting, case ingestion failed. Please check the logs for detailed error message."
            )
            sys.exit()

        # No errors
        else:
            if response.status_code == 201:
                if response.text:
                    family_size = len(payload["subjects"])
                    logfile.write(response.text)
                    display_id = response.json()["displayId"]
                    case_guid = response.json()["id"]

                    print("Case created!")
                    logfile.write(
                        f"\nCase created with Display ID: {display_id} and GUID: {case_guid}"
                    )
                    print(f"Case Display ID:\t{display_id}")
                    print(f"Case GUID:\t{case_guid}")
                    print(f"Pedigree Size:\t{family_size}")
                    return response.json()

            # Error posting case
            print("Unknown error occurred. Exiting, case ingestion failed.")
            logfile.write("Unknown error occurred. Exiting, case ingestion failed.\n")
            sys.exit()


# Process Case
def process_case(case_guid, config, output_dir):
    """Process a case"""
    directory = method_tools.format_path(os.path.abspath(output_dir))
    with open(directory + "process_case.log", "w", encoding="utf-8") as logfile:
        url_post = f"https://{config['domain']}.{config['url']}/crs/api/v1/cases"
        url_process = url_post + "/" + case_guid + "/process"
        headers = method_tools.get_headers_apikey(
            config["apikey"], config["domain"], config["wg"]
        )

        print(f"Attempting to  process the case, {case_guid}")
        logfile.write(f"\nAttempting to process the case, {case_guid}")

        print(f"Request URL:\t{url_process}")
        logfile.write(f"\nRequest URL:\t{url_process}")

        # Process case
        logfile.write("\n\nprocess_case server response:\n")
        try:
            response = requests.post(url_process, headers=headers, timeout=30)

            # If the response was successful, no Exception will be raised
            response.raise_for_status()

        # Error processing case
        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            logfile.write(f"HTTP error occurred: {http_err}")
            print(
                "Exiting, case processing failed. Please check logs for detailed error message."
            )
            sys.exit()

        # No errors
        else:
            if response.status_code == 200:
                # no server response if successful; nothing to write to logfile
                print("Case is now processing!\n")
                logfile.write(f"Case {case_guid} is now processing.")
            else:
                # Error processing case
                print("Unknown error occurred. Exiting, case ingestion failed.")
                sys.exit()


# Get Case
def get_case(case_guid, config):
    """Get case"""

    # Get case inputs
    headers = method_tools.get_headers_apikey(
        config["apikey"], config["domain"], config["wg"]
    )
    get_url = f"https://{config['domain']}.{config['url']}/crs/api/v1/cases/{case_guid}?directIdentifiers=false"

    # Get case by GUID
    try:
        response = requests.get(get_url, headers=headers, timeout=30)

    # Error getting case
    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print("Exiting, failed to get the case.")
        sys.exit()

    # No errors
    else:
        if response.status_code == 200:
            if response.text:
                # print("Case found!")
                return response.json()

        # Error getting case
        print("Unknown error occurred. Exiting, failed to get the case.")
        sys.exit()


# Get Case Details
def get_case_details(case_guid, config, list_out_files=False):
    """Get specific case details"""
    case_json = get_case(case_guid, config)

    # Print select case details
    print(f"Case ID:\t{case_json['id']}")
    print(f"Case Display ID:\t{case_json['displayId']}")
    print(f"Created Date:\t{case_json['createdDate']}")
    print(f"Test ID:\t{case_json['testDefinition']['id']}")
    print(f"Test Name:\t{case_json['testDefinition']['name']}")
    print(
        f"Reference Genome Build:\t{case_json['testDefinition']['secondaryAnalysis']['referenceGenomeBuild']}"
    )
    print(
        f"Workflow Name:\t{case_json['testDefinition']['secondaryAnalysis']['workflowName']}"
    )
    print(f"Status:\t{case_json['status']}")
    print(f"Sub State:\t{case_json['subState']}")

    # Loops through the input fastq files
    if case_json["subState"] not in [
        "MISSING_SAMPLE_INFORMATION",
        "AWAITING_MOLECULAR_DATA",
    ]:
        for subjects in case_json["caseSubjects"]:
            path = (
                os.path.dirname(
                    subjects["activeSample"]["molecularData"][0]["fastqLink"]
                )
                + "/"
            )
            get_presigned_url(path, config)

    # Print output files when available
    if list_out_files:
        try:
            ingestion = json.loads(case_json["ingestionResult"])

        # Error getting output files
        except TypeError:
            print("Analysis results do not exist (yet)")

        # No errors
        else:
            print("\nOutput files from analysis:")

            # Gets the links to the outputFiles.
            volume = ingestion["result"]["analysisInfo"]["outputVolume"]
            folder = ingestion["result"]["analysisInfo"]["outputFolder"]
            path = f"gds://{volume}{folder}"
            get_presigned_url(path, config)


# Get Pre-signed URL
def get_presigned_url(filepath, config):
    """Get pre-signed URL(s) for a GDS path"""

    # Get presigned URLs inputs
    headers = method_tools.get_headers_apikey(
        config["apikey"], config["domain"], config["wg"]
    )
    url_request = (
        f"https://{config['domain']}.{config['url']}/crs/api/v1/files?"
        f"includePresignedUrl=true&matchExactPath=false&path={filepath}"
    )

    print(f"Attempting to GET files under, {filepath}")
    print(f"Request URL:\t{url_request}")

    # Get presigned URLs
    try:
        response = requests.get(url_request, headers=headers, timeout=30)
        # If the response was successful, no Exception will be raised
        response.raise_for_status()

    # Error getting presigned URLs
    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # Python 3.6
        print("Exiting.")
        sys.exit()

    # No errors
    else:
        # If the response was successful, no Exception will be raised
        if response.status_code == 200:
            if response.json():
                # Loop over output files
                for i in range(len(response.json())):
                    print(f"Path:\t{response.json()[i]['path']}")
                    print(f"Pre-signed URL:\t{response.json()[i]['preSignedUrl']}")

        # path may not exist in wg/ domain
        else:
            print(
                f"Files do not exist for the domain ({config['domain']}), workgroup ({config['wg']}), "
                f"or file path ({filepath}) combination requested"
            )
            print(f"Response:\t{response.text}")


# Get CaseID
def get_case_id(display_id, config):
    """Get case guid"""
    # Get caseId inputs

    headers = method_tools.get_headers_apikey(
        config["apikey"], config["domain"], config["wg"]
    )
    get_url = f"https://{config['domain']}.{config['url']}{CASE_SEARCH_URL}?displayId={display_id}"
    print(f"Attempting to GET the case by display ID, {display_id}")
    print(f"Request URL:\t{get_url}")

    # Get case by displayId
    try:
        response = requests.get(get_url, headers=headers, timeout=30)

        # If the response was successful, no Exception will be raised
        response.raise_for_status()

    # Error getting case
    except HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # Python 3.6
        print("Exiting.")
        sys.exit()

    # No errors
    else:
        if response.status_code == 200:
            if response.json()["content"]:
                for i in range(len(response.json()["content"])):
                    if response.json()["content"][i]["displayId"] == display_id:
                        return response.json()["content"][i]["id"]

        # Error getting case ID
        print(f"Case with {display_id} does not exist!!")
        sys.exit()


# Override QC Status
def qc_override_case(case_guid, config):
    """QC override case"""
    # QC override inputs
    headers = method_tools.get_headers_apikey(
        config["apikey"], config["domain"], config["wg"]
    )
    url_override = f"https://{config['domain']}.{config['url']}/crs/api/v1/cases/{case_guid}/qc-actions?action=override"
    print(f"Attempting to QC override the case, {case_guid}")
    print(f"Request URL:\t{url_override}")

    # QC override case
    response = requests.post(url_override, headers=headers, timeout=30)

    # Case QC override
    if response.status_code == 200:
        print(
            "QC warning overridden! Case status has been moved to In PROGRESS - PROCESSING"
        )
        print(response.json()["message"])

    # Error overriding case
    elif response.status_code == 400:
        print(response.json()["code"])
        print(response.json()["message"])
        sys.exit()

    # Error overriding case
    else:
        print(response.json()["message"])
        sys.exit()


# Modify QC Status
def qc_modify_case(case_guid, config):
    """QC modify case"""
    # QC modify inputs
    headers = method_tools.get_headers_apikey(
        config["apikey"], config["domain"], config["wg"]
    )
    url_modify = f"https://{config['domain']}.{config['url']}/crs/api/v1/cases/{case_guid}/qc-actions?action=modify"
    print(f"Attempting to QC modify the case, {case_guid}")
    print(f"Request URL:\t{url_modify}")

    # QC modify case
    response = requests.post(url_modify, headers=headers, timeout=30)

    # QC modify
    if response.status_code == 200:
        print("QC warning modified. Case status has been moved to HAS - ISSUE")
        print(response.json()["message"])

    # Error modifying case
    elif response.status_code == 400:
        print(response.json()["code"])
        print(response.json()["message"])
        sys.exit()

    # Error modifying case
    else:
        print(response.json()["message"])
        sys.exit()


# DELETE Case
def delete_case(case_guid, config):
    """Delete case"""
    # Delete case inputs

    headers = method_tools.get_headers_apikey(
        config["apikey"], config["domain"], config["wg"]
    )

    url_delete = f"https://{config['domain']}.{config['url']}/crs/api/v1/cases/{case_guid}?force=true"

    print(f"Attempting to delete the case, {case_guid}")
    print(f"Request URL:\t{url_delete}")

    # Delete case
    response = requests.delete(url_delete, headers=headers, timeout=30)

    # Case deleted
    if response.status_code == 204:
        print("Case deleted!")

    # Error deleting case
    elif response.status_code == 400:
        print(response.json()["code"])
        print(response.json()["message"])

    # Error deleting case
    else:
        print(response.json()["message"])


# Update Case
def update_case(case_guid, data, config_dict):
    """Update case"""

    # Update case inputs
    headers = method_tools.get_headers_apikey(
        config_dict["apikey"], config_dict["domain"], config_dict["wg"]
    )
    url_update = f"https://{config_dict['domain']}.{config_dict['url']}/crs/api/v1/cases/{case_guid}?force=false"
    print(f"Attempting to update the case, {case_guid}")
    print(f"Request URL:\t{url_update}")

    # Update case
    response = requests.put(
        url_update, data=json.dumps(data), headers=headers, timeout=30
    )

    # Case updated
    if response.status_code == 200:
        print("Case updated!")

    # Error updating case
    else:
        print(f"[ERROR] {response.text}")
        sys.exit()


def modify_case_json(get_response, input_json):
    """Update the case json"""
    case_guid = get_response["id"]
    # Check case status - complete cases cannot be edited
    if get_response["status"] == "Complete":
        print(
            f"[ERROR] unable to edit a Complete case ({case_guid}). "
            "Please 'Edit Report(s)' before updating a complete case."
        )
        sys.exit()
    if get_response["subState"] == "QC_WARNING":
        print(
            "[ERROR] unable to edit a QC Warning case. Please 'QC Override' or 'QC Modify' "
            f"the case ({case_guid}) before updating a QC Warning case."
        )
        sys.exit()

    # Loop over get case response
    case_subjects = get_response["caseSubjects"]
    for subject in enumerate(case_subjects):
        # Get ids from get case response
        subject_guid = subject[1]["id"]
        relationship = subject[1]["relationshipToProband"]
        active_external_sample_id = subject[1]["activeSample"]["externalSampleId"]
        active_sample_guid = subject[1]["activeSample"]["id"]

        # Loop over input subject data
        original_subjects = input_json["subjects"]
        for og_subject in enumerate(original_subjects):
            # Loop over original sample data
            og_relationship = og_subject[1]["relationshipToProband"]
            original_sample = og_subject[1]["samples"]
            for og_sample in enumerate(original_sample):
                # Find the correct subject/ sample to update
                og_external_sample_id = og_sample[1]["externalSampleId"]
                if (
                    og_external_sample_id == active_external_sample_id
                    and og_relationship == relationship
                ):
                    # Add the ids and activeSample
                    input_json["subjects"][og_subject[0]]["id"] = subject_guid
                    input_json["subjects"][og_subject[0]]["samples"][0][
                        "id"
                    ] = active_sample_guid
                    input_json["subjects"][og_subject[0]]["samples"][0][
                        "status"
                    ] = "ACTIVE"
    return input_json


def get_args():
    """Get input arguments"""
    # Create the parser
    parser = argparse.ArgumentParser()

    # Add an argument
    parser.add_argument("-c", "--configFile", type=str, required=False)
    parser.add_argument(
        "-n",
        "--optionName",
        choices=[
            "post_case",
            "qc_override",
            "qc_modify",
            "get_case_details",
            "delete_case",
            "get_presigned_url",
            "update_case",
        ],
        help="""Command to execute""",
        required=True,
    )
    parser.add_argument(
        "-i",
        "--input_file",
        help="Specify an input CSV file with sample info",
        type=str,
        required=False,
    )
    parser.add_argument(
        "-j",
        "--input_json",
        help="Specify an input JSON file (required for update case "
        "and optional for post_case)",
        type=str,
        required=False,
    )
    parser.add_argument(
        "-d",
        "--display_id",
        help="Specify a case display ID (required for qc_override, qc_modify, "
        "get_case_details, delete_case, "
        "and update_case with a json (-j/--input_json))",
        type=str,
        required=False,
    )
    parser.add_argument(
        "-lo",
        "--list_outfiles",
        help="List analysis files when get_case_details is applied",
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-fp",
        "--file_path",
        help="Specify a complete GDS file path" "(required for -n get_presigned_url)",
        type=str,
        required=False,
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        help="Specify a directory for log files (required for post_case, and update_case)",
        type=str,
        required=False,
    )
    # Parse the argument
    args = parser.parse_args()
    return args


# Main
if __name__ == "__main__":
    arguments = get_args()

    # Check whether output directory was supplied (post_case, process_case and get_pre_singed_urls)
    # Will check the validity of directory path in the functions themselves, not in main function
    if (
        arguments.optionName
        in ["post_case", "process_case", "get_presigned_url", "update_case"]
        and not arguments.output_dir
    ):
        print(
            "[ERROR] For post_case, process_case, and update_case you must specify an output "
            "directory (-o, --output_dir)"
        )
        sys.exit()

    # Check for a case display ID in the ARGV
    if (
        arguments.optionName
        in ["qc_override", "qc_modify", "get_case_details", "delete_case"]
        and not arguments.display_id
    ):
        print(
            "[ERROR] For qc_override, qc_modify, get_case_details, and delete_case you must specify a "
            "case display ID (-d, --display_id)"
        )
        sys.exit()

    # Check for a filepath in the ARGV
    if arguments.optionName in ["get_presigned_url"] and not arguments.file_path:
        print(
            "[ERROR] For get_presigned_url, you must specify a GDS file path (-fp, --file_path)"
        )
        sys.exit()

    # Check post_case inputs
    if (
        arguments.optionName in ["post_case"]
        and not arguments.input_file
        and arguments.optionName in ["post_case"]
        and not arguments.input_json
    ):
        print(
            "[ERROR] post_case requires either an (1) -i/--input_file or (2) -j--input_json"
        )
        sys.exit()

    # Check update_case inputs for csv mode
    if (
        arguments.optionName in ["update_case"]
        and not arguments.input_file
        and arguments.optionName in ["update_case"]
        and not arguments.input_json
    ):
        print(
            "[ERROR] update_case requires either an (1) -i/--input_file or (2) -j/--input_json"
        )
        sys.exit()

    # check update_case inputs for json mode
    if (
        arguments.optionName in ["update_case"]
        and arguments.input_json
        and not arguments.display_id
    ):
        print(
            "[ERROR] update_case requires either an (1) -i/--input_file or -j/--input_json and (2) -d/--display_id"
        )
        sys.exit()

    # Get config_file
    # Default config file path
    configFile = arguments.configFile or HOME + "/.illumina/uploader-config.json"
    method_tools.check_path(configFile)
    configuration = method_tools.parse_config(configFile)

    # Post case
    if arguments.optionName == "post_case":
        output_directory = method_tools.format_path(
            os.path.abspath(arguments.output_dir)
        )

        # Get input csv file
        if arguments.input_file:
            sample_dictionary = read_case_csv(arguments.input_file)

            # Getting payload for each case/ family. This makes sure that a case is ingested per family
            for case in sample_dictionary.items():
                case_data = get_payload(case[1])
                pedigree_size = len(case[1])
                if pedigree_size > 5:
                    print(
                        f"Exiting, the family size {pedigree_size} is larger than five."
                    )
                    sys.exit()
                post_case_response = post_case(
                    case_data, configuration, arguments.output_dir
                )
                case_id = post_case_response["id"]
                process_case(case_id, configuration, arguments.output_dir)

                # Save case JSON to file
                with open(
                    output_directory + f"{case[0].upper()}.json", "w", encoding="utf-8"
                ) as outjson:
                    outjson.write(json.dumps(case_data))

        # Get input json file
        elif arguments.input_json:
            with open(arguments.input_json, "r", encoding="utf-8") as file:
                case_data = json.load(file)

            # Post & process the case
            post_case_response = post_case(
                case_data, configuration, arguments.output_dir
            )
            case_id = post_case_response["id"]
            process_case(case_id, configuration, arguments.output_dir)

    # QC override case
    elif arguments.optionName == "qc_override":
        case_id = get_case_id(arguments.display_id.upper(), configuration)
        qc_override_case(case_id, configuration)

    # QC modify case
    elif arguments.optionName == "qc_modify":
        case_id = get_case_id(arguments.display_id.upper(), configuration)
        qc_modify_case(case_id, configuration)

    # Delete case
    elif arguments.optionName == "delete_case":
        cases_to_delete = arguments.display_id.split(",")
        for case in cases_to_delete:
            case_id = get_case_id(case.upper(), configuration)
            delete_case(case_id, configuration)

    # Get files
    elif arguments.optionName == "get_presigned_url":
        output_directory = method_tools.format_path(
            os.path.abspath(arguments.output_dir)
        )
        get_presigned_url(arguments.file_path, configuration)

    # Get select case details
    elif arguments.optionName == "get_case_details":
        case_id = get_case_id(arguments.display_id.upper(), configuration).upper()
        get_case_details(case_id, configuration, arguments.list_outfiles)

    # Update case
    elif arguments.optionName == "update_case":
        output_directory = method_tools.format_path(
            os.path.abspath(arguments.output_dir)
        )

        # CSV input
        if arguments.input_file:
            sample_dictionary = read_case_csv(arguments.input_file)

            # Getting payload for each case/ family. This makes sure that a case is ingested per family
            for case in sample_dictionary.items():
                case_data = get_payload(case[1])

                # Get the case id and get case
                case_id = get_case_id(case[0].upper(), configuration)
                get_case_response = get_case(case_id, configuration)

                # Add sample id(s), subject id(s), and sample status to json
                modified_case_data = modify_case_json(get_case_response, case_data)

                # Update the case
                update_case(case_id, modified_case_data, configuration)

                # Write updated json to file
                with open(
                    output_directory + f"{case[0].upper()}_update_case.json",
                    "w",
                    encoding="utf-8",
                ) as output:
                    output.write(json.dumps(modified_case_data) + "\n")
                    print(f"Updated Case JSON:\t{os.path.abspath(output.name)}")

        # Case json input
        if arguments.input_json:
            # Open the case_json
            with open(arguments.input_json, "r", encoding="utf-8") as file:
                case_data = json.load(file)

            # Get the case id and get case
            case_id = get_case_id(arguments.display_id.upper(), configuration)
            get_case_response = get_case(case_id, configuration)

            # Add sample id(s), subject id(s), and sample status to json
            modified_case_data = modify_case_json(get_case_response, case_data)

            # Update the case
            update_case(case_id, modified_case_data, configuration)

            # Write updated json to file
            with open(
                output_directory + f"{arguments.display_id}_update_case.json",
                "w",
                encoding="utf-8",
            ) as output:
                output.write(json.dumps(modified_case_data) + "\n")
                print(f"Updated Case JSON:\t{os.path.abspath(output.name)}")
