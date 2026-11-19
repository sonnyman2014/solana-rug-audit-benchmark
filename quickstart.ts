// Minimal pre-buy gate for a Solana trading bot (Node 18+, zero deps).
//   RRS_API_KEY=... npx tsx quickstart.ts <MINT>
const API = process.env.RRS_AUDIT_URL ?? "https://rentandrugshield.com/api/audit";
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

export async function audit(mint: string): Promise<Audit> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (process.env.RRS_API_KEY) headers["X-API-Key"] = process.env.RRS_API_KEY;
  const res = await fetch(API, {
    method: "POST",
    headers,
    body: JSON.stringify({ mint }),
    signal: AbortSignal.timeout(5000),
  });
  return (await res.json()) as Audit;
}

export async function safeToBuy(mint: string): Promise<boolean> {
  const d = await audit(mint);
  if (!d.ok) return false; // fail closed on 402 / 429 / error
  const hardFail = d.mint_authority_active || d.freeze_authority_active || d.has_permanent_delegate;
  return (d.safety_score ?? 0) >= MIN_SCORE && !hardFail;
}

const mint = process.argv[2] ?? "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263";
safeToBuy(mint).then((ok) => console.log(JSON.stringify({ mint, safe_to_buy: ok })));
