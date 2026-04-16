# ATLAS2: Asset Tracking and Lifecycle Analysis System 2

## Installation Guide:
1. Clone repository

2. Configure you local variables environment variables
    - Configure your `.env` file:
        1. Copy the `.env.template` file to `.env`
        2. Edit the `RUNZERO_API_KEY` parameter to your RunZero organization key, **IMPORTANT: DO NOT SET THIS TO YOUR PRODUCTION RUNZERO ORGANIZATION, USE A SEPARATE ORGANIZATION TO AVOID FILLING YOUR ORG WITH POTENTIAL JUNK**
    
    - Configure your `.service` and `.timer` file *(Only applicable if you plan on running ATLAS2 automatically on a schedule)*
        1. Copy both `atlas2.service.template` and `atlas2.timer.template` to `atlas2.service` and `atlas2.timer` respectively
        2. Create a directory for 
        2. Open `atlas2.service` in a text editor
        3. Edit the `ConditionPathExists`



3. For a full install, including Systemd service/timer enabling, run:
    ```make service```

   Otherwise, for a normal system-wide CLI tool install without using Systemd servies, simply run:
    ```make```

## Usage:

To run ATLAS2 on a single PSU, use `atlas2`:

```
usage: atlas2 [-h] [-a ALLOWLIST] [-b BLOCKLIST] [-n CONCURRENCY] [-d DEPTH]
              [-m MAXPAGES] [-o OUTPUT] [-i] [-c] [-f [FOLDER]]
              [psu_id] [psu_name] [psu_domain] [block]

positional arguments:
  psu_id                ID of the PSU to scan (ex. 410 OR 31B)
  psu_name              Name of the PSU (ex. 'Pitt County Schools')
  psu_domain            Root domain of the given PSU (ex. pitt.k12.nc.us OR
                        daretolearn.org)
  block                 Allows for input of comma seperated IP blocks
                        (ex. 132.66.74.64/26,126.86.23.0/24)

options:
  -h, --help            show this help message and exit
  -a, --allowlist ALLOWLIST
                        Allowlist file for crawler (default: allowlist.txt)
  -b, --blocklist BLOCKLIST
                        Blocklist file for crawler (default: blocklist.txt)
  -n, --concurrency CONCURRENCY
                        Max concurrent sockets (default: 50)
  -d, --depth DEPTH     Max crawl depth (default: 3)
  -m, --maxpages MAXPAGES
                        Max pages to crawl (default: 1000)
  -o, --output OUTPUT   Output file for crawler results
  -i, --interactive     Interactive mode: program will prompt you to input PSU
                        ID and Domain
  -c, --csv             Enables .csv exporting to "{psu_id}_{psu_name}.csv"
  -f, --folder [FOLDER]
                        Path to directory where all output files will be
                        stored
```

To run ATLAS2 on a list of PSUs, use `atlas2_service`:

```
usage: atlas2_service [-h] [-t [THREADS]] [-f [TARFILE]] [-b [BLOCKLIST]]
                      psu_list output

positional arguments:
  psu_list              Path for the Master PSU list file
  output                Directory path for the output folders for each PSU
                        will be placed

options:
  -h, --help            show this help message and exit
  -t, --threads [THREADS]
                        Number of threads to run the program on
  -f, --tarfile [TARFILE]
                        Output tarfile where all output directories will be
                        archived to
  -b, --blocklist [BLOCKLIST]
                        Master blocklist file for the ATLAS Crawler
```

You must already have the master .csv file list of PSUs before running `atlas2_service`. 

Likewise, if using the `-b / --blocklist` flag, you must have the master blocklist file. 


