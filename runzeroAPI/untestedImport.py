#!/usr/bin/env python3
import requests
import sys
import json

# Environmental variable for org token?
RUNZERO_ORG_TOKEN = "OTBE19B320FC165EB9DC991ED378AC"
BASE_URL = "https://console.runzero.com/api/v1.0"
SCAN_ID_FILE = "last_scan_id.txt"

headers = {
    "Authorization": f"Bearer {RUNZERO_ORG_TOKEN}",
    "Content-Type": "application/json"
}

# User Input check
if len(sys.argv) != 3:
    print("Usage: script.py <SITE_NAME> <IP_ADDRESS>")
    sys.exit(1)

site_name_input = sys.argv[1]
ip = sys.argv[2]
cidr = f"{ip}/32"

# Use site name to get site id
try:
    r = requests.get(f"{BASE_URL}/org/sites", headers=headers, timeout=30)
    r.raise_for_status()
    sites = r.json()
    matching_sites = [s for s in sites if s.get("name") == site_name_input]

    if matching_sites:
        site = matching_sites[0]
        SITE_ID = site["id"]
        print(f"Found site '{site_name_input}' with ID: {SITE_ID}")
    else:
        # Prompt user to create the site if it doesn't exist
        create = input(f"Site '{site_name_input}' does not exist. Create it? [y/n]: ").strip().lower()
        if create != 'y':
            print("Exiting without creating site.")
            sys.exit(1)

        # Create the site
        payload = {"name": site_name_input, "subnets": []}
        r = requests.post(f"{BASE_URL}/org/sites", headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        site = r.json()
        SITE_ID = site["id"]
        print(f"Created new site '{site_name_input}' with ID: {SITE_ID}")

except requests.exceptions.RequestException as e:
    print(f"Error fetching or creating site: {e}")
    sys.exit(1)

# Append subnet
site_url = f"{BASE_URL}/org/sites/{SITE_ID}"

try:
    r = requests.get(site_url, headers=headers, timeout=30)
    r.raise_for_status()
    site_data = r.json()
    subnets = site_data.get("subnets", [])

    existing = {s["cidr"] for s in subnets if "cidr" in s}
    print(f"Existing subnets for site '{site_name_input}': {sorted(existing)}")

    if cidr not in existing:
        subnets.append({"cidr": cidr})
        payload = {"subnets": subnets, "name": site_data.get("name")}
        r = requests.patch(site_url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        print(f"Added subnet {cidr}")
    else:
        print(f"{cidr} already exists in site")

    # Trigger scan
    scan_url = f"{BASE_URL}/org/sites/{SITE_ID}/scan"
    r = requests.post(scan_url, headers=headers, timeout=30)
    r.raise_for_status()

    # Save scan_id if returned
    scan_id = None
    try:
        resp_json = r.json()
        scan_id = resp_json.get("id")
    except json.JSONDecodeError:
        pass

    if scan_id:
        with open(SCAN_ID_FILE, "w") as f:
            f.write(scan_id)
        print(f"Scan started asynchronously. scan_id saved to {SCAN_ID_FILE}")
    else:
        print("Scan started asynchronously (no scan_id returned)")

    print("Script exiting immediately, scan will continue in background.")

except requests.exceptions.RequestException as e:
    print(f"Request error: {e}")
    sys.exit(1)
