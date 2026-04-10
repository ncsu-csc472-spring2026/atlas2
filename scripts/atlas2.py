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
import atlas2_csv as csv # For CSV Exporting
import ipaddress

DOMAIN_RE = re.compile(r'^(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,}$') # Regex object for matching domains that take up the entire line (or from user input)
DOMAIN_START_RE = re.compile(r'^(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,}') # Regex object for matching domains at the start of lines (or strings)
IP_RE = re.compile(r'^(?:(?:25[0-5]|(?:2[0-4]|1\d|[1-9]|)\d)\.?\b){4}$', re.M) # Regex object for matching IPs at the start of lines

# Argument parser construction (global so all methods can use arguments)
parser = argparse.ArgumentParser()
parser.add_argument('psu_id', help='ID of the PSU to scan (ex. 410 OR 31B)', nargs='?', default='')
parser.add_argument('psu_name', help='Optional name of the PSU (ex. \'Pitt County Schools\')', nargs='?', default = '')
parser.add_argument('psu_domain', help='Root domain of the given PSU (ex. pitt.k12.nc.us OR daretolearn.org)', nargs='?', default='')
parser.add_argument('block', help='Allows for input of comma seperated IP blocks (ex.152.26.20.64/26,152.26.23.0/25)', nargs='?', default='')
parser.add_argument('-i', '--interactive', help='Interactive mode: program will prompt you to input PSU ID and Domain', action='store_true')
parser.add_argument('-c', '--csv', help='Enables .csv exporting to "{psu_id}_{psu_name}.csv"', action='store_true')

# Parse args into the 'args' variable. Arguments are accessible by using args.[argument name]
args = parser.parse_args()


# Asset Class (object)
class Asset:
    def __init__(self, ip):
        self.ip = ip                    # Asset IP address
        self.in_block = False           # Whether or not the IP is in the MCNC block for the supplied PSU (TODO: Implement check for this)
        self.ping_status = 'DOWN'       # Is this asset responding to pings? Default = DOWN
        self.asn = ''                   # ASN this IP belongs to
        self.domains = []               # List of domains associated with this IP
        self.source = ''                # What tool was used to find this Asset
        self.timestamp = ''             # Timestamp of when this Asset was last found
        self.comments = ''              # Additional comments about this Asset

    # Equality check between two Asset object, if the IPs are the same, the Assets are the same (usable with ==)
    def __eq__(self, other):
        if isInstance(other, Asset):
            return self.ip == other.ip
        return NotImplemented


# PSU Class (Object), instantiated after all assets for the particular PSU are found
class PSU:
    def __init__(self, name, id, root_domain, asset_count, assets, blocks):
        self.name = name                        # PSU name
        self.id = id                            # PSU ID
        self.root_domain = root_domain          # PSU root domain
        self.asset_count = asset_count          # Number of assets found for this PSU
        self.assets = assets                    # List of Asset objects found for this PSU
        self.blocks = blocks                    # List of IP blocks to check

'''
Returns true if the passed string is a domain, otherwise false
'''
def is_valid_domain(domain: str) -> bool:
    return bool(DOMAIN_RE.match(domain))

