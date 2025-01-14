from PyQt5.QtWidgets import QToolBar, QLineEdit, QPushButton
from PyQt5.QtCore import Qt


class CustomToolBar(QToolBar):
    """Custom Toolbar with navigation buttons, URL field, and settings button."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("""
            QToolBar {
                height: 50px;
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 10px;
                width: 40px;
                height: 40px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QLineEdit {
                height: 40px;
                font-size: 14px;
                border: 1px solid #cccccc;
                border-radius: 20px;
                padding: 0 10px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #0078d7;
            }
        """)

        # Back Button
        self.back_button = QPushButton("←")
        self.back_button.setToolTip("Go Back")
        self.back_button.clicked.connect(self.parent.on_back_clicked)
        self.addWidget(self.back_button)

        # Forward Button
        self.forward_button = QPushButton("→")
        self.forward_button.setToolTip("Go Forward")
        self.forward_button.clicked.connect(self.parent.on_forward_clicked)
        self.addWidget(self.forward_button)

        # Reload Button
        self.reload_button = QPushButton("⟳")
        self.reload_button.setToolTip("Reload")
        self.reload_button.clicked.connect(self.parent.on_reload_clicked)
        self.addWidget(self.reload_button)

        # URL Field
        self.url_field = QLineEdit()
        self.url_field.setPlaceholderText("Enter URL")
        self.url_field.returnPressed.connect(self.parent.on_url_entered)
        self.addWidget(self.url_field)

        # Settings Button
        self.settings_button = QPushButton(" ⠇")
        self.settings_button.setToolTip("Settings")
        self.settings_button.clicked.connect(self.parent.on_settings_clicked)
        self.addWidget(self.settings_button)

    def update_url(self, url):
        """Update the URL field."""
        self.url_field.setText(url.toString())
        self.url_field.setCursorPosition(0)
