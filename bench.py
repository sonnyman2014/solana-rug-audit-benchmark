#!/usr/bin/env python3
"""Live latency benchmark for the Rent & Rug Shield `POST /api/audit` endpoint.

Measures both HTTP/1.1 Keep-Alive latency (standard for persistent trading bots)
and per-request socket latency, plus the server-reported `audit_ms` telemetry,
across a rotating basket of real Solana mainnet mints.

Usage:
  python3 bench.py --url https://rentandrugshield.com/api/audit -n 200
  RRS_API_KEY=rsk_live_... python3 bench.py --url http://127.0.0.1:8088/api/audit -n 200 --json results/origin_keepalive.json
  RRS_API_KEY=rsk_live_... python3 bench.py --url http://127.0.0.1:8088/api/audit -n 200 --no-keepalive --json results/origin_cold_socket.json

Zero third-party dependencies (Python 3.9+ stdlib only).
"""
from __future__ import annotations

import argparse
import http.client
import json
import os
import platform
import ssl
import statistics
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

MINTS = {
    "BONK": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
    "JUP": "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN",
    "WIF": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm",
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "PYTH": "HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3",
    "RAY": "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R",
    "POPCAT": "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",
    "JTO": "jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL",
}

_TLS = threading.local()


def pct(vals, p):
    if not vals:
        return None
    s = sorted(vals)
    k = (len(s) - 1) * p / 100.0
    f, c = int(k), min(int(k) + 1, len(s) - 1)
    return round(s[f] + (s[c] - s[f]) * (k - f), 2)


def _get_conn(parsed, timeout):
    key = (parsed.scheme, parsed.netloc, timeout)
    conn = getattr(_TLS, "conn", None)
    if conn is not None and getattr(_TLS, "key", None) == key:
        return conn
    if parsed.scheme == "https":
        conn = http.client.HTTPSConnection(parsed.netloc, timeout=timeout, context=ssl.create_default_context())
    else:
        conn = http.client.HTTPConnection(parsed.netloc, timeout=timeout)
    _TLS.conn = conn
    _TLS.key = key
    return conn


def one_keepalive(parsed, path, mint, api_key, timeout):
    body = json.dumps({"mint": mint}).encode()
    h = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Connection": "keep-alive",
        "User-Agent": "rrs-audit-bench/1.0",
    }
    if api_key:
        h["X-API-Key"] = api_key
    for attempt in range(2):
        conn = _get_conn(parsed, timeout)
        t0 = time.perf_counter()
        try:
            conn.request("POST", path, body=body, headers=h)
            resp = conn.getresponse()
            raw = resp.read()
            code = resp.status
            ms = (time.perf_counter() - t0) * 1000
            break
        except (http.client.HTTPException, OSError) as e:
            _TLS.conn = None
            if attempt == 1:
                return {"ok": False, "http": 0, "err": type(e).__name__, "ms": (time.perf_counter() - t0) * 1000}
    try:
        d = json.loads(raw)
    except Exception:
        return {"ok": False, "http": code, "ms": ms, "err": "non-json"}
    if code >= 400:
        return {"ok": False, "http": code, "ms": ms, "code": d.get("code")}
    return {
        "ok": bool(d.get("ok")),
        "http": code,
        "ms": ms,
        "audit_ms": d.get("audit_ms"),
        "cached": d.get("cached"),
        "score": d.get("safety_score", d.get("score")),
        "layers": d.get("layers_checked"),
        "code": d.get("code"),
    }


def one_cold(url, mint, api_key, timeout):
    body = json.dumps({"mint": mint}).encode()
    h = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Connection": "close",
        "User-Agent": "rrs-audit-bench/1.0",
    }
    if api_key:
        h["X-API-Key"] = api_key
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request(url, data=body, headers=h, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            code = r.status
    except urllib.error.HTTPError as e:
        return {"ok": False, "http": e.code, "ms": (time.perf_counter() - t0) * 1000}
    except Exception as e:
        return {"ok": False, "http": 0, "err": type(e).__name__, "ms": (time.perf_counter() - t0) * 1000}
    ms = (time.perf_counter() - t0) * 1000
    try:
        d = json.loads(raw)
    except Exception:
        return {"ok": False, "http": code, "ms": ms, "err": "non-json"}
    return {
        "ok": bool(d.get("ok")),
        "http": code,
        "ms": ms,
        "audit_ms": d.get("audit_ms"),
        "cached": d.get("cached"),
        "score": d.get("safety_score", d.get("score")),
        "layers": d.get("layers_checked"),
        "code": d.get("code"),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="https://rentandrugshield.com/api/audit")
    ap.add_argument("-n", type=int, default=200)
    ap.add_argument("-c", "--concurrency", type=int, default=1)
    ap.add_argument("--warmup", type=int, default=len(MINTS))
    ap.add_argument("--timeout", type=float, default=15)
    ap.add_argument("--no-keepalive", action="store_true", help="open a fresh TCP/TLS socket per request")
    ap.add_argument("--json", help="write full benchmark JSON receipt to path")
    a = ap.parse_args()
    key = os.environ.get("RRS_API_KEY", "")
    mints = list(MINTS.values())
    parsed = urllib.parse.urlsplit(a.url)
    path = (parsed.path or "/api/audit") + (f"?{parsed.query}" if parsed.query else "")

    runner = (
        (lambda i: one_cold(a.url, mints[i % len(mints)], key, a.timeout))
        if a.no_keepalive
        else (lambda i: one_keepalive(parsed, path, mints[i % len(mints)], key, a.timeout))
    )

    for i in range(a.warmup):
        runner(i)

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max(1, a.concurrency)) as ex:
        res = list(ex.map(runner, range(a.n)))
    wall = time.perf_counter() - t0

    ok = [r for r in res if r["ok"]]
    client = [r["ms"] for r in ok]
    server = [float(r["audit_ms"]) for r in ok if isinstance(r.get("audit_ms"), (int, float))]
    errors = {}
    for r in res:
        if not r["ok"]:
            k = f"HTTP {r['http']}" + (f" {r.get('code') or r.get('err') or ''}".rstrip())
            errors[k] = errors.get(k, 0) + 1
    out = {
        "url": a.url,
        "mode": "cold_socket" if a.no_keepalive else "http11_keepalive",
        "measured_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "requests": a.n,
        "ok": len(ok),
        "errors": errors,
        "concurrency": a.concurrency,
        "warmup": a.warmup,
        "throughput_rps": round(a.n / wall, 2) if wall else None,
        "client_ms": {
            "p50": pct(client, 50),
            "p95": pct(client, 95),
            "p99": pct(client, 99),
            "mean": round(statistics.mean(client), 2) if client else None,
            "min": round(min(client), 2) if client else None,
            "max": round(max(client), 2) if client else None,
        },
        "server_audit_ms": {
            "p50": pct(server, 50),
            "p95": pct(server, 95),
            "p99": pct(server, 99),
        },
        "cached_ratio": round(sum(1 for r in ok if r.get("cached")) / len(ok), 3) if ok else None,
        "python": platform.python_version(),
        "platform": platform.system() + " " + platform.machine(),
        "mints": MINTS,
    }
    print(json.dumps(out, indent=2))
    if a.json:
        os.makedirs(os.path.dirname(a.json) or ".", exist_ok=True)
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
