#!/usr/bin/env python3

import requests
import sys
import os
import json

# ================= CONFIG =================
RUNZERO_ORG_TOKEN = "OTBE19B320FC165EB9DC991ED378AC"
BASE_URL = "https://console.runzero.com/api/v1.0/org"
# =========================================

if len(sys.argv) < 3:
    print("Usage: python3 add_asset_scan.py <SITE_NAME> <IP1> [<IP2> ...]")
    sys.exit(1)

SITE_NAME_INPUT = sys.argv[1]
IPS = sys.argv[2:]
CIDRS = [f"{ip}/32" for ip in IPS]

HEADERS = {
    "Authorization": f"Bearer {RUNZERO_ORG_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def get_sites():
    url = f"{BASE_URL}/sites"
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()

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

def trigger_scan(site_id, cidr_list):
    scan_url = f"{BASE_URL}/sites/{site_id}/scan"
    targets_str = ",".join(cidr_list)  # API requires a comma-separated string
    payload = {
        "hosted-zone-name": "auto",
        "targets": targets_str
    }
    r = requests.put(scan_url, headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()
    print("[+] Scan triggered using Hosted Explorer.")
    try:
        resp_json = r.json()
        scan_id = resp_json.get("id")
        if scan_id:
            with open("last_scan_id.txt", "w") as f:
                f.write(scan_id)
            print(f"[+] Scan ID saved: {scan_id}")
    except json.JSONDecodeError:
        pass

# ===== MAIN SCRIPT =====
try:
    sites = get_sites()
    matching_sites = [s for s in sites if s.get("name") == SITE_NAME_INPUT]

    if matching_sites:
        site = matching_sites[0]
        SITE_ID = site["id"]
        print(f"[+] Found site '{SITE_NAME_INPUT}' with ID: {SITE_ID}")
    else:
        create = input(f"Site '{SITE_NAME_INPUT}' does not exist. Create it? [y/n]: ").strip().lower()
        if create != "y":
            print("Exiting without creating site.")
            sys.exit(1)
        site = create_site(SITE_NAME_INPUT)
        SITE_ID = site["id"]
        print(f"[+] Created new site '{SITE_NAME_INPUT}' with ID: {SITE_ID}")

    # Fetch latest site data
    site_data = get_site_data(SITE_ID)
    subnets_data = site_data.get("subnets", {})

    # Handle dict style subnets
    existing_subnets = []
    if isinstance(subnets_data, dict):
        existing_subnets = list(subnets_data.keys())
    elif isinstance(subnets_data, list):
        existing_subnets = subnets_data

    print(f"[+] Existing subnets: {existing_subnets}")

    # Add any new CIDRs
    updated = False
    for cidr in CIDRS:
        if cidr not in existing_subnets:
            if isinstance(subnets_data, dict):
                subnets_data[cidr] = {}  # preserve metadata
            else:
                subnets_data.append(cidr)
            print(f"[+] Subnet {cidr} added.")
            updated = True
        else:
            print(f"[+] Subnet {cidr} already exists.")

    if updated:
        update_site_subnets(SITE_ID, subnets_data, site_data.get("name"))
        print("[+] Site updated successfully with new subnets.")

    # Trigger scan using Hosted Explorer
    trigger_scan(SITE_ID, CIDRS)

except requests.exceptions.HTTPError as e:
    print(f"[!] HTTP error: {e} - {e.response.text}")
    sys.exit(1)
except requests.exceptions.RequestException as e:
    print(f"[!] Request error: {e}")
    sys.exit(1)