'''
Checks if the input IP blocks are valid
'''
def is_valid_blocks(blocks_str: str) -> list:
    blocks = []
    if(blocks_str == ""):
        print(f"[!] No block given", file = sys.stderr)
        sys.exit(1)
    else:
        for block in blocks_str.split(','):
            block = block.strip()
        try:
            blocks.append(ipaddress.ip_network(block, strict=False))
        except ValueError:
            print(f"[!] Invalid block: {block}", file = sys.stderr)
            sys.exit(1)

    return blocks

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
            name = input("Enter PSU Name (e.g. Pitt County Schools): ").strip().replace(' ', '_')

        root_domain = input("Enter root domain (e.g. gcsnc.com): ").strip()
        while not is_valid_domain(root_domain):
            print(f"Invalid domain: {root_domain}")
            root_domain = input("Enter root domain (e.g. gcsnc.com): ").strip()

        blocks_input = input("Enter a list of ip blocks seperated by commas (e.g.152.26.20.64/26,152.26.23.0/25): ").strip()
        blocks = is_valid_blocks(blocks_input)

        return psu, name, root_domain, blocks
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
    result = subprocess.run(command, capture_output=True, text=True)

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

        # If not found, continue to next line, otherwise break out of for loop
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
Get the current timestamp in ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
'''
def timestamp() -> str:
    return dt.datetime.now().isoformat(timespec='seconds')


'''
Return list of tuples containing each unique Harvester domain and their corresponding list of IPs
e.g. [ ('www.example.com', ['1.2.3.4', '2.3.4.5']), ('test.school.com', ['8.8.8.8']) ]
'''
def get_harvester_domains(harvester_output: str) -> list:
    result = [] # List of tuples 
    # For each line in the harvester_output file passed...
    for line in harvester_output.splitlines():
        ips = []
        d = ''
        # ... check if the line starts with a domain string, and if so, split line into the domain string and the comma-separated list of IPs
        if DOMAIN_START_RE.match(line): # If the line contains a domain at the start of the string
            d, s, ip_commas = line.partition(':')
            ips = ip_commas.split(',') # Split comma-separated list into an actual List object
            result.append((d, ips)) # Add finished tuple to the results list
        elif line == "[*] Searching Shodan.": # If we get to the line where theHarvester started searching Shodan, we can return
            return result

    return result
'''
Checks if an ip address is in the provided list of IP blocks
'''
def ip_block_checker(ip: str, blocks: list) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
        for block in blocks:
            if ip_obj in block:
                return True
    except ValueError:
        return False
    return False

'''
Return list of domains associated with the passed IP and return List from get_harvester_domains()
'''
def get_domains_from_ip(domain_list: list, ip: str) -> list:
    domains = []
    # For each (domain, [ips]) tuple in domain_list...
    for pair in domain_list:
        # ... if IP in the tuple, add the domain of the tuple to the domains list to return
        if ip in pair[1] and pair[0] not in domains: # Avoid duplicates as well
            domains.append(pair[0])

    return domains

'''
Main function, starts program execution
'''
def main():

    # Holds list of blocks input by the user
    blocks = []

    # If interactive mode, ask user for inputs
    if args.interactive:
        psu, name, root_domain, blocks = get_inputs()
    else: # otherwise fill in variable from args
        psu = args.psu_id.strip()
        name = args.psu_name.strip().replace(' ', '_')
        root_domain = args.psu_domain.strip()
        if args.block:
            blocks = is_valid_blocks(args.block)

        # Exit on error (non-interactive mode and empty arguments)
        if not psu or not root_domain or not name or not is_valid_domain(root_domain):
            print("[!] Invalid PSU ID or Domain or Name", file=sys.stderr)
            sys.exit(1)

    # Find all necessary utilities in PATH
    harvester_bin = find_tool("theHarvester")

    # ── Step 1: Run theHarvester, capturing both stdout + stderr ──────────────
    print("\n[*] Running theHarvester...")

    # theHarvester command in List for for subprocess.run()
    harvester_cmd = [harvester_bin, "-d", root_domain, "-r", "-s", "-b", "all"]

    # Execute theHarvester
    harvester_result = subprocess.run(
        harvester_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,  # capture stderr too — some versions write here
    )

    # Combine stdout + stderr so nothing is lost and convert to string
    harvester_output = (harvester_result.stdout + harvester_result.stderr).decode('UTF-8')

    # If theHarvester output is empty, something has gone horribly wrong, so exit with error
    if not harvester_output.strip():
        print("[!] theHarvester produced no output", file=sys.stderr)
        sys.exit(2)

    # If theHarvester return code != 0, print an error but don't exit
    if harvester_result.returncode != 0:
        print(f"[!] theHarvester exited with code {harvester_result.returncode}", file=sys.stderr)
        # Don't hard-exit — theHarvester sometimes returns non-zero even on partial success

    print("[+] theHarvester completed")


    # ── Step 2: Parse theHarvester output into JSON objects ─────────
    print("\n[*] Starting Harvester Output Parsing")

    # print(harvester_output) # DEBUG
    # print(find_harvester_ips(harvester_output)) ## DEBUG

    # Iterate over all IPs found by theHarvester
    harvester_assets = []
    timestamp_string = timestamp()
    harvester_domains = get_harvester_domains(harvester_output)
    # print(harvester_domains) # DEBUG

    # Construct Asset objects for every IP found by theHarvester
    for ip in find_harvester_ips(harvester_output):
        asset = Asset(ip)                                               # Set IP
        asset.ping_status = ping_status(ip)                             # Set Ping status
        asset.asn = asn(ip)                                             # Set ASN
        asset.domains = get_domains_from_ip(harvester_domains, ip)      # Set Domains List
        asset.source = 'theHarvester'                                   # Set Source (theHarvester)
        asset.timestamp = timestamp_string                              # Set Timestamp to timestamp calculated before the for loop
    
        # Checks if the ip of the asset is in the blocks
        if blocks:
            asset.in_block = ip_block_checker(ip, blocks)
    
        harvester_assets.append(asset)                                  # Append asset to harvester_assets, will combine later with crawler_assets to create unified list

    # JSONify every Asset (DEBUG)
    for asset in harvester_assets:
        asset_string = json.dumps(asset, default=lambda o: o.__dict__, indent=4) # DEBUG, JSONify the Asset object
        print(asset_string) # DEBUG, print JSON to stdout

    print(f"\n[+] Finished Harvester Parsing, got {len(harvester_assets)} assets!")


    ### DATA EXPORTING DEBUG ###

    # Create PSU object
    psu_object = PSU(name, psu, root_domain, 123, harvester_assets)
    # CSV export functions if the flag is set
    if args.csv:
        csv.export_assets_as_csv(f'asset_list.csv', harvester_assets)
        csv.export_psu_as_csv(psu_object)

if __name__ == "__main__":
    main()

