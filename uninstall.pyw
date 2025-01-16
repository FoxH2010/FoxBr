import sys
import os
import shutil
import ctypes
import winshell  # pip install winshell
from PyQt5.QtWidgets import (
    QApplication, QVBoxLayout, QLabel, QPushButton, QProgressBar, QMessageBox, QWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import winreg

# Determine the directory of the uninstaller
if getattr(sys, 'frozen', False):
    INSTALL_DIR = os.path.dirname(sys.executable)  # PyInstaller executable directory
else:
    INSTALL_DIR = os.path.dirname(os.path.abspath(__file__))  # Script directory

REGISTRY_KEY_PATH = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\FoxBr"
DESKTOP_SHORTCUT_NAME = "FoxBr.lnk"
MAIN_EXECUTABLE_NAME = "FoxBr.exe"  # The file to check for validity


def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def remove_registry_entry():
    """Remove the program's registry entry."""
    try:
        winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, REGISTRY_KEY_PATH)
    except FileNotFoundError:
        pass  # No registry entry found, ignore
    except Exception as e:
        QMessageBox.critical(None, "Registry Error", f"Failed to remove registry entry: {e}")


def remove_shortcut():
    """Remove the desktop shortcut for FoxBr."""
    try:
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, DESKTOP_SHORTCUT_NAME)
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
    except Exception as e:
        print(f"Failed to remove desktop shortcut: {e}")


class UninstallerWorker(QThread):
    progress_updated = pyqtSignal(int)
    uninstallation_complete = pyqtSignal()

    def __init__(self, uninstall_path, uninstaller_path):
        super().__init__()
        self.uninstall_path = uninstall_path
        self.uninstaller_path = uninstaller_path

    def run(self):
        try:
            # Count total files, excluding the uninstaller itself
            total_files = sum(len(files) for _, _, files in os.walk(self.uninstall_path))
            total_files -= 1  # Exclude the uninstaller itself
            deleted_files = 0

            for root, dirs, files in os.walk(self.uninstall_path, topdown=False):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file_path == self.uninstaller_path:
                        continue  # Skip the uninstaller
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    deleted_files += 1
                    progress = int((deleted_files / total_files) * 100)
                    self.progress_updated.emit(progress)
                for directory in dirs:
                    dir_path = os.path.join(root, directory)
                    if os.path.exists(dir_path):
                        shutil.rmtree(dir_path)

            if os.path.exists(self.uninstall_path):
                shutil.rmtree(self.uninstall_path, ignore_errors=True)

            self.progress_updated.emit(100)  # Ensure progress reaches 100%
            self.uninstallation_complete.emit()
        except Exception as e:
            print(f"Error during uninstallation: {e}")
            self.uninstallation_complete.emit()  # Ensure completion signal is sent


class Uninstaller(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("FoxBr Uninstaller")
        self.setFixedSize(400, 250)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.title_label = QLabel("FoxBr Uninstaller")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.layout.addWidget(self.title_label)

        self.info_label = QLabel("This will completely remove FoxBr from your system.")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.info_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.progress_bar)

        self.uninstall_button = QPushButton("Uninstall")
        self.uninstall_button.clicked.connect(self.start_uninstallation)
        self.layout.addWidget(self.uninstall_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        self.layout.addWidget(self.cancel_button)

    def start_uninstallation(self):
        """Begin the uninstallation process."""
        if not self.validate_installation_directory():
            QMessageBox.critical(
                self, "Error", f"The uninstaller is not in the correct directory.\n"
                               f"Ensure {MAIN_EXECUTABLE_NAME} is present in the same folder."
            )
            self.close()
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Uninstallation",
            "Are you sure you want to uninstall FoxBr?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.uninstall_button.setEnabled(False)
            self.cancel_button.setEnabled(False)

            # Remove the desktop shortcut before starting the uninstallation
            remove_shortcut()

            self.worker = UninstallerWorker(INSTALL_DIR, sys.executable)
            self.worker.progress_updated.connect(self.update_progress)
            self.worker.uninstallation_complete.connect(self.complete_uninstallation)
            self.worker.start()

    def validate_installation_directory(self):
        """Ensure the uninstaller is in the correct directory."""
        main_executable_path = os.path.join(INSTALL_DIR, MAIN_EXECUTABLE_NAME)
        return os.path.exists(main_executable_path)

    def update_progress(self, progress):
        """Update the progress bar."""
        self.progress_bar.setValue(progress)

    def complete_uninstallation(self):
        """Handle the completion of the uninstallation process."""
        remove_registry_entry()
        QMessageBox.information(self, "Uninstallation Complete", "FoxBr has been successfully removed.")
        self.delete_uninstaller()

    def delete_uninstaller(self):
        """Create a batch file to delete the uninstaller itself."""
        uninstaller_path = sys.executable
        batch_file = os.path.join(INSTALL_DIR, "delete_self.bat")

        # Create the batch script
        with open(batch_file, "w") as batch:
            batch.write(f"""@echo off
:repeat
del "{uninstaller_path}" > nul 2>&1
if exist "{uninstaller_path}" goto repeat
del "%~f0" > nul 2>&1
""")

        # Execute the batch script
        os.startfile(batch_file)
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    if not is_admin():
        QMessageBox.critical(None, "Permission Error", "This uninstaller must be run as an administrator.")
        sys.exit(1)

    uninstaller = Uninstaller()
    uninstaller.show()
    sys.exit(app.exec_())
