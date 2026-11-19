#!/usr/bin/env python3
"""Minimal pre-buy gate for a Solana trading bot (stdlib only).

    RRS_API_KEY=... python3 quickstart.py <MINT>
"""
import json
import os
import sys
import urllib.request

API = os.environ.get("RRS_AUDIT_URL", "https://rentandrugshield.com/api/audit")
MIN_SCORE = int(os.environ.get("RRS_MIN_SCORE", "85"))


def audit(mint: str) -> dict:
    headers = {"Content-Type": "application/json"}
    if os.environ.get("RRS_API_KEY"):
        headers["X-API-Key"] = os.environ["RRS_API_KEY"]
    req = urllib.request.Request(API, data=json.dumps({"mint": mint}).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def safe_to_buy(mint: str) -> bool:
    d = audit(mint)
    if not d.get("ok"):
        return False  # fail closed: 402 (pay via x402 / API key), 429, or error
    hard_fail = d.get("mint_authority_active") or d.get("freeze_authority_active") or d.get("has_permanent_delegate")
    return (d.get("safety_score") or 0) >= MIN_SCORE and not hard_fail


if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
    print(json.dumps({"mint": m, "safe_to_buy": safe_to_buy(m)}))
