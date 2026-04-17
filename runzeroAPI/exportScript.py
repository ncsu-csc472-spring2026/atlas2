#!/usr/bin/env python3

import requests
import sys

# === Configuration ===
RUNZERO_ORG_TOKEN = ""

URL = "https://console.runzero.com/api/v1.0/export/org/assets.csv"

headers = {
    "Authorization": f"Bearer {RUNZERO_ORG_TOKEN}"
}

try:
    response = requests.get(URL, headers=headers, timeout=60)

    with open("assets.csv", "wb") as f:
        f.write(response.content)

    if response.status_code != 200:
        print(f"Request failed: {response.status_code}", file=sys.stderr)
        sys.exit(1)

    print("Download complete: assets.csv")

except requests.exceptions.RequestException as e:
    print(f"Request error: {e}", file=sys.stderr)
    sys.exit(1)
