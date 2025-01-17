import sys
import os
import ctypes
import requests
import zipfile
import winreg

VERSION_URL = "https://raw.githubusercontent.com/FoxH2010/FoxBr/refs/heads/main/version"
DOWNLOAD_URL_TEMPLATE = "https://github.com/FoxH2010/FoxBr/releases/download/{}/FoxBr.zip"
ZIP_FILENAME = "FoxBr_Update.zip"
REGISTRY_KEY_PATH = r"SOFTWARE\FoxTeam\FoxBr"
INSTALL_PATH_KEY = "InstallPath"
MAIN_EXECUTABLE_NAME = "FoxBr.exe"


def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def fetch_latest_version():
    """Fetch the latest version from the server."""
    try:
        response = requests.get(VERSION_URL, timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException as e:
        print(f"[Updater] Error fetching version: {e}")
        return None


def download_update(version, save_path):
    """Download the update ZIP file."""
    try:
        download_url = DOWNLOAD_URL_TEMPLATE.format(version)
        response = requests.get(download_url, stream=True, timeout=30)
        response.raise_for_status()

        with open(save_path, "wb") as file:
            for chunk in response.iter_content(1024):
                if chunk:
                    file.write(chunk)
        return True
    except requests.RequestException as e:
        print(f"[Updater] Error downloading update: {e}")
        return False


def extract_and_replace(zip_path, install_path):
    """Extract the ZIP file and replace old files."""
    try:
        # Define paths for current and backup executables
        current_executable = os.path.join(install_path, MAIN_EXECUTABLE_NAME)
        old_executable = os.path.join(install_path, "FoxBr_old.exe")

        # Remove existing backup if it exists
        if os.path.exists(old_executable):
            os.remove(old_executable)

        # Rename the current executable to a backup
        if os.path.exists(current_executable):
            os.rename(current_executable, old_executable)

        # Extract the new files
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(install_path)

        # Remove the ZIP file after extraction
        os.remove(zip_path)
        return True
    except Exception as e:
        print(f"[Updater] Error extracting update: {e}")
        return False


def read_registry_install_path():
    """Retrieve the installation path from the Windows registry."""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REGISTRY_KEY_PATH) as key:
            install_path, _ = winreg.QueryValueEx(key, INSTALL_PATH_KEY)
            return install_path
    except FileNotFoundError:
        print("[Updater] Installation path not found in registry.")
        return None
    except Exception as e:
        print(f"[Updater] Failed to read registry: {e}")
        return None


def read_installed_version(install_path):
    """Read the installed version from the version file."""
    version_file_path = os.path.join(install_path, "version.txt")
    if os.path.exists(version_file_path):
        with open(version_file_path, "r") as version_file:
            return version_file.read().strip()
    return None


def write_installed_version(install_path, version):
    """Write the new version to the version file."""
    version_file_path = os.path.join(install_path, "version.txt")
    with open(version_file_path, "w") as version_file:
        version_file.write(version)


def main():
    # Ensure the updater has admin privileges
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
        sys.exit(0)

    # Retrieve the installation path
    install_path = read_registry_install_path()
    if not install_path:
        print("[Updater] Installation path not found. Exiting.")
        sys.exit(1)

    # Fetch the latest version
    latest_version = fetch_latest_version()
    if not latest_version:
        print("[Updater] Failed to fetch the latest version. Exiting.")
        sys.exit(1)

    # Read the currently installed version
    current_version = read_installed_version(install_path)
    if current_version == latest_version:
        print("[Updater] FoxBr is already up-to-date. Exiting.")
        sys.exit(0)

    print(f"[Updater] Updating from version {current_version} to {latest_version}...")

    # Download the update
    zip_path = os.path.join(install_path, ZIP_FILENAME)
    if not download_update(latest_version, zip_path):
        print("[Updater] Failed to download the update. Exiting.")
        sys.exit(1)

    # Extract and replace files
    if not extract_and_replace(zip_path, install_path):
        print("[Updater] Failed to install the update. Exiting.")
        sys.exit(1)

    # Write the new version to the version file
    write_installed_version(install_path, latest_version)
    print("[Updater] Update complete. Exiting.")


if __name__ == "__main__":
    main()
