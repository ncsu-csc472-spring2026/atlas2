SHELL := /bin/bash # Use bash shell to use source command

build: pip_install # Install atlas2 and atlas2_service files into system PATH /usr/bin/ directory
	sudo cp .venv/bin/atlas2 .venv/bin/atlas2_service /usr/bin/
	echo "[+] Copied built Python scripts to /usr/bin/"

service: build # Copy service/timer files to systemd user services folder
	# Make sure the actual timer and service files exist, not just the templates
	if [[ ! -f "./atlas2.timer" || ! -f "./atlas2.service" ]]; then \
		echo "[!] atlas2.timer and atlas2.service must be present, not just the templates!"; \
		exit 1; \
	fi
	sudo cp atlas2.service atlas2.timer /etc/systemd/system/
	echo "[+] Copied Systemd service and timer files to /etc/systemd/system/"
	sudo systemctl daemon-reload
	echo "[*] Reloaded Systemd Daemons"
	sudo systemctl enable atlas2.timer
	sudo systemctl start atlas2.timer
	echo "[+] Enabled ATLAS2 Systemd timer (2:00 AM EST Daily)"

pip_install: make_venv # Build Python project in venv
	source ./.venv/bin/activate && pip install .
	echo "[+] Built ATLAS2 scripts"

make_venv: # Create Python venv if one does not already exist with the name ".venv"
	if [ ! -d ".venv" ]; then \
		python -m venv .venv; \
		echo "[+] Created Python virtual environment (.venv)"; \
	fi

