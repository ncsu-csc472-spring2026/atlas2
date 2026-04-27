SHELL := /bin/bash # Use bash shell to use source command
VENV_NAME := atlas2
VENV_DIR := /usr/lib/$(VENV_NAME)
BIN_DIR := $(VENV_DIR)/bin
SERVICE_DIR := /etc/systemd/system
BANNER_FILE := ./src/banner.txt
SERVICE_OUTPUT_DIR := /etc/atlas2
SRC_DIR := ./src/atlas2

# ATLAS Crawler Makefile Vars
CRAWLER_REPO := https://github.com/ncsu-csc472-spring2026/atlas-crawler/
CFLAGS := -ggdb -Wall -Wextra
CRAWLER_SRC := ./atlas-crawler
CRAWLER_BIN := $(CRAWLER_SRC)/bin
CC := gcc
LDLIBS := -lcurl

# Suppress output except for echoes
ifndef VERBOSE
.SILENT:
endif

copy_to_PATH: build # Install atlas2 and atlas2_service files into /usr/bin/
	if [[ -e "/usr/bin/atlas2" || -e "/usr/bin/atlas2_service" ]]; then \
		echo "[!] ATLAS2 binaries already exist in /usr/bin/, removing..."; \
		sudo rm /usr/bin/atlas2; \
		sudo rm /usr/bin/atlas2_service; \
	fi
	sudo ln -s $(BIN_DIR)/atlas2 /usr/bin/atlas2
	sudo ln -s $(BIN_DIR)/atlas2_service /usr/bin/atlas2_service
	echo "[+] Symlinked Python scripts to /usr/bin/"
	sudo rm -r ./build
	echo "[-] Cleaned up build/ directory"

test: copy_to_PATH # Run PyTest after build
	source $(BIN_DIR)/activate && python -m pytest $(SRC_DIR)

service: copy_to_PATH make_service_out_dir # Copy service/timer files to systemd user services folder
	# Make sure the actual timer and service files exist, not just the templates
	if [[ ! -f "$(SRC_DIR)/atlas2.timer" || ! -f "$(SRC_DIR)/atlas2.service" ]]; then \
		echo "[!] atlas2.timer and atlas2.service must be present, not just the templates!"; \
		exit 1; \
	fi
	sudo cp $(SRC_DIR)/atlas2.service $(SRC_DIR)/atlas2.timer $(SERVICE_DIR)
	echo "[+] Copied Systemd service and timer files to /etc/systemd/system/"
	sudo systemctl daemon-reload
	echo "[*] Reloaded Systemd Daemons"
	sudo systemctl enable atlas2.timer
	sudo systemctl start atlas2.timer
	echo "[+] Enabled ATLAS2 Systemd timer (2:00 AM EST Daily)"

make_service_out_dir:
	if [ ! -d "$(SERVICE_OUTPUT_DIR)" ]; then \
		sudo mkdir $(SERVICE_OUTPUT_DIR); \
		echo "[+] Created directory for service outputs at $(SERVICE_OUTPUT_DIR)"; \
	fi

build: print_banner make_venv install_theHarvester crawler # Build Python project in venv
	source $(BIN_DIR)/activate && sudo $(BIN_DIR)/pip install .
	echo "[+] Built ATLAS2 scripts in $(BIN_DIR)"

make_venv: # Create Python venv if one does not already exist in "/usr/lib/atlas2"
	if [ ! -d "$(VENV_DIR)" ]; then \
		sudo python -m venv $(VENV_DIR); \
		echo "[+] Created Python virtual environment ($(VENV_DIR))"; \
	fi

print_banner: # Print a pretty banner from banner.txt
	sed "s/\[VERSION\!\]/$$(printf '%-10s' $$(grep -Po '(?<=version = \")[^\"]*' pyproject.toml))/g" $(BANNER_FILE)

install_theHarvester: # Install theHarvester through apt if not present on system
	if ! dpkg-query -s theharvester 2>/dev/null | grep -q "ok installed"; then \
		echo "[+] Installing theHarvester through apt"; \
		sudo apt install theharvester; \
	fi

# Builds crawler and placed binary in /usr/bin
crawler: install_libcurl clone_crawler crawler_bin
	$(CC) $(CFLAGS) $(CRAWLER_SRC)/atlas_crawler.c -o $(CRAWLER_BIN)/atlas_crawler $(LDLIBS)
	sudo cp $(CRAWLER_BIN)/atlas_crawler /usr/bin/atlas_crawler
	echo "[+] Built and copied ATLAS Crawler binary to /usr/bin"

crawler_bin: # Create bin directory in atlas-crawler
	mkdir -p $(CRAWLER_BIN)

clone_crawler: # Clone atlas-crawler repo into crawler dir
	if [ ! -d "$(CRAWLER_SRC)" ]; then \
		git clone $(CRAWLER_REPO); \
	fi
	git -C $(CRAWLER_SRC) pull # Update Crawler repo before building

install_libcurl: # Installs libcurl4-openssl-dev package if not present, needed for crawler
	if ! dpkg-query -s libcurl4-openssl-dev 2>/dev/null | grep -q "ok installed"; then \
		echo "[+] Installing libcurl4-openssl-dev through apt"; \
		sudo apt install libcurl4-openssl-dev; \
	fi

clean: print_banner # Delete all installed files and directories
	if [ -d "$(CRAWLER_SRC)" ]; then sudo rm -r $(CRAWLER_SRC); fi
	if [ -f "/usr/bin/atlas_crawler" ]; then sudo rm /usr/bin/atlas_crawler; fi
	if [ -f "/usr/bin/atlas2" ]; then sudo rm /usr/bin/atlas2; fi
	if [ -f "/usr/bin/atlas2_service" ]; then sudo rm /usr/bin/atlas2_service; fi
	if [ -d "/usr/lib/atlas2" ]; then sudo rm -r /usr/lib/atlas2; fi
	if [ -d "/etc/atlas2" ]; then sudo rm -r /etc/atlas2; fi
	if [ -f "/etc/systemd/system/atlas2.service" ]; then sudo rm /etc/systemd/system/atlas2.service; fi
	if [ -f "/etc/systemd/system/atlas2.timer" ]; then sudo rm /etc/systemd/system/atlas2.timer; fi
	sudo systemctl daemon-reload
	echo "[-] Removed all installed ATLAS2 files and directories, reloaded services"
