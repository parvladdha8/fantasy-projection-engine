// Injury badge text for the projections table and player pages (no server code: safe in the browser).

/** Short badge for an injury status text, with a colour tone. Null when the player isn't on an injury report. */
export function injuryBadge(status: string | null | undefined, pPlay: number | null | undefined): { label: string; tone: "bad" | "warn" | "info" } | null {
  if (!status) return null;
  const pct = pPlay == null ? "" : ` · ${Math.round(pPlay * 100)}% play`;
  // Latest news, official report not out yet (Sleeper; DECISIONS.md 2026-11-11): Out or Doubtful → "Trending out".
  if (status.includes("per latest news") && /^(Out|Doubtful)/.test(status)) return { label: "Trending out", tone: "bad" };
  const wk = status.match(/\(week (\d+)\)/)?.[1];
  if (status.startsWith("Out last game")) return { label: `Out wk ${wk}${pct}`, tone: "bad" };
  if (status.startsWith("Doubtful last game")) return { label: `Doubtful wk ${wk}${pct}`, tone: "bad" };
  if (/^(Injured reserve|PUP list|Suspended|Not active)/.test(status)) return { label: status.split(/[,·]/)[0].trim(), tone: "bad" };
  if (status.startsWith("Out")) return { label: `Out${pct}`, tone: "bad" };
  if (status.startsWith("Doubtful")) return { label: `Doubtful${pct}`, tone: "bad" };
  if (status.startsWith("Questionable")) return { label: `Questionable${pct}`, tone: "warn" };
  if (status.startsWith("Did not practice")) return { label: "DNP", tone: "warn" };
  if (status.startsWith("Limited")) return { label: "Limited", tone: "info" };
  if (status.startsWith("Full")) return { label: "Full practice", tone: "info" };
  return { label: status.split(" · ")[0], tone: "info" };
}
