"""
BloodFANG Adapters integration
"""

import importlib
import traceback
import time

# --- helper import ---
def _import_module(name):
    try:
        return importlib.import_module(f"BloodFANG.core.{name}")
    except Exception:
        try:
            return importlib.import_module(name)
        except Exception as e:
            raise ImportError(f"Could not import {name}: {e}")

def _safe_call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        raise RuntimeError(f"{func.__name__}() failed: {e}")

# -----------------------------------------------------------------
# XSS
# -----------------------------------------------------------------
def safe_xss(url, param, emit, stop_event=None):
    emit(f"[SAFE] Starting XSS scan for {url} :: {param}")
    try:
        m = _import_module("fangxss")
        func = getattr(m, "scan_xss", None) or getattr(m, "scan", None)
        if not callable(func):
            emit("[SAFE] fangxss has no callable scan_xss or scan()")
            return
        func(url, param, emit)
        emit("[SAFE] XSS scan completed.")
    except Exception as e:
        emit(f"[SAFE] XSS error: {e}\n{traceback.format_exc()}")

# -----------------------------------------------------------------
# SQLi
# -----------------------------------------------------------------
def safe_sql(url, param, emit, stop_event=None):
    emit(f"[SAFE] Starting SQLi scan for {url} :: {param}")
    try:
        m = _import_module("fangsql")
        func = getattr(m, "scan_sqli", None) or getattr(m, "scan", None)
        if not callable(func):
            emit("[SAFE] fangsql has no callable scan_sqli or scan()")
            return
        func(url, param, emit)
        emit("[SAFE] SQLi scan completed.")
    except Exception as e:
        emit(f"[SAFE] SQLi error: {e}\n{traceback.format_exc()}")

# -----------------------------------------------------------------
# LFI
# -----------------------------------------------------------------
def safe_lfi(url, param, emit, stop_event=None):
    emit(f"[SAFE] Starting LFI scan for {url} :: {param}")
    try:
        m = _import_module("fanglfi")
        func = getattr(m, "scan_lfi", None) or getattr(m, "scan", None)
        if not callable(func):
            emit("[SAFE] fanglfi has no callable scan_lfi or scan()")
            return
        func(url, param, emit)
        emit("[SAFE] LFI scan completed.")
    except Exception as e:
        emit(f"[SAFE] LFI error: {e}\n{traceback.format_exc()}")

# -----------------------------------------------------------------
# RCE
# -----------------------------------------------------------------
def safe_rce(url, param, emit, stop_event=None):
    emit(f"[SAFE] Starting RCE scan for {url} :: {param}")
    try:
        m = _import_module("fangrce")
        func = getattr(m, "scan_rce", None) or getattr(m, "scan", None)
        if not callable(func):
            emit("[SAFE] fangrce has no callable scan_rce or scan()")
            return
        func(url, param, emit)
        emit("[SAFE] RCE scan completed.")
    except Exception as e:
        emit(f"[SAFE] RCE error: {e}\n{traceback.format_exc()}")

# -----------------------------------------------------------------
# Brute Force
# -----------------------------------------------------------------
def safe_brute(base, path, emit, stop_event=None):
    emit(f"[SAFE] Starting Brute Force on {base}{path}")
    try:
        m = _import_module("fangbrute")
        func = getattr(m, "password_spray", None) or getattr(m, "run", None)
        if not callable(func):
            emit("[SAFE] fangbrute has no callable password_spray() or run()")
            return
        usernames = ["admin", "user", "test"]
        passwords = ["123456", "password", "admin"]
        func(base, usernames, passwords, path, emit)
        emit("[SAFE] Brute Force completed.")
    except Exception as e:
        emit(f"[SAFE] Brute Force error: {e}\n{traceback.format_exc()}")

# -----------------------------------------------------------------
# API Discovery
# -----------------------------------------------------------------
def safe_api(url, emit, stop_event=None):
    emit(f"[SAFE] Starting API discovery on {url}")
    try:
        m = _import_module("fangapi")
        func = getattr(m, "discover_api_endpoints", None) or getattr(m, "scan", None)
        if not callable(func):
            emit("[SAFE] fangapi has no callable discover_api_endpoints() or scan()")
            return
        func(url, emit)
        emit("[SAFE] API discovery completed.")
    except Exception as e:
        emit(f"[SAFE] API error: {e}\n{traceback.format_exc()}")

# -----------------------------------------------------------------
# Sleep/respect stop events
# -----------------------------------------------------------------
def _check_stop(stop_event):
    if stop_event and getattr(stop_event, "is_set", None):
        return stop_event.is_set()
    return False

# -----------------------------------------------------------------
# generic heartbeat helper
# -----------------------------------------------------------------
def safe_sleep(emit, stop_event, duration=0.5):
    """Heartbeat-friendly sleep that respects stop requests."""
    for _ in range(int(duration * 10)):
        if _check_stop(stop_event):
            emit("[SAFE] Operation aborted by user.")
            return True
        time.sleep(0.1)
    return False
