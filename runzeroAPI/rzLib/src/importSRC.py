import os
import requests
import json


# Example import "from importSRC import add_assets_to_site"
#
# Function usage:
# add_assets_to_site(
#    site_name: str,
#    ips: list[str],
#    descriptions: list[str],
#    create_if_missing: bool = False
# ) -> dict
#
# Returned dictionary:
# {
#    "site_id": "string",
#    "updated": bool,
#    "scan_id": "string or None",
#    "total_ips": int
# }

# Config
BASE_URL = "https://console.runzero.com/api/v1.0/org"
RUNZERO_API_TOKEN = "placeholder"

HEADERS = {
    "Authorization": f"Bearer {RUNZERO_API_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}


# API functions used in import function
def get_sites():
    r = requests.get(f"{BASE_URL}/sites", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def get_site_by_name(site_name):
    sites = get_sites()
    for site in sites:
        if site.get("name") == site_name:
            return site
    return None


def create_site(site_name):
    payload = {"name": site_name, "subnets": []}
    r = requests.post(f"{BASE_URL}/sites", headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def get_site_data(site_id):
    r = requests.get(f"{BASE_URL}/sites/{site_id}", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def update_site_subnets(site_id, subnets, site_name):
    payload = {"subnets": subnets, "name": site_name}
    r = requests.patch(f"{BASE_URL}/sites/{site_id}", headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def trigger_scan(site_id, cidrs):
    payload = {
        "hosted-zone-name": "auto",
        "targets": ",".join(cidrs)
    }

    r = requests.put(
        f"{BASE_URL}/sites/{site_id}/scan",
        headers=HEADERS,
        json=payload,
        timeout=30
    )
    r.raise_for_status()

    try:
        return r.json().get("id")
    except json.JSONDecodeError:
        return None


# Import function to be called
def add_assets_to_site(site_name, ips, descriptions, create_if_missing=False):
    """
    Main import function:
    - Adds IPs with per-IP descriptions
    - Preserves existing subnet descriptions
    - Triggers scan once per call
    """

    if len(ips) != len(descriptions):
        raise ValueError("IPs and descriptions must have the same length")

    cidrs = [f"{ip}/32" for ip in ips]
    ip_desc_pairs = list(zip(ips, descriptions))

    # Get site, if site doesn't exist create it or exit depending on create_if_missing
    site = get_site_by_name(site_name)

    if not site:
        if not create_if_missing:
            raise ValueError(f"Site '{site_name}' does not exist")
        site = create_site(site_name)

    site_id = site["id"]

    # Get current site state
    site_data = get_site_data(site_id)
    subnets_data = site_data.get("subnets", {})

    # Normalize existing subnets
    if isinstance(subnets_data, dict):
        existing_subnets = list(subnets_data.keys())
    elif isinstance(subnets_data, list):
        existing_subnets = subnets_data
    else:
        existing_subnets = []

    updated = False

    # Apply new subnets
    for ip, desc in ip_desc_pairs:
        cidr = f"{ip}/32"

        if cidr not in existing_subnets:
            if isinstance(subnets_data, dict):
                subnets_data[cidr] = {"description": desc}
            else:
                subnets_data.append(cidr)

            updated = True

    # Push update once
    if updated:
        update_site_subnets(site_id, subnets_data, site_data.get("name"))

    # Always trigger scan
    scan_id = trigger_scan(site_id, cidrs)

    return {
        "site_id": site_id,
        "updated": updated,
        "scan_id": scan_id,
        "total_ips": len(ips)
    }
