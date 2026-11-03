import subprocess
import socket
import os
from pathlib import Path
import requests
import re
import platform
import uuid
import sys

# Constants
SERVER_DOMAIN = 'supplychain.sentinel-cyber.sg'
USERNAME = 'admin'
PASSWORD = 'password123'
UPDATE_TIMEOUT = 3
DOWNLOAD_TIMEOUT = 30
CURRENT_VERSION = "1.1"

def version_tuple(version):
    return tuple(int(part) for part in version.split('.'))

def artifact_suffix():
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Windows":
        return "exe"
    if system == "Linux":
        return "linux"
    if system == "Darwin":
        return "macos-arm64.app" if machine in ("arm64", "aarch64") else "macos-intel.app"
    raise OSError(f"Unsupported platform: {system}: {machine}")

def get_local_file_path():
    suffix = artifact_suffix()

    if os.name == 'nt':  # Windows
        local_dir = Path("C:/temp")

    if platform.system() == "Linux": # ChromeOS
        local_dir = Path.home() / ".local" / "bin"

    if platform.system() == "Darwin":  # macOS
        local_dir = Path.home() / "temp"

    local_dir.mkdir(parents=True, exist_ok=True)
    return local_dir / f"chatapp_1.2.{suffix}"

def check_for_updates(status_callback): 
    # Construct URL to query latest version
    suffix = artifact_suffix()
    system = platform.system()
    local_file_path = get_local_file_path()
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

    for file_name in re.findall(r'href="([^"]+)"', version_query.text):
        match = re.search(pattern, file_name)
        if match:
            latest_version = match.group(2)

    if latest_version is None:
        return None

    if version_tuple(latest_version) <= version_tuple(CURRENT_VERSION):
        return None

    

    # Check OS first, then check file for Windows and dir for macOS
    if system == "Windows":
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
    
    if system == "Darwin":
        # check if app bundle is dir
        if local_file_path.is_dir():
            return str(local_file_path)
        # download and unzip app bundle
        local_dir = local_file_path.parent
        archive_path = local_dir / f"chatapp_{latest_version}.{suffix}.zip"
        staging_dir = local_dir / f"staging-{uuid.uuid4().hex}"
        staging_dir.mkdir()

        try:
            status_callback("Connecting to update server...")
            response = requests.get(f"http://{SERVER_DOMAIN}:8080/chatapp_{latest_version}.{suffix}.zip", timeout=DOWNLOAD_TIMEOUT)
            response.raise_for_status()
            archive_path.write_bytes(response.content)
            subprocess.run(["ditto", "-x", "-k", str(archive_path), str(staging_dir)], check=True, timeout=DOWNLOAD_TIMEOUT)
            
            staged_app = staging_dir / suffix
            if not staged_app.is_dir():
                raise FileNotFoundError(f"Bundle not found in archive: {suffix}")

            staged_app.rename(local_file_path)
            status_callback("Update downloaded successfully")
            return str(local_file_path)

        except(requests.RequestException, subprocess.SubprocessError, OSError) as e:
            status_callback(f"Failed to get update: {e}")
            return None

    if system == "Linux":
        update_path = local_file_path.parent / f"chatapp_{latest_version}.{suffix}"

        if update_path.is_file():
            return str(update_path)

        try:
            status_callback("Connecting to update server...")
            url = f"http://{SERVER_DOMAIN}:8080/chatapp_{latest_version}.{suffix}"

            subprocess.run(
                [
                    "curl", "--fail", "--location",
                    "-H", "Cache-Control: no-cache",
                    "-o", str(update_path),
                    url,
                ],
                check=True,
                timeout=DOWNLOAD_TIMEOUT,
            )

            os.chmod(update_path, 0o755)
            status_callback("Update downloaded successfully")
            return str(update_path)

        except (OSError, subprocess.SubprocessError) as exc:
            status_callback(f"Failed to get update: {exc}")
            return None
    

