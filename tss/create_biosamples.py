# !/usr/bin/env python3

"""Create and update biosample in BSSH"""

#######################################################################
# Author: LeAnne Lovato
# Email: llovato@illumina.com
# Create a BioSamples from a v2 sample sheet
# 1. Inputs: Sample sheet (v2)
# 2. Outputs: BioSample manifest, BioSample created or updated in BSSH
# Notes: System requirements are listed in the readme
#######################################################################

import os
import re
import sys
import json
import method_tools

BS_CLI = "bs"


# determine the users region
def user_region_info(tss_config, logfile):
    """Get user region from TSS config"""

    logfile.write("Extracting region information from the TSS config file\n")
    print("Extracting region information from the TSS config file")

    # london
    if re.search("euw2", tss_config["url"]):
        api_url = "https://api.euw2.sh.basespace.illumina.com"
        bssh_url = f"https://{tss_config['domain']}.euw2.sh.basespace.illumina.com"

    # canada
    elif re.search("cac1", tss_config["url"]):
        api_url = "https://api.cac1.sh.basespace.illumina.com"
        bssh_url = f"https://{tss_config['domain']}.cac1.sh.basespace.illumina.com"

    # europe
    elif re.search("euc1", tss_config["url"]):
        api_url = "https://api.euc1.sh.basespace.illumina.com"
        bssh_url = f"https://{tss_config['domain']}.euc1.sh.basespace.illumina.com"

    # default to US prod
    else:
        # preprod
        if re.search("preprod", tss_config["url"]):
            api_url = "https://api.use1-preprod.sh.basespace.illumina.com"
            bssh_url = (
                f"https://{tss_config['domain']}.use1-preprod.sh.basespace.illumina.com"
            )

        # prod
        else:
            api_url = "https://api.basespace.illumina.com"
            bssh_url = f"https://{tss_config['domain']}.basespace.illumina.com"

    logfile.write(f"BSSH UI URL:\t{bssh_url}\n")
    logfile.write(f"BSSH API URL:\t{api_url}\n")

    return bssh_url, api_url


# convert sample sheet to dictionary
def read_sample_sheet(sample_sheet, logfile):
    """Read sample sheet"""

    logfile.write(f"\nReading from the sample sheet, {sample_sheet}\n")
    print(f"\nReading from the sample sheet, {sample_sheet}")

    # read sample sheet and create dict
    ss_dict = {}
    with open(sample_sheet, "r", encoding="utf-8") as data:
        content = data.readlines()
        for line in content:
            info = line.rstrip().split(",")

            # header line
            if info[0].startswith("["):
                section = info.pop(0).strip("[]")
                ss_dict[section] = []

            # section content
            else:
                content_key = info.pop(0)
                if content_key != "":
                    ss_dict[section].append(line.strip())

    return ss_dict


# convert sample sheet to biosample manifest
def extract_biosamples(sample_sheet_dict, logfile):
    """Extract biosamples from the sample sheet"""
    logfile.write("\nExtracting BioSamples from the [Cloud_Data] section\n")
    print("\nExtracting BioSamples from the [Cloud_Data] section")

    biosamples = None
    # locate the header section
    try:
        header = sample_sheet_dict["Header"]
        cloud_data = sample_sheet_dict["Cloud_Data"]
    except TypeError:
        logfile.write(
            "[ERROR] unable to locate the '[Header]' and/or [Cloud_Data] section(s) in the v2 sample sheet\n"
        )
        print(
            "[ERROR] unable to locate the '[Header]' and/or [Cloud_Data] section(s) in the v2 sample sheet"
        )
    else:
        # get header info
        version = "unknown"
        for entry in header:
            details = entry.split(",")
            if details[0] == "FileFormatVersion" and int(details[1]) == 2:
                version = 2
            elif details[0] == "FileFormatVersion" and int(details[1]) == 1:
                version = 1
            else:
                pass

        # sample sheet version
        logfile.write(f"Sample Sheet Version:\t{version}\n")
        print(f"Sample Sheet Version:\t{version}")
        if version == 1:
            logfile.write(
                "[ERROR] a v1 sample sheet was detected. V1 sample sheets are not supported.\n"
            )
            print(
                "[ERROR] a v1 sample sheet was detected. v1 sample sheets are not supported."
            )
            sys.exit()
        if version == "unknown":
            logfile.write(
                "[WARNING] the sample sheet version is unknown. Assuming v2 due to the presence of [Cloud_Data]\n"
            )
            print(
                "[WARNING] the sample sheet version is unknown. Assuming v2 due to the presence of [Cloud_Data]"
            )

        # get biosample info
        biosamples = []
        for entry in cloud_data:
            details = entry.split(",")
            if details[0] != "Sample_ID":
                biosamples.append(details[0])

    logfile.write(f"Identified {len(biosamples)} BioSamples:\n{biosamples}\n")
    print(f"Identified {len(biosamples)} BioSamples:\n{biosamples}")

    return biosamples


# parse cli output
def communicate_cli_output(output, logfile, print_too=False):
    """Write BSSH CLI output to screen"""

    for line in output:
        text = line.decode()
        logfile.write(f"{text}\n")
        if print_too:
            print(text)


