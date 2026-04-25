# ATLAS2: Asset Tracking and Lifecycle Analysis System 2

## Installation
### **NOTE: This installation only works on Debian-based (or Kali) Linux distros that use `apt` as their package manager!**

1. Clone repository
    ```bash
    git clone https://github.com/ncsu-csc472-spring2026/atlas2.git --depth 1
    ```

2. Configure you local variables environment variables
    - Nagivate to `src/atlas2/`
    - Configure your `.env` file:
        1. Copy the `.env.template` file to `.env`
        ```bash
        cp .env.template .env
        ```
        2. Edit the `RUNZERO_API_KEY` parameter to your RunZero organization key (**Note: Use a separate runZero organization**)
    - Configure your `.service` and `.timer` file *(Only applicable if you plan on running ATLAS2 automatically on a schedule)*
        1. Copy both `atlas2.service.template` and `atlas2.timer.template` to `atlas2.service` and `atlas2.timer` respectively
        ```bash
        cp atlas2.service.template atlas2.service; cp atlas2.timer.template atlas2.timer
        ```
        2. Open `atlas2.service` in a text editor
            1. Replace `[PATH TO MASTER PSU CSV]` with an absolute path to the master PSU CSV file (master_psu_list.csv)
            2. Replace `[PATH TO ALLOWLISTS DIRECTORY]` with the absolute path to the directory containing allowlists for each PSU
            3. Replace `[PATH TO MASTER CRAWLER BLOCKLIST]` with the absolute path to the master blocklist txt file
            4. Save the file and exit
        3. Open `atlas2.timer` in a text editor
            1. Replace `[OnCalendar TIME UNIT]` with a valid Systemd calendar time \
            (See [Systemd Time Manual](https://man7.org/linux/man-pages/man7/systemd.time.7.html#CALENDAR_EVENTS) for more information)
            2. Save the file and exit
    - Return to the root repository directory

- For a full install, including Systemd service/timer enabling, run:
    ```bash
    make service
    ```

    This enables the Systemd timer to run ATLAS2 on all PSUs as often as set in the `atlas2.timer` file.
    The time values can be edited and `make service` can be rerun to replace the old files and restart the timer
    **The service outputs to /etc/atlas2 as timestamped, compressed .tar files by default**

- Otherwise, for a normal system-wide CLI tool install without using the Systemd service, simply run:
    ```bash
    make
    ```

- To remove all installed files and directories, run:
    ```bash
    make clean
    ```

## Usage

To run ATLAS2 on a single PSU, use:
```bash
atlas2
```

```
usage: atlas2 [-h] [-a ALLOWLIST] [-b BLOCKLIST] [-n CONCURRENCY] [-d DEPTH]
              [-m MAXPAGES] [-o OUTPUT] [-i] [-c] [-f [FOLDER]] [-r]
              [psu_id] [psu_name] [psu_domain] [block]

positional arguments:
  psu_id                ID of the PSU to scan (ex. 410 OR 31B)
  psu_name              Name of the PSU (ex. 'Pitt County Schools')
  psu_domain            Root domain of the given PSU (ex. pitt.k12.nc.us OR
                        daretolearn.org)
  block                 Allows for input of comma seperated IP blocks (ex.
                        152.26.20.64/26,152.26.23.0/25)

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
  -r, --runzero         Enables export to runZero (Must have API Token filled
                        in .env file to work!)
```

To run ATLAS2 on a list of PSUs, use:
```bash
atlas2_service
```

```
usage: atlas2_service [-h] [-t [THREADS]] [-f] [-a [ALLOWLIST]]
                      [-b [BLOCKLIST]] [-c] [-r]
                      psu_list output

positional arguments:
  psu_list              Path for the Master PSU list file
  output                Base path for the output. PSU folders will be placed
                        in [output]/psus

options:
  -h, --help            show this help message and exit
  -t, --threads [THREADS]
                        Number of threads to run the program on
  -f, --tarfile         Enables tarfile output to [output] directory with name
                        'atlas2_{date/time}.tar'
  -a, --allowlist [ALLOWLIST]
                        allowlists for each PSU are located
  -b, --blocklist [BLOCKLIST]
                        Master blocklist file for the ATLAS Crawler
  -c, --csv             Enables .csv exporting for all PSUs
  -r, --runzero         Enables export to runZero (Must have API Token filled
                        in .env file to work!)
```

## Configuring theHarvester API Keys
theHarvester has a few optional search engines that are not set up by default and require API keys. See [theHarvester GitHub repository](https://github.com/laramies/theHarvester#modules-that-require-an-api-key) for more information about which seach engines are avaiable and their costs. Some search engines are free to sign up for, but usage may be limited.


API keys for theHarvester are stored in
```bash
/etc/theHarvester/api-keys.yaml
```
Edit this file and add your API keys in the respective search engines, for example:
```bash
brave:
    key: BU8t38jHiuhfa4H9l89gh98PFj2
```

## Output:
The ATLAS2 system has several output options:
    - JSON file (always and default)
    - CSV file (-c/--csv flag)
    - runZero API Import (-r/--runzero flag, requires .env setup)
        - Only assets not in their PSU's assigned IP blocks are added to runZero

### JSON Format:
Each JSON file is a representation of a single PSU and all the assets in it.
```json
{
    “name”: ”Example County Schools”,
    “id”: “00A”,
    “root_domain”: “example.k12.nc.us”
    “asset_count”: number,
    "blocks": [MCNC ASSIGNED IP BLOCKS],
    “assets”: [
        {
            “ip”: “152.xx.xx.201”,
            "in_block”: false|true, # Whether or not this asset is in its PSU's assigned IP block
            “ping_status”: “UP”|”DOWN”, # Is this asset responding to pings
            “asn”: “Cloudflare”,
            “domains”: [“www.example.com”, “www3.example.com” ],
            “source”: “tool used”,
            “timestamp”: “YYYY-MM-DDTHH:mm:SS",
            “comments”: “”
        },
        ...
    ]
}
```

### CSV
Each CSV file is a list of assets for a single PSU. Each file has headers corresponding to each JSON asset's parameters. Assets from theHarvester are shown first, as they are the highest confidence assets with direct subdomains listed.

## Creating a Master PSU List File (eddie_parser.py)
To create a master PSU list from the EDDIE database (in case it needs to be remade):
1. Export an "Customer Report - School" CSV file from [EDDIE](https://apps.schools.nc.gov/eddie)
    - Select only the following columns by clicking `Actions -> Select Columns`:
        PSU Number, PSU Name, Principal Email, and URL School Address
    - Click "Apply"
    - Export by clicking "Actions -> Download -> Download"
2. Upload the raw EDDIE data to the ATLAS2 Server through any means
3. Obtain the assigned IP blocks file from runZero (provided in hand-off package)
4. Run eddie_parser.py with the EDDIE CSV file and the IP Blocks CSV File as arguments:
    ```bash
    ./eddie_parser.py [EDDIE CSV] [IP BLOCKS CSV]
    ```
5. The file exports to `master_psu_list.csv` and can be used with atlas2_service

