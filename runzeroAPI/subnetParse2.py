#!/usr/bin/env python3

import requests
import os
import sys

# ====== CONFIG ======
API_TOKEN = "OTBE19B320FC165EB9DC991ED378AC"
SITE_ID = "2f119478-eb16-4790-b6a0-55073977b356"
BASE_URL = "https://console.runzero.com/api/v1.0/org"
# ====================


def get_site_data(token, site_id):
    url = f"{BASE_URL}/sites/{site_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"[!] API Error: {response.status_code}")
        print(response.text)
        sys.exit(1)

    return response.json()


def extract_subnets(site_json):
    subnets = []

    subnet_data = site_json.get("subnets", {})

    # ✅ Handle dict where keys are subnets (your case)
    if isinstance(subnet_data, dict):
        for subnet, meta in subnet_data.items():
            description = ""
            if isinstance(meta, dict):
                description = meta.get("description", "")
            subnets.append((subnet, description))

    # ⚠️ Fallback: if it's ever a list
    elif isinstance(subnet_data, list):
        for subnet in subnet_data:
            subnets.append((subnet, ""))

    # ⚠️ Fallback: check scope if subnets empty
    if not subnets:
        scope = site_json.get("scope", "")
        if scope:
            for s in scope.split(","):
                s = s.strip()
                if s:
                    subnets.append((s, "from scope"))

    return subnets


def main():
    print("[*] Fetching site data...")

    if not API_TOKEN:
        print("[!] No API token set.")
        sys.exit(1)

    site_data = get_site_data(API_TOKEN, SITE_ID)

    print(f"[+] Site Name: {site_data.get('name', 'Unknown')}")
    print(f"[+] Site ID: {site_data.get('id', 'Unknown')}")
    print("\n[+] Subnets:\n")

    subnets = extract_subnets(site_data)

    if not subnets:
        print("[-] No subnets found.")
        return

    for subnet, desc in subnets:
        if desc:
            print(f"  - {subnet} ({desc})")
        else:
            print(f"  - {subnet}")


if __name__ == "__main__":
    main()
