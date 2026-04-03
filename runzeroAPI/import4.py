#!/usr/bin/env python3

import requests
import os
import sys
import json

# ================= CONFIG =================
RUNZERO_ORG_TOKEN = "OTBE19B320FC165EB9DC991ED378AC"
BASE_URL = "https://console.runzero.com/api/v1.0/org"
SCAN_ID_FILE = "last_scan_id.txt"
# =========================================

if len(sys.argv) != 3:
    print("Usage: script.py <SITE_NAME> <IP_ADDRESS>")
    sys.exit(1)

site_name_input = sys.argv[1]
ip = sys.argv[2]
cidr = f"{ip}/32"

headers = {
    "Authorization": f"Bearer {RUNZERO_ORG_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# --- Helper: Fetch site list ---
def get_site_by_name(site_name):
    r = requests.get(f"{BASE_URL}/sites", headers=headers, timeout=30)
    r.raise_for_status()
    sites = r.json()
    for s in sites:
        if s.get("name") == site_name:
            return s
    return None

# --- Helper: Fetch full site data ---
def get_site_data(site_id):
    r = requests.get(f"{BASE_URL}/sites/{site_id}", headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()

# --- Helper: Extract existing subnets ---
def extract_subnets(site_json):
    subnets = []

    subnet_data = site_json.get("subnets", {})

    if isinstance(subnet_data, dict):
        for s, meta in subnet_data.items():
            subnets.append(s)
    elif isinstance(subnet_data, list):
        for s in subnet_data:
            subnets.append(s)
    else:
        subnets = []

    # Fallback: use scope if subnets empty
    if not subnets:
        scope = site_json.get("scope", "")
        if scope:
            for s in scope.split(","):
                s = s.strip()
                if s:
                    subnets.append(s)

    return subnets

# --- Step 1: Find or create site ---
site = get_site_by_name(site_name_input)
if site:
    site_id = site["id"]
    print(f"[+] Found site '{site_name_input}' with ID: {site_id}")
else:
    create = input(f"Site '{site_name_input}' does not exist. Create it? [y/n]: ").strip().lower()
    if create != "y":
        print("Exiting without creating site.")
        sys.exit(1)
    payload = {"name": site_name_input, "subnets": []}
    r = requests.post(f"{BASE_URL}/sites", headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    site = r.json()
    site_id = site["id"]
    print(f"[+] Created site '{site_name_input}' with ID: {site_id}")

# --- Step 2: Append subnet ---
site_data = get_site_data(site_id)
existing_subnets = extract_subnets(site_data)
print(f"[+] Existing subnets for site '{site_name_input}': {existing_subnets}")

if cidr in existing_subnets:
    print(f"[-] Subnet {cidr} already exists, skipping append.")
else:
    # Preserve existing subnets format
    new_subnets = site_data.get("subnets", [])
    if isinstance(new_subnets, dict):
        new_subnets[cidr] = {}
    elif isinstance(new_subnets, list):
        new_subnets.append(cidr)
    else:
        new_subnets = [cidr]

    payload = {"name": site_data.get("name"), "subnets": new_subnets}
    r = requests.patch(f"{BASE_URL}/sites/{site_id}", headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    print(f"[+] Added subnet {cidr}")

    # Confirm patch
    site_data = get_site_data(site_id)
    updated_subnets = extract_subnets(site_data)
    print(f"[+] Updated subnets: {updated_subnets}")

# --- Step 3: Trigger scan ---
scan_url = f"{BASE_URL}/sites/{site_id}/scan"
r = requests.put(scan_url, headers=headers, timeout=30)
if r.status_code == 403:
    print("[!] Forbidden: Token lacks permission to start scan (expected if OT token not privileged)")
elif r.status_code != 200:
    print(f"[!] Scan request failed: {r.status_code} {r.text}")
else:
    try:
        resp_json = r.json()
        scan_id = resp_json.get("id")
        if scan_id:
            with open(SCAN_ID_FILE, "w") as f:
                f.write(scan_id)
            print(f"[+] Scan started asynchronously, scan_id saved to {SCAN_ID_FILE}")
        else:
            print("[+] Scan started asynchronously (no scan_id returned)")
    except json.JSONDecodeError:
        print("[+] Scan started asynchronously (response not JSON)")

print("[+] Script complete.")
