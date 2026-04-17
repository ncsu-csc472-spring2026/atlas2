SHELL := /bin/bash # Use bash shell to use source command
VENV_NAME := atlas2
VENV_DIR := /usr/lib/$(VENV_NAME)
BIN_DIR := $(VENV_DIR)/bin
SERVICE_DIR := /etc/systemd/system
BANNER_FILE := banner.txt
SERVICE_OUTPUT_DIR := /etc/atlas2

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

service: copy_to_PATH make_service_out_dir # Copy service/timer files to systemd user services folder
	# Make sure the actual timer and service files exist, not just the templates
	if [[ ! -f "./atlas2.timer" || ! -f "./atlas2.service" ]]; then \
		echo "[!] atlas2.timer and atlas2.service must be present, not just the templates!"; \
		exit 1; \
	fi
	sudo cp atlas2.service atlas2.timer $(SERVICE_DIR)
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

build: make_venv # Build Python project in venv
	source $(BIN_DIR)/activate && sudo $(BIN_DIR)/pip install .
	echo "[+] Built ATLAS2 scripts in $(BIN_DIR)"

make_venv: print_banner # Create Python venv if one does not already exist in "/usr/lib/atlas2"
	if [ ! -d "$(VENV_DIR)" ]; then \
		sudo python -m venv $(VENV_DIR); \
		echo "[+] Created Python virtual environment ($(VENV_DIR))"; \
	fi

print_banner: # Print a pretty banner from banner.txt
	sed "s/\[VERSION\!\]/$$(printf '%-10s' $$(grep -Po '(?<=version = \")[^\"]*' pyproject.toml))/g" banner.txt

clean:
	if [ -f "/usr/bin/atlas2" ]; then sudo rm /usr/bin/atlas2; fi
	if [ -f "/usr/bin/atlas2_service" ]; then sudo rm /usr/bin/atlas2_service; fi
	if [ -d "/usr/lib/atlas2" ]; then sudo rm -r /usr/lib/atlas2; fi
	if [ -d "/etc/atlas2" ]; then sudo rm -r /etc/atlas2; fi
	if [ -f "/etc/systemd/system/atlas2.service" ]; then sudo rm /etc/systemd/system/atlas2.service; fi
	if [ -f "/etc/systemd/system/atlas2.timer" ]; then sudo rm /etc/systemd/system/atlas2.timer; fi
	sudo systemctl daemon-reload
	echo "[-] Removed all installed ATLAS2 files and directories, reloaded services"

