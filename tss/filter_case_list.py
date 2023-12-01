#!/usr/bin/env python3
"""Filter cases with include and exclude criteria"""

############################################################################################
# Author: LeAnne Lovato
# Email: llovato@illumina.com
# 1. Inputs: config, output dir, search option, include criteria, exclude criteria
# 2. Outputs: log file
############################################################################################

import os
import sys
import argparse
import pathlib
import time
import requests
from requests.exceptions import HTTPError
import method_tools
import search
import case_mgt_v2


# get args
def get_args():
    """Input arguments"""
    parser = argparse.ArgumentParser(
        description="Filter cases with include and exclude criteria"
    )
    parser.add_argument(
        "-o", "--output_dir", help="Path for output", type=pathlib.Path, required=True
    )
    parser.add_argument(
        "-c",
        "--config_file",
        help="Full path to a TSS config file",
        type=pathlib.Path,
        required=True,
    )
    parser.add_argument(
        "-s",
        "--search",
        help="Criteria for case list: (1) tags require -it/--include_tags, (2) status requires "
        "-is/--include_status, (3) creators require -ic/--include_creators, "
        "(4) dates require -id/--include_dates",
        type=str,
        choices=["tags", "status", "creators", "dates"],
        required=True,
    )
    parser.add_argument(
        "-it",
        "--include_tags",
        help="Include cases with any of the tag(s). Provide a case-sensitive "
        "comma separated list with quotes around tags with whitespace "
        '(e.g. "On Hold",Overdue,"review ASAP"). ',
        type=str,
    )
    parser.add_argument(
        "-is",
        "--include_status",
        help='Include cases with a specific status: Draft, New, "In Progress", '
        "Complete, Canceled, Deletion. Provide a case-sensitive comma separated list "
        'with quotes around statuses with whitespace (e.g. New,"In Progress",Complete). ',
        type=str,
    )
    parser.add_argument(
        "-ic",
        "--include_creators",
        help="Include case creator(s). Provide a comma separated list with quotes "
        'around the first and last names (e.g. "June Salazar","May Jenkins").',
        type=str,
    )
    parser.add_argument(
        "-id",
        "--include_dates",
        help="Include cases with a creation date range. "
        "Provide a comma separated date range (e.g. YYYY-MM-DD,YYYY-MM-DD)",
        type=str,
    )
    parser.add_argument(
        "-et",
        "--exclude_tags",
        help="Exclude cases with any of the tag(s). Provide a case-sensitive "
        "comma separated list with quotes around tags with whitespace "
        '(e.g. "On Hold",Overdue,"review ASAP"). ',
        type=str,
    )
    parser.add_argument(
        "-es",
        "--exclude_status",
        help='Include cases with a specific status: Draft, New, "In Progress", '
        "Complete, Canceled, Deletion. Provide a case-sensitive comma separated list "
        'with quotes around statuses with whitespace (e.g. New,"In Progress",Complete). ',
        type=str,
    )
    parser.add_argument(
        "-ec",
        "--exclude_creators",
        help="Exclude cases by case creator(s). Provide a comma separated list with "
        'quotes around the first and last name (e.g. "June Salazar","May Jenkins").',
        type=str,
    )
    parser.add_argument(
        "-ed",
        "--exclude_dates",
        help="Exclude cases with a creation date range. "
        "Provide a comma separated date range (e.g. YYYY-MM-DD,YYYY-MM-DD)",
        type=str,
    )
    arguments = parser.parse_args()
    return arguments


def build_case_list(search_response):
    """converts search response to a list of case IDs"""

    # get the case id
    case_list = []
    if search_response:
        for entry in search_response["content"]:
            case_list.append(entry["id"])
    return case_list


def search_by_tags(query, config_dict, logfile):
    """searching for cases by tag"""
    print(f"\nSearching for cases with any of the tag(s): {query}")
    logfile.write(f"\nSearching for cases by tag(s): {query}\n")

    processed_tags = [entry.strip() for entry in query.split(",")]
    tags_terms = "&tags=".join(processed_tags)
    results = search.search(
        option="tags", search_term=tags_terms, config_dict=config_dict
    )
    logfile.write(f"{results}\n")
    case_list = build_case_list(results)
    print(f"Cases Found:\t{len(case_list)}")
    logfile.write(f"Cases Found:\t{len(case_list)}\n")

    return case_list


def search_by_status(query, config_dict, logfile):
    """searching for cases by status"""
    print(f"\nSearching for cases by status (or statuses): {query}")
    logfile.write(
        f"\nSearching for cases by status (or statuses): {query}\n"
    )

    processed_status = [entry.strip() for entry in query.split(",")]
    case_list = []
    for status in processed_status:
        results = search.search(
            option="status", search_term=status, config_dict=config_dict
        )
        logfile.write(f"{results}\n")
        search_list = build_case_list(results)
        print(f"{status} Cases Found:\t{len(search_list)}")
        logfile.write(f"{status} Cases Found:\t{len(search_list)}\n")
        case_list.extend(search_list)
    return case_list


