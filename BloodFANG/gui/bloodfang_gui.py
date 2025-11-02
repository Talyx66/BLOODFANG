# gui/bloodfang_gui.py
import sys
import os
import traceback
import importlib
import threading
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QGridLayout, QHBoxLayout, QSplitter, QScrollArea,
    QFileDialog, QGroupBox
)
from PyQt5.QtGui import QMovie, QColor, QFont, QIcon, QKeySequence, QTextCursor
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

# Make sure core modules are importable (repo layout: BloodFANG/)
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent  # BloodFANG/
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# If your modules live as `core.fangxss` relative to this gui/ folder, this will work.
CORE_PACKAGE_NAMES = ["core", "BloodFANG.core"]  # try both import roots


def discover_core_module_names(core_dir):
    mods = []
    try:
        for p in sorted(core_dir.glob("fang*.py")):
            if not p.name.startswith("__"):
                mods.append(p.stem)  # fangxss
    except Exception:
        pass
    return mods


class WorkerThread(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, module_name, func_name_hint, target):
        super().__init__()
        self.module_name = module_name
        self.func_hint = func_name_hint  # e.g., 'scan_xss' or None
        self.target = target
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def emit_log(self, text, level="INFO"):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_signal.emit(f"[{ts}] [{level}] {text}")

    def _module_emit(self, message):
        self.emit_log(message)

    def _import_module(self, modname):
        # Try multiple package roots
        for root in CORE_PACKAGE_NAMES:
            try:
                full = f"{root}.{modname}"
                mod = importlib.import_module(full)
                return mod
            except Exception:
                continue
        # Last-ditch: try direct import
        try:
            return importlib.import_module(modname)
        except Exception as e:
            raise ImportError(f"Could not import '{modname}' (tried roots): {e}")

    def run(self):
        try:
            self.emit_log(f"Worker starting: module='{self.module_name}' target='{self.target}'")
            module = None
            try:
                module = self._import_module(self.module_name)
            except Exception as e:
                self.emit_log(f"Import error: {e}", level="ERROR")
                self.error_signal.emit(str(e))
                self.finished_signal.emit()
                return

            # Determine callable strategy
            candidates = []

            # If a func hint exists (like scan_xss) prefer that
            if self.func_hint:
                candidates.append((self.func_hint, True))   # try with stop_event
                candidates.append((self.func_hint, False))  # try without stop_event

            # Common entrypoints
            candidates += [
                ("run", True),
                ("run", False),
                ("scan", True),
                ("scan", False),
                ("main", False),
            ]

            invoked = False
            for name, with_stop in candidates:
                func = getattr(module, name, None)
                if callable(func):
                    try:
                        if with_stop:
                            self.emit_log(f"Calling {self.module_name}.{name}(target, emit, stop_event)")
                            func(self.target, self._module_emit, self._stop_event)
                        else:
                            # try (target, emit) else (target)
                            try:
                                self.emit_log(f"Calling {self.module_name}.{name}(target, emit)")
                                func(self.target, self._module_emit)
                            except TypeError:
                                self.emit_log(f"Calling {self.module_name}.{name}(target)")
                                func(self.target)
                        invoked = True
                        break
                    except Exception as e:
                        self.emit_log(f"Error during {self.module_name}.{name}: {e}", level="ERROR")
                        tb = traceback.format_exc()
                        self.emit_log(tb, level="DEBUG")

            if not invoked:
                # Try function name patterns inside module, like scan_xss, scan_sqli, etc.
                if self.func_hint:
                    alt = getattr(module, self.func_hint, None)
                    if callable(alt):
                        try:
                            alt(self.target, self._module_emit, self._stop_event)
                            invoked = True
                        except Exception as e:
                            self.emit_log(f"Alt call {self.func_hint} failed: {e}", level="ERROR")

            if not invoked:
                self.emit_log(f"No compatible entry point found for module '{self.module_name}'.", level="ERROR")
                self.error_signal.emit(f"No entry point found for {self.module_name}")
            else:
                self.emit_log(f"Module '{self.module_name}' finished.")
        except Exception as e:
            self.emit_log(f"Unhandled worker exception: {e}", level="ERROR")
            self.error_signal.emit(str(e))
        finally:
            self.finished_signal.emit()


class BloodFangGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BLOODFANG - Offensive Security")
        self.settings = QSettings("Talyx", "BLOODFANG")

        # Restore geometry if present
        geom = self.settings.value("geometry")
        if geom:
            try:
                self.restoreGeometry(geom)
            except Exception:
                pass

        self.setMinimumSize(900, 600)

        # Basic stylesheet (kept from your original)
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

        # Main widget + layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_v = QVBoxLayout(self.central_widget)
        main_v.setContentsMargins(8, 8, 8, 8)

        # Header: hacker name, title, github
        header_h = QHBoxLayout()
        hacker_name_label = QLabel("Talyx")
        hacker_name_label.setStyleSheet("font-size: 18px; color: #ff4d4d; font-weight: bold;")
        header_h.addWidget(hacker_name_label, alignment=Qt.AlignLeft)

        title_label = QLabel("BLOODFANG")
        title_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #ff0000;")
        title_label.setAlignment(Qt.AlignCenter)
        header_h.addWidget(title_label, stretch=1)

        github_label = QLabel("Github.com/Talyx66")
        github_label.setStyleSheet("font-size: 14px; color: #ff4d4d; font-style: italic;")
        header_h.addWidget(github_label, alignment=Qt.AlignRight)

        main_v.addLayout(header_h)

        # Top area: grid controls on the left, placeholder on right (splitter between)
        self.splitter = QSplitter(Qt.Horizontal)
        main_v.addWidget(self.splitter, 10)

        # Left controls (in a scroll area to avoid overflow)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(6, 6, 6, 6)

        grid = QGridLayout()
        grid.setSpacing(8)

        # XSS
        self.xss_url = QLineEdit()
        self.xss_url.setPlaceholderText("XSS Target URL")
        self.xss_param = QLineEdit()
        self.xss_param.setPlaceholderText("XSS Parameter")
        xss_btn = QPushButton("Run XSS")
        xss_btn.clicked.connect(self._start_xss)

        # SQLi
        self.sqli_url = QLineEdit(); self.sqli_url.setPlaceholderText("SQLi Target URL")
        self.sqli_param = QLineEdit(); self.sqli_param.setPlaceholderText("SQLi Parameter")
        sqli_btn = QPushButton("Run SQLi"); sqli_btn.clicked.connect(self._start_sqli)

        # LFI
        self.lfi_url = QLineEdit(); self.lfi_url.setPlaceholderText("LFI Target URL")
        self.lfi_param = QLineEdit(); self.lfi_param.setPlaceholderText("LFI Parameter")
        lfi_btn = QPushButton("Run LFI"); lfi_btn.clicked.connect(self._start_lfi)

        # RCE
        self.rce_url = QLineEdit(); self.rce_url.setPlaceholderText("RCE Target URL")
        self.rce_param = QLineEdit(); self.rce_param.setPlaceholderText("RCE Parameter")
        rce_btn = QPushButton("Run RCE"); rce_btn.clicked.connect(self._start_rce)

        # Brute Force
        self.brute_url = QLineEdit(); self.brute_url.setPlaceholderText("Brute Base URL")
        self.brute_path = QLineEdit(); self.brute_path.setPlaceholderText("Login Path")
        brute_btn = QPushButton("Run Brute Force"); brute_btn.clicked.connect(self._start_brute)

        # API Discovery
        self.api_url = QLineEdit(); self.api_url.setPlaceholderText("API Base URL")
        api_btn = QPushButton("Discover API"); api_btn.clicked.connect(self._start_api)

        # Placement in grid
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

        left_layout.addLayout(grid)

        # Presets / Quick Actions box (kept for compatibility)
        self.presets_box = QGroupBox("Presets / Quick Actions")
        self.presets_layout = QVBoxLayout()
        self.presets_box.setLayout(self.presets_layout)
        left_layout.addWidget(self.presets_box)

        left_layout.addStretch(1)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(left_widget)

        self.splitter.addWidget(left_scroll)

        # Right placeholder: can show module info; but primarily used to allocate space
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_label = QLabel("Module Preview / Details")
        right_label.setAlignment(Qt.AlignTop)
        right_layout.addWidget(right_label)
        self.splitter.addWidget(right_widget)

        # Bottom: output console takes big area — place under splitter but large
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        font = QFont("Consolas", 11)
        self.output_console.setFont(font)
        self.output_console.setLineWrapMode(QTextEdit.NoWrap)
        main_v.addWidget(self.output_console, 6)

        # Save/clear/stop controls under console
        controls_h = QHBoxLayout()
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_worker)
        self.clear_btn = QPushButton("Clear Output")
        self.clear_btn.clicked.connect(self.output_console.clear)
        self.save_btn = QPushButton("Save Log...")
        self.save_btn.clicked.connect(self._save_log)

        controls_h.addWidget(self.stop_btn)
        controls_h.addWidget(self.clear_btn)
        controls_h.addWidget(self.save_btn)
        controls_h.addStretch(1)
        main_v.addLayout(controls_h)

        # Background GIF
        gif_path = os.path.join(os.path.dirname(__file__), "assets", "Talyxlogo6.gif")
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.lower()  # keep behind everything
        if os.path.exists(gif_path):
            try:
                self.bg_movie = QMovie(gif_path)
                if self.bg_movie.isValid():
                    self.bg_label.setMovie(self.bg_movie)
                    self.bg_movie.start()
                else:
                    self._log_to_console("[WARN] GIF file seems invalid.")
            except Exception as e:
                self._log_to_console(f"[WARN] GIF load error: {e}")
        else:
            self._log_to_console(f"[WARN] GIF not found: {gif_path}")

        # Red glow effect (visual)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(255, 0, 2, 180))
        shadow.setOffset(0)
        self.central_widget.setGraphicsEffect(shadow)
        self.central_widget.setStyleSheet("background-color: rgba(10, 10, 20, 50);")

        # Thread tracking
        self.worker = None

        # Restore splitter state
        splitter_state = self.settings.value("splitterState")
        if splitter_state:
            try:
                self.splitter.restoreState(splitter_state)
            except Exception:
                pass

        # Shortcuts
        self.output_console.setContextMenuPolicy(Qt.DefaultContextMenu)
        self.output_console.append = self._append_safe  # override append to keep format consistent

    def resizeEvent(self, ev):
        # keep gif spanning background
        try:
            self.bg_label.resize(self.size())
        except Exception:
            pass
        super().resizeEvent(ev)

    def closeEvent(self, ev):
        # persist geometry and splitter state
        try:
            self.settings.setValue("geometry", self.saveGeometry())
            self.settings.setValue("splitterState", self.splitter.saveState())
        except Exception:
            pass

        # try to stop running worker
        if self.worker and isinstance(self.worker, WorkerThread) and self.worker.isRunning():
            self._log_to_console("[INFO] Stopping worker (closing)...")
            self.worker.stop()
            self.worker.wait(2000)
        super().closeEvent(ev)

    # --------------------
    # Logging helpers
    # --------------------
    def _append_safe(self, text):
        # thread-safe append; if called from main thread it's fine
        self.output_console.moveCursor(QTextCursor.End)
        self.output_console.insertPlainText(text + "\n")
        self.output_console.moveCursor(QTextCursor.End)

    def _log_to_console(self, text):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._append_safe(f"[{ts}] {text}")

    # --------------------
    # Worker lifecycle
    # --------------------
    def _start_worker(self, module_name, func_hint, target):
        if self.worker and self.worker.isRunning():
            self._log_to_console("[WARN] A worker is already running. Stop it first.")
            return

        self.worker = WorkerThread(module_name, func_hint, target)
        self.worker.log_signal.connect(self._append_safe)
        self.worker.error_signal.connect(lambda e: self._append_safe(f"[ERROR] {e}"))
        self.worker.finished_signal.connect(self._on_worker_finished)
        self.stop_btn.setEnabled(True)
        self._log_to_console(f"[INFO] Launching {module_name} for {target}")
        self.worker.start()

    def _stop_worker(self):
        if self.worker and self.worker.isRunning():
            self._log_to_console("[INFO] Stop requested.")
            self.worker.stop()
            # UI will be reset in finished handler
        else:
            self._log_to_console("[INFO] No worker to stop.")

    def _on_worker_finished(self):
        self._log_to_console("[INFO] Worker finished.")
        self.stop_btn.setEnabled(False)
        # re-enable any UI controls if you disabled them

    # --------------------
    # Module-specific starts (wrap old run_* semantics)
    # --------------------
    def _start_xss(self):
        url = self.xss_url.text().strip()
        param = self.xss_param.text().strip()
        if not url:
            self._log_to_console("[!] XSS Target URL is empty.")
            return
        # prefer a module name that maps to your core file (fangxss)
        module_name = "fangxss"
        # pass a hint like 'scan_xss' to find a specific function
        func_hint = "scan_xss"
        target = f"{url}::{param}"
        self._start_worker(module_name, func_hint, target)

    def _start_sqli(self):
        url = self.sqli_url.text().strip()
        param = self.sqli_param.text().strip()
        if not url:
            self._log_to_console("[!] SQLi Target URL is empty.")
            return
        module_name = "fangsql"
        func_hint = "scan_sqli"
        target = f"{url}::{param}"
        self._start_worker(module_name, func_hint, target)

    def _start_lfi(self):
        url = self.lfi_url.text().strip()
        param = self.lfi_param.text().strip()
        if not url:
            self._log_to_console("[!] LFI Target URL is empty.")
            return
        module_name = "fanglfi"
        func_hint = "scan_lfi"
        target = f"{url}::{param}"
        self._start_worker(module_name, func_hint, target)

    def _start_rce(self):
        url = self.rce_url.text().strip()
        param = self.rce_param.text().strip()
        if not url:
            self._log_to_console("[!] RCE Target URL is empty.")
            return
        module_name = "fangrce"
        func_hint = "scan_rce"
        target = f"{url}::{param}"
        self._start_worker(module_name, func_hint, target)

    def _start_brute(self):
        url = self.brute_url.text().strip()
        path = self.brute_path.text().strip()
        if not url or not path:
            self._log_to_console("[!] Brute Force URL or path is empty.")
            return
        module_name = "fangbrute"
        func_hint = "password_spray"
        target = f"{url}::{path}"
        self._start_worker(module_name, func_hint, target)

    def _start_api(self):
        url = self.api_url.text().strip()
        if not url:
            self._log_to_console("[!] API Base URL is empty.")
            return
        module_name = "fangapi"
        func_hint = "discover_api_endpoints"
        target = url
        self._start_worker(module_name, func_hint, target)

    # --------------------
    # Save log
    # --------------------
    def _save_log(self):
        suggested = f"bloodfang_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path, _ = QFileDialog.getSaveFileName(self, "Save log as...", suggested, "Text Files (*.txt);;All Files (*)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.output_console.toPlainText())
                self._log_to_console(f"[INFO] Saved log to {path}")
            except Exception as e:
                self._log_to_console(f"[ERROR] Could not save log: {e}")

# --------------------
# Run the GUI
# --------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = BloodFangGUI()
    gui.show()
    # Ensure we call the PyQt5 exec_ naming
    try:
        sys.exit(app.exec_())
    except Exception:
        # Some environments may use exec; fallback:
        sys.exit(app.exec())
