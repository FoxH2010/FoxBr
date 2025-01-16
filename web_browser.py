from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QToolButton, QPushButton, QLabel, QToolBar, QLineEdit
)
from PyQt5.QtCore import Qt, QUrl, QEvent, QRect, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView
from title_bar import CustomTitleBar
from PyQt5.QtGui import QPixmap
from toolbar import CustomToolBar


class WebBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FoxBr")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setGeometry(100, 100, 1024, 768)

        # Map tab buttons to browser instances
        self.tab_map = {}

        # Main Layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Custom Title Bar
        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)

        # Toolbar
        self.toolbar = CustomToolBar(self)
        main_layout.addWidget(self.toolbar)

        # Stacked Widget for Tab Content
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Add the first tab
        self.add_new_tab()

    def eventFilter(self, source, event):
        """Handle middle-click to close tabs."""
        if source == self.title_bar.tab_bar and event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.MiddleButton:
                tab_container = source.childAt(event.pos())
                if tab_container:
                    index = self.title_bar.tab_bar_layout.indexOf(tab_container)
                    if index >= 0:
                        self.close_tab(index)
        return super().eventFilter(source, event)
    
    def toggle_maximized(self):
        """Toggle between maximized and normal window states."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def add_new_tab(self, url="https://www.google.com"):
        """Add a new tab with functional hover and click behavior, and fix layout issues."""
        # Browser content
        browser = QWebEngineView()
        browser.setHtml("<h1>Loading...</h1>")  # Placeholder content
        browser.titleChanged.connect(lambda title: self.update_tab_title(browser, title))
        browser.urlChanged.connect(lambda url: self.update_url_field_and_tab_title(browser, url))
        browser.iconChanged.connect(lambda icon: self.update_tab_icon(browser, tab_button_icon))

        self.content_stack.addWidget(browser)

        # Tab Container (holds favicon, title, and close button)
        tab_container = QWidget(self)
        tab_container.setFixedSize(200, 40)
        tab_container.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 5px; /* Internal padding for comfortable spacing */
            }
            QWidget:hover {
                background-color: #e0e0e0;
            }
        """)

        # Layout for the Tab Container
        tab_layout = QHBoxLayout(tab_container)
        tab_layout.setContentsMargins(5, 0, 5, 0)
        tab_layout.setSpacing(5)

        # Favicon (icon on the left)
        tab_button_icon = QPushButton(tab_container)
        tab_button_icon.setFlat(True)
        tab_button_icon.setFixedSize(20, 20)
        tab_button_icon.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
            }
        """)

        # Tab Title
        tab_title = QPushButton("Loading...", tab_container)  # Changed to QPushButton for consistency
        tab_title.setFlat(True)
        tab_title.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                text-align: left;
                font-size: 14px;
                color: black;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0); /* Keep hover effect consistent */
            }
        """)
        tab_title.setFixedHeight(20)

        # Close Button
        close_button = QPushButton("✕", tab_container)
        close_button.setFlat(True)
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                color: #ff0000;
            }
            QPushButton:hover {
                color: #cc0000;
                background-color: rgba(255, 0, 0, 0.1);
            }
        """)
        close_button.clicked.connect(lambda: self.close_tab(tab_container))

        # Hidden Button for Tab Interaction
        hidden_tab_button = QToolButton(tab_container)
        hidden_tab_button.setFixedSize(200, 40)  # Match tab container size
        hidden_tab_button.setStyleSheet("""
            QToolButton {
                border: none;
                background-color: transparent;
            }
            QToolButton:hover {
                background-color: rgba(0, 0, 0, 0); /* Let hover effect propagate to parent */
            }
        """)
        hidden_tab_button.clicked.connect(lambda: self.switch_to_tab(tab_container))

        # Add hidden button over the tab container
        hidden_button_layout = QVBoxLayout(tab_container)
        hidden_button_layout.setContentsMargins(0, 0, 0, 0)
        hidden_button_layout.addWidget(hidden_tab_button)
        hidden_button_layout.setAlignment(Qt.AlignTop)

        # Add widgets to the Tab Layout
        tab_layout.addWidget(tab_button_icon)
        tab_layout.addWidget(tab_title)
        tab_layout.addStretch()
        tab_layout.addWidget(close_button)

        # Add Tab Container to the Tab Bar Layout
        self.title_bar.tab_bar_layout.insertWidget(self.title_bar.tab_bar_layout.count() - 1, tab_container)

        # Map the Tab Container to the Browser
        self.tab_map[tab_container] = browser
        browser.tab_button_title = tab_title  # Dynamically update the tab title

        # Connect Favicon Update
        browser.iconChanged.connect(lambda: self.update_tab_icon(browser, tab_button_icon))

        # Switch to the new tab
        self.switch_to_tab(tab_container)

        # Clear the URL field for the new tab
        self.toolbar.url_field.clear()
        self.toolbar.url_field.setPlaceholderText("Search or enter address")

        # Load the URL after initializing
        QTimer.singleShot(0, lambda: browser.setUrl(QUrl(url)))

    def _setup_tab_hover(self, tab_container, tab_button_icon, tab_title, close_button):
        """Unify hover behavior for the entire tab."""
        def hover_event(event):
            if event.type() == Qt.Enter:
                # Highlight entire tab on hover
                tab_container.setStyleSheet("""
                    QWidget {
                        background-color: #e0e0e0;
                        border: 1px solid #cccccc;
                        border-radius: 5px;
                    }
                """)
            elif event.type() == Qt.Leave:
                # Reset highlight when hover ends
                tab_container.setStyleSheet("""
                    QWidget {
                        background-color: #ffffff;
                        border: 1px solid #cccccc;
                        border-radius: 5px;
                    }
                """)
            return super(QWidget, tab_container).event(event)

        # Apply hover event to the container
        tab_container.event = hover_event

    def update_tab_icon(self, browser, tab_button_icon):
        """Update the favicon on the tab button."""
        icon = browser.icon()
        if not icon.isNull():
            tab_button_icon.setIcon(icon)  # Use setIcon for QPushButton
            tab_button_icon.setIconSize(tab_button_icon.size())  # Match the icon size to the button size

    def update_tab_title(self, browser, title):
        """Update the title of the tab associated with the given browser."""
        for tab_container, mapped_browser in self.tab_map.items():
            if mapped_browser == browser:
                tab_title = tab_container.layout().itemAt(1).widget()  # Second widget is the title button
                if isinstance(tab_title, QPushButton):  # Ensure it's the title button
                    tab_title.setText(title)

    def switch_to_tab(self, tab_container):
        """Switch to the tab associated with the given tab container."""
        if tab_container in self.tab_map:
            browser = self.tab_map[tab_container]
            index = self.content_stack.indexOf(browser)
            if index != -1:
                self.content_stack.setCurrentIndex(index)

            # Highlight the active tab
            self.highlight_active_tab(tab_container)

            # Update the URL field for the active tab
            current_url = browser.url().toString()
            if current_url == "https://www.google.com/":
                self.toolbar.url_field.clear()
                self.toolbar.url_field.setPlaceholderText("Search or enter address")
            else:
                self.toolbar.url_field.setText(current_url)

    def close_tab(self, tab_container):
        """Close the tab associated with the given tab container."""
        if tab_container in self.tab_map:
            # Remove browser content
            browser = self.tab_map.pop(tab_container)
            self.content_stack.removeWidget(browser)
            browser.deleteLater()

            # Remove the tab container
            self.title_bar.tab_bar_layout.removeWidget(tab_container)
            tab_container.deleteLater()

            # If no tabs remain, close the browser
            if not self.tab_map:
                self.close()
            else:
                # Switch to the first available tab
                first_tab = next(iter(self.tab_map.keys()))
                self.switch_to_tab(first_tab)

    def highlight_active_tab(self, active_tab):
        """Highlight the active tab and reset the styles of inactive tabs."""
        for i in range(self.title_bar.tab_bar_layout.count() - 1):
            tab_container = self.title_bar.tab_bar_layout.itemAt(i).widget()
            if tab_container == active_tab:
                tab_container.setStyleSheet("""
                    QWidget {
                        background-color: #d0d0d0;
                        border: 1px solid #cccccc;
                        border-radius: 5px;
                    }
                """)
            else:
                tab_container.setStyleSheet("""
                    QWidget {
                        background-color: #ffffff;
                        border: 1px solid #cccccc;
                        border-radius: 5px;
                    }
                    QWidget:hover {
                        background-color: #e0e0e0;
                    }
                """)

    def update_url_field_and_tab_title(self, browser, url):
        """Update the URL field and tab title when the browser URL changes."""
        # Update the URL field only if this is the active tab
        if self.content_stack.currentWidget() == browser:
            if url.toString() == "https://www.google.com/":
                self.toolbar.url_field.clear()  # Clear URL field for searches
                self.toolbar.url_field.setPlaceholderText("Search or enter address")
            else:
                self.toolbar.url_field.setText(url.toString())

        # Update the tab title based on the browser's title
        self.update_tab_title(browser, browser.title())

    def on_url_entered(self):
        """Load the URL or perform a search based on the entered text."""
        text = self.toolbar.url_field.text().strip()
        if not text:
            return

        # Detect if the entered text is a valid URL
        if text.startswith("http://") or text.startswith("https://"):
            url = text
        elif "." in text:  # Likely a domain
            url = "http://" + text
        else:
            # Treat as a search query and redirect to Google
            search_engine = "https://www.google.com/search?q="
            url = search_engine + text.replace(" ", "+")

        # Load the URL or search query
        current_tab = self.content_stack.currentWidget()
        if isinstance(current_tab, QWebEngineView):
            current_tab.setUrl(QUrl(url))

        # Clear focus from the URL field after submission
        self.toolbar.url_field.clearFocus()

    def select_url_on_click(self, event):
        """Select the entire URL when the field is clicked."""
        self.toolbar.url_field.selectAll()
        self.toolbar.url_field.setFocus()

    def on_back_clicked(self):
        """Go back in the browser history."""
        current_tab = self.content_stack.currentWidget()
        if isinstance(current_tab, QWebEngineView):
            current_tab.back()

    def on_forward_clicked(self):
        """Go forward in the browser history."""
        current_tab = self.content_stack.currentWidget()
        if isinstance(current_tab, QWebEngineView):
            current_tab.forward()

    def on_reload_clicked(self):
        """Reload the current page."""
        current_tab = self.content_stack.currentWidget()
        if isinstance(current_tab, QWebEngineView):
            current_tab.reload()

    def on_settings_clicked(self):
        """Handle Settings button click."""
        print("Settings button clicked!")  # Replace with actual settings logic

    def mousePressEvent(self, event):
        """Start resizing or pass to other components."""
        if event.button() == Qt.LeftButton and hasattr(self, "resize_direction") and self.resize_direction:
            self.resizing = True
            self.start_position = event.globalPos()
            self.start_geometry = self.geometry()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Stop resizing."""
        self.resizing = False
        self.resize_direction = None
        self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        """Handle resizing or update cursor shape."""
        if hasattr(self, "resizing") and self.resizing and hasattr(self, "resize_direction") and self.resize_direction:
            self.perform_resizing(event.globalPos())
        else:
            self.update_cursor(event.pos())
        super().mouseMoveEvent(event)

    def perform_resizing(self, global_pos):
        """Resize the window based on drag direction."""
        diff = global_pos - self.start_position
        rect = QRect(self.start_geometry)

        if "top" in self.resize_direction:
            rect.setTop(rect.top() + diff.y())
        if "bottom" in self.resize_direction:
            rect.setBottom(rect.bottom() + diff.y())
        if "left" in self.resize_direction:
            rect.setLeft(rect.left() + diff.x())
        if "right" in self.resize_direction:
            rect.setRight(rect.right() + diff.x())

        self.setGeometry(rect)