# !/usr/bin/env python3

"""TSS sample pipeline: biosamples, fastqs, and analyses"""

##################################################################
# Author: LeAnne Lovato
# Email: llovato@illumina.com
# TSS sample pipeline
# 1. Inputs: (1) sample pipeline (bssh, fastq, analysis) (2) input file
# 2. Outputs: BioSample manifest
# Notes: System requirements are listed in the readme
##################################################################

import argparse
import os
import pathlib
import sys
import time
from datetime import datetime
import create_biosamples
import method_tools


# get args
def get_args():
    """Get commandline arguments"""
    parser = argparse.ArgumentParser(description="Start TSS Sample pipeline")

    parser.add_argument(
        "-o",
        "--output_dir",
        help="Path for output. Please specify a directory with no escapes or spaces in the name.",
        type=pathlib.Path,
        required=True,
    )
    parser.add_argument(
        "--pipeline",
        choices=["bssh", "fastq", "analysis"],
        help="Select bssh, fastq, or analysis as the pipeline",
        type=str,
        required=True,
    )
    parser.add_argument(
        "--tss_config",
        help="Specify the path to a TSS config",
        type=pathlib.Path,
        required=True,
    )
    parser.add_argument(
        "--bssh_config",
        help="[Optional] Specify a BSSH config file name (excluding the path). Defaults to 'None'",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--biosample",
        choices={"biosample_manifest", "create_new", "update_existing"},
        help="Specify the BioSample workflow: biosample_manifest, create_new, update_existing",
        type=str,
        required="bssh" in sys.argv,
    )
    parser.add_argument(
        "-s",
        "--sample_sheet",
        help="Specify the path to a v2 sample sheet",
        type=pathlib.Path,
        required="bssh" in sys.argv,
    )
    parser.add_argument(
        "-y",
        "--yield_required",
        help="Specify the required yield in gigabases (GB)",
        type=int,
        required="bssh" in sys.argv,
    )
    parser.add_argument(
        "-p",
        "--project",
        help="Specify a BSSH project to stores TSS Connect v1.1 logs",
        type=str,
        required="bssh" in sys.argv,
    )
    parser.add_argument(
        "-c",
        "--csv",
        help="Specify the input CSV file",
        type=pathlib.Path,
        required="fastq" in sys.argv or "analysis" in sys.argv,
    )
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        help="Specify the number of threads for upload. Defaults to 1",
        default=1,
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Specify --overwrite when sample(s) already exist",
        default="store_false",
    )

    args = parser.parse_args()
    return args


# summarize the runtime
def runtime_summary(start_time, time_stamp):
    """Sample pipeline runtime summary"""
    stop_time = time.perf_counter()
    runtime = stop_time - start_time
    minutes = runtime / 60
    hours = runtime / 3600
    if minutes < 60:
        print(f"{time_stamp}\tTotal Runtime:\t{round(minutes, 3)} minutes")
    else:
        print(f"{time_stamp}\tTotal Runtime:\t{round(hours, 3)} hours")


# main function
if __name__ == "__main__":
    # start timer
    start = time.perf_counter()

    # get args
    arguments = get_args()
    cwd = os.getcwd()

    # check and format the output dir
    directory = method_tools.format_path(str(arguments.output_dir))

    # logging
    print(
        f"{datetime.now()}\tStarting TSS Sample Pipeline{arguments.pipeline.upper()} sample pipeline"
    )
    print(f"{datetime.now()}\tCurrent Working Directory:\t{cwd}")
    print(f"{datetime.now()}\tOutput Directory:\t{directory}")

    # bssh fastq pipeline
    if arguments.pipeline == "bssh":
        # check for configs
        if arguments.bssh_config is None and arguments.tss_config is None:
            print(
                "[ERROR] Please provide either a BSSH config (*.cfg) or a TSS config (*.json) file. "
                "\n**Providing a TSS config file will initiate BSSH authorization. "
                "\n**Providing a BSSH config will by-pass BSSH authorization. "
                "Note, the config must point to the workgroup where sequences will be uploaded."
            )
            sys.exit()
        # run create_biosample.py
        bssh_args = {
            "biosample_workflow": arguments.biosample,
            "output_dir": directory,
            "sample_sheet": arguments.sample_sheet,
            "bssh_project": arguments.project,
            "required_yield": arguments.yield_required,
            "tss_config_file": str(arguments.tss_config),
            "bssh_config_name": arguments.bssh_config,
        }
        create_biosamples.main(bssh_args)

        # End Pipeline
        print(f"\n{datetime.now()}\TSS sample pipeline has completed")
        runtime_summary(start, datetime.now())

    # upload pipelines
    else:
        input_file = arguments.csv
        overwrite = str(arguments.overwrite).upper or None
        threads = arguments.threads

        # tss config
        tss_config = method_tools.parse_config(str(arguments.tss_config_file))

        # fastq upload pipeline
        if arguments.pipeline == "fastq":
            print("Coming Soon...")

            # End Pipeline
            print(f"\n{datetime.now()}\tTSS sample pipeline has completed")
            runtime_summary(start, datetime.now())
            sys.exit()

        # analysis upload pipeline
        if arguments.pipeline == "analysis":
            print("Coming Soon...")

            # End Pipeline
            print(f"\n{datetime.now()}\tTSS sample pipeline has completed")
            runtime_summary(start, datetime.now())
            sys.exit()
