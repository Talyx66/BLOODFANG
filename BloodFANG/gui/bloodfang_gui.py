# gui/bloodfang_gui.py
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

        title = QLabel("🩸 BloodFANG - Offensive Security Toolkit")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #ff0000;")
        main_layout.addWidget(title)

        # Grid for inputs and buttons
        grid = QGridLayout()

        # --- XSS ---
        grid.addWidget(QLabel("XSS Target URL:"), 0, 0)
        self.xss_url = QLineEdit()
        self.xss_url.setPlaceholderText("http://target.com/search")
        self.xss_url.setStyleSheet("color: #ff1a1a; background: transparent; border: 1px solid #ff1a1a; padding: 5px;")
        grid.addWidget(self.xss_url, 0, 1)

        grid.addWidget(QLabel("Parameter:"), 0, 2)
        self.xss_param = QLineEdit()
        self.xss_param.setText("q")
        self.xss_param.setStyleSheet("color: #ff1a1a; background: transparent; border: 1px solid #ff1a1a; padding: 5px;")
        grid.addWidget(self.xss_param, 0, 3)

        self.xss_btn = QPushButton("Run XSS Scan")
        self.xss_btn.setStyleSheet("background-color: #ff1a1a; color: black; font-weight: bold;")
        self.xss_btn.clicked.connect(self.run_xss)
        grid.addWidget(self.xss_btn, 0, 4)

        # --- SQLi ---
        grid.addWidget(QLabel("SQLi Target URL:"), 1, 0)
        self.sqli_url = QLineEdit()
        self.sqli_url.setPlaceholderText("http://target.com/item")
        self.sqli_url.setStyleSheet("color: #ff1a1a; background: transparent; border: 1px solid #ff1a1a; padding: 5px;")
        grid.addWidget(self.sqli_url, 1, 1)

        grid.addWidget(QLabel("Parameter:"), 1, 2)
        self.sqli_param = QLineEdit()
        self.sqli_param.setText("id")
        self.sqli_param.setStyleSheet("color: #ff1a1a; background: transparent; border: 1px solid #ff1a1a; padding: 5px;")
        grid.addWidget(self.sqli_param, 1, 3)

        self.sqli_btn = QPushButton("Run SQLi Scan")
        self.sqli_btn.setStyleSheet("background-color: #ff1a1a; color: black; font-weight: bold;")
        self.sqli_btn.clicked.connect(self.run_sqli)
        grid.addWidget(self.sqli_btn, 1, 4)

        # --- LFI ---
        grid.addWidget(QLabel("LFI Target URL:"), 2, 0)
        self.lfi_url = QLineEdit()
        self.lfi_url.setPlaceholderText("http://target.com/view")
        self.lfi_url.setStyleSheet("color: #ff1a1a; background: transparent; border: 1px solid #ff1a1a; padding: 5px;")
        grid.addWidget(self.lfi_url, 2, 1)

        grid.addWidget(QLabel("Parameter:"), 2, 2)
        self.lfi_param = QLineEdit()
        self.lfi_param.setText("file")
        self.lfi_param.setStyleSheet("color: #ff1a1a; background: transparent; border: 1px solid #ff1a1a; padding: 5px;")
        grid.addWidget(self.lfi_param, 2, 3)

        self.lfi_btn = QPushButton("Run LFI Scan")
        self.lfi_btn.setStyleSheet("background-color: #ff1a1a; color: black; font-weight: bold;")
        self.lfi_btn.clicked.connect(self.run_lfi)
        grid.addWidget(self.lfi_btn, 2, 4)

        # --- RCE ---
        grid.addWidget(QLabel("RCE Target URL:"), 3, 0)
        self.rce_url = QLineEdit()
        self.rce_url.setPlaceholderText("http://target.com/exec")
        self.rce_url.setStyleSheet("color: #ff1a1a; background: transparent; border: 1px solid #ff1a1a; padding: 5px;")
        grid.addWidget(self.rce_url, 3, 1)

        grid.addWidget(QLabel("Parameter:"), 3, 2)
        self.rce_param = QLineEdit()
        self.rce_param.setText("cmd")
        self.rce_param.setStyleSheet("color: #ff1a1a; background: transparent; border: 1px solid #ff1a1a; padding: 5px;")
        grid.addWidget(self.rce_param, 3, 3)

        self.rce_btn = QPushButton("Run RCE Scan")
        self.rce_btn.setStyleSheet("background-color: #ff1a1a; color: black; font-weight: bold;")
        self.rce_btn.clicked.connect(self.run_rce)
        grid.addWidget(self.rce_btn, 3, 4)

        # --- Brute Force ---
        grid.addWidget(QLabel("Brute Force Base URL:"), 4, 0)
        self.brute_url = QLineEdit()
        self.brute_url.setPlaceholderText("http://target.com")
        self.brute_url.setStyleSheet("color: #ff1a1a; background: transparent; border: 1px solid #ff1a1a; padding: 5px;")
        grid.addWidget(self.brute_url, 4, 1)

        grid.addWidget(QLabel("Login Path:"), 4, 2)
        self.brute_path = QLineEdit()
        self.brute_path.setPlaceholderText("/login")
        self.brute_path.setText("/login")
        self.brute_path.setStyleSheet("color: #ff1a1a; background: transparent; border: 1px solid #ff1a1a; padding: 5px;")
        grid.addWidget(self.brute_path, 4, 3)

        self.brute_btn = QPushButton("Run Brute Force")
        self.brute_btn.setStyleSheet("background-color: #ff1a1a; color: black; font-weight: bold;")
        self.brute_btn.clicked.connect(self.run_brute)
        grid.addWidget(self.brute_btn, 4, 4)

        # --- API Discovery ---
        grid.addWidget(QLabel("API Base URL:"), 5, 0)
        self.api_url = QLineEdit()
        self.api_url.setPlaceholderText("http://target.com")
        self.api_url.setStyleSheet("color: #ff1a1a; background: transparent; border: 1px solid #ff1a1a; padding: 5px;")
        grid.addWidget(self.api_url, 5, 1)

        self.api_btn = QPushButton("Run API Discovery")
        self.api_btn.setStyleSheet("background-color: #ff1a1a; color: black; font-weight: bold;")
        self.api_btn.clicked.connect(self.run_api)
        grid.addWidget(self.api_btn, 5, 4)

        main_layout.addLayout(grid)

        # Output console
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setStyleSheet("background-color: #1a1a1a; color: #00ff00; font-family: Consolas;")
        main_layout.addWidget(self.output_console)

        # Footer
        footer_layout = QHBoxLayout()
        hacker_name_label = QLabel("Talyx")
        hacker_name_label.setStyleSheet("color: #ff1a1a; font-weight: bold;")
        footer_layout.addWidget(hacker_name_label, alignment=Qt.AlignLeft)

        github_label = QLabel('<a href="https://github.com/Talyx66" style="color: #ff1a1a; text-decoration: none;">github.com/Talyx66</a>')
        github_label.setOpenExternalLinks(True)
        footer_layout.addWidget(github_label, alignment=Qt.AlignRight)

        main_layout.addLayout(footer_layout)

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

        # Sample username/password lists (replace or extend as needed)
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
    import sys
    app = QApplication(sys.argv)
    gui = BloodFangGUI()
    gui.show()
    sys.exit(app.exec_())
