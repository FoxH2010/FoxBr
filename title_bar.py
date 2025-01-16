from PyQt5.QtWidgets import QWidget, QHBoxLayout, QToolButton, QPushButton
from PyQt5.QtCore import Qt, QPoint


class CustomTitleBar(QWidget):
    """Custom title bar with tabs and control buttons."""

    DRAG_THRESHOLD = 5  # Minimum distance to consider it a drag

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.drag_position = None
        self.drag_started = False
        self.initial_click_position = None

        # Layout for the custom title bar
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab Bar
        self.tab_bar = QWidget(self)
        self.tab_bar_layout = QHBoxLayout()
        self.tab_bar_layout.setContentsMargins(5, 5, 5, 5)  # Internal margins for the tab bar
        self.tab_bar_layout.setSpacing(5)  # Spacing between tabs
        self.tab_bar_layout.setAlignment(Qt.AlignLeft)  # Strict left alignment for tabs
        self.tab_bar.setLayout(self.tab_bar_layout)
        self.tab_bar.setStyleSheet("background-color: #f0f0f0;")
        
        # Add "+" button for opening new tabs
        self.add_tab_button = QToolButton(self)
        self.add_tab_button.setText("+")
        self.add_tab_button.setFixedSize(50, 40)
        self.add_tab_button.setToolTip("Open a new tab")
        self.add_tab_button.clicked.connect(lambda: parent.add_new_tab("https://www.google.com"))
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

        # Apply the layout to the title bar
        self.setLayout(layout)

    def mousePressEvent(self, event):
        """Handle mouse press events for dragging the window."""
        if event.button() == Qt.LeftButton:
            self.drag_started = False  # Reset drag state
            self.initial_click_position = event.globalPos()  # Record the initial click position
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
            # Calculate the distance moved
            distance_moved = (event.globalPos() - self.initial_click_position).manhattanLength()
            if not self.drag_started and distance_moved > self.DRAG_THRESHOLD:
                self.drag_started = True  # Start the drag only after exceeding the threshold
            if self.drag_started:
                self.parent.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """Maximize the window if dragged to the top of the screen."""
        if self.drag_started:
            # Only maximize if the drag ended at the top of the screen
            if event.globalPos().y() <= 0:  # Top of the screen
                self.parent.showMaximized()
        elif not self.drag_started and self.initial_click_position:  
            # Handle a simple click
            event.accept()
        self.drag_started = False  # Reset drag state