def get_all_cases(config_dict, logfile):
    """search for cases across all statuses: New, In Progress, Complete"""
    print("\nCompiling a list of all cases: New, In Progress, and Complete")
    logfile.write("\nCompiling a list of all cases: New, In Progress, Complete\n")

    # new cases
    results = search.search(option="status", search_term="New", config_dict=config_dict)
    new_cases = build_case_list(results)
    logfile.write(f"New Cases:\t{len(new_cases)}\n")
    logfile.write(f"{results}\n")

    # in progress cases
    results = search.search(
        option="status", search_term="In Progress", config_dict=config_dict
    )
    ip_cases = build_case_list(results)
    logfile.write(f"In Progress Cases:\t{len(ip_cases)}\n")
    logfile.write(f"{results}\n")

    # complete cases
    results = search.search(
        option="status", search_term="Complete", config_dict=config_dict
    )
    complete_cases = build_case_list(results)
    logfile.write(f"Complete Cases:\t{len(complete_cases)}\n")
    logfile.write(f"{results}\n")

    return new_cases + ip_cases + complete_cases


def get_users(config_dict, logfile):
    """Get a list of workgroup users"""
    url = (
        f"https://{config_dict['domain']}.{config_dict['url']}/crs/api/v1/session/users"
    )
    headers = method_tools.get_headers_apikey(
        config_dict["apikey"], config_dict["domain"], config_dict["wg"]
    )
    response = None

    try:
        response = requests.get(url, headers=headers, timeout=30)

        # If the response was successful, no Exception will be raised
        response.raise_for_status()

    # Error posting case
    except HTTPError as http_err:
        logfile.write(f"HTTP error occurred: {http_err}\n")
        logfile.write(f"{response.text}")
        print(
            "Exiting, case ingestion failed. Please check the logs for detailed error message."
        )
        sys.exit()
    else:
        if response.status_code == 200:
            return response.json()
        # Error posting case
        logfile.write(f"{response.text}")
        print(
            "Exiting, case ingestion failed. Please check the logs for detailed error message."
        )
        sys.exit()


def filter_by_tags(case_info, query):
    """filter cases via tags"""
    tags = query.split(",")
    case_tags = case_info["tags"]
    match_count = 0
    for filter_tag in tags:
        for tag in case_tags:
            if filter_tag == tag:
                match_count += 1
    return bool(match_count > 0)


def filter_by_status(case_info, query):
    """filter cases via status"""
    statuses = query.split(",")
    match_count = 0
    for state in statuses:
        if state == case_info["status"]:
            match_count += 1
    return bool(match_count > 0)


def filter_by_creators(case_info, query, users):
    """filter cases via createdBy"""
    creators = query.split(",")
    match_count = 0
    for person in creators:
        for entry in users:
            name = entry["fullName"]
            if name == person:
                user_guid = entry["guid"]
                if case_info["createdBy"] == user_guid:
                    match_count += 1
    return bool(match_count > 0)


def filter_by_dates(case_info, query):
    """filter cases via creationDate"""
    dates = query.split(",")
    start_date = time.strptime(dates[0], "%Y-%m-%d")
    stop_date = time.strptime(dates[1], "%Y-%m-%d")
    date_info = case_info["createdDate"].split("-")
    creation_date_str = f"{date_info[0]}-{date_info[1]}-{date_info[2].split('T')[0]}"
    creation_date = time.strptime(creation_date_str, "%Y-%m-%d")
    return bool(start_date <= creation_date <= stop_date)


