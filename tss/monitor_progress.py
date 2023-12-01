#!/usr/bin/env python3
"""Continuously monitor a TSS case processing"""

##################################################################
# Author: LeAnne Lovato
# Email: llovato@illumina.com
# Monitor the progress of a case or sample
# 1. Inputs: caseDisplayID or sampleID and an outputDir
# 2. Outputs: case status update, sample status update
# Notes:
##################################################################

import os
import time
from datetime import datetime
import method_tools
import case_mgt_v2


def main(case_id, wait_time_min, interval_min, output_dir, config_file):
    """Monitor a processing case"""

    config_dict = method_tools.parse_config(config_file)

    # check and format the output dir
    directory = method_tools.format_path(output_dir)

    # create logging file
    with open(directory + "monitor_progress.log", "w", encoding="UTF-8") as log_file:

        # logging
        print(f"{datetime.now()}\tStarting case monitoring.")
        log_file.write(f"{datetime.now()}\tStarting case monitoring.\n")
        log_file.write(f"{datetime.now()}\tCurrent Working Directory:\t{os.getcwd()}\n")
        log_file.write(f"{datetime.now()}\tOutput Directory:\t{os.path.abspath(directory)}\n")
        log_file.write(f"{datetime.now()}\tLog File:\t{os.path.abspath(log_file.name)}\n")

        # get case info
        log_file.write(f"{datetime.now()}\tCase ID:\t{case_id}\n")
        exit_status = ["IN PROGRESS - READY FOR INTERPRETATION",
                       "IN PROGRESS - HAS ISSUE",
                       "IN PROGRESS - QC WARNING",
                       "IN PROGRESS - READY FOR REVIEW",
                       "IN PROGRESS - MISSING SAMPLE INFORMATION"]
        attempts = 0
        max_attempts = wait_time_min / interval_min
        start = time.perf_counter()
        runtime = None
        case_status = None

        while case_status is None:
            # counter
            attempts += 1
            log_file.write("{datetime.now()}\tAttempt Number:\t{attempts}\n")
            if attempts >= max_attempts:
                log_file.write(f"{datetime.now()}\tThe maximum attempts, {max_attempts}, were reached.\n")
                log_file.write(f"{datetime.now()}\tRuntime:\t{round(runtime, 3)} (min.)\n")
                break

            result = case_mgt_v2.get_case(case_id, config_dict)
            case_status = f"{result['status'].upper()} - {result['subState'].upper().replace('_', ' ')}"
            log_file.write(f"{datetime.now()}\tCase Status:\t{result}\n")

            # exit if RFI or Has Issues or QC Warning
            # Keeps monitoring when edge cases are found
            if case_status in exit_status or result["status"] in ["New", "Complete"]:
                runtime = (time.perf_counter() - start) / 60
                print(f"{datetime.now()}\tCase monitoring complete.".format())
                print(f"{datetime.now()}\tCase Status:\t{case_status}")
                print(f"{datetime.now()}\tScript Runtime:\t{round(runtime, 3)} (min.)")
                break

            # keep waiting but check for case status changes
            # print the status update
            runtime = (time.perf_counter() - start) / 60
            print(f"{datetime.now()}\tCase Status:\t{case_status}")
            print(f"{datetime.now()}\tScript Runtime:\t{round(runtime, 3)} (min.)")
            print(f"{datetime.now()}\tSleeping for {interval_min} minutes. Please check back then.")

            # wait for RFI result
            log_file.write(f"{datetime.now()}\tCase Status:\t{result}\n")
            log_file.write(f"{datetime.now(datetime.now())}\tScript Runtime:\t{round(runtime, 3)} (min.)\n")
            log_file.write(f"{datetime.now()}\tSleeping for {interval_min} minutes. Please check back then.\n")
            time.sleep(interval_min * 60)
            case_status = None

        return case_status
