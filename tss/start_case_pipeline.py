#!/usr/bin/env python3

##################################################################
# Author: LeAnne Lovato
# Email: llovato@illumina.com
# Start TSS case pipeline
# 1. Inputs: EHR JSON, output dir, [optional] config
# 2. Outputs: None
# Pipeline Steps:
# Pipeline Step - Debug_Mode (skip case & sample creation)
# Pipeline Step - Get TSS Credentials
# Pipeline Step - Create Config
# Pipeline Step - Parse Input
# Pipeline Step - Create Case
# Pipeline Step - Monitor for Case Status
##################################################################

import argparse
import os
import sys
import time
from datetime import datetime
import pathlib
import method_tools
import parse_ehr
import monitor_progress
import case_mgt_v2

TSS_CLI = "tss-cli-2.2.0.jar"


# get args
def get_args():
    parser = argparse.ArgumentParser(description="Start TSS case pipeline")
    parser.add_argument(
        "-o",
        "--outputDir",
        help="Path for output. Please specify a directory with no escapes or spaces in the name.",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-c", "--configFile", help="Path to JSON config file", type=str, required=True
    )
    parser.add_argument(
        "-i", "--input", help="Input EHR JSON", type=pathlib.PosixPath, required=True
    )
    args = parser.parse_args()
    return args


# summarize the runtime
def runtime_summary(start, time_stamp):
    stop = time.perf_counter()
    runtime = stop - start
    minutes = runtime / 60
    hours = runtime / 3600
    if minutes < 60:
        print("{}\tTotal Runtime:\t{} minutes".format(time_stamp, round(minutes, 3)))
    else:
        print("{}\tTotal Runtime:\t{} hours".format(time_stamp, round(hours, 3)))


# main function
if __name__ == "__main__":
    # start timer
    start_time = time.perf_counter()

    # get args
    arguments = get_args()
    cwd = os.getcwd()
    input_file = arguments.input
    output_dir = arguments.outputDir
    config_file = arguments.configFile

    # check and format the output dir
    directory = method_tools.format_path(os.path.abspath(output_dir))

    # logging
    print("{}\tStarting TSS case pipeline".format(datetime.now()))
    print("{}\tCurrent Working Directory:\t{}".format(datetime.now(), cwd))
    print(
        "{}\tOutput Directory:\t{}".format(datetime.now(), os.path.abspath(directory))
    )

    # setup
    case_json = None
    case_display_id = None
    case_guid = None
    step_number = 0

    # parse configFile into dictionary
    config = method_tools.parse_config(config_file)

    # Pipeline Step - Parse Input
    step_number += 1
    step_name = "parse_ehr.py"

    # invoke parse_ehr.py
    print("\n{}\tStep {}. Executing {}".format(datetime.now(), step_number, step_name))

    # open input
    method_tools.check_path(input_file)
    print("{}\tInput File:\t{}".format(datetime.now(), os.path.abspath(input_file)))

    case_info = parse_ehr.main(input_file, directory, config)
    if case_info:
        case_json = case_info[0]
        case_json_file_name = case_info[1]
        print(
            "{}\tCase JSON File Path:\t{}".format(datetime.now(), case_json_file_name)
        )
    else:
        print(
            "{}\tExiting {}. The pipeline step was unsuccessful".format(
                datetime.now(), step_name
            )
        )
        runtime_summary(start_time, datetime.now())
        sys.exit()
    print("{}\tExiting {}".format(datetime.now(), step_name))

    # Pipeline Step - Create Case
    step_number += 1
    step_name = "case_mgt.py"

    # invoke case_mgt_v2.py
    print("\n{}\tStep {}. Executing {}".format(datetime.now(), step_number, step_name))
    case_results = case_mgt_v2.post_case(case_json, config, output_dir)
    if case_results:
        case_guid = case_results["id"]
        case_subjects = case_results["caseSubjects"]
        case_mgt_v2.process_case(case_guid, config, output_dir)
        case_mgt_v2.get_case_details(case_guid, config)
    else:
        print(
            "{}\tThere was an error posting the case. Please review the error(s) and correct the issue(s).".format(
                datetime.now()
            )
        )
        print(
            "{}\tExiting {}. The pipeline step was unsuccessful".format(
                datetime.now(), step_name
            )
        )
        runtime_summary(start_time, datetime.now())
        sys.exit()
    print("{}\tExiting {}".format(datetime.now(), step_name))

    # Pipeline Step - Monitor Case Status
    step_number += 1
    step_name = "monitor_progress.py"

    # invoke monitor_progress.py
    print("\n{}\tStep {}. Executing {}".format(datetime.now(), step_number, step_name))

    # Decide how long to wait based on pedigree
    if len(case_subjects) == 1:
        wait_time = 330  # 5 hrs for singleton cases
    else:
        wait_time = 540  # 9 hrs for extended pedigree

    status = monitor_progress.main(case_guid, wait_time, 5, output_dir, config_file)
    if status == "IN PROGRESS - READY FOR INTERPRETATION":
        print(
            "{}\tProceeding with the interpretation portion of the pipeline.".format(
                datetime.now()
            )
        )
    else:
        print(
            "{}\tUnexpected case status, {}. Please review the output for errors.".format(
                datetime.now(), status
            )
        )
        print(
            "{}\tExiting {}. The pipeline was unsuccessful".format(
                datetime.now(), step_name
            )
        )
        runtime_summary(start_time, datetime.now())
        sys.exit()
    print("{}\tExiting {}".format(datetime.now(), step_name))

    # End Pipeline
    print("\n{}\tTSS case has completed".format(datetime.now()))
    runtime_summary(start_time, datetime.now())
