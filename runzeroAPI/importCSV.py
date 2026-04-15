#!/usr/bin/env python3

import requests
import sys
import json
import csv

# ================= CONFIG =================
RUNZERO_ORG_TOKEN = "placeholder"
BASE_URL = "https://console.runzero.com/api/v1.0/org"
# =========================================

if len(sys.argv) != 3:
    print("Usage: python3 importCSV.py <SITE_NAME> <CSV_FILE> \nCSV Format: ip,description")
    sys.exit(1)

SITE_NAME_INPUT = sys.argv[1]
CSV_FILE = sys.argv[2]

HEADERS = {
    "Authorization": f"Bearer {RUNZERO_ORG_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def load_csv(file_path):
    data = {}
    try:
        with open(file_path, newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 2:
                    continue
                ip = row[0].strip()
                desc = row[1].strip()
                if ip:
                    data[f"{ip}/32"] = desc
    except Exception as e:
        print(f"[!] Failed to read CSV: {e}")
        sys.exit(1)
    return data

def get_sites():
    r = requests.get(f"{BASE_URL}/sites", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()

def create_site(site_name):
    payload = {"name": site_name, "subnets": {}}
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
    targets_str = ",".join(cidr_list)

    payload = {
        "hosted-zone-name": "auto",
        "targets": targets_str
    }

    r = requests.put(scan_url, headers=HEADERS, json=payload, timeout=30)
    r.raise_for_status()

    print("[+] Scan triggered.")

    try:
        resp_json = r.json()
        scan_id = resp_json.get("id")
        if scan_id:
            with open("last_scan_id.txt", "w") as f:
                f.write(scan_id)
            print(f"[+] Scan ID saved: {scan_id}")
    except json.JSONDecodeError:
        pass

# ================= MAIN =================

try:
    csv_data = load_csv(CSV_FILE)
    cidrs = list(csv_data.keys())

    sites = get_sites()
    matching_sites = [s for s in sites if s["name"] == SITE_NAME_INPUT]

    if matching_sites:
        site = matching_sites[0]
        SITE_ID = site["id"]
        print(f"[+] Found site '{SITE_NAME_INPUT}' with ID: {SITE_ID}")
    else:
        create = input(f"Site '{SITE_NAME_INPUT}' does not exist. Create it? [y/n]: ").strip().lower()
        if create != "y":
            print("Exiting.")
            sys.exit(1)

        site = create_site(SITE_NAME_INPUT)
        SITE_ID = site["id"]
        print(f"[+] Created site '{SITE_NAME_INPUT}'")

    site_data = get_site_data(SITE_ID)
    subnets_data = site_data.get("subnets", {})

    # Normalize to dict format
    if isinstance(subnets_data, list):
        subnets_data = {cidr: {} for cidr in subnets_data}
    elif not isinstance(subnets_data, dict):
        subnets_data = {}

    updated = False

    for cidr, desc in csv_data.items():
        if cidr not in subnets_data:
            subnets_data[cidr] = {"description": desc}
            print(f"[+] Added {cidr} ({desc})")
            updated = True
        else:
            existing_desc = subnets_data[cidr].get("description")
            if not existing_desc:
                subnets_data[cidr]["description"] = desc
                print(f"[+] Added missing description to {cidr} -> {desc}")
                updated = True
            else:
                print(f"[+] {cidr} exists, keeping existing description")

    if updated:
        update_site_subnets(SITE_ID, subnets_data, site_data.get("name"))
        print("[+] Site updated.")
    else:
        print("[+] No changes needed.")

    trigger_scan(SITE_ID, cidrs)

except requests.exceptions.HTTPError as e:
    print(f"[!] HTTP error: {e} - {e.response.text}")
    sys.exit(1)
except requests.exceptions.RequestException as e:
    print(f"[!] Request error: {e}")
    sys.exit(1)
