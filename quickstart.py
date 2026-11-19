#!/usr/bin/env python3
"""Minimal pre-buy gate for a Solana trading bot (stdlib only).

Automatically resolves https://rentandrugshield.com/live_endpoint.json if a POST
to the static GitHub Pages origin returns HTTP 405.

    RRS_API_KEY=... python3 quickstart.py <MINT>
"""
import json
import os
import sys
import urllib.error
import urllib.request

API = os.environ.get("RRS_AUDIT_URL", "https://rentandrugshield.com/api/audit")
MIN_SCORE = int(os.environ.get("RRS_MIN_SCORE", "85"))


def _resolve_tunnel() -> str:
    req = urllib.request.Request("https://rentandrugshield.com/live_endpoint.json", headers={"User-Agent": "rrs-quickstart/1.0"})
    with urllib.request.urlopen(req, timeout=4) as r:
        cfg = json.loads(r.read())
    return str(cfg.get("api_base") or cfg.get("endpoint") or "").rstrip("/") + "/api/audit"


def audit(mint: str) -> dict:
    headers = {"Content-Type": "application/json", "User-Agent": "rrs-quickstart/1.0"}
    if os.environ.get("RRS_API_KEY"):
        headers["X-API-Key"] = os.environ["RRS_API_KEY"]
    body = json.dumps({"mint": mint}).encode()
    try:
        req = urllib.request.Request(API, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 405 and "rentandrugshield.com" in API:
            req = urllib.request.Request(_resolve_tunnel(), data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=5) as r:
                return json.loads(r.read())
        return {"ok": False, "status": e.code}


def safe_to_buy(mint: str) -> tuple[bool, dict]:
    d = audit(mint)
    if not d.get("ok"):
        return False, d  # fail closed: 402 (pay via x402 / API key), 429, or error
    hard_fail = d.get("mint_authority_active") or d.get("freeze_authority_active") or d.get("has_permanent_delegate")
    ok = (d.get("safety_score") or 0) >= MIN_SCORE and not hard_fail
    return ok, d


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
    ok, d = safe_to_buy(m)
    print(json.dumps({"mint": m, "safe_to_buy": ok, "safety_score": d.get("safety_score"), "audit_ms": d.get("audit_ms")}))
