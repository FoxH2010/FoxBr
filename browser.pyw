import sys
from PyQt5.QtWidgets import QApplication
from web_browser import WebBrowser

if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = WebBrowser()
    window.showMaximized()  # Start in maximized mode
    sys.exit(app.exec_())
