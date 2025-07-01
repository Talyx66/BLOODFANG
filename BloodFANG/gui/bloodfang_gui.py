import sys
import os

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout,
    QWidget, QLabel, QTextEdit, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QMovie

# Path fix: always find core modules and assets no matter where script is run
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)

# Import core tool modules
from core import fangxss, fangsql, fanglfi, fangrce, fangbrute, fangapi

class BloodFangGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BLOODFANG Offensive Toolkit")
        self.setGeometry(100, 100, 900, 600)
        self.setStyleSheet("background-color: black; color: crimson;")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        main_layout = QVBoxLayout()

        # Logo section with animated or static bat
        logo_layout = QVBoxLayout()
        logo_label = QLabel("BLOODFANG")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("font-size: 40px; font-weight: bold; color: crimson;")
        logo_layout.addWidget(logo_label)

        bat_image = QLabel()
        bat_path = os.path.join(parent_dir, "assets", "hacker_bat.gif")  # <-- make sure this file exists

        if os.path.exists(bat_path):
            if bat_path.endswith(".gif"):
                movie = QMovie(bat_path)
                bat_image.setMovie(movie)
                movie.start()
            else:
                pixmap = QPixmap(bat_path)
                bat_image.setPixmap(pixmap.scaledToHeight(150))
            bat_image.setAlignment(Qt.AlignCenter)
        else:
            bat_image.setText("🦇 [Missing hacker_bat.gif in /assets]")
            bat_image.setAlignment(Qt.AlignCenter)

        logo_layout.addWidget(bat_image)
        main_layout.addLayout(logo_layout)

        # Button layout
        button_layout = QVBoxLayout()
        buttons = [
            ("XSS Scanner", self.run_xss),
            ("SQLi Scanner", self.run_sqli),
            ("LFI Scanner", self.run_lfi),
            ("RCE Scanner", self.run_rce),
            ("Brute Forcer", self.run_brute),
            ("API Endpoint Finder", self.run_api),
        ]

        for label, callback in buttons:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #111;
                    color: crimson;
                    font-size: 16px;
                    padding: 12px;
                    border: 1px solid crimson;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: crimson;
                    color: black;
                }
            """)
            btn.clicked.connect(callback)
            button_layout.addWidget(btn)

        # Output log window
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("background-color: #111; color: lime; font-family: monospace;")

        # Combine button + output layouts
        content_layout = QHBoxLayout()
        content_layout.addLayout(button_layout, 2)
        content_layout.addWidget(self.output, 5)

        main_layout.addLayout(content_layout)
        self.central_widget.setLayout(main_layout)

    def log(self, message):
        self.output.append(message)

    def run_xss(self):
        try:
            fangxss.scan_xss("http://example.com", "q", self.log)
        except Exception as e:
            self.log(f"[XSS] Error: {e}")

    def run_sqli(self):
        try:
            fangsql.run()
        except Exception as e:
            self.log(f"[SQLi] Error: {e}")

    def run_lfi(self):
        try:
            fanglfi.run()
        except Exception as e:
            self.log(f"[LFI] Error: {e}")

    def run_rce(self):
        try:
            fangrce.run()
        except Exception as e:
            self.log(f"[RCE] Error: {e}")

    def run_brute(self):
        try:
            fangbrute.run()
        except Exception as e:
            self.log(f"[Brute] Error: {e}")

    def run_api(self):
        try:
            fangapi.run()
        except Exception as e:
            self.log(f"[API] Error: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = BloodFangGUI()
    gui.show()
    sys.exit(app.exec_())