# authenticate
def bssh_authorization(tss_config, bssh_config_name, logfile):
    """Authenticate the BSSH CLI"""

    # get user info from tss config
    bssh_url, api_url = user_region_info(tss_config, logfile)

    # user instructions
    print(
        f"\nPlease do the following to authenticate the BSSH CLI:\n"
        f"(1) Log into your private domain BSSH account, {bssh_url}\n"
        "(2) In BSSH, navigate to the workgroup where the run will be uploaded\n"
        "(4) In the terminal, press ENTER to continue\n"
        "(5) Load the BSSH authentication URL provided in the terminal\n"
        "(6) Click 'Accept'\n"
        "(7) See the expected message, 'Thanks! You may close this browser window'"
    )

    # authorize bssh cli
    input("")

    logfile.write("\nInitiating BSSH authorization\n")
    print("\nInitiating BSSH authorization")

    command = (
        f"{BS_CLI} authenticate --config={bssh_config_name} --force --api-server={api_url} "
        "--scopes='CREATE GLOBAL,BROWSE GLOBAL,READ GLOBAL,WRITE GLOBAL,CREATE RUNS,CREATE PROJECTS,"
        "START APPLICATIONS'"
    )
    logfile.write(f"Command:\t{command}\n")
    method_tools.run_shell_with_screen(command)


# bs whoami
def bssh_whoami(bssh_config_name, logfile):
    """Run WHOAMI with BSSH CLI"""

    logfile.write("\nInitiating BSSH Who Am I?\n")
    print("\nInitiating BSSH Who Am I?")

    command = f"{BS_CLI} whoami --config={bssh_config_name} -f json"
    logfile.write(f"Command:\t{command}\n")
    stdout, stderr = method_tools.run_shell_with_pipe(command)

    # check for errors
    if re.search("ERROR", str(stderr)):
        communicate_cli_output(stderr, logfile, True)
        sys.exit()

    # extract workgroup from whoami
    whoami = []
    for line in stdout:
        text = line.decode()
        whoami.append(text)
    json_text = json.loads(str(" ".join(whoami)).strip("[]"))
    workgroup = json_text["Name"]

    # logging
    logfile.write(json.dumps(json_text) + "\n")
    is_workgroup = json_text["IsWorkgroup"]
    if is_workgroup is False:
        logfile.write(
            "[WARNING] The BSSH config is pointed to a personal workspace and not a workgroup.\n"
        )
        print(
            "[WARNING] The BSSH config is pointed to a personal workspace and not a workgroup."
        )
        logfile.write(f"Personal Space:\t{workgroup}\n")
        print(f"Personal Space:\t{workgroup}")
    else:
        print(f"Workgroup:\t{workgroup}")


# create biosample manifest
def create_manifest(biosamples, bssh_project, required_yield, directory, logfile):
    """Create the biosample manifest file"""

    logfile.write("\nCreating the BioSample manifest\n")
    print("\nCreating the BioSample manifest")

    with open(directory + "biosample_manifest.csv", "w", encoding="utf-8") as manifest:
        manifest.write(
            "[Header],,,,,,,,,\nFileVersion,1,,,,,,,,\n[Data],,,,,,,,,\nBioSample Name,Default Project,"
            "Container Name,Container Position,Prep Request,Required Yield Gbp,Analysis Workflow,"
            "Analysis Group,Sample Label,Delivery Mode\n"
        )
        for sample in biosamples:
            manifest.write(
                f"{sample},{bssh_project},,,Unknown,{required_yield},TSS Connect v1.1,,,\n"
            )

        logfile.write(f"BioSample Manifest Path:\t{os.path.abspath(manifest.name)}\n")
        print(f"BioSample Manifest Path:\t{os.path.abspath(manifest.name)}")
        return manifest.name


# upload bs manifest
def post_biosample_manifest(manifest, bssh_config_name, logfile):
    """Post the biosample manifest to BSSH using the BSSH CLI"""
    logfile.write("\nPosting the BioSample manifest\n")
    print("\nPosting the BioSample manifest")

    command = f"{BS_CLI} manifest accession {manifest} --config={bssh_config_name}"
    logfile.write(f"Command:\t{command}\n")
    stdout, stderr = method_tools.run_shell_with_pipe(command)

    # check for errors
    if re.search("ERROR", str(stderr)):
        communicate_cli_output(stderr, logfile, True)
        communicate_cli_output(stdout, logfile, True)
    else:
        communicate_cli_output(stdout, logfile, True)


# lookup biosamples
def lookup_biosamples(biosample_name, bssh_config_name, logfile):
    """Look up a biosample in BSSH using the BSSH CLI"""

    logfile.write(f"\nLooking up BioSample, {biosample_name}\n")
    print(f"\nLooking up BioSample, {biosample_name}")

    command = f"{BS_CLI} biosample get --config={bssh_config_name} --name={biosample_name} -f json"
    logfile.write(f"Command:\t{command}\n")
    stdout, stderr = method_tools.run_shell_with_pipe(command)

    # check for errors
    if re.search("ERROR", str(stderr)):
        communicate_cli_output(stderr, logfile, True)
    else:
        # convert stdout to json
        print("BioSample found in BSSH!")
        lookup = []
        for line in stdout:
            text = line.decode()
            lookup.append(text)
        json_text = json.loads(str(" ".join(lookup)).strip("[]"))
        logfile.write(json.dumps(json_text) + "\n")


