import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { latestProjections, playerHistory } from "@/lib/data";
import { parseExplanation } from "@/lib/explain";

const PLAIN: Record<string, string> = {
  "recent average": "His recent scoring, weighting newer games more (the simple-average baseline).",
  "role & efficiency (own history)": "His expected opportunities (targets, carries, pass attempts) times points per opportunity, both shrunk toward league norms so a few big games don't over-count.",
  "team context": "His share of the team's offense, applied to how much offense his team is expected to have.",
  "betting lines: team volume": "Sportsbook game total and spread: teams expected to score more run more plays.",
  "efficiency calibration": "A per-position correction fitted on past seasons so efficiency isn't systematically too high or low.",
  "betting lines: scoring environment": "In games the market expects to be high-scoring, each target and carry is worth more.",
  "median adjustment": "Converts the average outcome into the median. Fantasy scores are skewed (a few huge weeks), so the typical week sits below the average.",
};

export async function generateMetadata({ params }: PageProps<"/player/[id]">): Promise<Metadata> {
  const id = decodeURIComponent((await params).id);
  const { rows } = await latestProjections();
  const p = rows.find((r) => r.player_id === id);
  const canonical = { canonical: `/player/${encodeURIComponent(id)}` };
  if (!p) return { title: "Player projection", alternates: canonical, robots: { index: false } };
  const title = `${p.player_name} Week ${p.week} projection (full PPR)`;
  const description = `${p.player_name} (${p.position}, ${p.team}) Week ${p.week} full-PPR projection: ${p.median.toFixed(1)} points ` +
    `(floor ${p.floor.toFixed(1)}, ceiling ${p.ceiling.toFixed(1)}), with every step of how it was calculated.`;
  return { title, description, alternates: canonical, openGraph: { title, description } };
}

export default function PlayerPage({ params }: PageProps<"/player/[id]">) {
  return (
    <Suspense fallback={<p className="text-subtle">Loading player…</p>}>
      {params.then(({ id }) => <Player id={decodeURIComponent(id)} />)}
    </Suspense>
  );
}

async function Player({ id }: { id: string }) {
  const [{ rows }, hist] = await Promise.all([latestProjections(), playerHistory(id)]);
  const p = rows.find((r) => r.player_id === id);
  const steps = parseExplanation(p?.explanation ?? null);
  const maxChange = Math.max(0.1, ...steps.filter((s) => s.kind === "change").map((s) => Math.abs(s.value)));
  const actual = new Map(hist.actuals.map((a) => [a.game_id, a.points_ppr]));
  const graded = hist.frozen.filter((f) => actual.has(f.game_id));

  if (!p && hist.frozen.length === 0) {
    return <div className="space-y-3"><p>No projection for this player this week.</p><Link className="underline" href="/">Back to projections</Link></div>;
  }
  return (
    <div className="space-y-8">
      <Link href="/" className="text-sm text-subtle hover:underline">← All projections</Link>
      {p && (
        <section className="space-y-4">
          <div className="fade-up">
            <p className="text-sm font-medium text-accent">{p.position} · {p.team} · Week {p.week}</p>
            <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight mt-1">{p.player_name}</h1>
          </div>
          <div className="fade-up delay-1 grid grid-cols-3 gap-3 max-w-lg">
            {[["Floor", p.floor, "a bad week"], ["Median", p.median, "our projection"], ["Ceiling", p.ceiling, "a great week"]].map(([k, v, note]) => (
              <div key={k as string} className={`card p-4 text-center ${k === "Median" ? "ring-2 ring-accent/40" : ""}`}>
                <div className="text-[11px] uppercase tracking-wider text-subtle">{k}</div>
                <div className={`num text-3xl tracking-tight mt-1 ${k === "Median" ? "font-semibold" : ""}`}>{(v as number).toFixed(1)}</div>
                <div className="text-[11px] text-subtle mt-0.5">{note}</div>
              </div>
            ))}
          </div>
        </section>
      )}
      {steps.length > 0 && (
        <section className="fade-up delay-2 space-y-3">
          <h2 className="text-2xl font-semibold tracking-tight">How this projection was built</h2>
          <ol className="divide-y divide-line card overflow-hidden">
            {steps.map((s, i) => (
              <li key={i} className="flex items-start justify-between gap-4 px-4 py-3">
                <div>
                  <div className={s.kind === "change" ? "" : "font-semibold"}>{s.kind === "end" ? "Median projection" : s.label}</div>
                  {PLAIN[s.label] && <div className="text-xs text-subtle mt-0.5 max-w-xl">{PLAIN[s.label]}</div>}
                </div>
                <div className="flex shrink-0 items-center gap-3">
                  {s.kind === "change" && (
                    <div className="hidden sm:block h-1.5 w-24 rounded-full bg-muted overflow-hidden" aria-hidden>
                      <div className={`grow-x h-full rounded-full ${s.value >= 0 ? "bg-good" : "bg-bad"}`}
                        style={{ width: `${Math.min(100, (Math.abs(s.value) / maxChange) * 100)}%`, animationDelay: `${i * 60}ms` }} />
                    </div>
                  )}
                  <div className={`num w-14 text-right ${s.kind === "change" ? (s.value > 0 ? "text-good" : s.value < 0 ? "text-bad" : "text-subtle") : "font-semibold text-lg"}`}>
                    {s.kind === "change" ? `${s.value > 0 ? "+" : ""}${s.value.toFixed(1)}` : s.value.toFixed(1)}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}
      {graded.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-2xl font-semibold tracking-tight">Track record (projection locked at kickoff vs actual)</h2>
          <div className="card overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-[11px] uppercase tracking-wider text-subtle border-b border-line">
                <tr><th className="px-3 py-2">Week</th><th className="px-3 py-2 text-right">Projected</th><th className="px-3 py-2 text-right">Actual</th><th className="px-3 py-2 text-right">Miss</th></tr>
              </thead>
              <tbody>
                {graded.map((f) => {
                  const a = actual.get(f.game_id)!;
                  return (
                    <tr key={f.game_id} className="border-t border-line">
                      <td className="px-3 py-2">{f.season} week {f.week}</td>
                      <td className="px-3 py-2 text-right num">{f.projected.toFixed(1)}</td>
                      <td className="px-3 py-2 text-right num">{a.toFixed(1)}</td>
                      <td className="px-3 py-2 text-right num text-subtle">{(a - f.projected > 0 ? "+" : "") + (a - f.projected).toFixed(1)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
