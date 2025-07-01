import sys
import os

from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt

# Ensure core modules are discoverable regardless of where script is run from
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)

# Import core tools
from core import fangxss, fangsql, fanglfi, fangrce, fangbrute, fangapi

class BloodFangGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BLOODFANG Offensive Toolkit")
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout()

        title = QLabel("BLOODFANG")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: crimson;")
        layout.addWidget(title)

        # Tool Buttons
        tools = [
            ("XSS Scanner", self.run_xss),
            ("SQLi Scanner", self.run_sqli),
            ("LFI Scanner", self.run_lfi),
            ("RCE Scanner", self.run_rce),
            ("Brute Forcer", self.run_brute),
            ("API Endpoint Finder", self.run_api),
        ]

        for label, method in tools:
            btn = QPushButton(label)
            btn.setStyleSheet("padding: 10px; font-size: 14px;")
            btn.clicked.connect(method)
            layout.addWidget(btn)

        self.central_widget.setLayout(layout)

    # Tool launchers — assumes each module has a `run()` or similar function
    def run_xss(self):
        try:
            fangxss.run()
        except Exception as e:
            print(f"[XSS] Error: {e}")

    def run_sqli(self):
        try:
            fangsql.run()
        except Exception as e:
            print(f"[SQLi] Error: {e}")

    def run_lfi(self):
        try:
            fanglfi.run()
        except Exception as e:
            print(f"[LFI] Error: {e}")

    def run_rce(self):
        try:
            fangrce.run()
        except Exception as e:
            print(f"[RCE] Error: {e}")

    def run_brute(self):
        try:
            fangbrute.run()
        except Exception as e:
            print(f"[Brute] Error: {e}")

    def run_api(self):
        try:
            fangapi.run()
        except Exception as e:
            print(f"[API] Error: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = BloodFangGUI()
    gui.show()
    sys.exit(app.exec_())
