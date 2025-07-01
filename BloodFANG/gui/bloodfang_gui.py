import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QVBoxLayout,
    QWidget, QLabel, QTextEdit, QHBoxLayout
)
from PyQt5.QtGui import QMovie, QPalette, QColor
from PyQt5.QtCore import Qt

# Fix for relative imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)

# Import all BLOODFANG modules
from core import fangxss, fangsql, fanglfi, fangrce, fangbrute, fangapi

class BloodFangGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BLOODFANG Offensive Toolkit")
        self.setGeometry(100, 100, 1000, 650)
        self.setStyleSheet("background: transparent; color: crimson;")

        # === Background GIF ===
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, 1000, 650)
        bg_path = os.path.join(parent_dir, "assets", "Talyxlogo6.gif")
        if os.path.exists(bg_path):
            self.movie = QMovie(bg_path)
            self.bg_label.setMovie(self.movie)
            self.movie.start()
        else:
            self.bg_label.setText("[!] Background GIF missing: Talyxlogo6.gif")

        self.central_widget = QWidget(self)
        self.central_widget.setStyleSheet("background: transparent;")
        self.setCentralWidget(self.central_widget)

        # Layouts
        main_layout = QVBoxLayout()
        title_label = QLabel("BLOODFANG")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 40px; font-weight: bold; color: crimson; background: transparent;")
        main_layout.addWidget(title_label)

        button_layout = QVBoxLayout()
        buttons = [
            ("XSS Scanner", self.run_xss),
            ("SQLi Scanner", self.run_sqli),
            ("LFI Scanner", self.run_lfi),
            ("RCE Scanner", self.run_rce),
            ("Brute Forcer", self.run_brute),
            ("API Endpoint Finder", self.run_api),
        ]
        for text, callback in buttons:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 0, 0, 200);
                    color: crimson;
                    font-size: 16px;
                    padding: 10px;
                    border: 1px solid crimson;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: crimson;
                    color: black;
                }
            """)
            button_layout.addWidget(btn)

        # Output field
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("""
            background-color: rgba(0, 0, 0, 200);
            color: lime;
            font-family: monospace;
        """)

        content_layout = QHBoxLayout()
        content_layout.addLayout(button_layout, 2)
        content_layout.addWidget(self.output, 5)

        main_layout.addLayout(content_layout)
        self.central_widget.setLayout(main_layout)

        # Stack background under everything
        self.bg_label.lower()

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
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(0, 0, 0))
    app.setPalette(palette)

    gui = BloodFangGUI()
    gui.show()
    sys.exit(app.exec_())
