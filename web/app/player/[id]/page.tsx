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
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{p.player_name}</h1>
            <p className="text-subtle">{p.position} · {p.team} · Week {p.week}</p>
          </div>
          <div className="grid grid-cols-3 gap-3 max-w-md">
            {[["Floor", p.floor], ["Median", p.median], ["Ceiling", p.ceiling]].map(([k, v]) => (
              <div key={k as string} className="rounded-lg border border-line p-3 text-center">
                <div className="text-xs uppercase tracking-wide text-subtle">{k}</div>
                <div className={`num text-xl ${k === "Median" ? "font-semibold" : ""}`}>{(v as number).toFixed(1)}</div>
              </div>
            ))}
          </div>
        </section>
      )}
      {steps.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">How this projection was built</h2>
          <ol className="divide-y divide-line rounded-lg border border-line">
            {steps.map((s, i) => (
              <li key={i} className="flex items-start justify-between gap-4 px-4 py-3">
                <div>
                  <div className={s.kind === "change" ? "" : "font-semibold"}>{s.kind === "end" ? "Median projection" : s.label}</div>
                  {PLAIN[s.label] && <div className="text-xs text-subtle mt-0.5 max-w-xl">{PLAIN[s.label]}</div>}
                </div>
                <div className={`num shrink-0 text-right ${s.kind === "change" ? (s.value > 0 ? "text-good" : s.value < 0 ? "text-bad" : "text-subtle") : "font-semibold"}`}>
                  {s.kind === "change" ? `${s.value > 0 ? "+" : ""}${s.value.toFixed(1)}` : s.value.toFixed(1)}
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}
      {graded.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-lg font-semibold">Track record (projection locked at kickoff vs actual)</h2>
          <div className="overflow-x-auto rounded-lg border border-line">
            <table className="w-full text-sm">
              <thead className="bg-muted text-left text-xs uppercase tracking-wide text-subtle">
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
