import sys
import subprocess
import winreg
from PyQt5.QtWidgets import QApplication
from web_browser import WebBrowser

# Define the registry key path
REGISTRY_KEY_PATH = r"SOFTWARE\FoxTeam\FoxBr"

def read_registry_install_path():
    """Retrieve the installation path from the Windows registry."""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, REGISTRY_KEY_PATH) as key:
            install_path, _ = winreg.QueryValueEx(key, "InstallPath")
            return install_path
    except FileNotFoundError:
        print("Installation path not found in registry.")
        return None
    except Exception as e:
        print(f"Failed to read registry: {e}")
        return None


def run_updater(updater_path):
    """Launch the updater.exe with administrative privileges."""
    try:
        # Run updater.exe with elevated privileges
        subprocess.Popen(
            ["powershell", "Start-Process", f"'{updater_path}'", "-Verb", "RunAs"],
            shell=True
        )
    except Exception as e:
        print(f"Failed to run updater.exe: {e}")


if __name__ == "__main__":
    # Retrieve the installation path from the registry
    install_path = read_registry_install_path()

    if install_path:
        # Construct the full path to updater.exe
        updater_executable = f"{install_path}\\updater.exe"
        run_updater(updater_executable)
    else:
        print("Updater executable could not be located.")

    # Launch the main browser application
    app = QApplication(sys.argv)
    window = WebBrowser()
    window.showMaximized()  # Start in maximized mode
    sys.exit(app.exec_())
