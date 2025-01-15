import sys
import os
import ctypes
import requests
import zipfile
import winshell  # pip install winshell
from PyQt5.QtWidgets import (
    QApplication, QStackedWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QWidget, QLineEdit, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

VERSION_URL = "https://raw.githubusercontent.com/FoxH2010/FoxBr/refs/heads/main/version"
DOWNLOAD_URL_TEMPLATE = "https://github.com/FoxH2010/FoxBr/releases/download/{}/FoxBr.zip"
DEFAULT_INSTALL_PATH = r"C:\Program Files\FoxTeam\FoxBr"
ZIP_FILENAME = "FoxBr.zip"


def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


class VersionFetcher(QThread):
    version_fetched = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            response = requests.get(VERSION_URL, timeout=10)
            response.raise_for_status()
            version = response.text.strip()
            self.version_fetched.emit(version)
        except requests.RequestException as e:
            self.error_occurred.emit(str(e))


class InstallerDownloader(QThread):
    download_progress = pyqtSignal(int)
    download_complete = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, download_url, save_path):
        super().__init__()
        self.download_url = download_url
        self.save_path = save_path
        self._is_canceled = False

    def run(self):
        try:
            response = requests.get(self.download_url, stream=True, timeout=30)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0

            with open(self.save_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    if self._is_canceled:
                        file.close()
                        os.remove(self.save_path)
                        return
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        progress = int((downloaded_size / total_size) * 100)
                        self.download_progress.emit(progress)

            if not self._is_canceled:
                self.download_complete.emit()
        except requests.RequestException as e:
            self.error_occurred.emit(str(e))

    def cancel(self):
        """Cancel the download process."""
        self._is_canceled = True


class InstallerWizard(QStackedWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.welcome_page = WelcomePage(self)
        self.path_selection_page = PathSelectionPage(self)
        self.download_page = DownloadPage(self)
        self.canceled_page = CanceledPage(self)
        self.completion_page = CompletionPage(self)

        self.addWidget(self.welcome_page)
        self.addWidget(self.path_selection_page)
        self.addWidget(self.download_page)
        self.addWidget(self.canceled_page)
        self.addWidget(self.completion_page)

        self.setWindowTitle("FoxBr Installer Wizard")
        self.resize(600, 400)
        self.setCurrentWidget(self.welcome_page)

class BasePage(QWidget):
    def __init__(self, wizard):
        super().__init__()
        self.wizard = wizard
        self.layout = QVBoxLayout()

        self.content_layout = QVBoxLayout()  # Content at the top
        self.layout.addLayout(self.content_layout)
        self.layout.addStretch()  # Spacer to push buttons to the bottom

        self.button_layout = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.setFixedWidth(80)
        self.back_button.clicked.connect(self.go_back)

        self.next_button = QPushButton("Next")
        self.next_button.setFixedWidth(80)
        self.next_button.clicked.connect(self.go_next)

        self.button_layout.addStretch()  # Spacer for right alignment
        self.button_layout.addWidget(self.back_button)
        self.button_layout.addWidget(self.next_button)
        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

    def go_back(self):
        current_index = self.wizard.currentIndex()
        self.wizard.setCurrentIndex(max(0, current_index - 1))

    def go_next(self):
        current_index = self.wizard.currentIndex()
        self.wizard.setCurrentIndex(min(self.wizard.count() - 1, current_index + 1))

class WelcomePage(BasePage):
    def __init__(self, wizard):
        super().__init__(wizard)

        title_label = QLabel("Welcome to the FoxBr Installer!")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")

        self.content_layout.addStretch()  # Spacer for vertical centering
        self.content_layout.addWidget(title_label)
        self.content_layout.addStretch()  # Spacer for vertical centering

        self.back_button.setEnabled(False)

class PathSelectionPage(BasePage):
    def __init__(self, wizard):
        super().__init__(wizard)

        self.path_label = QLabel("Install Path:")
        self.path_label.setAlignment(Qt.AlignLeft)
        self.path_input = QLineEdit(DEFAULT_INSTALL_PATH)
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_path)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(browse_button)

        self.content_layout.addWidget(self.path_label)
        self.content_layout.addLayout(path_layout)

        self.next_button.setText("Install")
        self.next_button.clicked.connect(self.install_action)

    def browse_path(self):
        selected_dir = QFileDialog.getExistingDirectory(self, "Select Installation Directory", DEFAULT_INSTALL_PATH)
        if selected_dir:
            self.path_input.setText(selected_dir)

    def install_action(self):
        selected_path = self.path_input.text()
        if not os.path.exists(selected_path):
            os.makedirs(selected_path)  # Create the directory if it doesn't exist
        self.wizard.download_page.install_path = selected_path
        self.wizard.setCurrentWidget(self.wizard.download_page)
        self.wizard.download_page.start_version_fetch()


class DownloadPage(BasePage):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.status_label = QLabel("Preparing to download...")
        self.progress_bar = QProgressBar()

        self.content_layout.addWidget(self.status_label)
        self.content_layout.addWidget(self.progress_bar)

        self.install_path = None
        self.version = None
        self.downloader = None

        self.button_layout.removeWidget(self.back_button)
        self.back_button.deleteLater()  # Remove back button during download
        self.back_button = None

        self.next_button.setText("Cancel")
        self.next_button.clicked.connect(self.cancel_download)

    def start_version_fetch(self):
        self.status_label.setText("Fetching latest version...")
        self.fetcher = VersionFetcher()
        self.fetcher.version_fetched.connect(self.start_download)
        self.fetcher.error_occurred.connect(self.show_error)
        self.fetcher.start()

    def start_download(self, version):
        self.version = version
        download_url = DOWNLOAD_URL_TEMPLATE.format(version)
        save_path = os.path.join(self.install_path, ZIP_FILENAME)

        self.status_label.setText(f"Downloading FoxBr v{version} to {self.install_path}...")
        self.downloader = InstallerDownloader(download_url, save_path)
        self.downloader.download_progress.connect(self.progress_bar.setValue)
        self.downloader.download_complete.connect(self.download_complete)
        self.downloader.error_occurred.connect(self.show_error)
        self.downloader.start()

    def download_complete(self):
        self.status_label.setText("Download complete! Extracting files...")
        zip_path = os.path.join(self.install_path, ZIP_FILENAME)

        try:
            # Extract the ZIP file
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(self.install_path)

            # Remove the ZIP file
            os.remove(zip_path)

            # Create a shortcut on the desktop for the browser
            browser_path = os.path.join(self.install_path, "FoxBr.exe")
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "FoxBr.lnk")
            winshell.CreateShortcut(
                Path=shortcut_path,
                Target=browser_path,
                Icon=(browser_path, 0),
                Description="FoxBr Browser"
            )
            self.wizard.setCurrentWidget(self.wizard.completion_page)
        except Exception as e:
            self.status_label.setText(f"Error extracting files: {e}")

    def cancel_download(self):
        if self.downloader:
            self.downloader.cancel()
        self.wizard.setCurrentWidget(self.wizard.canceled_page)

    def show_error(self, error):
        self.status_label.setText(f"Error: {error}")