# create biosample
def create_biosample(biosample_args):
    """Create a biosample using the BSSH CLI"""

    command = (
        f"{BS_CLI} biosample create "
        f"--config={biosample_args['bssh_config_name']} "
        f"--project={biosample_args['bssh_project']} "
        f"--name={biosample_args['biosample_name']} "
        "--analysis-workflow='TSS Connect v1.1' "
        "--prep-request='Unknown' "
        f"--required-yield={biosample_args['required_yield']}"
    )

    # update existing biosample
    if biosample_args["overwrite"]:
        command = command + " --allow-existing"
        biosample_args["logfile"].write(
            f"\nUpdating BioSample, {biosample_args['biosample_name']}\n"
        )
        print(f"\nUpdating BioSample, {biosample_args['biosample_name']}")
    else:
        biosample_args["logfile"].write(
            f"\nCreating BioSample, {biosample_args['biosample_name']}\n"
        )
        print(f"\nCreating BioSample, {biosample_args['biosample_name']}")

    biosample_args["logfile"].write(f"Command:\t{command}\n")
    stdout, stderr = method_tools.run_shell_with_pipe(command)

    # check for errors
    if re.search("ERROR", str(stderr)):
        communicate_cli_output(stderr, biosample_args["logfile"], True)
    else:
        # convert stdout to json
        biosample_args["logfile"].write("Success!\n")
        biosample_info = []
        for line in stdout:
            text = line.decode()
            biosample_info.append(text)
        json_text = json.loads(str(" ".join(biosample_info)).strip("[]"))
        biosample_args["logfile"].write(json.dumps(json_text) + "\n")

        # parse info from json
        biosample_name = json_text["BioSamples"][0]["BioSample"]["BioSampleName"]
        biosample_args["logfile"].write(f"BioSample Name:\t{biosample_name}\n")
        statuses = json_text["BioSamples"][0]["Statuses"]
        for status in statuses:
            print(f"{status['Type']}: {status['StatusMessage']}")
            biosample_args["logfile"].write(
                f"{status['Type']}: {status['StatusMessage']}\n"
            )
        biosample_args["logfile"].write(f"BioSample {biosample_name} is ready!\n")
        print(f"BioSample {biosample_name} is ready!")


# main function
def main(bssh_args):
    """Create & update biosamples"""

    # check and format the output dir
    directory = method_tools.format_path(bssh_args["output_dir"])

    # logging
    with open(directory + "create_biosamples.log", "w", encoding="utf-8") as logfile:
        logfile.write(f"Output Directory:\t{directory}\n")

        # authorization needed
        if bssh_args["bssh_config_name"] is None:
            # get user info from tss config
            tss_config_file = method_tools.parse_config(bssh_args["tss_config_file"])
            bssh_args["bssh_config_name"] = tss_config_file["domain"] + "_tss_samples"

            # authorize bssh cli
            bssh_authorization(tss_config_file, bssh_args["bssh_config_name"], logfile)

        # bssh whoami
        bssh_whoami(bssh_args["bssh_config_name"], logfile)

        # parse sample sheet and extract samples
        sample_sheet_dict = read_sample_sheet(bssh_args["sample_sheet"], logfile)
        biosamples = extract_biosamples(sample_sheet_dict, logfile)

        # create biosample manifest
        if bssh_args["biosample_workflow"] == "biosample_manifest":
            # create biosample manifest
            manifest = create_manifest(
                biosamples,
                bssh_args["bssh_project"],
                bssh_args["required_yield"],
                directory,
                logfile,
            )

            # post manifest to BSSH workgroup
            post_biosample_manifest(
                os.path.abspath(manifest), bssh_args["bssh_config_name"], logfile
            )

            # lookup biosamples
            for entry in biosamples:
                lookup_biosamples(entry, bssh_args["bssh_config_name"], logfile)

        # create or update biosamples
        else:
            # loop over biosamples
            for entry in biosamples:
                # create new biosample
                if bssh_args["biosample_workflow"] == "create_new":
                    create_args = {
                        "biosample_name": entry,
                        "bssh_project": bssh_args["bssh_project"],
                        "required_yield": bssh_args["required_yield"],
                        "bssh_config_name": bssh_args["bssh_config_name"],
                        "logfile": logfile,
                        "overwrite": False,
                    }
                    create_biosample(create_args)

                # update existing biosample
                else:
                    create_args = {
                        "biosample_name": entry,
                        "bssh_project": bssh_args["bssh_project"],
                        "required_yield": bssh_args["required_yield"],
                        "bssh_config_name": bssh_args["bssh_config_name"],
                        "logfile": logfile,
                        "overwrite": True,
                    }
                    create_biosample(create_args)
