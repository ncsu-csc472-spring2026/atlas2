#!/usr/bin/python3

import sys # Arguments and exiting
import os # For file/folder creation
import threading # For concurrent running instances of atlas2.py
import csv # To read master PSU list
import subprocess # To run atlas2 with command-line arguments
import ast # To get literal List objects from CSV
import argparse
import tarfile # For zipping output

# Constants defining indeces of the PSU's ID, name, domain, URL (unused), and IP blocks in the master PSU CSV
ID_IDX = 0
NAME_IDX = 1
DOMAIN_IDX = 2
URL_IDX = 3 # UNUSED
BLOCKS_IDX = 4

DEFAULT_MODE = 0o755

# Maximum number of ATLAS2 scans capable of running concurrently
MAX_THREADS = 10

# Command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("psu_list", help="Path for the Master PSU list file")
parser.add_argument("output", help="Directory path for the output folders for each PSU will be placed")
parser.add_argument("-t", "--threads", help="Number of threads to run the program on", nargs="?", type=int, default=MAX_THREADS)
parser.add_argument("-f", "--tarfile", help="Output tarfile where all output directories will be archived to", nargs="?", default="")
parser.add_argument("-b", "--blocklist", help="Master blocklist file for the ATLAS Crawler", nargs="?", default="")

args = parser.parse_args()

# Bounded Semaphore that each thread must acquire to start, bounding the number of threads running
sema = threading.BoundedSemaphore(value=args.threads)

"""
Thread Task that runs that atlas2 program with the passed arguments
Task must acquire a semaphore to run
"""
def run_atlas2(process_str: list, full_dir: str, full_name: str):
    with sema: # Automatically acquire and release semaphore
        # Open stderr and stdout text fiels for output redirection
        with open(os.path.join(full_dir, f"{full_name}_stdout.txt"), "w", encoding="UTF-8") as stdout_file, open(os.path.join(full_dir, f"{full_name}_stderr.txt"), "w", encoding="UTF-8") as stderr_file:
            # Run ATLAS2 Script
            print(f"Running ATLAS2 on {full_name}")
            subprocess.run(process_str, stdout=stdout_file, stderr=stderr_file, check=True)

    return


"""
Main function, creates threads out of all master PSU list file rows and waits for them to finish
"""
def main():

    threads = [] # List of thread worker, one for each PSU

    # Context manager, open file pointed to by psu_list argument
    with open(args.psu_list, "r", encoding="UTF-8") as master_list:
        master_reader = csv.reader(master_list, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # ID, NAME, DOMAIN, URL (unused), ASSIGNED IP BLOCK ARRAY
        for row in master_reader: # Each PSU
            full_name = '_'.join([row[ID_IDX], row[NAME_IDX]]) # For use in file/folder storage
            full_dir = os.path.join(args.output, full_name) # /usr/atlas2/{ID}_{NAME}

            # Get List of IP blocks from master list, literally evaluating the column as a List
            blocks_list = ast.literal_eval(row[BLOCKS_IDX])
            # Convert List to comma-separated str to pass to atlas2
            blocks_str = ','.join(blocks_list) if blocks_list else ""

            # String List for the atlas2 program and arguments
            # TODO: Add crawler arguments (allowlist, blocklist, depth, etc.)
            process_str = [ "atlas2",
                            row[ID_IDX],
                            row[NAME_IDX],
                            row[DOMAIN_IDX],
                            blocks_str,
                            "-c",
                            "-f", full_dir
                           ]

            # If global blocklist is defined...
            if args.blocklist:
                # Make sure the path is valid first
                if os.path.exists(args.blocklist):
                    process_str.extend(["-b", args.blocklist]) # Append flag + arg to the atlas2 command-line arguments
                else: # If blocklist path is invalid, print error and quit
                    print(f"[!] Invalid blocklist path!")
                    sys.exit(1)

            # If the full PSU path does not exist, create it
            if not os.path.exists(full_dir):
                os.mkdir(full_dir, DEFAULT_MODE)

            print(f"[+] Creating thread for {full_name} with blocks string: {blocks_str}")
            t = threading.Thread(target=run_atlas2, args=(process_str, full_dir, full_name))
            threads.append(t)

    for t in threads:
        t.start()

    i = len(threads)
    for t in threads:
        print(f"[-] Threads Remaining: {i}", file=sys.stdout)
        t.join()
        i -= 1

    if args.tarfile:
        print(f"[*] Writing Tarfile to {args.tarfile}")
        if os.path.exists(args.tarfile):
            print(f"[!] {args.tarfile} already exists, removing")
            os.remove(args.tarfile)
        with tarfile.open(args.tarfile, "w:gz") as tar:
            tar.add(args.output, recursive=True)
            print(f"[+] Tarfile written to {args.tarfile}")

if __name__ == "__main__":
    main()
    sys.exit(0)