class CanceledPage(BasePage):
    def __init__(self, wizard):
        super().__init__(wizard)

        label = QLabel("The download was canceled. You can restart the installer later.")
        label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(label)

        self.button_layout.removeWidget(self.back_button)
        self.back_button.deleteLater()  # Remove back button
        self.back_button = None

        self.next_button.setText("Finish")
        self.next_button.clicked.connect(QApplication.instance().quit)

class CompletionPage(BasePage):
    def __init__(self, wizard):
        super().__init__(wizard)

        # Create attention-catching message
        label = QLabel("Installation Complete!")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 24px; font-weight: bold; color: green;")

        # Add a thank-you message below the main title
        sub_label = QLabel("Thank you for installing FoxBr.")
        sub_label.setAlignment(Qt.AlignCenter)
        sub_label.setStyleSheet("font-size: 16px;")

        self.content_layout.addStretch()  # Add stretch for vertical centering
        self.content_layout.addWidget(label)
        self.content_layout.addWidget(sub_label)
        self.content_layout.addStretch()  # Add stretch for vertical centering

        # Remove Back button and configure Finish button
        self.button_layout.removeWidget(self.back_button)
        self.back_button.deleteLater()  # Remove back button
        self.back_button = None

        self.next_button.setText("Finish")
        self.next_button.clicked.connect(QApplication.instance().quit)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    if os.name == "nt" and not is_admin():
        QMessageBox.critical(None, "Permission Error", "This installer must be run as an administrator.")
        sys.exit(1)

    wizard = InstallerWizard()
    wizard.show()
    sys.exit(app.exec_())
