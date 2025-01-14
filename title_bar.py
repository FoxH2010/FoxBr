from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QToolButton
from PyQt5.QtCore import Qt, QPoint


class CustomTitleBar(QWidget):
    """Custom title bar with tabs and control buttons."""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.drag_position = None
        self.drag_ratio = None

        # Layout for the custom title bar
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)  # Add some spacing between elements

        # Tab Bar
        self.tab_bar = QWidget(self)
        self.tab_bar_layout = QHBoxLayout()
        self.tab_bar_layout.setContentsMargins(5, 5, 5, 5)
        self.tab_bar_layout.setSpacing(5)
        self.tab_bar.setLayout(self.tab_bar_layout)
        self.tab_bar.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
            }
            QToolButton {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 5px;
                width: 200px; /* Fixed width */
                height: 40px; /* Tab height */
                text-align: left;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
            }
            QToolButton:checked {
                background-color: #d0d0d0;
            }
        """)

        # Add a "+" button to the tab bar
        self.add_tab_button = QToolButton(self)
        self.add_tab_button.setText("+")
        self.add_tab_button.setFixedSize(50, 40)
        self.add_tab_button.setToolTip("Open a new tab")
        self.add_tab_button.clicked.connect(lambda: parent.add_new_tab("New Tab", "https://www.google.com"))
        self.tab_bar_layout.addWidget(self.add_tab_button)

        # Add the tab bar to the title bar layout
        layout.addWidget(self.tab_bar)

        # Spacer to push control buttons to the right
        layout.addStretch()

        # Action Buttons (Minimize, Maximize/Restore, Close)
        self.minimize_btn = QPushButton("–")
        self.minimize_btn.setFixedSize(50, 40)
        self.minimize_btn.setToolTip("Minimize")
        self.minimize_btn.clicked.connect(parent.showMinimized)
        layout.addWidget(self.minimize_btn)

        self.maximize_btn = QPushButton("☐")
        self.maximize_btn.setFixedSize(50, 40)
        self.maximize_btn.setToolTip("Maximize/Restore")
        self.maximize_btn.clicked.connect(parent.toggle_maximized)
        layout.addWidget(self.maximize_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(50, 40)
        self.close_btn.setToolTip("Close")
        self.close_btn.clicked.connect(parent.close)
        layout.addWidget(self.close_btn)

        self.setLayout(layout)

    def mousePressEvent(self, event):
        """Handle mouse press events for dragging the window."""
        if event.button() == Qt.LeftButton:
            if self.parent.isMaximized():
                # Calculate drag position ratio when maximized
                self.drag_ratio = event.pos().x() / self.width()
                self.parent.showNormal()
                new_x = event.globalPos().x() - self.drag_ratio * self.parent.width()
                self.drag_position = QPoint(int(new_x), int(event.globalPos().y() - self.parent.geometry().y()))
            else:
                self.drag_position = event.globalPos() - self.parent.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse movement for dragging."""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.parent.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Maximize the window if dragged to the top of the screen."""
        if event.globalPos().y() == 0:  # Top of the screen
            self.parent.showMaximized()
