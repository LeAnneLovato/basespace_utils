#!/usr/bin/env python3
"""Launch BSSH DRAGEN GERMLINE: 3.8.9, 4.0.3"""

##########################################
# Author: LeAnne Lovato
# GitHub: https://github.com/LeAnneLovato
##########################################

import subprocess
import argparse
import pathlib
import sys


# launch  app
def launch_app(command_line):
    """Launch DRAGEN with the CLI"""
    print(command_line)
    try:
        with subprocess.Popen(command_line, shell=True) as process:
            process.wait(timeout=120)
            process.kill()
    except subprocess.SubprocessError:
        print("Timeout error...")
    else:
        pass


# subset a list
def subset_list(long_list, max_items):
    """Split a long list into short lists"""
    sub_lists = []
    for i in range(0, len(long_list), max_items):
        index = i
        sub_lists.append(long_list[index:index + max_items])
    return sub_lists


# get args
def get_args():
    """Get commandline arguments"""
    parser = argparse.ArgumentParser(description="Launch DRAGEN Germline")

    parser.add_argument(
        "-s",
        "--sample_list",
        help="Path to a sample list",
        type=pathlib.Path,
        required=True,
    )
    parser.add_argument(
        "-c",
        "--config",
        help="BSSH config",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-p",
        "--project",
        help="BSSH Project",
        type=str,
        required=True,
    )
    parser.add_argument(
        "-d",
        "--dragen_version",
        help="DRAGEN Version: 3.8.9, 4.0.3",
        type=str,
        required=True,
    )

    args = parser.parse_args()
    return args


if __name__ == "__main__":

    # get args from cmd line
    cmd_args = get_args()

    # read samples file
    with open(cmd_args.sample_list, 'r', encoding='utf-8') as file:
        samples = file.readlines()

    # set the app ID and app settings
    APP_ID = None
    SETTINGS = None
    if cmd_args.dragen_version == "4.0.3":
        APP_ID = "14129115"
        SETTINGS = {
            "app-session-name": f"Auto_Launch_{cmd_args.dragen_version}",
            "project-id": cmd_args.project,
            "ht-ref": "hg38-altaware-graph.v8",
            "input_list.cram-id": None,
            "cnv_checkbox": "1",
            "sv_checkbox": "1",
            "eh_checkbox": "1",
            "eh_dropdown": "default_plus_smn",
            "cyp2d6_checkbox": "1",
            "cyp2b6_checkbox": "1",
            "gba_checkbox": "1",
            "smn_checkbox": "1",
            "star_checkbox": "1",
            "metrics_checkbox": "1",
            "nirvana": "1",
            "phased-variants": "true",
            "enable-ml": "on"
        }
    elif cmd_args.dragen_version == "3.8.9":
        APP_ID = "15141126"
        SETTINGS = {
            "app-session-name": f"Auto_Launch_{cmd_args.dragen_version}",
            "project-id": cmd_args.project,
            "ht-ref": "hg38-altaware-graph.v8",
            "input_list.cram-id": None,
            "cnv_checkbox": "1",
            "sv_checkbox": "1",
            "eh_checkbox": "1",
            "cyp2d6": "1",
            "metrics_checkbox": "1",
            "nirvana": "1"
        }
    else:
        print("DRAGEN version must be 3.8.9 or 4.0.3")
        sys.exit()

    # extract samples from CSV
    sample_list = []
    for line in samples:
        bs_id, file_name = line.rstrip().split(",")
        sample_list.append(bs_id)
    mini_lists = subset_list(sample_list, 25)

    # create batch lists (max set to 25 CRAMs)
    for entry in mini_lists:
        SETTINGS['input_list.cram-id'] = ",".join(entry).strip("'")
        bs_args = []
        for item in SETTINGS.items():
            bs_args.append(f"-o {item[0]}:{item[1]}")

        # launch DRAGEN with custom settings
        BS_ARG_STR = " ".join(bs_args)
        launch_app(f"bs application launch -f json -c {cmd_args.config} -i {APP_ID} {BS_ARG_STR}")
