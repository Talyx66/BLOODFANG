# BloodFANG/gui/bloodfang_gui.py
# Final drop-in replacement (PyQt5)
# - auto path fix for BLOODFANG imports (fixes "no module named BloodFANG")
# - adaptive layout, threaded workers, persistent geometry
# - module preview with explicit params and real payload samples
# - special-case fangbrute handling (uses brute_usernames/passwords if present)
# - integrates adapters.safe_* if present for deterministic safe scans
# - uses PyQt5 app.exec_() at the bottom

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
    QFileDialog, QGroupBox, QGraphicsDropShadowEffect, QMenu, QAction, QInputDialog
)
from PyQt5.QtGui import QMovie, QColor, QFont, QTextCursor
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSettings, QTimer, QDateTime, QTimeZone

# -------------------------
# Path configuration fix
# -------------------------
HERE = Path(__file__).resolve().parent            # .../BLOODFANG/BloodFANG/gui
# PROJECT_ROOT should point to the repo root that contains the BloodFANG package.
# Given layout: REPO_ROOT/BLOODFANG/BloodFANG/gui -> we want REPO_ROOT/BLOODFANG
# That is two levels up from this file (parents[1] -> BloodFANG inner package, parents[2] -> repo root?).
# To be robust: if this file is at BLOODFANG/BloodFANG/gui, then HERE.parents[1] == BLOODFANG (inner).
# We want the directory that contains the inner 'BloodFANG' package. That's HERE.parents[1].parent
# Simpler: climb until we find a directory named "BloodFANG" that contains a "core" folder.
def _find_repo_root():
    cur = HERE
    for _ in range(5):
        candidate = cur.parent
        # check for /<candidate>/BloodFANG/core
        test = candidate / "BloodFANG" / "core"
        if test.exists():
            return candidate
        cur = cur.parent
    # fallback: two levels up
    return HERE.parents[1]

PROJECT_ROOT = _find_repo_root()
CORE_PACKAGE = "BloodFANG.core"
PAYLOADS_DIR = PROJECT_ROOT / "BloodFANG" / "core" / "payloads"

# ensure project root on path so Python can import BloodFANG
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# try loading adapters for safe scanning (optional)
try:
    from BloodFANG.core import adapters  # type: ignore
except Exception:
    adapters = None

# -------------------------
# Utility: read payloads
# -------------------------
def read_payload_file(fname: Path):
    try:
        if fname.exists():
            lines = [line.rstrip() for line in fname.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()]
            return lines
    except Exception:
        pass
    return []

