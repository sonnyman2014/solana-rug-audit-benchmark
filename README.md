# Solana Rent & Rug Shield — `<120ms` Pre-Buy `POST /api/audit` Benchmark & Bot Quickstart

Reproducible latency benchmark and zero-dependency **Python** + **TypeScript** pre-buy firewall quickstarts for Solana sniper, copy-trading, and autonomous x402 agents.

- **Web App**: [https://rentandrugshield.com/app](https://rentandrugshield.com/app)
- **30% Atomic `?ref=` Affiliate Program**: [https://rentandrugshield.com/affiliates](https://rentandrugshield.com/affiliates)
- **Pricing**: 1st 11-Layer Token Audit **FREE** (lifetime) · 1st Empty ATA Rent Reclaim **0% fee** (lifetime proof, `2.0%` atomic on ATA `#2+`) · Extra API calls `10¢` via **Solana x402** or `$1.99` 24h Pass (`X-API-Key`).

---

## Live Measured Latency (`2026-11-19 UTC`, `n = 200` Requests)

Measured with [`bench.py`](./bench.py) across 8 real Solana mainnet mints (`BONK`, `JUP`, `WIF`, `USDC`, `PYTH`, `RAY`, `POPCAT`, `JTO`) after an 8-mint warm-up pass. Raw JSON receipts are committed in [`results/`](./results/).

| Transport Mode | Requests (`ok`) | Server `audit_ms` **p50** | Server `audit_ms` **p95** | Client RTT **p50** | Client RTT **Mean** | Client RTT **Min** | Client RTT **p95** | Throughput |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Live Public HTTPS Tunnel** (`awards-northern-needed-rom.trycloudflare.com/api/audit`) | `50 / 50` (`100%`) | **`4.0 ms`** | **`4.0 ms`** | **`74.71 ms`** | **`80.20 ms`** | `59.15 ms` | **`110.87 ms`** | `12.15 req/s` |
| **Origin HTTP/1.1 Keep-Alive** (`bench.py`, `n = 200`) | `200 / 200` (`100%`) | **`4.0 ms`** | **`4.0 ms`** | **`69.61 ms`** | **`80.18 ms`** | `12.35 ms` | `184.89 ms` | `12.40 req/s` |
| **Origin Cold Socket (`--no-keepalive`)** (`Connection: close`) | `200 / 200` (`100%`) | **`4.0 ms`** | **`4.0 ms`** | **`54.03 ms`** | **`105.92 ms`** | `13.12 ms` | `447.87 ms` | `9.42 req/s` |

> **Endpoint Discovery Note**: `https://rentandrugshield.com` serves its static frontend via GitHub Pages CDN and publishes the active HTTPS backend bridge at [`https://rentandrugshield.com/live_endpoint.json`](https://rentandrugshield.com/live_endpoint.json) (`api_base + "/api/audit"`). Both `bench.py` and the quickstarts automatically resolve `live_endpoint.json` if a `POST` to the static CDN returns `HTTP 405`.

---

## What the 11-Layer Firewall Checks Before Your Bot Buys

1. **L1 · Mint Authority**: Rejects active mint authorities (infinite supply inflation risk).
2. **L2 · Freeze Authority**: Rejects active freeze authorities (instant honeypot / unsellable trap).
3. **L3 · Token-2022 `PermanentDelegate`**: Detects irrevocable delegate hooks that can seize or burn holder balances without signature.
4. **L4 · Token-2022 `TransferHook` & `TransferFeeConfig`**: Flags malicious CPI transfer hooks and punitive sell taxes (`transfer_fee_bps`).
5. **L5 · Canonical LP Burn / Lock**: On-chain verification of Raydium, PumpSwap, and Orca LP burn/lock status (`is_canonical_burned_lp`).
6. **L6 · Liquidity Viability**: Liquidity-to-MC ratio and dead-pool checks (`liquidity_viability_passed`).
7. **L7 · Top Holder Concentration**: Non-pool top-1 / top-5 / top-10 / top-15 concentration caps.
8. **L8 · Block-0 Sybil Funder Cluster**: Detects bundled creator-funded sniper wallets (`sybil_cluster_pct`).
9. **L9 · Spoofed Migration LP**: Catches fake Pump.fun / Raydium graduation pools (`spoofed_migration_lp`).
10. **L10 · Hidden PDA Rent Trap**: Flags malicious account-sizing / close-authority traps (`hidden_pda_rent_trap`).
11. **L11 · Inner-CPI Drainer Simulation**: Pre-execution guard against nested `SetAuthority` / `Approve` / drain instructions.

---

## 30-Second Quickstart

### 1. Python (`Python 3.9+`, zero dependencies)

```bash
# Run a single pre-buy check (uses free quota or RRS_API_KEY)
RRS_API_KEY=rsk_live_your_key python3 quickstart.py DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263
# -> {"mint": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263", "safe_to_buy": true, "safety_score": 99, "audit_ms": 4}
```

### 2. TypeScript / Node 18+ (`fetch`, zero dependencies)

```bash
RRS_API_KEY=rsk_live_your_key npx tsx quickstart.ts DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263
```

### 3. Reproduce the Latency Benchmark Yourself

```bash
# Against auto-discovered live HTTPS endpoint (or pass --url http://127.0.0.1:8088/api/audit)
RRS_API_KEY=rsk_live_your_key python3 bench.py -n 200 --json results/my_run.json

# Interactive browser benchmark
# Open index.html in any browser to test live RTT from your region!
```

---

## Sample `POST /api/audit` JSON Response

```json
{
  "ok": true,
  "mint": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
  "symbol": "BONK",
  "safety_score": 99,
  "verdict": "SAFE • 11-LAYER ADAPTIVE SHIELD PASSED",
  "layers_checked": 11,
  "layers_passed": 11,
  "mint_authority_active": false,
  "freeze_authority_active": false,
  "has_permanent_delegate": false,
  "has_transfer_hook": false,
  "transfer_fee_bps": 0,
  "is_canonical_burned_lp": true,
  "hidden_pda_rent_trap": false,
  "sybil_cluster_pct": 0.0,
  "audit_ms": 4,
  "cached": true
}
```

## Earn 30% Atomic On-Chain Commissions (`?ref=`)

Building a Telegram/Discord scanner bot or trading terminal? Append `?ref=<YourSolanaPubkey>` to every outbound `https://rentandrugshield.com/app?ref=<YourSolanaPubkey>` link — **30% of every 2.0% ATA rent cleanup fee (`#2+`) and Pro pass** splits atomically on-chain to your wallet inside the user's own transaction. Generate links & grab the open-source group bot at [https://rentandrugshield.com/affiliates](https://rentandrugshield.com/affiliates).
