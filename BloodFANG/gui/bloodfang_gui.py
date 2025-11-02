# gui/bloodfang_gui.py
# Drop-in replacement — preserves repo layout and assets.
# Features: PyQt5 GUI, adaptive layout, threaded worker, persistent geometry,
# module preview with explicit param usage & sample payloads from core/payloads.

import sys
import os
import traceback
import importlib
import inspect
import threading
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTextEdit, QGridLayout, QHBoxLayout, QSplitter, QScrollArea,
    QFileDialog, QGroupBox
)
from PyQt5.QtGui import QMovie, QColor, QFont, QTextCursor
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

# Paths
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent  # BloodFANG/
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

CORE_PACKAGE_NAMES = ["core", "BloodFANG.core"]
PAYLOADS_DIR = PROJECT_ROOT / "core" / "payloads"

def read_payload_file(fname: Path):
    try:
        if fname.exists():
            lines = [line.rstrip() for line in fname.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]
            return lines
    except Exception:
        pass
    return []

class WorkerThread(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, module_name, func_name_hint, target):
        super().__init__()
        self.module_name = module_name
        self.func_hint = func_name_hint
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
        for root in CORE_PACKAGE_NAMES:
            try:
                full = f"{root}.{modname}"
                mod = importlib.import_module(full)
                return mod
            except Exception:
                continue
        try:
            return importlib.import_module(modname)
        except Exception as e:
            raise ImportError(f"Could not import '{modname}' (tried roots): {e}")

    def run(self):
        try:
            self.emit_log(f"Worker starting: module='{self.module_name}' target='{self.target}'")
            try:
                module = self._import_module(self.module_name)
            except Exception as e:
                self.emit_log(f"Import error: {e}", level="ERROR")
                self.error_signal.emit(str(e))
                self.finished_signal.emit()
                return

            candidates = []
            if self.func_hint:
                candidates.append((self.func_hint, True))
                candidates.append((self.func_hint, False))

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

            if not invoked and self.func_hint:
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

        geom = self.settings.value("geometry")
        if geom:
            try:
                self.restoreGeometry(geom)
            except Exception:
                pass

        self.setMinimumSize(1000, 640)

        # Styles (preserve your theme)
        self.setStyleSheet("""
            QMainWindow { background-color: black; }
            QLabel { color: #ff4d4d; font-family: Consolas; }
            QPushButton { background-color: #1a1a1a; color: #ff1a1a; border: 1px solid #ff1a1a; padding: 6px; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #330000; }
            QLineEdit { background-color: #222; color: #ffcccc; border: 1px solid #ff1a1a; padding: 4px; font-family: Consolas; }
            QTextEdit { background-color: #111; color: #ff4d4d; font-family: Consolas; font-size: 13px; }
        """)

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_v = QVBoxLayout(self.central_widget)
        main_v.setContentsMargins(10, 10, 10, 10)

        # Header
        header_h = QHBoxLayout()
        hacker_name_label = QLabel("Talyx")
        hacker_name_label.setStyleSheet("font-size: 18px; color: #ff4d4d; font-weight: bold;")
        header_h.addWidget(hacker_name_label, alignment=Qt.AlignLeft)

        title_label = QLabel("BLOODFANG")
        title_label.setStyleSheet("font-size: 52px; font-weight: bold; color: #ff0000;")
        title_label.setAlignment(Qt.AlignCenter)
        header_h.addWidget(title_label, stretch=1)

        github_label = QLabel("Github.com/Talyx66")
        github_label.setStyleSheet("font-size: 14px; color: #ff4d4d; font-style: italic;")
        header_h.addWidget(github_label, alignment=Qt.AlignRight)

        main_v.addLayout(header_h)

        # Splitter: left controls / right preview
        self.splitter = QSplitter(Qt.Horizontal)
        main_v.addWidget(self.splitter, 10)

        # Left controls (scrollable)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(6, 6, 6, 6)

        grid = QGridLayout()
        grid.setSpacing(8)

        # We'll store references to fields for callbacks
        self._fields = {}

        def add_row(i, label_placeholder, param_placeholder, run_cb, module_name, func_hint=None, param_tip=None):
            url_field = QLineEdit()
            url_field.setPlaceholderText(label_placeholder)
            if param_placeholder:
                param_field = QLineEdit()
                param_field.setPlaceholderText(param_placeholder)
                if param_tip:
                    param_field.setToolTip(param_tip)
            else:
                param_field = QLineEdit()
                param_field.setPlaceholderText("—")
                param_field.setEnabled(False)

            run_btn = QPushButton("Run")
            run_btn.clicked.connect(run_cb)
            info_btn = QPushButton("i")
            info_btn.setFixedWidth(28)
            info_btn.setToolTip("Show module info (usage, params, samples)")
            info_btn.clicked.connect(lambda _, m=module_name, fh=func_hint: self.populate_preview(m, fh))

            grid.addWidget(url_field, i, 0)
            grid.addWidget(param_field, i, 1)
            grid.addWidget(run_btn, i, 2)
            grid.addWidget(info_btn, i, 3)

            # store
            self._fields[module_name] = (url_field, param_field)
            return url_field, param_field

        # Add rows with explicit param guidance (placeholders and tooltips)
        add_row(0,
                "XSS Target URL (e.g. https://target.com/search)",
                "Parameter name (e.g. q, search, input)",
                lambda: self._start_xss(),
                "fangxss",
                "scan_xss",
                "Typical injectable param names: q, search, s, input — pass as URL::param")

        add_row(1,
                "SQLi Target URL (e.g. https://target.com/product)",
                "Parameter name (e.g. id, product_id)",
                lambda: self._start_sqli(),
                "fangsql",
                "scan_sqli",
                "IDs and DB lookup params: id, product_id, sku — pass as URL::param")

        add_row(2,
                "LFI Target URL (e.g. https://target.com/view)",
                "Parameter name (e.g. file, page, path)",
                lambda: self._start_lfi(),
                "fanglfi",
                "scan_lfi",
                "File include params: file, page, path — pass as URL::param (e.g. /etc/passwd)")

        add_row(3,
                "RCE Target URL (e.g. https://target.com/exec)",
                "Parameter name (e.g. cmd, exec, command)",
                lambda: self._start_rce(),
                "fangrce",
                "scan_rce",
                "Command parameters: cmd, exec, command — pass as URL::param")

        add_row(4,
                "Brute Force Base URL (e.g. https://target.com)",
                "Login path (e.g. /admin/login)",
                lambda: self._start_brute(),
                "fangbrute",
                "password_spray",
                "Login path and form endpoint, e.g. /admin/login or /auth/login")

        add_row(5,
                "API Base URL (e.g. https://target.com)",
                None,
                lambda: self._start_api(),
                "fangapi",
                "discover_api_endpoints",
                "Base URL; scanner will probe common API prefixes like /api/, /v1/, /v2/, /graphql")

        left_layout.addLayout(grid)

        self.presets_box = QGroupBox("Presets / Quick Actions")
        self.presets_layout = QVBoxLayout()
        self.presets_box.setLayout(self.presets_layout)
        left_layout.addWidget(self.presets_box)
        left_layout.addStretch(1)

        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(left_widget)

        self.splitter.addWidget(left_scroll)

        # Right preview widget (rich text)
        self.preview_widget = QTextEdit()
        self.preview_widget.setReadOnly(True)
        self.preview_widget.setLineWrapMode(QTextEdit.WidgetWidth)
        self.preview_widget.setFont(QFont("Consolas", 11))
        self.splitter.addWidget(self.preview_widget)

        # Bottom: output console (large)
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        font = QFont("Consolas", 11)
        self.output_console.setFont(font)
        self.output_console.setLineWrapMode(QTextEdit.NoWrap)
        main_v.addWidget(self.output_console, 6)

        # Controls under console
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

        # GIF background
        gif_path = os.path.join(os.path.dirname(__file__), "assets", "Talyxlogo6.gif")
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.lower()
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

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(255, 0, 2, 180))
        shadow.setOffset(0)
        self.central_widget.setGraphicsEffect(shadow)
        self.central_widget.setStyleSheet("background-color: rgba(10, 10, 20, 50);")

        # Thread tracking
        self.worker = None

        splitter_state = self.settings.value("splitterState")
        if splitter_state:
            try:
                self.splitter.restoreState(splitter_state)
            except Exception:
                pass

        # Replace default append with thread-safe
        self.output_console.append = self._append_safe

    def resizeEvent(self, ev):
        try:
            self.bg_label.resize(self.size())
        except Exception:
            pass
        super().resizeEvent(ev)

    def closeEvent(self, ev):
        try:
            self.settings.setValue("geometry", self.saveGeometry())
            self.settings.setValue("splitterState", self.splitter.saveState())
        except Exception:
            pass

        if self.worker and isinstance(self.worker, WorkerThread) and self.worker.isRunning():
            self._log_to_console("[INFO] Stopping worker (closing)...")
            self.worker.stop()
            self.worker.wait(2000)
        super().closeEvent(ev)

    # ---- Logging helpers ----
    def _append_safe(self, text):
        self.output_console.moveCursor(QTextCursor.End)
        self.output_console.insertPlainText(text + "\n")
        self.output_console.moveCursor(QTextCursor.End)

    def _log_to_console(self, text):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._append_safe(f"[{ts}] {text}")

    # ---- Preview population with explicit params & payload samples ----
    def populate_preview(self, module_name: str, func_hint: str = None):
        pieces = []
        pieces.append(f"<h2 style='color:#ff4d4d'>{module_name}</h2>")

        # 1) Module docstring & introspection
        try:
            mod = None
            for root in CORE_PACKAGE_NAMES:
                try:
                    mod = importlib.import_module(f"{root}.{module_name}")
                    break
                except Exception:
                    continue
            if not mod:
                try:
                    mod = importlib.import_module(module_name)
                except Exception:
                    mod = None

            if mod:
                doc = (mod.__doc__ or "").strip()
                if doc:
                    pieces.append(f"<b>Description:</b><br><pre>{doc}</pre>")

                funcs = []
                for name, obj in inspect.getmembers(mod, inspect.isfunction):
                    if name.startswith("_"):
                        continue
                    try:
                        sig = str(inspect.signature(obj))
                    except Exception:
                        sig = "(signature unavailable)"
                    funcs.append((name, sig))
                if funcs:
                    func_html = "<b>Functions:</b><br><ul>"
                    for n, s in funcs:
                        func_html += f"<li><code>{n}{s}</code></li>"
                    func_html += "</ul>"
                    pieces.append(func_html)
                else:
                    pieces.append("<b>Functions:</b> None discovered.")
            else:
                pieces.append("<b>Module:</b> Not importable for detailed introspection.")
        except Exception as e:
            pieces.append(f"<b>Preview error:</b> {e}")

        # 2) Explicit parameter usage & examples
        param_guidance = {
            "fangxss": {
                "usage": "Pass as: URL::param — e.g. https://target.com/search::q",
                "desc": "Supply a target page URL and an injectable GET parameter name (q, search, input).",
                "example_target": "https://target.com/search::q"
            },
            "fangsql": {
                "usage": "Pass as: URL::param — e.g. https://target.com/product::id",
                "desc": "Provide a resource URL and a numeric or string param often used in DB queries (id, product_id).",
                "example_target": "https://target.com/product::id"
            },
            "fanglfi": {
                "usage": "Pass as: URL::param — e.g. https://target.com/view::file",
                "desc": "File include parameters (file, page, path). Try payloads like ../../../../etc/passwd.",
                "example_target": "https://target.com/view::file"
            },
            "fangrce": {
                "usage": "Pass as: URL::param — e.g. https://target.com/exec::cmd",
                "desc": "Command-execution parameters (cmd, exec, command). Provide small test commands first (id, whoami).",
                "example_target": "https://target.com/exec::cmd"
            },
            "fangbrute": {
                "usage": "Pass as: BASE_URL::path — e.g. https://target.com::/admin/login",
                "desc": "Base URL and the login path where credential form posts to.",
                "example_target": "https://target.com::/admin/login"
            },
            "fangapi": {
                "usage": "Pass as: BASE_URL — e.g. https://target.com",
                "desc": "Provide the API base URL or domain; scanner will probe /api/, /v1/, /graphql etc.",
                "example_target": "https://target.com"
            }
        }
        guidance = param_guidance.get(module_name)
        if guidance:
            pieces.append(f"<b>Usage:</b><br><pre>{guidance['usage']}</pre>")
            pieces.append(f"<b>What to pass:</b><br><pre>{guidance['desc']}</pre>")
            pieces.append(f"<b>Example:</b><br><pre>{guidance['example_target']}</pre>")

        # 3) Payload examples from core/payloads (first 8 lines)
        try:
            mapping = {
                "fangxss": ["xss_payloads.txt"],
                "fangsql": ["sql_payloads.txt"],
                "fanglfi": ["lfi_payloads.txt"],
                "fangrce": ["rce_payloads.txt"],
                "fangbrute": ["brute_usernames.txt", "brute_passwords.txt"],
                "fangapi": ["api_endpoints.txt"]
            }
            files = mapping.get(module_name, [])
            for fn in files:
                p = PAYLOADS_DIR / fn
                entries = read_payload_file(p)
                if entries:
                    sample = entries[:8]
                    pieces.append(f"<b>{fn} (sample payloads):</b><br><pre>{chr(10).join(sample)}</pre>")
                else:
                    # Skip empty files quietly
                    pass
        except Exception:
            pass

        # 4) Quick tips
        tips = """
        <b>Quick tips:</b>
        <ul>
          <li>Start with a single target and a single param to validate behavior before batch testing.</li>
          <li>For XSS/SQLi, try harmless probes (e.g., <code>&lt;script&gt;alert(1)&lt;/script&gt;</code>) in staging.</li>
          <li>Respect rules of engagement. Only run against authorized targets.</li>
          <li>Use the Stop button to cancel; modules that spawn blocking subprocesses may take a bit longer to stop.</li>
        </ul>
        """
        pieces.append(tips)

        html = "<hr>".join(pieces)
        self.preview_widget.setHtml(html)

    # ---- Worker lifecycle ----
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
        # show guidance in preview
        self.populate_preview(module_name, func_hint)
        self.worker.start()

    def _stop_worker(self):
        if self.worker and self.worker.isRunning():
            self._log_to_console("[INFO] Stop requested.")
            self.worker.stop()
        else:
            self._log_to_console("[INFO] No worker to stop.")

    def _on_worker_finished(self):
        self._log_to_console("[INFO] Worker finished.")
        self.stop_btn.setEnabled(False)

    # ---- Module-specific starts (reads inputs and composes standardized target strings) ----
    def _start_xss(self):
        url_field, param_field = self._fields.get("fangxss", (None, None))
        url = url_field.text().strip() if url_field else ""
        param = param_field.text().strip() if param_field else ""
        if not url:
            self._log_to_console("[!] XSS Target URL is empty.")
            return
        module_name = "fangxss"
        func_hint = "scan_xss"
        target = f"{url}::{param}"
        self._start_worker(module_name, func_hint, target)

    def _start_sqli(self):
        url_field, param_field = self._fields.get("fangsql", (None, None))
        url = url_field.text().strip() if url_field else ""
        param = param_field.text().strip() if param_field else ""
        if not url:
            self._log_to_console("[!] SQLi Target URL is empty.")
            return
        module_name = "fangsql"
        func_hint = "scan_sqli"
        target = f"{url}::{param}"
        self._start_worker(module_name, func_hint, target)

    def _start_lfi(self):
        url_field, param_field = self._fields.get("fanglfi", (None, None))
        url = url_field.text().strip() if url_field else ""
        param = param_field.text().strip() if param_field else ""
        if not url:
            self._log_to_console("[!] LFI Target URL is empty.")
            return
        module_name = "fanglfi"
        func_hint = "scan_lfi"
        target = f"{url}::{param}"
        self._start_worker(module_name, func_hint, target)

    def _start_rce(self):
        url_field, param_field = self._fields.get("fangrce", (None, None))
        url = url_field.text().strip() if url_field else ""
        param = param_field.text().strip() if param_field else ""
        if not url:
            self._log_to_console("[!] RCE Target URL is empty.")
            return
        module_name = "fangrce"
        func_hint = "scan_rce"
        target = f"{url}::{param}"
        self._start_worker(module_name, func_hint, target)

    def _start_brute(self):
        url_field, path_field = self._fields.get("fangbrute", (None, None))
        url = url_field.text().strip() if url_field else ""
        path = path_field.text().strip() if path_field else ""
        if not url or not path:
            self._log_to_console("[!] Brute Force Base URL or path is empty.")
            return
        module_name = "fangbrute"
        func_hint = "password_spray"
        target = f"{url}::{path}"
        self._start_worker(module_name, func_hint, target)

    def _start_api(self):
        url_field, _ = self._fields.get("fangapi", (None, None))
        url = url_field.text().strip() if url_field else ""
        if not url:
            self._log_to_console("[!] API Base URL is empty.")
            return
        module_name = "fangapi"
        func_hint = "discover_api_endpoints"
        target = url
        self._start_worker(module_name, func_hint, target)

    # ---- Save log ----
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

# ---- Run the GUI ----
if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = BloodFangGUI()
    gui.show()
    try:
        sys.exit(app.exec_())
    except Exception:
        sys.exit(app.exec())