# -------------------------
# WorkerThread
# -------------------------
class WorkerThread(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    error_signal = pyqtSignal(str)

    def __init__(self, module_name: str, func_hint: str, target: str):
        super().__init__()
        self.module_name = module_name
        self.func_hint = func_hint
        self.target = target
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def emit_log(self, text: str, level: str = "INFO"):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_signal.emit(f"[{ts}] [{level}] {text}")

    def _module_emit(self, message: str):
        # expose module logs to GUI
        self.emit_log(message)

    def _import_module(self, modname: str):
        full = f"{CORE_PACKAGE}.{modname}"
        try:
            return importlib.import_module(full)
        except Exception as e:
            try:
                return importlib.import_module(modname)
            except Exception:
                raise ImportError(f"Could not import {full} or {modname}: {e}")

    def run(self):
        try:
            self.emit_log(f"Worker starting: module='{self.module_name}' target='{self.target}'")

            # Prefer safe adapter wrappers if available
            safe_fn_name = f"safe_{self.module_name.replace('fang', '')}"
            if adapters and hasattr(adapters, safe_fn_name):
                fn = getattr(adapters, safe_fn_name)
                self.emit_log(f"[INFO] Using adapters.{safe_fn_name} for controlled scanning.")
                try:
                    # handle fangbrute signature differently
                    if self.module_name == "fangbrute":
                        base, path = (self.target.split("::", 1) + [""])[:2]
                        fn(base, path, self._module_emit, self._stop_event)
                    elif self.module_name == "fangapi":
                        fn(self.target, self._module_emit, self._stop_event)
                    else:
                        url, param = (self.target.split("::", 1) + [""])[:2]
                        fn(url, param, self._module_emit, self._stop_event)
                    self.emit_log(f"[INFO] Safe adapter finished for {self.module_name}")
                    self.finished_signal.emit()
                    return
                except Exception as e:
                    self.emit_log(f"[ERROR] Adapter {safe_fn_name} raised: {e}", level="ERROR")
                    tb = traceback.format_exc()
                    self.emit_log(tb, level="DEBUG")
                    # fallthrough to original module attempt

            # Import target module from BloodFANG.core or fallback
            try:
                module = self._import_module(self.module_name)
            except Exception as e:
                self.emit_log(f"Import error: {e}", level="ERROR")
                self.error_signal.emit(str(e))
                self.finished_signal.emit()
                return

            invoked = False

            # Special-case brute if module implements password_spray
            if self.module_name == "fangbrute":
                try:
                    base, path = (self.target.split("::", 1) + [""])[:2]
                except Exception:
                    base, path = self.target, ""
                usernames = read_payload_file(PAYLOADS_DIR / "brute_usernames.txt") or ["admin", "user", "test"]
                passwords = read_payload_file(PAYLOADS_DIR / "brute_passwords.txt") or ["123456", "password", "admin123"]
                func = getattr(module, "password_spray", None)
                if callable(func):
                    try:
                        self.emit_log(f"Calling {self.module_name}.password_spray(base, usernames, passwords, path, logger)")
                        func(base, usernames, passwords, path, self._module_emit)
                        invoked = True
                    except Exception as e:
                        self.emit_log(f"Error in password_spray: {e}", level="ERROR")
                        tb = traceback.format_exc()
                        self.emit_log(tb, level="DEBUG")

            # Prepare candidate names & parse target
            candidates = []
            if self.func_hint:
                candidates.append((self.func_hint, True))
                candidates.append((self.func_hint, False))
            candidates += [
                ("scan", True),
                ("scan", False),
                ("run", True),
                ("run", False),
                ("main", False),
            ]

            url = self.target
            param = ""
            if "::" in self.target:
                parts = self.target.split("::", 1)
                url = parts[0]
                param = parts[1]

            for name, with_stop in candidates:
                func = getattr(module, name, None)
                if not callable(func):
                    continue
                try:
                    # Try most common signatures safely
                    if param:
                        # try url, param, logger
                        try:
                            self.emit_log(f"Trying {self.module_name}.{name}(url, param, logger)")
                            func(url, param, self._module_emit)
                            invoked = True
                            break
                        except TypeError:
                            pass
                    # try (target, emit, stop_event) or (target, emit)
                    try:
                        if with_stop:
                            self.emit_log(f"Trying {self.module_name}.{name}(target, emit, stop_event)")
                            func(self.target, self._module_emit, self._stop_event)
                        else:
                            self.emit_log(f"Trying {self.module_name}.{name}(target, emit)")
                            func(self.target, self._module_emit)
                        invoked = True
                        break
                    except TypeError:
                        pass
                    # last fallback: (target)
                    try:
                        self.emit_log(f"Trying {self.module_name}.{name}(target)")
                        func(self.target)
                        invoked = True
                        break
                    except TypeError:
                        pass
                except Exception as e:
                    self.emit_log(f"Exception during {self.module_name}.{name}: {e}", level="ERROR")
                    tb = traceback.format_exc()
                    self.emit_log(tb, level="DEBUG")
                    continue

            # try func_hint direct if not yet invoked
            if not invoked and self.func_hint:
                alt = getattr(module, self.func_hint, None)
                if callable(alt):
                    try:
                        if param:
                            self.emit_log(f"Trying {self.module_name}.{self.func_hint}(url, param, logger)")
                            alt(url, param, self._module_emit)
                        else:
                            self.emit_log(f"Trying {self.module_name}.{self.func_hint}(target, logger)")
                            alt(self.target, self._module_emit)
                        invoked = True
                    except Exception as e:
                        self.emit_log(f"Alt call {self.func_hint} failed: {e}", level="ERROR")
                        tb = traceback.format_exc()
                        self.emit_log(tb, level="DEBUG")

            if not invoked:
                self.emit_log(f"No compatible entry point found for module '{self.module_name}'.", level="ERROR")
                self.error_signal.emit(f"No entry point found for {self.module_name}")
            else:
                self.emit_log(f"Module '{self.module_name}' finished.")
        except Exception as e:
            self.emit_log(f"Unhandled worker exception: {e}", level="ERROR")
            self.error_signal.emit(str(e))
            tb = traceback.format_exc()
            self.emit_log(tb, level="DEBUG")
        finally:
            self.finished_signal.emit()

# -------------------------
# GUI
# -------------------------
class BloodFangGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BLOODFANG - Offensive Security")
        self.settings = QSettings("Talyx", "BLOODFANG")

        # restore geometry & splitter state
        geom = self.settings.value("geometry")
        if geom:
            try:
                self.restoreGeometry(geom)
            except Exception:
                pass

        self.setMinimumSize(1000, 640)
        # styling
        self.setStyleSheet("""
            QMainWindow { background-color: black; }
            QLabel { color: #ff4d4d; font-family: Consolas; }
            QPushButton { background-color: #1a1a1a; color: #ff1a1a; border: 1px solid #ff1a1a; padding: 6px; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #330000; }
            QLineEdit { background-color: #222; color: #ffcccc; border: 1px solid #ff1a1a; padding: 4px; font-family: Consolas; }
            QTextEdit { background-color: #111; color: #ff4d4d; font-family: Consolas; font-size: 13px; }
        """)

        # main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_v = QVBoxLayout(self.central_widget)
        main_v.setContentsMargins(10, 10, 10, 10)

        # header
        header_h = QHBoxLayout()
        hacker_name_label = QLabel("Talyx")
        hacker_name_label.setStyleSheet("font-size:18px;color:#ff4d4d;font-weight:bold;")
        header_h.addWidget(hacker_name_label, alignment=Qt.AlignLeft)

        title_label = QLabel("BLOODFANG")
        title_label.setStyleSheet("font-size:52px;font-weight:bold;color:#ff0000;")
        title_label.setAlignment(Qt.AlignCenter)
        header_h.addWidget(title_label, stretch=1)

        github_label = QLabel("Github.com/Talyx66")
        github_label.setStyleSheet("font-size:14px;color:#ff4d4d;font-style:italic;")
        header_h.addWidget(github_label, alignment=Qt.AlignRight)

        main_v.addLayout(header_h)

        # splitter
        self.splitter = QSplitter(Qt.Horizontal)
        main_v.addWidget(self.splitter, 10)

        # left controls (scrollable)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(6, 6, 6, 6)
        grid = QGridLayout()
        grid.setSpacing(8)

        self._fields = {}

        def add_row(i, label_placeholder, param_placeholder, run_cb, module_name, func_hint=None, param_tip=None):
            url_field = QLineEdit(); url_field.setPlaceholderText(label_placeholder)
            if param_placeholder:
                param_field = QLineEdit(); param_field.setPlaceholderText(param_placeholder)
                if param_tip:
                    param_field.setToolTip(param_tip)
            else:
                param_field = QLineEdit(); param_field.setPlaceholderText("—"); param_field.setEnabled(False)

            run_btn = QPushButton("Run"); run_btn.clicked.connect(run_cb)
            info_btn = QPushButton("i"); info_btn.setFixedWidth(28)
            info_btn.setToolTip("Show module info (usage, params, samples)")
            info_btn.clicked.connect(lambda _, m=module_name, fh=func_hint: self.populate_preview(m, fh))

            grid.addWidget(url_field, i, 0)
            grid.addWidget(param_field, i, 1)
            grid.addWidget(run_btn, i, 2)
            grid.addWidget(info_btn, i, 3)

            self._fields[module_name] = (url_field, param_field)
            return url_field, param_field

        # rows
        add_row(0, "XSS Target URL (e.g. https://target.com/search)", "Parameter name (e.g. q, search, input)", lambda: self._start_xss(), "fangxss", "scan_xss",
                "Typical injectable param names: q, search, s, input — pass as URL::param")
        add_row(1, "SQLi Target URL (e.g. https://target.com/product)", "Parameter name (e.g. id, product_id)", lambda: self._start_sqli(), "fangsql", "scan_sqli",
                "IDs and DB lookup params: id, product_id, sku — pass as URL::param")
        add_row(2, "LFI Target URL (e.g. https://target.com/view)", "Parameter name (e.g. file, page, path)", lambda: self._start_lfi(), "fanglfi", "scan_lfi",
                "File include params: file, page, path — pass as URL::param (e.g. ../../../../etc/passwd)")
        add_row(3, "RCE Target URL (e.g. https://target.com/exec)", "Parameter name (e.g. cmd, exec, command)", lambda: self._start_rce(), "fangrce", "scan_rce",
                "Command parameters: cmd, exec, command — pass as URL::param (try 'id' then 'whoami')")
        add_row(4, "Brute Force Base URL (e.g. https://target.com)", "Login path (e.g. /admin/login)", lambda: self._start_brute(), "fangbrute", "password_spray",
                "Login path and form endpoint, e.g. /admin/login or /auth/login — pass as BASE::/path")
        add_row(5, "API Base URL (e.g. https://target.com)", None, lambda: self._start_api(), "fangapi", "discover_api_endpoints",
                "Base URL; scanner will probe /api/, /v1/, /graphql, etc.")

        left_layout.addLayout(grid)

        self.presets_box = QGroupBox("Presets / Quick Actions")
        self.presets_layout = QVBoxLayout()
        self.presets_box.setLayout(self.presets_layout)
        left_layout.addWidget(self.presets_box)
        left_layout.addStretch(1)

        left_scroll = QScrollArea(); left_scroll.setWidgetResizable(True); left_scroll.setWidget(left_widget)
        self.splitter.addWidget(left_scroll)


        # right preview
        self.preview_widget = QTextEdit(); self.preview_widget.setReadOnly(True)
        self.preview_widget.setLineWrapMode(QTextEdit.WidgetWidth); self.preview_widget.setFont(QFont("Consolas", 11))
        self.splitter.addWidget(self.preview_widget)

        # bottom console
        self.output_console = QTextEdit(); self.output_console.setReadOnly(True); self.output_console.setFont(QFont("Consolas", 11)); self.output_console.setLineWrapMode(QTextEdit.NoWrap)
        main_v.addWidget(self.output_console, 6)

        # controls
        controls_h = QHBoxLayout()
        self.stop_btn = QPushButton("Stop"); self.stop_btn.setEnabled(False); self.stop_btn.clicked.connect(self._stop_worker)
        self.clear_btn = QPushButton("Clear Output"); self.clear_btn.clicked.connect(self.output_console.clear)
        self.save_btn = QPushButton("Save Log..."); self.save_btn.clicked.connect(self._save_log)
        controls_h.addWidget(self.stop_btn); controls_h.addWidget(self.clear_btn); controls_h.addWidget(self.save_btn); controls_h.addStretch(1)

        # digital clock label (red)
        self.clock_label = QLabel()
        self.clock_label.setStyleSheet("color: #ff2b2b; font-family: Consolas; font-size: 13px;")
        # keep it compact
        self.clock_label.setMinimumWidth(120)
        controls_h.addWidget(self.clock_label, alignment=Qt.AlignRight)

        # internal state for timezone + timer end
        self._bf_timezone = QTimeZone.systemTimeZone()
        self._bf_timer_end = None

        def _update_clock():
            now = QDateTime.currentDateTime().toTimeZone(self._bf_timezone)
            clock_str = now.toString("HH:mm:ss")
            # show date optionally (comment/uncomment)
            # clock_str = now.toString("yyyy-MM-dd HH:mm:ss")
            # if timer set, compute remaining
            if self._bf_timer_end:
                remaining_ms = QDateTime.currentDateTime().msecsTo(self._bf_timer_end)
                if remaining_ms > 0:
                    total_sec = int(remaining_ms / 1000)
                    mins, secs = divmod(total_sec, 60)
                    hrs, mins = divmod(mins, 60)
                    clock_str += f"  |  ⏱ {hrs:02d}:{mins:02d}:{secs:02d}"
                else:
                    clock_str += "  |  ⏱ DONE"
                    # clear after showing DONE once
                    self._bf_timer_end = None
            self.clock_label.setText(clock_str)
        
        # start timer updating every second
        self._bf_clock_timer = QTimer(self)
        self._bf_clock_timer.timeout.connect(_update_clock)
        self._bf_clock_timer.start(1000)
        _update_clock()
        
        # settings button with small menu for timezone & set timer
        self.clock_btn = QPushButton("⚙")
        self.clock_btn.setFixedWidth(34)
        self.clock_btn.setToolTip("Clock settings: timezone / set timer")
        self.clock_btn.setStyleSheet("background-color: #1a1a1a; color: #ff4d4d; border:1px solid #ff1a1a;")
        
        # menu actions
        menu = QMenu(self)
        
        def _set_timezone():
            zones = ["Local", "UTC", "America/New_York", "America/Los_Angeles", "Europe/London", "Asia/Tokyo"]
            tz_choice, ok = QInputDialog.getItem(self, "Select Timezone", "Timezone:", zones, 0, False)
            if ok:
                if tz_choice == "Local":
                    self._bf_timezone = QTimeZone.systemTimeZone()
                elif tz_choice == "UTC":
                    self._bf_timezone = QTimeZone(b"UTC")
                else:
                    # QTimeZone expects bytes
                    self._bf_timezone = QTimeZone(tz_choice.encode())
                _update_clock()
        
        def _set_timer():
            # ask minutes first (int)
            mins, ok = QInputDialog.getInt(self, "Set Countdown Timer", "Minutes:", 5, 0, 9999, 1)
            if ok:
                # optional seconds
                secs, ok2 = QInputDialog.getInt(self, "Set Countdown Timer (seconds)", "Additional seconds:", 0, 0, 59, 1)
                if ok2:
                    total = mins * 60 + secs
                    self._bf_timer_end = QDateTime.currentDateTime().addSecs(total)
                    _update_clock()
        
        def _clear_timer():
            self._bf_timer_end = None
            _update_clock()
        
        menu.addAction(QAction("Change Timezone", self, triggered=_set_timezone))
        menu.addAction(QAction("Set Timer (minutes)", self, triggered=_set_timer))
        menu.addAction(QAction("Clear Timer", self, triggered=_clear_timer))
        
        self.clock_btn.setMenu(menu)
        controls_h.addWidget(self.clock_btn, alignment=Qt.AlignRight)
        # ---------- end clock ----------
        
        main_v.addLayout(controls_h)

        # background GIF
        gif_path = PROJECT_ROOT / "BloodFANG" / "gui" / "assets" / "Talyxlogo6.gif"
        if not gif_path.exists():
            gif_path = HERE / "assets" / "Talyxlogo6.gif"
        self.bg_label = QLabel(self); self.bg_label.setScaledContents(True); self.bg_label.lower()
        if gif_path.exists():
            try:
                self.bg_movie = QMovie(str(gif_path))
                if self.bg_movie.isValid():
                    self.bg_label.setMovie(self.bg_movie); self.bg_movie.start()
                else:
                    self._log_to_console("[WARN] GIF file seems invalid.")
            except Exception as e:
                self._log_to_console(f"[WARN] GIF load error: {e}")
        else:
            self._log_to_console(f"[WARN] GIF not found: {gif_path}")

        shadow = QGraphicsDropShadowEffect(self); shadow.setBlurRadius(40); shadow.setColor(QColor(255, 0, 2, 180)); shadow.setOffset(0)
        self.central_widget.setGraphicsEffect(shadow); self.central_widget.setStyleSheet("background-color: #0a0a14;")

        self.worker = None

        splitter_state = self.settings.value("splitterState")
        if splitter_state:
            try:
                self.splitter.restoreState(splitter_state)
            except Exception:
                pass

        # thread-safe append
        self.output_console.append = self._append_safe

    # lifecycle
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

    # logging helpers
    def _append_safe(self, text: str):
        self.output_console.moveCursor(QTextCursor.End)
        self.output_console.insertPlainText(text + "\n")
        self.output_console.moveCursor(QTextCursor.End)

    def _log_to_console(self, text: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._append_safe(f"[{ts}] {text}")

    # preview
    def populate_preview(self, module_name: str, func_hint: str = None):
        parts = []
        parts.append(f"<h2 style='color:#ff4d4d'>{module_name}</h2>")
        # module introspection
        try:
            mod = None
            try:
                mod = importlib.import_module(f"{CORE_PACKAGE}.{module_name}")
            except Exception:
                try:
                    mod = importlib.import_module(module_name)
                except Exception:
                    mod = None

            if mod:
                doc = (mod.__doc__ or "").strip()
                if doc:
                    parts.append(f"<b>Description:</b><br><pre>{doc}</pre>")

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
                    parts.append(func_html)
                else:
                    parts.append("<b>Functions:</b> None discovered.")
            else:
                parts.append("<b>Module:</b> Not importable for detailed introspection.")
        except Exception as e:
            parts.append(f"<b>Preview error:</b> {e}")

        # guidance + payloads
        guidance = {
            "fangxss": {"usage": "URL::param", "desc": "Page URL + GET parameter (q, search, input)", "example": "https://target.com/search::q", "payload_files": ["xss_payloads.txt"]},
            "fangsql": {"usage": "URL::param", "desc": "Resource + lookup param (id, product_id)", "example": "https://target.com/product::id", "payload_files": ["sql_payloads.txt"]},
            "fanglfi": {"usage": "URL::param", "desc": "File include params (file, page, path)", "example": "https://target.com/view::file", "payload_files": ["lfi_payloads.txt"]},
            "fangrce": {"usage": "URL::param", "desc": "Command param (cmd, exec)", "example": "https://target.com/exec::cmd", "payload_files": ["rce_payloads.txt"]},
            "fangbrute": {"usage": "BASE::path", "desc": "Base URL + login path; uses brute_usernames/passwords", "example": "https://target.com::/admin/login", "payload_files": ["brute_usernames.txt", "brute_passwords.txt"]},
            "fangapi": {"usage": "BASE_URL", "desc": "API base; probes /api/, /v1/, /graphql", "example": "https://target.com", "payload_files": ["api_endpoints.txt"]}
        }

        g = guidance.get(module_name)
        if g:
            parts.append(f"<b>Usage:</b><br><pre>{g['usage']}</pre>")
            parts.append(f"<b>What to pass:</b><br><pre>{g['desc']}</pre>")
            parts.append(f"<b>Example:</b><br><pre>{g['example']}</pre>")
            for fn in g.get("payload_files", []):
                p = PAYLOADS_DIR / fn
                entries = read_payload_file(p)
                if entries:
                    sample = entries[:10]
                    parts.append(f"<b>{fn} (sample):</b><br><pre>{chr(10).join(sample)}</pre>")
                else:
                    parts.append(f"<b>{fn}:</b> (no file or empty)")

        tips = """
        <b>Quick tips</b>
        <ul>
          <li>Start with one target & one parameter.</li>
          <li>Use safe payloads first (alert(1)).</li>
          <li>Stop requests are cooperative — modules that spawn subprocesses may need extra time to cancel.</li>
        </ul>
        """
        parts.append(tips)

        html = "<hr>".join(parts)
        self.preview_widget.setHtml(html)

    # worker lifecycle
    def _start_worker(self, module_name: str, func_hint: str, target: str):
        if self.worker and self.worker.isRunning():
            self._log_to_console("[WARN] A worker is already running. Stop it first.")
            return
        self.worker = WorkerThread(module_name, func_hint, target)
        self.worker.log_signal.connect(self._append_safe)
        self.worker.error_signal.connect(lambda e: self._append_safe(f"[ERROR] {e}"))
        self.worker.finished_signal.connect(self._on_worker_finished)
        self.stop_btn.setEnabled(True)
        self._log_to_console(f"[INFO] Launching {module_name} for {target}")
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

    # starters
    def _start_xss(self):
        url_field, param_field = self._fields.get("fangxss", (None, None))
        url = url_field.text().strip() if url_field else ""
        param = param_field.text().strip() if param_field else ""
        if not url:
            self._log_to_console("[!] XSS Target URL is empty.")
            return
        self._start_worker("fangxss", "scan_xss", f"{url}::{param}")

    def _start_sqli(self):
        url_field, param_field = self._fields.get("fangsql", (None, None))
        url = url_field.text().strip() if url_field else ""
        param = param_field.text().strip() if param_field else ""
        if not url:
            self._log_to_console("[!] SQLi Target URL is empty.")
            return
        self._start_worker("fangsql", "scan_sqli", f"{url}::{param}")

    def _start_lfi(self):
        url_field, param_field = self._fields.get("fanglfi", (None, None))
        url = url_field.text().strip() if url_field else ""
        param = param_field.text().strip() if param_field else ""
        if not url:
            self._log_to_console("[!] LFI Target URL is empty.")
            return
        self._start_worker("fanglfi", "scan_lfi", f"{url}::{param}")

    def _start_rce(self):
        url_field, param_field = self._fields.get("fangrce", (None, None))
        url = url_field.text().strip() if url_field else ""
        param = param_field.text().strip() if param_field else ""
        if not url:
            self._log_to_console("[!] RCE Target URL is empty.")
            return
        self._start_worker("fangrce", "scan_rce", f"{url}::{param}")

    def _start_brute(self):
        url_field, path_field = self._fields.get("fangbrute", (None, None))
        url = url_field.text().strip() if url_field else ""
        path = path_field.text().strip() if path_field else ""
        if not url or not path:
            self._log_to_console("[!] Brute Force Base URL or path is empty.")
            return
        self._start_worker("fangbrute", "password_spray", f"{url}::{path}")

    def _start_api(self):
        url_field, _ = self._fields.get("fangapi", (None, None))
        url = url_field.text().strip() if url_field else ""
        if not url:
            self._log_to_console("[!] API Base URL is empty.")
            return
        self._start_worker("fangapi", "discover_api_endpoints", url)

    # save log
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

# -------------------------
# Run (PyQt5 safe block)
# -------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = BloodFangGUI()
    gui.show()
    try:
        sys.exit(app.exec_())
    except Exception:
        # fallback if exec_ not available for some reason
        sys.exit(app.exec())
