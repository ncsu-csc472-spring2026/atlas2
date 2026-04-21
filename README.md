# ATLAS2: Asset Tracking and Lifecycle Analysis System 2

## Installation
### **NOTE: This installation only works on Debian-based (or Kali) Linux distros that use `apt` as their package manager!**

1. Clone repository \
    ```bash
    git clone https://github.com/ncsu-csc472-spring2026/atlas2.git --depth 1
    ```

2. Configure you local variables environment variables
    - Nagivate to `src/atlas2/`
    - Configure your `.env` file:
        1. Copy the `.env.template` file to `.env` \
        ```bash
        cp .env.template .env
        ```
        2. Edit the `RUNZERO_API_KEY` parameter to your RunZero organization key (**Note: Use a separate runZero organization**)
    - Configure your `.service` and `.timer` file *(Only applicable if you plan on running ATLAS2 automatically on a schedule)*
        1. Copy both `atlas2.service.template` and `atlas2.timer.template` to `atlas2.service` and `atlas2.timer` respectively \
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

3. For a full install, including Systemd service/timer enabling, run: \
    ```bash
    make service
    ```


    This enables the Systemd timer to run ATLAS2 on all PSUs as often as set in the `atlas2.timer` file.
    The time values can be edited and `make service` can be rerun to replace the old files and restart the timer
    **The service outputs to /etc/atlas2 as timestamped, compressed .tar files by default**

    Otherwise, for a normal system-wide CLI tool install without using the Systemd service, simply run: \
    ```bash
    make
    ```

    To remove all installed files and directories, run: \
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
usage: atlas2_service [-h] [-t [THREADS]] [-f] [-a [ALLOWLISTS]]
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
  -a, --allowlists [ALLOWLISTS]
                        Directory where all of the ATLAS web crawler
                        allowlists for each PSU are located
  -b, --blocklist [BLOCKLIST]
                        Master blocklist file for the ATLAS Crawler
  -c, --csv             Enables .csv exporting for all PSUs
  -r, --runzero         Enables export to runZero (Must have API Token filled
                        in .env file to work!)
```

