#!/usr/bin/env bash
# =============================================================================
# download_files.sh
#
# Downloads:
#   1. A Python script from your public GitHub repo
#   2. A shell script (harvesthelper) from your public GitHub repo
#   3. A C file from a submodule repo linked from the first repo
#   4. theHarvester — cloned, installed, and added to PATH
#
# Usage:
#   chmod +x download_files.sh
#   ./download_files.sh
#
# All files are saved to the current working directory.
# =============================================================================
 
set -euo pipefail
 
# -----------------------------------------------------------------------------
# CONFIGURATION — update these values before use
# -----------------------------------------------------------------------------
 
# Repo owner (your GitHub org)
YOUR_GITHUB_USER="ncsu-csc472-spring2026"
 
# Your first repo: the one containing the Python script and harvesthelper
YOUR_REPO="atlas2"
YOUR_REPO_BRANCH="main"
PYTHON_SCRIPT_PATH="scripts/atlas2.py"
PYTHON_SCRIPT_PATH2="scripts/harvesthelper.sh"
 
# Submodule repo: contains the C file (linked from your first repo)
SUBMODULE_REPO="atlas-crawler"
SUBMODULE_OWNER="ncsu-csc472-spring2026"
SUBMODULE_BRANCH="498f836"
C_FILE_PATH="atlas_crawler.c"
 
# Third-party repo: theHarvester (cloned in full — it requires its full directory structure)
THEHARVESTER_REPO="https://github.com/laramies/theHarvester.git"
THEHARVESTER_DIR="theHarvester"
 
# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------
 
# Build a raw.githubusercontent.com URL
raw_url() {
    local owner="$1" repo="$2" branch="$3" filepath="$4"
    echo "https://raw.githubusercontent.com/${owner}/${repo}/${branch}/${filepath}"
}
 
# Download a file, print progress, and verify it landed
download_file() {
    local url="$1"
    local dest="$2"
    local label="$3"
 
    echo "[*] Downloading ${label}..."
    echo "    URL : ${url}"
    echo "    Dest: ${PWD}/${dest}"
 
    if command -v curl &>/dev/null; then
        curl -fsSL --retry 3 --retry-delay 2 -o "${dest}" "${url}"
    elif command -v wget &>/dev/null; then
        wget -q --tries=3 --waitretry=2 -O "${dest}" "${url}"
    else
        echo "[ERROR] Neither curl nor wget is available. Install one and retry." >&2
        exit 1
    fi
 
    if [[ -s "${dest}" ]]; then
        echo "    OK  : $(wc -c < "${dest}") bytes saved."
    else
        echo "[ERROR] Download succeeded but '${dest}' is empty. Check the URL." >&2
        exit 1
    fi
}
 
# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
 
echo "============================================================"
echo " download_files.sh — starting downloads"
echo " Working directory: ${PWD}"
echo "============================================================"
echo ""
 
# 1. Python script from your repo
PY_URL=$(raw_url "${YOUR_GITHUB_USER}" "${YOUR_REPO}" "${YOUR_REPO_BRANCH}" "${PYTHON_SCRIPT_PATH}")
PY_DEST=$(basename "${PYTHON_SCRIPT_PATH}")
download_file "${PY_URL}" "${PY_DEST}" "Python script (your repo)"
echo ""
 
# 2. Harvesthelper shell script from your repo
HH_URL=$(raw_url "${YOUR_GITHUB_USER}" "${YOUR_REPO}" "${YOUR_REPO_BRANCH}" "${PYTHON_SCRIPT_PATH2}")
HH_DEST=$(basename "${PYTHON_SCRIPT_PATH2}")
download_file "${HH_URL}" "${HH_DEST}" "Harvest helper script (your repo)"
chmod +x "${HH_DEST}"
 
# Install harvesthelper to a directory already on PATH
echo "[*] Installing harvesthelper to /usr/local/bin..."
sudo cp "${HH_DEST}" /usr/local/bin/harvesthelper
sudo chmod +x /usr/local/bin/harvesthelper
echo "    OK  : harvesthelper is now callable from any directory"
 
# 3. C file from the submodule repo
C_URL=$(raw_url "${SUBMODULE_OWNER}" "${SUBMODULE_REPO}" "${SUBMODULE_BRANCH}" "${C_FILE_PATH}")
C_DEST=$(basename "${C_FILE_PATH}")
download_file "${C_URL}" "${C_DEST}" "C file (submodule repo)"
echo ""
 
# 4. Clone theHarvester and install it system-wide
echo "[*] Cloning theHarvester..."
if ! command -v git &>/dev/null; then
    echo "[ERROR] git is not installed. Install it with: sudo apt-get install git" >&2
    exit 1
fi
 
if [[ -d "${THEHARVESTER_DIR}/.git" ]]; then
    echo "    Found existing clone — pulling latest changes..."
    git -C "${THEHARVESTER_DIR}" pull --ff-only
else
    git clone --depth=1 "${THEHARVESTER_REPO}" "${THEHARVESTER_DIR}"
fi
 
echo "[*] Installing theHarvester..."
 
# Install pip if not present
if ! command -v pip &>/dev/null && ! command -v pip3 &>/dev/null; then
    echo "[*] pip not found — installing..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get install -y python3-pip
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3-pip
    elif command -v yum &>/dev/null; then
        sudo yum install -y python3-pip
    else
        echo "[ERROR] Could not install pip — unsupported package manager." >&2
        exit 1
    fi
fi
 
PIP=$(command -v pip || command -v pip3)
 
cd "${THEHARVESTER_DIR}"
$PIP install . --break-system-packages
 
# Add theHarvester to PATH
HARVESTER_BIN=$(python3 -m site --user-base)/bin
if [[ ":$PATH:" != *":${HARVESTER_BIN}:"* ]]; then
    echo "export PATH=\"${HARVESTER_BIN}:\$PATH\"" >> ~/.bashrc
    export PATH="${HARVESTER_BIN}:$PATH"
    echo "    OK  : Added ${HARVESTER_BIN} to PATH"
fi
 
cd ..
echo "    OK  : theHarvester installed and available system-wide"
echo ""
 
echo "============================================================"
echo " All downloads complete."
echo " Files in ${PWD}:"
ls -lh "${PY_DEST}" "${HH_DEST}" "${C_DEST}"
echo ""
echo " theHarvester directory:"
ls -1 "${THEHARVESTER_DIR}" | head -10
echo "============================================================"