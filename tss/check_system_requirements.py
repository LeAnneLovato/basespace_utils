#!/usr/bin/env python3
"""Check system requirements for TSS case pipeline"""

##################################################################
# Author: LeAnne Lovato
# Email: llovato@illumina.com
# Check system requirements for TSS case pipeline
# 1. Inputs: None
# 2. Update/ Install pip, pandas, requests
# 3. Import required modules
# 4. Check the Java version
# 5. Outputs: Log file
# Notes: System requirements are listed in the readme
##################################################################

import os
import sys
import argparse
import method_tools


# install pip
def install_module(py_module, log):
    """Install missing python modules"""

    log.write(f"Attempting to Install (or Upgrade):\t{py_module}\n")
    python = sys.executable
    command = python + " -m pip install --upgrade --user " + py_module
    log.write(f"Command:\t{command}\n")
    out, err = method_tools.run_shell_with_pipe(command)
    if err:
        log.write("StdErr:\n")
        for line in err:
            log.write(line.decode() + "\n")
    else:
        log.write("StdOut:\n")
        for line in out:
            log.write(line.decode() + "\n")


# import required modules
def import_module(py_module, log):
    """Import missing python modules"""
    try:
        __import__(py_module)
    except ModuleNotFoundError as err:
        log.write(f"[ERROR] Module Not Found:\t{py_module}, {err}\n")
    else:
        log.write(f"Module Exists:\t{py_module}\n")


# install java
def check_java(log):
    """Check the JAVA version installed"""
    java = None
    jdk = None
    command = "java -version"
    _, java_out = method_tools.run_shell_with_pipe(command)
    for line in java_out:
        info = line.decode()
        if info.startswith("java version"):
            java = info.split()[2].strip('"')
        if info.startswith("Java(TM) SE Runtime Environment"):
            jdk = info.split()[4]

    log.write(f"Java Version:\t{java}\n")
    log.write(f"Java Developer Toolkit (JDK) Version:\t{jdk}\n")
    install_java_message = """[ERROR] java 11 is not installed. Please install java before starting the pipeline.
    Java 11 Downloads - https://www.oracle.com/java/technologies/javase/jdk11-archive-downloads.html
    Install Instructions - https://docs.oracle.com/en/java/javase/18/install/overview-jdk-installation.html
        """

    # java and jdk version is not None
    if java and jdk:
        # check version
        if int(java.split(".")[0]) < 11 or int(jdk.split(".")[0]) < 18:
            log.write(install_java_message)

    # java or jdk version is  None
    else:
        log.write(install_java_message)


# get args
def get_args():
    """Get command line args"""
    parser = argparse.ArgumentParser(
        description="Check system requirements for TSS pipelines"
    )
    parser.add_argument(
        "-o", "--outputDir", help="Path for logging", type=str, required=True
    )
    args = parser.parse_args()
    return args


# main function
if __name__ == "__main__":
    arguments = get_args()
    outputDir = os.path.abspath(arguments.outputDir)
    cwd = os.getcwd()

    # check and format the output dir
    directory = method_tools.format_path(outputDir)

    # create logging file
    with open(directory + "check_system_requirements.log", "w", encoding="UTF-8") as logfile:

        # logging
        logfile.write(f"Current Working Directory:\t{cwd}\n")
        logfile.write(f"Output Directory:\t{directory}\n")
        logfile.write(f"Log File:\t{os.path.abspath(logfile.name)}\n")

        # Python modules: os and sys are called in this script
        install_modules = ["pip", "requests", "pandas"]
        required_modules = [
            "pandas",
            "requests",
            "argparse",
            "csv",
            "getpass",
            "json",
            "mimetypes",
            "re",
            "smtplib",
            "subprocess",
            "threading",
            "time",
            "mailer",
            "method_tools",
            "monitor_progress",
            "download_reports",
            "get_credentials",
            "get_headers",
            "get_variants_by_tier",
            "assign_approve_report",
            "add_to_report_Tier1",
            "case_mgt_v2",
            "create_config",
            "parse_ehr",
            "psToken_handler",
        ]

        # check python version
        py_version = sys.version.splitlines()
        for entry in py_version:
            if entry.startswith("3"):
                logfile.write(f"Python Version:\t{entry}\n")
                version = entry.split(".")[:-1]
                major_version = float(".".join(version))
                if major_version < 3.6:
                    logfile.write(
                        """[ERROR] Python version 3.6 or newer is required. Please download python3.
                    Python Downloads - https://www.python.org/downloads/
                    Usage and Setup - https://docs.python.org/3.9/using/index.html
                """
                    )
                else:
                    # loop over must install/ upgrade modules
                    for module in install_modules:
                        install_module(module, logfile)

                    # loop over required modules
                    for module in required_modules:
                        import_module(module, logfile)

        # check java version
        check_java(logfile)

        # print log file to screen
        logfile.close()
        with open(os.path.abspath(logfile.name), "r", encoding="UTF-8") as logging:
            for entry in logging:
                print(entry.strip())
