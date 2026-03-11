#!/usr/bin/env python3
"""atlas2.py

Prompt for PSU name and root domain, run theHarvester, pipe output to harvesthelper,
and save harvesthelper's output to harvesthelper.txt
"""
import re
import shutil
import subprocess
import sys

DOMAIN_RE = re.compile(r"^(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,}$")


def is_valid_domain(domain: str) -> bool:
    return bool(DOMAIN_RE.match(domain))


def get_inputs():
    try:
        psu = input("Enter PSU ID (e.g. 410): ").strip()
        while not psu:
            print("PSU ID cannot be empty.")
            psu = input("Enter PSU ID (e.g. 410): ").strip()

        root_domain = input("Enter root domain (e.g. gcsnc.com): ").strip()
        while not is_valid_domain(root_domain):
            print(f"Invalid domain: {root_domain}")
            root_domain = input("Enter root domain (e.g. gcsnc.com): ").strip()

        return psu, root_domain
    except (EOFError, KeyboardInterrupt):
        print("\nInput cancelled.", file=sys.stderr)
        sys.exit(1)


def find_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        print(f"[!] Could not find '{name}' in PATH", file=sys.stderr)
        sys.exit(1)
    return path


def main():
    psu, root_domain = get_inputs()

    harvester_bin = find_tool("theHarvester")
    harvesthelper_bin = find_tool("harvesthelper")

    # ── Step 1: Run theHarvester, capturing both stdout + stderr ──────────────
    print("\n[*] Running theHarvester...")
    harvester_cmd = [harvester_bin, "-d", root_domain, "-r", "-s", "-b", "all"]

    harvester_result = subprocess.run(
        harvester_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,  # capture stderr too — some versions write here
    )

    # Combine stdout + stderr so nothing is lost
    harvester_output = harvester_result.stdout + harvester_result.stderr

    if not harvester_output.strip():
        print("[!] theHarvester produced no output", file=sys.stderr)
        sys.exit(1)

    # Save raw output for reference / debugging
    with open("harvester_output.txt", "wb") as f:
        f.write(harvester_output)

    if harvester_result.returncode != 0:
        print(f"[!] theHarvester exited with code {harvester_result.returncode}", file=sys.stderr)
        # Don't hard-exit — theHarvester sometimes returns non-zero even on partial success

    print("[+] theHarvester completed")

    # ── Step 2: Run harvesthelper with the output file as an argument ─────────
    print("[*] Running harvesthelper...")
    harvesthelper_cmd = ["bash", harvesthelper_bin, psu, "harvester_output.txt"]

    harvesthelper_result = subprocess.run(
        harvesthelper_cmd,
        stderr=subprocess.PIPE,  # only capture stderr for error reporting
        # stdout is NOT captured — let harvesthelper write its own output file
    )

    if harvesthelper_result.returncode != 0:
        print(f"[!] harvesthelper failed (exit {harvesthelper_result.returncode})", file=sys.stderr)
        print(harvesthelper_result.stderr.decode(errors="replace"), file=sys.stderr)
        sys.exit(1)

    print("[+] harvesthelper finished")


if __name__ == "__main__":
    main()
