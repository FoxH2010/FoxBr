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

    def add_new_tab(self, title="New Tab", url="https://www.google.com"):
        """Add a new tab and load content asynchronously."""
        # Browser content (placeholder during Chromium loading)
        browser = QWebEngineView()
        browser.setHtml("<h1>Loading...</h1>")  # Lightweight placeholder
        browser.titleChanged.connect(lambda title: self.update_tab_title(browser, title))
        browser.urlChanged.connect(self.update_url_bar)

        # Connect to the iconChanged signal
        browser.iconChanged.connect(lambda icon: self.update_tab_icon(browser, icon))

        self.content_stack.addWidget(browser)

        # Tab Button with Icon and Title
        tab_button_icon = QLabel()  # Icon holder
        tab_button_icon.setFixedSize(20, 20)
        tab_button_icon.setStyleSheet("border: none;")  # No border or background

        tab_button_title = QToolButton(self)  # Title holder
        tab_button_title.setText(title)
        tab_button_title.setCheckable(True)
        tab_button_title.setFixedSize(180, 40)
        tab_button_title.setStyleSheet("text-align: left; padding-left: 10px;")
        tab_button_title.clicked.connect(lambda: self.switch_to_tab(tab_button_title))

        close_button = QToolButton(self)
        close_button.setText("✕")
        close_button.setFixedSize(40, 40)
        close_button.clicked.connect(lambda: self.close_tab(tab_button_title, browser))

        # Tab layout
        tab_layout = QHBoxLayout()
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(5)
        tab_layout.addWidget(tab_button_icon)
        tab_layout.addWidget(tab_button_title)
        tab_layout.addWidget(close_button)

        # Tab container
        tab_container = QWidget()
        tab_container.setLayout(tab_layout)
        self.title_bar.tab_bar_layout.insertWidget(self.title_bar.tab_bar_layout.count() - 1, tab_container)

        # Store references for future updates
        browser.tab_button_icon = tab_button_icon
        browser.tab_button_title = tab_button_title

        # Switch to the new tab
        self.switch_to_tab(tab_button_title)

        # Clear the URL field for the new tab
        self.toolbar.url_field.clear()
        self.toolbar.url_field.setPlaceholderText("Search or enter address")

        # Defer loading actual content
        QTimer.singleShot(0, lambda: browser.setUrl(QUrl(url)))

    def update_tab_icon(self, browser, icon):
        """Update the icon on the tab button associated with the browser."""
        if hasattr(browser, "tab_button_icon"):
            # Convert QIcon to QPixmap and set it on the QLabel
            pixmap = icon.pixmap(20, 20)  # Ensure the favicon fits within 20x20 size
            browser.tab_button_icon.setPixmap(pixmap)

    def update_tab_title(self, browser, title):
        """Update the title of the tab associated with the given browser."""
        for i in range(self.title_bar.tab_bar_layout.count() - 1):
            tab_container = self.title_bar.tab_bar_layout.itemAt(i).widget()
            tab_button = tab_container.layout().itemAt(0).widget()
            if self.content_stack.widget(i) is browser:
                tab_button.setText(title)

    def switch_to_tab(self, tab_button):
        """Switch to the tab associated with the given tab button."""
        index = self.title_bar.tab_bar_layout.indexOf(tab_button.parentWidget())
        if index >= 0 and index < self.content_stack.count():
            self.content_stack.setCurrentIndex(index)
            self.highlight_active_tab(index)

    def close_tab(self, tab_button, browser):
        """Close the tab associated with the given tab button."""
        index = self.title_bar.tab_bar_layout.indexOf(tab_button.parentWidget())
        if index >= 0:
            # Remove tab content
            self.content_stack.removeWidget(browser)
            browser.deleteLater()

            # Remove tab button
            widget_to_remove = tab_button.parentWidget()
            self.title_bar.tab_bar_layout.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()

            # Check if there are any tabs left
            if self.content_stack.count() > 0:
                self.content_stack.setCurrentIndex(0)
                self.highlight_active_tab(0)
            else:
                # No tabs left, close the window
                self.close()

    def highlight_active_tab(self, index):
        """Highlight the active tab."""
        for i in range(self.title_bar.tab_bar_layout.count() - 1):
            tab_container = self.title_bar.tab_bar_layout.itemAt(i).widget()
            tab_button = tab_container.layout().itemAt(0).widget()
            if i == index:
                tab_button.setStyleSheet("background-color: #d0d0d0;")
            else:
                tab_button.setStyleSheet("background-color: #ffffff;")

    def update_url_bar(self, url):
        """Update the URL bar when the current tab's URL changes."""
        current_tab = self.content_stack.currentWidget()
        if isinstance(current_tab, QWebEngineView):
            if url.toString() != "https://www.google.com/":  # Only update if not the default page
                self.toolbar.url_field.setText(url.toString())
                self.toolbar.url_field.setCursorPosition(0)

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