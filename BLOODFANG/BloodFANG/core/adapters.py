
import importlib
import traceback
import time

CORE_ROOT = "BloodFANG.core"

def _import_module(name):
    tried = []
    try:
        full = f"{CORE_ROOT}.{name}"
        tried.append(full)
        return importlib.import_module(full)
    except Exception:
        tried.append(name)
        try:
            return importlib.import_module(name)
        except Exception as e:
            raise ImportError(f"Could not import {name} (tried: {tried}): {e}") from e

def safe_xss(url, param, emit, stop_event):
    try:
        m = _import_module("fangxss")
    except Exception as e:
        emit(f"[SAFE] XSS error: Could not import fangxss: {e}")
        emit(traceback.format_exc())
        raise

    fn = getattr(m, "scan_xss", None) or getattr(m, "scan", None)
    if not callable(fn):
        emit("[SAFE] fangxss has no callable scan entrypoint.")
        raise ImportError("No entrypoint in fangxss")

    emit(f"[SAFE] Starting XSS scan for {url} :: {param}")
    try:
        try:
            fn(url, param, emit, stop_event)
        except TypeError:
            fn(f"{url}::{param}", emit, stop_event)
    except Exception as e:
        emit(f"[SAFE] Adapter caught exception: {e}")
        emit(traceback.format_exc())
        raise
    emit(f"[SAFE] XSS adapter finished for {url} :: {param}")

def safe_sql(url, param, emit, stop_event):
    try:
        m = _import_module("fangsql")
    except Exception as e:
        emit(f"[SAFE] SQL error: Could not import fangsql: {e}")
        emit(traceback.format_exc())
        raise

    fn = getattr(m, "scan_sqli", None) or getattr(m, "scan", None)
    if not callable(fn):
        emit("[SAFE] fangsql has no callable entrypoint.")
        raise ImportError("No entrypoint in fangsql")

    emit(f"[SAFE] Starting SQLi scan for {url} :: {param}")
    try:
        try:
            fn(url, param, emit, stop_event)
        except TypeError:
            fn(f"{url}::{param}", emit, stop_event)
    except Exception as e:
        emit(f"[SAFE] Adapter caught exception: {e}")
        emit(traceback.format_exc())
        raise
    emit(f"[SAFE] SQL adapter finished for {url} :: {param}")

# Add safe_lfi, safe_rce, safe_brute, safe_api similarly if needed.