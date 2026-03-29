#!/usr/bin/env python3
"""
atlas2.py

Prompt for PSU name and root domain, run theHarvester, pipe output to harvesthelper,
and save harvesthelper's output to harvesthelper.txt
"""
import re               # Regex parser
import shutil
import subprocess
import sys
import argparse         # For command-line argument parsing
import json             # For JSON object export
import datetime as dt   # For timestamps (see strftime())

DOMAIN_RE = re.compile(r'^(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,}$') # Regex object for matching domains at the start of lines (or strings)
IP_RE = re.compile(r'^(?:(?:25[0-5]|(?:2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$', re.M) # Regex object for matching IPs at the start of lines

# Argument parser construction (global so all methods can use arguments)
parser = argparse.ArgumentParser()
parser.add_argument('psu_id', help='ID of the PSU to scan (ex. 410 OR 31B)', nargs='?', default='')
parser.add_argument('psu_name', help='Optional name of the PSU (ex. \'Pitt County Schools\')', nargs='?', default = '')
parser.add_argument('psu_domain', help='Root domain of the given PSU (ex. pitt.k12.nc.us OR daretolearn.org)', nargs='?', default='')
parser.add_argument('-i', '--interactive', help='Interactive mode: program will prompt you to input PSU ID and Domain', action='store_true')

# Parse args into the 'args' variable. Arguments are accessible by using args.[argument name]
args = parser.parse_args()


# Asset Class (object)
class Asset:
    def __init__(self, ip):
        self.ip = ip                    # Asset IP address
        self.in_block = False           # Whether or not the IP is in the MCNC block for the supplied PSU (TODO: Implement check for this)
        self.ping_status = 'DOWN'       # Is this asset responding to pings? Default = DOWN
        self.asn = ''                   # ASN this IP belongs to
        self.domains = {}               # Set of domains associated with this IP (NO DUPLICATES ALLOWED)
        self.source = ''                # What tool was used to find this Asset
        self.timestamp = ''             # Timestamp of when this Asset was last found
        self.comments = ''              # Additional comments about this Asset


# PSU Class (Object), instantiated after all assets for the particular PSU are found
class PSU:
    def __init__(self, name, id, root_domain, asset_count, assets):
        self.name = name                        # PSU name
        self.id = id                            # PSU ID
        self.root_domain = root_domain          # PSU root domain
        self.asset_count = asset_count          # Number of assets found for this PSU
        self.assets = assets                    # List of Asset objects found for this PSU


'''
Returns true if the passed string is a domain, otherwise false
'''
def is_valid_domain(domain: str) -> bool:
    return bool(DOMAIN_RE.match(domain))


'''
If tool is in interactive mode (-i or --interactive), get PSU ID and Domain from the user's stdin
'''
def get_inputs():
    try:
        psu = input("Enter PSU ID (e.g. 410): ").strip()
        while not psu:
            print("PSU ID cannot be empty.")
            psu = input("Enter PSU ID (e.g. 410): ").strip()

        name = input("Enter PSU Name (e.g. Pitt County Schools): ").strip()
        while not name:
            print("PSU Name cannot be empty.")
            psu = input("Enter PSU Name (e.g. Pitt County Schools): ").strip()

        root_domain = input("Enter root domain (e.g. gcsnc.com): ").strip()
        while not is_valid_domain(root_domain):
            print(f"Invalid domain: {root_domain}")
            root_domain = input("Enter root domain (e.g. gcsnc.com): ").strip()

        return psu, name, root_domain
    except (EOFError, KeyboardInterrupt):
        print("\nInput cancelled.", file=sys.stderr)
        sys.exit(1)


'''
Locates a tool with the passed name on the host system, program exits if tool is not found in PATH
'''
def find_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        print(f"[!] Could not find '{name}' in PATH", file=sys.stderr)
        sys.exit(1)
    return path


'''
Returns a string of all IPs found in the harvester_output (or any passed string)
'''
def find_harvester_ips(harvester_output: str) -> str:
    return IP_RE.findall(harvester_output)

'''
Returns UP or DOWN depending if the passes IP is responding to pings
'''
def ping_status(ip: str) -> str:
    print(f'[*] Pinging {ip}')
    command = ['ping', '-c', '1', '-W', '0.5', ip] # Ping once, timeout after 0.5 seconds
    result = subprocess.run(command, capture_output=False, text=True)

    if not result.returncode: # result will == 0 upon success
        return 'UP'
    else:
        return 'DOWN'


'''
Returns the ASN of the passed IP
'''
def asn(ip: str) -> str:
    print(f'[*] Finding ASN of {ip}')
    command = ['whois', ip]
    result = subprocess.run(command, capture_output=True, text=True).stdout
    result = result.splitlines()
    index = -1
    line: str = None

    for line in result:
        # Check to find various spellings of Organization
        index = line.find('Organization')
        if index == -1:
            index = line.find('OrgName')
        if index == -1:
            index = line.find('Organisation')

        # If not found, continue to next line, otherwise break out of 
        if index == -1:
            continue
        else:
            break

    # If not found in any line, return empty string
    if not line:
        return ''

    # Return the 'after' portion of the tuple returned by line.partition(':')
    return line.partition(":")[-1].strip()


'''
Main function, starts program execution
'''
def main():
    # If interactive mode, ask user for inputs
    if args.interactive:
        psu, name, root_domain = get_inputs()
    else: # otherwise fill in variable from args
        psu = args.psu_id
        name = args.psu_name
        root_domain = args.psu_domain

        # Exit on error (non-interactive mode and empty arguments)
        if not psu or not root_domain or not name or not is_valid_domain(root_domain):
            print("[!] Invalid PSU ID or Domain or Name", file=sys.stderr)
            sys.exit(1)

    # Find all necessary utilities in PATH
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

    # Combine stdout + stderr so nothing is lost and convert to string
    harvester_output = (harvester_result.stdout + harvester_result.stderr).decode('UTF-8')

    if not harvester_output.strip():
        print("[!] theHarvester produced no output", file=sys.stderr)
        sys.exit(2)


    '''
    # Save raw output for reference / debugging
    with open("harvester_output.txt", "wb") as f:
        f.write(harvester_output)
    '''

    if harvester_result.returncode != 0:
        print(f"[!] theHarvester exited with code {harvester_result.returncode}", file=sys.stderr)
        # Don't hard-exit — theHarvester sometimes returns non-zero even on partial success

    print("[+] theHarvester completed")


    # ── Step 2: Parse theHarvester output into JSON objects ─────────

    print(harvester_output) # DEBUG
    print(find_harvester_ips(harvester_output)) ## DEBUG
    
    # Iterate over all IPs found by theHarvester
    harvester_assets = []
    for ip in find_harvester_ips(harvester_output):
        asset = Asset(ip)
        asset.ping_status = ping_status(ip)
        asset.asn = asn(ip)
        asset_string = json.dumps(asset, default=lambda o: o.__dict__, indent=4) # DEBUG
        print(asset_string) # DEBUG
        # TODO: Add functions to pupulate the rest of the asset object fields!
        harvester_assets.append(asset) # Last thing in the for loop will be adding the asset object to the list

if __name__ == "__main__":
    main()
