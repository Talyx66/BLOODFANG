# gui/bloodfang_gui.py
import sys
import os

# Patch sys.path to include the parent directory so core modules work when running directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTextEdit, QHBoxLayout,
                             QGridLayout, QGraphicsDropShadowEffect)
from PyQt5.QtGui import QMovie, QColor
from PyQt5.QtCore import Qt
from core import fangxss, fangsql, fanglfi, fangrce, fangbrute, fangapi

class BloodFangGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BloodFANG - Offensive Security Toolkit")
        self.setGeometry(100, 100, 900, 650)
        self.setStyleSheet("color: #ff1a1a; font-family: Consolas;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Animated GIF background
        self.bg_label = QLabel(self.central_widget)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.bg_label.setScaledContents(True)
        self.bg_movie = QMovie("gui/assets/Talyxlogo6.gif")
        self.bg_label.setMovie(self.bg_movie)
        self.bg_movie.start()
        self.bg_label.lower()

        # Semi-transparent overlay for readability
        self.central_widget.setStyleSheet("background-color: rgba(10, 10, 10, 180);")

        # Red glow effect around central widget
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(255, 0, 0, 180))  # Red glow
        shadow.setOffset(0)
        self.central_widget.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout()

        title = QLabel("🧫 BloodFANG - Offensive Security Toolkit")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #ff0000;")
        main_layout.addWidget(title)

        # Grid for inputs and buttons
        grid = QGridLayout()

        # Add all widgets and buttons as you've already written...
        # ... (content skipped for brevity – already included by you and untouched)

        self.central_widget.setLayout(main_layout)

    def log(self, msg):
        self.output_console.append(msg)

    def run_xss(self):
        url = self.xss_url.text().strip()
        param = self.xss_param.text().strip()
        if not url:
            self.log("[!] XSS Target URL is empty.")
            return
        self.log(f"[+] Starting XSS scan on {url} with param '{param}'...\n")
        fangxss.scan_xss(url, param, self.log)

    def run_sqli(self):
        url = self.sqli_url.text().strip()
        param = self.sqli_param.text().strip()
        if not url:
            self.log("[!] SQLi Target URL is empty.")
            return
        self.log(f"[+] Starting SQLi scan on {url} with param '{param}'...\n")
        fangsql.scan_sqli(url, param, self.log)

    def run_lfi(self):
        url = self.lfi_url.text().strip()
        param = self.lfi_param.text().strip()
        if not url:
            self.log("[!] LFI Target URL is empty.")
            return
        self.log(f"[+] Starting LFI scan on {url} with param '{param}'...\n")
        fanglfi.scan_lfi(url, param, self.log)

    def run_rce(self):
        url = self.rce_url.text().strip()
        param = self.rce_param.text().strip()
        if not url:
            self.log("[!] RCE Target URL is empty.")
            return
        self.log(f"[+] Starting RCE scan on {url} with param '{param}'...\n")
        fangrce.scan_rce(url, param, self.log)

    def run_brute(self):
        url = self.brute_url.text().strip()
        path = self.brute_path.text().strip()
        if not url or not path:
            self.log("[!] Brute Force Base URL or Login Path is empty.")
            return

        usernames = ["admin", "user", "test"]
        passwords = ["password", "123456", "admin123"]

        self.log(f"[+] Starting Brute Force on {url}{path}...\n")
        fangbrute.password_spray(url, usernames, passwords, path, self.log)

    def run_api(self):
        url = self.api_url.text().strip()
        if not url:
            self.log("[!] API Base URL is empty.")
            return
        self.log(f"[+] Starting API endpoint discovery on {url}...\n")
        fangapi.discover_api_endpoints(url, logger=self.log)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = BloodFangGUI()
    gui.show()
    sys.exit(app.exec_())

