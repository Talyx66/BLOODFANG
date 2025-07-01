
# gui/bloodfang_gui.py

import sys
import os

# Ensure core modules are accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QLineEdit, QPushButton, QTextEdit, QGridLayout)
from PyQt5.QtGui import QMovie, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

from core import fangxss, fangsql, fanglfi, fangrce, fangbrute, fangapi

class BloodFangGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BloodFANG - Offensive Security Toolkit")
        self.setGeometry(100, 100, 1000, 700)

        self.setStyleSheet("""
            QMainWindow {
                background-color: black;
            }
            QLabel {
                color: #ff4d4d;
                font-family: Consolas;
            }
            QPushButton {
                background-color: #1a1a1a;
                color: #ff1a1a;
                border: 1px solid #ff1a1a;
                padding: 6px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #330000;
            }
            QLineEdit {
                background-color: #222;
                color: #ffcccc;
                border: 1px solid #ff1a1a;
                padding: 4px;
                font-family: Consolas;
            }
            QTextEdit {
                background-color: #111;
                color: #ff4d4d;
                font-family: Consolas;
                font-size: 13px;
            }
        """)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Load and check GIF path
        gif_path = os.path.join(os.path.dirname(__file__), "assets", "Talyxlogo6.gif")
        if not os.path.exists(gif_path):
            print(f"[!] GIF not found at: {gif_path}")

        # Background GIF logo
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.bg_label.setScaledContents(True)

        self.bg_movie = QMovie(gif_path)
        if not self.bg_movie.isValid():
            print("[!] Invalid GIF file or path.")
        self.bg_label.setMovie(self.bg_movie)
        self.bg_movie.start()
        self.bg_label.lower()

        # Red glow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(255, 0, 0, 180))
        shadow.setOffset(0)
        self.central_widget.setGraphicsEffect(shadow)

        # Transparent overlay so GIF shows through
        self.central_widget.setStyleSheet("background-color: rgba(20, 20, 20, 100);")

        layout = QVBoxLayout()

        title = QLabel("BLOODFANG")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 55px; font-weight: bold; color: #ff0000;")
        layout.addWidget(title)

        # Main input grid
        grid = QGridLayout()

        # XSS
        self.xss_url = QLineEdit(); self.xss_url.setPlaceholderText("XSS Target URL")
        self.xss_param = QLineEdit(); self.xss_param.setPlaceholderText("XSS Parameter")
        xss_btn = QPushButton("Run XSS"); xss_btn.clicked.connect(self.run_xss)

        # SQLi
        self.sqli_url = QLineEdit(); self.sqli_url.setPlaceholderText("SQLi Target URL")
        self.sqli_param = QLineEdit(); self.sqli_param.setPlaceholderText("SQLi Parameter")
        sqli_btn = QPushButton("Run SQLi"); sqli_btn.clicked.connect(self.run_sqli)

        # LFI
        self.lfi_url = QLineEdit(); self.lfi_url.setPlaceholderText("LFI Target URL")
        self.lfi_param = QLineEdit(); self.lfi_param.setPlaceholderText("LFI Parameter")
        lfi_btn = QPushButton("Run LFI"); lfi_btn.clicked.connect(self.run_lfi)

        # RCE
        self.rce_url = QLineEdit(); self.rce_url.setPlaceholderText("RCE Target URL")
        self.rce_param = QLineEdit(); self.rce_param.setPlaceholderText("RCE Parameter")
        rce_btn = QPushButton("Run RCE"); rce_btn.clicked.connect(self.run_rce)

        # Brute Force
        self.brute_url = QLineEdit(); self.brute_url.setPlaceholderText("Brute Base URL")
        self.brute_path = QLineEdit(); self.brute_path.setPlaceholderText("Login Path")
        brute_btn = QPushButton("Run Brute Force"); brute_btn.clicked.connect(self.run_brute)

        # API Discovery
        self.api_url = QLineEdit(); self.api_url.setPlaceholderText("API Base URL")
        api_btn = QPushButton("Discover API"); api_btn.clicked.connect(self.run_api)

        # Add to grid
        elements = [
            (self.xss_url, self.xss_param, xss_btn),
            (self.sqli_url, self.sqli_param, sqli_btn),
            (self.lfi_url, self.lfi_param, lfi_btn),
            (self.rce_url, self.rce_param, rce_btn),
            (self.brute_url, self.brute_path, brute_btn),
            (self.api_url, None, api_btn)
        ]

        for i, (url, param, btn) in enumerate(elements):
            grid.addWidget(url, i, 0)
            if param:
                grid.addWidget(param, i, 1)
            grid.addWidget(btn, i, 2)

        layout.addLayout(grid)
        # Static tool info + parameter examples
        tool_info = QLabel("""
        <b style="font-size:14px;">Tool Descriptions:</b><br>
           <b>XSS Scanner</b>: Detects reflected/stored cross-site scripting.<br>
           <b>SQLi Scanner</b>: Probes for SQL injection flaws via input params.<br>
           <b>LFI Scanner</b>: Attempts local file reads using traversal payloads.<br>
           <b>RCE Scanner</b>: Tests for command execution via vulnerable input.<br>
           <b>Brute Forcer</b>: Username/password spray for weak logins.<br>
           <b>API Finder</b>: Scans for common REST API endpoints.<br><br>

        <b style="font-size:14px;">Parameter Examples:</b><br>
        XSS/SQLi/LFI/RCE Param: <code>q</code>, <code>search</code>, <code>id</code>, <code>file</code><br>
        Brute Force Path: <code>/login</code>, <code>/admin/auth</code><br>
        API Base URL: <code>http://target.com</code> or <code>http://target.com/api</code>
        """)
        tool_info.setStyleSheet("""
            color: #ff4d4d;
            font-size: 12px;
            background-color: rgba(30, 30, 30, 180);
            padding: 8px;
            border: 1px solid #ff1a1a;
            border-radius: 5px;
        """)        
        tool_info.setStyleSheet("color: #ff4d4d; font-size: 12px; background-color: rgba(30,30,30,180); padding: 6px;")
        tool_info.setAlignment(Qt.AlignLeft)
        tool_info.setWordWrap(True)
        layout.addWidget(tool_info)

        # Console Output
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        layout.addWidget(self.output_console)

        self.central_widget.setLayout(layout)

    def resizeEvent(self, event):
        self.bg_label.resize(self.size())
        super().resizeEvent(event)

    # Logging
    def log(self, msg):
        self.output_console.append(msg)

    # Tool logic bindings
    def run_xss(self):
        url = self.xss_url.text().strip()
        param = self.xss_param.text().strip()
        if not url:
            self.log("[!] XSS Target URL is empty.")
            return
        self.log(f"[+] XSS scan on {url} with param '{param}'")
        fangxss.scan_xss(url, param, self.log)

    def run_sqli(self):
        url = self.sqli_url.text().strip()
        param = self.sqli_param.text().strip()
        if not url:
            self.log("[!] SQLi Target URL is empty.")
            return
        self.log(f"[+] SQLi scan on {url} with param '{param}'")
        fangsql.scan_sqli(url, param, self.log)

    def run_lfi(self):
        url = self.lfi_url.text().strip()
        param = self.lfi_param.text().strip()
        if not url:
            self.log("[!] LFI Target URL is empty.")
            return
        self.log(f"[+] LFI scan on {url} with param '{param}'")
        fanglfi.scan_lfi(url, param, self.log)

    def run_rce(self):
        url = self.rce_url.text().strip()
        param = self.rce_param.text().strip()
        if not url:
            self.log("[!] RCE Target URL is empty.")
            return
        self.log(f"[+] RCE scan on {url} with param '{param}'")
        fangrce.scan_rce(url, param, self.log)

    def run_brute(self):
        url = self.brute_url.text().strip()
        path = self.brute_path.text().strip()
        if not url or not path:
            self.log("[!] Brute Force URL or path is empty.")
            return
        usernames = ["admin", "user", "test"]
        passwords = ["123456", "admin123", "password"]
        self.log(f"[+] Brute Force on {url}{path}")
        fangbrute.password_spray(url, usernames, passwords, path, self.log)

    def run_api(self):
        url = self.api_url.text().strip()
        if not url:
            self.log("[!] API Base URL is empty.")
            return
        self.log(f"[+] Discovering API endpoints on {url}")
        fangapi.discover_api_endpoints(url, logger=self.log)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = BloodFangGUI()
    gui.show()
    sys.exit(app.exec_())
