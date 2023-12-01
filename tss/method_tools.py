#!/usr/bin/env python3
"""Commonly used functions in TSS case and sample pipelines"""

############################################################################################
# Author 1: Batsal Devkota
# Author Email 1: bdevkota@illumina.com
# Author 2: LeAnne Lovato
# Author Email 2: llovato@illumina.com
# Author 3: Jennifer Shah
# Author Email 3: jshah@illumina.com
# A set of helper functions to get header fields for various API calls
############################################################################################

import os
import subprocess
import json
import sys


# get header with an APIKEY
def get_headers_apikey(apikey, domain_name, wg):
    """Construct API key header"""

    headers = {
        "accept": "*/*",
        "content-type": "application/json",
        "X-Auth-Token": "apikey {apikey}".format(apikey=apikey),
        "X-ILMN-Domain": "{domain_name}".format(domain_name=domain_name),
        "X-ILMN-Workgroup": "{wg}".format(wg=wg),
    }
    return headers


# format the directory path
def format_path(path):
    """Add trailing backslash when needed"""

    if path.endswith("/"):
        pass
    else:
        path = path + "/"
    return path


# run a shell command and return stdout
def run_shell_with_pipe(command):
    """Run shell command with stream"""

    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True) as process:
        stdout = process.stdout.read().splitlines()
        stderr = process.stderr.read().splitlines()

        # clean up
        process.kill()
        process.wait()
        process.stdout.close()
        process.stderr.close()
    return stdout, stderr


# run a shell command and return stdout
def run_shell_with_screen(command):
    """Run shell to screen"""

    with subprocess.Popen(command, shell=True) as process:
        process.wait()
        process.kill()


# indications to json
def indications_to_json(key, string):
    """Convert indications to JSON"""

    json_array = []

    # if indications are not provided then empty array is returned
    try:
        string_2_array = string.strip(";").split(";")

        for value in string_2_array:
            pheno_dict = {key: value, "source": "HPO"}
            if string != "":
                json_array.append(pheno_dict)
    except AssertionError:
        pass

    return json_array


# for better error reporting
def error_messaging(jsonobject):
    """Extract error message"""

    error_message = json.loads(jsonobject)
    try:
        print(error_message["code"])
        print(error_message["message"])
        print(error_message["details"])
    except KeyError:
        pass


# parse TSS config file
def parse_config(config_file):
    """Create dictionary from TSS config file"""

    print("\nPreparing config file, " + config_file)

    try:
        with open(os.path.expanduser(config_file), "r", encoding="UTF-8") as config:
            load_config = json.load(config)
            config = {
                "domain": load_config["domain"],
                "url": load_config["url"],
                "wg": load_config["workgroup"],
                "apikey": load_config["apiKey"],
            }
    except FileNotFoundError:
        print("Config file not found. Please check.")
        sys.exit()
    except KeyError:
        print("Config file error. Please check the terms.")
        sys.exit()
    else:
        return config


# extracted from legacy/test_mgt.py
# search test by name and get details
def get_test(test_name, test_version, config):
    """Get the test JSON (CURL required)"""

    # initialize
    print("Attempting to get the test definition...")
    test_id = None
    report_ids = []

    # curl command, request does not work :(
    command = (
        f"curl -X GET \"https://{config['domain']}.{config['url']}/tms/api/v1/testDefinitions\""
        f' -H "accept: application/json"'
        f" -H \"Authorization: apikey {config['apikey']}\""
        f" -H \"X-ILMN-Workgroup: {config['wg']}\""
        f" -H \"X-ILMN-Domain: {config['domain']}\""
    )

    print(f"Command:\t{command}")
    output, _ = run_shell_with_pipe(command)
    if output:
        try:
            data = json.loads(output[0])["items"]
        except AssertionError:
            pass
        else:
            for item in data:
                if item["name"] == test_name and item["version"] == test_version:
                    test_id = item["id"]
                    for report in item["reports"]:
                        report_ids.append(report["id"])

    print(f"TestId:\t{test_id}")
    print(f"Report Types:\t{report_ids}")
    return test_id, report_ids
