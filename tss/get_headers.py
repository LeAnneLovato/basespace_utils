#!/usr/bin/env python3
"""TSS API Headers"""

############################################################################################
# Author 1: Batsal Devkota
# Author Email 1: bdevkota@illumina.com
# Author 2: LeAnne Lovato
# Author Email 2: llovato@illumina.com
# Author 3: Jennifer Shah
# Author Email 3: jshah@illumina.com
# A set of helper functions to get header fields for various API calls
############################################################################################


# OUI API calls
def get_headers_oui(ps_token, domain_name, wg):
    """Interpretation (OUI) headers"""

    oui_headers = {
        "accept": "*/*",
        "Content-Type": "application/json",
        "Authorization": "{0}".format(ps_token),
        "X-ILMN-Domain": "{0}".format(domain_name),
        "X-ILMN-Workgroup": "{0}".format(wg),
    }
    return oui_headers


# VRS API calls
def get_headers_vrs(ps_token, domain_name, wg):
    """Interpretation (VRS) headers"""

    vrs_headers = {
        "accept": "*/*",
        "Content-Type": "application/json",
        "Authorization": "{0}".format(ps_token),
        "X-ILMN-Domain": "{0}".format(domain_name),
        "X-ILMN-Workgroup": "{0}".format(wg),
    }
    return vrs_headers


# FMS API calls
def get_headers_fms(ps_token, wg):
    """Filter (FMS) headers"""

    fms_headers = {
        "accept": "*/*",
        "Authorization": "{0}".format(ps_token),
        "X-ILMN-Workgroup": "{0}".format(wg),
    }
    return fms_headers


# KNS API calls
def get_headers_kns(ps_token, domain_name):
    """Knowledge Network (KNS) headers"""

    kns_headers = {
        "accept": "*/*",
        "Content-Type": "application/json",
        "X-Auth-Token": "{0}".format(ps_token),
        "X-ILMN-Domain": "{0}".format(domain_name),
    }
    return kns_headers


# DRS API calls
def get_headers_drs(ps_token, domain_name, wg):
    """Reporting (DRS) headers"""

    drs_headers = {
        "accept": "*/*",
        "X-Auth-Token": "{0}".format(ps_token),
        "X-ILMN-Domain": "{0}".format(domain_name),
        "X-ILMN-Workgroup": "{0}".format(wg),
    }
    return drs_headers
