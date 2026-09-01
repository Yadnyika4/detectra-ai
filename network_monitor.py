"""
network_monitor.py
-------------------
Collects real, locally-observable network + system metrics using psutil and
the OS ping command. Every function is defensive: if a measurement fails
(no internet, permission error, missing counter, changed interface, etc.)
it degrades gracefully instead of crashing the app.

Public entry point: collect_metrics() -> dict
"""

import platform
import re
import statistics
import subprocess
import time
from datetime import datetime

import psutil

import config


def _safe(default=None):
    """Decorator: catch any exception in a metric-collection function and
    return a safe default instead of propagating the error."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception:
                return default
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Ping-based latency / packet loss / jitter
# ---------------------------------------------------------------------------
def _run_ping(host: str, count: int, timeout_s: int):
    """Run the OS-appropriate ping command and return raw stdout text.
    Returns None if the command itself could not be executed."""
    system = platform.system().lower()
    try:
        if system == "windows":
            # -n count, -w timeout(ms)
            cmd = ["ping", "-n", str(count), "-w", str(int(timeout_s * 1000)), host]
        else:
            # -c count, -W timeout(s)  (Linux/Mac)
            cmd = ["ping", "-c", str(count), "-W", str(int(timeout_s)), host]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s * count + 5,
        )
        return result.stdout
    except Exception:
        return None


def _parse_ping_windows(output: str):
    """Extract per-packet round-trip times and loss % from Windows ping output."""
    times_ms = [float(t) for t in re.findall(r"time[=<]([\d.]+)ms", output, re.IGNORECASE)]
    loss_match = re.search(r"\((\d+)%\s*loss\)", output)
    loss_pct = float(loss_match.group(1)) if loss_match else None
    return times_ms, loss_pct


def _parse_ping_unix(output: str):
    """Extract per-packet round-trip times and loss % from Linux/Mac ping output."""
    times_ms = [float(t) for t in re.findall(r"time=([\d.]+)\s*ms", output, re.IGNORECASE)]
    loss_match = re.search(r"([\d.]+)%\s*packet loss", output)
    loss_pct = float(loss_match.group(1)) if loss_match else None
    return times_ms, loss_pct


@_safe(default={"latency": None, "packet_loss": None, "jitter": None, "connectivity_ok": False})
def measure_latency_and_loss(host: str = None, count: int = None, timeout_s: int = None):
    """Ping a reliable host and derive average latency (ms), packet loss (%)
    and jitter (stddev of latency samples, ms)."""
    host = host or config.PING_HOST
    count = count or config.PING_COUNT
    timeout_s = timeout_s or config.PING_TIMEOUT_S

    output = _run_ping(host, count, timeout_s)
    if not output:
        # Ping command unavailable/failed entirely -> treat as no connectivity
        return {"latency": None, "packet_loss": 100.0, "jitter": None, "connectivity_ok": False}

    if platform.system().lower() == "windows":
        times_ms, loss_pct = _parse_ping_windows(output)
    else:
        times_ms, loss_pct = _parse_ping_unix(output)

    if loss_pct is None:
        # Could not parse loss - assume total loss if no times were captured either
        loss_pct = 100.0 if not times_ms else 0.0

    latency = round(statistics.mean(times_ms), 2) if times_ms else None
    jitter = round(statistics.pstdev(times_ms), 2) if len(times_ms) > 1 else 0.0
    connectivity_ok = bool(times_ms) and loss_pct < 100.0

    return {
        "latency": latency,
        "packet_loss": round(loss_pct, 2),
        "jitter": jitter,
        "connectivity_ok": connectivity_ok,
    }


# ---------------------------------------------------------------------------
# Throughput / bandwidth usage estimate
# ---------------------------------------------------------------------------
@_safe(default={"bytes_sent_rate": 0.0, "bytes_recv_rate": 0.0, "network_usage": 0.0})
def measure_throughput(interval_s: float = None):
    """Sample net_io_counters twice, interval_s apart, to estimate current
    send/receive rate in Mbps, then convert to a 0-100% usage estimate
    against the assumed link capacity."""
    interval_s = interval_s or config.IO_SAMPLE_INTERVAL_S

    c1 = psutil.net_io_counters()
    t1 = time.time()
    time.sleep(interval_s)
    c2 = psutil.net_io_counters()
    t2 = time.time()

    elapsed = max(t2 - t1, 0.001)
    sent_bps = (c2.bytes_sent - c1.bytes_sent) * 8 / elapsed
    recv_bps = (c2.bytes_recv - c1.bytes_recv) * 8 / elapsed

    sent_mbps = round(sent_bps / 1_000_000, 3)
    recv_mbps = round(recv_bps / 1_000_000, 3)

    total_mbps = sent_mbps + recv_mbps
    usage_pct = min(100.0, round((total_mbps / config.ASSUMED_BANDWIDTH_MBPS) * 100, 1))

    return {
        "bytes_sent_rate": sent_mbps,
        "bytes_recv_rate": recv_mbps,
        "network_usage": usage_pct,
        "network_errors": (c2.errin - c1.errin) + (c2.errout - c1.errout)
        + (c2.dropin - c1.dropin) + (c2.dropout - c1.dropout),
    }


# ---------------------------------------------------------------------------
# System / connection metrics
# ---------------------------------------------------------------------------
@_safe(default=0.0)
def measure_cpu_usage():
    return psutil.cpu_percent(interval=0.3)


@_safe(default=0)
def measure_active_connections():
    """Count active network connections. On some OSes/permission levels this
    can raise AccessDenied - handled by the _safe decorator (returns 0)."""
    try:
        conns = psutil.net_connections(kind="inet")
    except (psutil.AccessDenied, PermissionError):
        # Fall back to per-process connection counting if available
        total = 0
        for p in psutil.process_iter():
            try:
                total += len(p.net_connections(kind="inet"))
            except Exception:
                continue
        return total
    return len(conns)


# ---------------------------------------------------------------------------
# Master collector
# ---------------------------------------------------------------------------
def collect_metrics() -> dict:
    """Collect a full, real-time metrics snapshot. Never raises - every
    sub-measurement is individually protected, and missing values are
    filled with safe fallbacks so the ML/diagnosis pipeline always
    receives numeric input."""

    ping_result = measure_latency_and_loss()
    throughput_result = measure_throughput()
    cpu = measure_cpu_usage()
    active_connections = measure_active_connections()

    latency = ping_result.get("latency")
    packet_loss = ping_result.get("packet_loss")
    connectivity_ok = ping_result.get("connectivity_ok", False)
    jitter = ping_result.get("jitter") or 0.0

    # If ping totally failed, fall back to worst-case numeric values so the
    # ML model / rules can still reason about "no connectivity" instead of
    # receiving None (which would crash downstream math).
    if latency is None:
        latency = 999.0
    if packet_loss is None:
        packet_loss = 100.0 if not connectivity_ok else 0.0

    metrics = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "source": "real",
        "latency": float(latency),
        "packet_loss": float(packet_loss),
        "jitter": float(jitter),
        "network_usage": float(throughput_result.get("network_usage", 0.0) or 0.0),
        "bytes_sent_rate": float(throughput_result.get("bytes_sent_rate", 0.0) or 0.0),
        "bytes_recv_rate": float(throughput_result.get("bytes_recv_rate", 0.0) or 0.0),
        "active_connections": int(active_connections or 0),
        "cpu_usage": float(cpu or 0.0),
        "network_errors": int(throughput_result.get("network_errors", 0) or 0),
        "connectivity_ok": bool(connectivity_ok),
    }
    return metrics
