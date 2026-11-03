import subprocess
import socket
import os
from pathlib import Path
import requests
import re
import platform

# Constants
SERVER_DOMAIN = 'supplychain.sentinel-cyber.sg'
USERNAME = 'admin'
PASSWORD = 'password123'
UPDATE_TIMEOUT = 3
DOWNLOAD_TIMEOUT = 30

def artifact_suffix():
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Windows":
        return "exe"
    if system == "Linux":
        return "linux"
    if system == "Darwin":
        return "macos-arm64" if machine in ("arm64", "aarch64") else "macos-intel"
    raise OSError(f"Unsupported platform: {system}: {machine}")

def get_local_file_path():
    if os.name == 'nt':  # Windows
        local_dir = Path("C:/temp")

    elif platform.system() == "Linux": # ChromeOS
        local_dir = Path.home() / ".local" / "bin"

    else:  # macOS
        local_dir = Path.home() / "temp"
    
    local_dir.mkdir(parents=True, exist_ok=True)
    return local_dir / f"chatapp_1.2.{artifact_suffix}"

def check_for_updates(status_callback): 
    # Construct URL to query latest version
    suffix = artifact_suffix()
    packages_url = f"http://{SERVER_DOMAIN}:8080/"

    headers = {
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
    }
    version_query = requests.get(packages_url, headers=headers, timeout=UPDATE_TIMEOUT)
    version_query_html = version_query.text

    # latest_files = re.findall(r'href="([^"]+)"', version_query_html)
    pattern = rf'(chatapp)_(\d+\.\d+)\.{re.escape(suffix)}'
    latest_version = None

    # for file_name in latest_files:
        # Gets the latest version for us
   #     match = re.search(r'(chatapp)_(\d+\.\d+)\.exe', file_name)

   #     if match:
    #        latest_version = match.group(2)

    for file_name in re.findall(r'href="([^"]+)"', version_query.text):
        match = re.search(pattern, file_name)
        if match:
            latest_version = match.group(2)

    if latest_version is None:
        return None

    local_file_path = get_local_file_path()

    if local_file_path.is_file():
        return str(local_file_path)

    try:
        status_callback("Connecting to update server...")
        # Construct URL for updating
        url = f"http://{SERVER_DOMAIN}:8080/chatapp_{latest_version}.{suffix}"
        cmd = ["curl", "-H", "Cache-Control: no-cache", "-f", "-o", str(local_file_path), url]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=DOWNLOAD_TIMEOUT) 
        
        if suffix == "linux":
            os.chmod(local_file_path, 0o755) # Executable on first use

        status_callback("Update downloaded successfully")
        return str(local_file_path)
            
    except Exception as e:
        status_callback("Failed to check for updates: {}".format(e))
        return None

