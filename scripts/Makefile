SHELL := /bin/bash

service: build
	sudo cp atlas2.service atlas2.timer /etc/systemd/system/
	echo "[+] Copied Systemd service and timer files to /etc/systemd/system/"
	sudo systemctl daemon-reload
	echo "[*] Reloaded Systemd Daemons"
	sudo systemctl enable atlas2.timer
	sudo systemctl start atlas2.timer
	echo "[+] Enabled ATLAS2 Systemd timer (2:00 AM EST Daily)"

build: pip_install
	sudo cp .venv/bin/atlas2 .venv/bin/atlas2_service /usr/bin/
	echo "[+] Copied built Python scripts to /usr/bin/"

pip_install: make_venv
	source ./.venv/bin/activate && pip install .
	echo "[+] Built ATLAS2 scripts"

make_venv:
	if [ ! -d ".venv" ]; then \
		python -m venv .venv; \
		echo "[+] Created Python virtual environment (.venv)"; \
	fi