def filter_case_list(case_list, criteria, config_dict, logfile):
    """apply filters specified in args"""

    print("\nApplying Include and Exclude Criteria")
    logfile.write("\nApplying Include and Exclude Criteria\n")
    logfile.write(f"{case_list}\n")

    # summarize search/ filter criteria
    users = {}
    expected_results = []
    for item, _ in criteria.items():
        print(f"{item}:\t{_}")
        logfile.write(f"{item}:\t{_}\n")

        # get users
        if item.endswith("creators"):
            users = get_users(config_dict=config_dict, logfile=logfile)

        # set expectations for include/ exclude
        if item.startswith("include"):
            expected_results.append(True)
        else:
            expected_results.append(False)

    # loop over case list
    include_list = []
    exclude_list = []
    for case_guid in enumerate(case_list):
        # get the case info
        get_case_results = case_mgt_v2.get_case(case_guid[1], config_dict)

        # filter on include criteria
        # exclude filtering when only tags are applied
        results = []
        for flag, _ in criteria.items():
            if flag.endswith("tags"):
                results.append(filter_by_tags(case_info=get_case_results, query=_))
            if flag.endswith("status"):
                results.append(filter_by_status(case_info=get_case_results, query=_))
            if flag.endswith("creators"):
                results.append(
                    filter_by_creators(case_info=get_case_results, query=_, users=users)
                )
            if flag.endswith("dates"):
                results.append(filter_by_dates(case_info=get_case_results, query=_))

        # summary of include/ exclude status per case
        print(case_guid[1], expected_results, results)
        if results == expected_results:
            logfile.write(f"Match found, {case_guid[1]}\n")
            include_list.append(case_guid[1])
        else:
            logfile.write(f"Not a match, case will be filtered out, {case_guid[1]}\n")
            exclude_list.append(case_guid[1])

    # summary of include/ exclude status across all cases
    print(f"Number of Cases Filtered Out:\t{len(exclude_list)}")
    logfile.write(f"Number of Cases Filtered Out:\t{len(exclude_list)}\n")
    print(f"Number of Cases Remaining:\t{len(include_list)}")
    logfile.write(f"Number of Cases Remaining:\t{len(include_list)}\n")

    return include_list, exclude_list


def summary_of_case_list(case_list, logfile, output_file):
    """print case IDs"""

    with open(f"{output_file}", "w", encoding="utf-8") as file:
        file.write("#case_id\n")
        # loop over final case list
        for case in case_list:
            logfile.write(f"{case}\n")
            file.write(f"{case}\n")


if __name__ == "__main__":
    # get args
    args = get_args()

    # parse config
    config = method_tools.parse_config(str(args.config_file))

    # check and format the output dir
    directory = os.path.abspath(args.output_dir)

    # logging
    with open(f"{directory}/filter_case_list.log", "w", encoding="utf-8") as log:
        print(f"Current Working Directory:\t{os.getcwd()}")
        print(f"Output Directory:\t{directory}")
        log.write(f"Current Working Directory:\t{os.getcwd()}\n")
        log.write(f"Output Directory:\t{directory}\n")

        # set up case lists
        search_case_list = []
        included_case_list = []

        # filter criteria
        filter_options = {}
        for option in vars(args):
            value = getattr(args, option)
            if value:
                if option.startswith("include") or option.startswith("exclude"):
                    filter_options.update({option: value})

        # search by tag(s)
        if args.search == "tags":
            # check for include option
            if args.include_tags is None:
                print("Provide one or more tags to search for cases")
                sys.exit()

            # search for cases
            else:
                search_case_list = search_by_tags(
                    query=args.include_tags, config_dict=config, logfile=log
                )

                # apply filtering
                del filter_options["include_tags"]
                included_case_list, excluded_case_list = filter_case_list(
                    case_list=search_case_list,
                    criteria=filter_options,
                    config_dict=config,
                    logfile=log,
                )

        # search by status
        if args.search == "status":
            # check for include option
            if args.include_status is None:
                print(
                    "Provide one or more statuses to search for cases: New, 'In Progress', or Complete"
                )
                sys.exit()

            # search for cases
            else:
                search_case_list = search_by_status(
                    query=args.include_status, config_dict=config, logfile=log
                )

                # apply filtering
                del filter_options["include_status"]
                included_case_list, excluded_case_list = filter_case_list(
                    case_list=search_case_list,
                    criteria=filter_options,
                    config_dict=config,
                    logfile=log,
                )

        # search by creator or date
        if args.search in ("creators", "dates"):
            # check for include option
            if args.search == "creators" and args.include_creators is None:
                print("Provide one or more case creators to search for cases\n")
                sys.exit()
            elif args.search == "dates" and args.include_dates is None:
                print("Provide a date range to search for cases")
                sys.exit()

            # search across all New, Complete, and In Progress cases
            else:
                search_case_list = get_all_cases(config_dict=config, logfile=log)
                included_case_list, excluded_case_list = filter_case_list(
                    case_list=search_case_list,
                    criteria=filter_options,
                    config_dict=config,
                    logfile=log,
                )

        # cases matching criteria
        case_file = f"{directory}/included_case_list.txt"
        log.write(f"\nCase IDs Matching Search Criteria:\t{case_file}\n")
        print(f"\nCase IDs Matching Search Criteria:\t{case_file}")
        summary_of_case_list(
            case_list=included_case_list, logfile=log, output_file=case_file
        )

        # cases not matching criteria
        case_file = f"{directory}/excluded_case_list.txt"
        log.write(f"\nCase IDs Filtered Out:\t{case_file}\n")
        print(f"\nCase IDs Filtered Out:\t{case_file}")
        summary_of_case_list(
            case_list=excluded_case_list, logfile=log, output_file=case_file
        )
