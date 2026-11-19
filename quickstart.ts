// Minimal pre-buy gate for a Solana trading bot (Node 18+, zero deps).
// Auto-resolves https://rentandrugshield.com/live_endpoint.json on static-CDN HTTP 405.
//   RRS_API_KEY=... npx tsx quickstart.ts <MINT>
const DEFAULT_API = process.env.RRS_AUDIT_URL ?? "https://rentandrugshield.com/api/audit";
const MIN_SCORE = Number(process.env.RRS_MIN_SCORE ?? 85);

interface Audit {
  ok: boolean;
  safety_score?: number;
  verdict?: string;
  audit_ms?: number;
  mint_authority_active?: boolean;
  freeze_authority_active?: boolean;
  has_permanent_delegate?: boolean;
  code?: string;
}

async function resolveTunnel(): Promise<string> {
  const r = await fetch("https://rentandrugshield.com/live_endpoint.json", { signal: AbortSignal.timeout(4000) });
  const cfg = (await r.json()) as { api_base?: string; endpoint?: string };
  return `${(cfg.api_base ?? cfg.endpoint ?? "").replace(/\/+$/, "")}/api/audit`;
}

export async function audit(mint: string): Promise<Audit> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (process.env.RRS_API_KEY) headers["X-API-Key"] = process.env.RRS_API_KEY;
  const body = JSON.stringify({ mint });
  let res = await fetch(DEFAULT_API, { method: "POST", headers, body, signal: AbortSignal.timeout(5000) });
  if (res.status === 405 && DEFAULT_API.includes("rentandrugshield.com")) {
    res = await fetch(await resolveTunnel(), { method: "POST", headers, body, signal: AbortSignal.timeout(5000) });
  }
  return (await res.json()) as Audit;
}

export async function safeToBuy(mint: string): Promise<{ ok: boolean; data: Audit }> {
  const d = await audit(mint);
  if (!d.ok) return { ok: false, data: d }; // fail closed on 402 / 429 / error
  const hardFail = d.mint_authority_active || d.freeze_authority_active || d.has_permanent_delegate;
  return { ok: (d.safety_score ?? 0) >= MIN_SCORE && !hardFail, data: d };
}

const mint = process.argv[2] ?? "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263";
safeToBuy(mint).then(({ ok, data }) =>
  console.log(JSON.stringify({ mint, safe_to_buy: ok, safety_score: data.safety_score, audit_ms: data.audit_ms }))
);
