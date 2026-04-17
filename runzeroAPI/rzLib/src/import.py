#!/usr/bin/env python3

import requests
import sys
import json

# ================= CONFIG =================
RUNZERO_ORG_TOKEN = "placeholder"
BASE_URL = "https://console.runzero.com/api/v1.0/org"
# =========================================

if len(sys.argv) < 4 or (len(sys.argv) - 2) % 2 != 0:
    print("Usage: python3 add_asset_scan.py <SITE_NAME> <IP1> <DESC1> [<IP2> <DESC2> ...]")
    sys.exit(1)

SITE_NAME_INPUT = sys.argv[1]

# Parse IP/description pairs
args = sys.argv[2:]
ip_desc_pairs = [(args[i], args[i + 1]) for i in range(0, len(args), 2)]

CIDRS = [f"{ip}/32" for ip, _ in ip_desc_pairs]

HEADERS = {
    "Authorization": f"Bearer {RUNZERO_ORG_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def get_sites():
    r = requests.get(f"{BASE_URL}/sites", headers=HEADERS, timeout=30)
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
    payload = {
        "hosted-zone-name": "auto",
        "targets": ",".join(cidr_list)
    }

    r = requests.put(f"{BASE_URL}/sites/{site_id}/scan", headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()

    print("[+] Scan triggered.")

    try:
        scan_id = r.json().get("id")
        if scan_id:
            with open("last_scan_id.txt", "w") as f:
                f.write(scan_id)
            print(f"[+] Scan ID saved: {scan_id}")
    except json.JSONDecodeError:
        pass


# ===== MAIN =====
try:
    sites = get_sites()
    matching_sites = [s for s in sites if s.get("name") == SITE_NAME_INPUT]

    if matching_sites:
        site = matching_sites[0]
        SITE_ID = site["id"]
        print(f"[+] Found site '{SITE_NAME_INPUT}'")
    else:
        create = input(f"Site '{SITE_NAME_INPUT}' does not exist. Create it? [y/n]: ").strip().lower()
        if create != "y":
            sys.exit(1)

        site = create_site(SITE_NAME_INPUT)
        SITE_ID = site["id"]
        print(f"[+] Created site '{SITE_NAME_INPUT}'")

    site_data = get_site_data(SITE_ID)
    subnets_data = site_data.get("subnets", {})

    # Normalize existing subnets
    if isinstance(subnets_data, dict):
        existing_subnets = list(subnets_data.keys())
    elif isinstance(subnets_data, list):
        existing_subnets = subnets_data
    else:
        existing_subnets = []

    print(f"[+] Existing subnets: {existing_subnets}")

    updated = False

    for ip, desc in ip_desc_pairs:
        cidr = f"{ip}/32"

        if cidr not in existing_subnets:
            if isinstance(subnets_data, dict):
                subnets_data[cidr] = {"description": desc}
            else:
                subnets_data.append(cidr)

            print(f"[+] Added {cidr} with description: {desc}")
            updated = True
        else:
            print(f"[+] {cidr} already exists. Description unchanged.")

    if updated:
        update_site_subnets(SITE_ID, subnets_data, site_data.get("name"))
        print("[+] Site updated.")

    trigger_scan(SITE_ID, CIDRS)

except requests.exceptions.HTTPError as e:
    print(f"[!] HTTP error: {e} - {e.response.text}")
    sys.exit(1)
except requests.exceptions.RequestException as e:
    print(f"[!] Request error: {e}")
    sys.exit(1)
