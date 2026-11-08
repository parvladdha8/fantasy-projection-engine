import type { Metadata } from "next";

export const metadata: Metadata = { title: "Methodology" };

const REJECTED = [
  ["Week-of-season ramp (early / mid / late season)", "Slightly worse out of sample"],
  ["Week 1 effect (position-level and player-specific)", "No significant gain; player-specific version was worse"],
  ["Prime-time games", "No gain; a placebo test also exposed (and we fixed) a fitting bug"],
  ["Bad weather (wind ≥ 15 mph or ≤ 32°F, outdoors)", "No gain on top players"],
  ["Opponent strength vs position (schedule-adjusted)", "No gain; defensive strength barely persists week to week once shrunk"],
  ["Vacated opportunity (redistributing an injured teammate's targets)", "No gain, tested twice"],
  ["Team context on its own (share × team's historical volume)", "No gain until combined with betting lines"],
];

export default function Methodology() {
  return (
    <article className="max-w-3xl space-y-12 text-[15px] leading-relaxed">
      <header className="space-y-3 fade-up">
        <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight"><span className="gradient-text">Methodology</span></h1>
        <p className="text-subtle">
          How the projections are made, how we tested them, and what didn&apos;t work. Every number below is from a
          pre-registered test; the code and logs are public on GitHub.
        </p>
      </header>

      <section className="reveal space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">The model, step by step</h2>
        <ol className="list-decimal pl-5 space-y-2">
          <li><strong>Baseline.</strong> A recency-weighted average of a player&apos;s past full-PPR points (each game&apos;s weight halves every 8 games). Everything else has to beat this.</li>
          <li><strong>Opportunity × efficiency.</strong> Points = opportunities (targets, carries, pass attempts) × points per opportunity. Both are estimated separately and <em>shrunk</em> toward league and long-run averages (empirical Bayes), so a few big games don&apos;t over-count.</li>
          <li><strong>Betting market.</strong> Sportsbook game totals and spreads give each team&apos;s implied points. That sets how much offense to expect (volume) and how valuable each touch is (scoring environment).</li>
          <li><strong>Median, not mean.</strong> Fantasy scores are skewed: a few huge weeks pull the average up. A per-position correction, fitted by least absolute deviations, turns the average into the median, the number that minimises the typical miss.</li>
          <li><strong>Floor and ceiling.</strong> The 10th and 90th percentiles, fitted on past seasons and widened for more volatile players. In the 2025 test, 82.7% of top-player outcomes landed between them (target: about 80%).</li>
          <li><strong>Injuries.</strong> Players designated <em>Out</em> on the injury report are removed. Questionable players keep their projection.</li>
        </ol>
      </section>

      <section className="reveal space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">Rules we hold ourselves to</h2>
        <ul className="list-disc pl-5 space-y-1">
          <li><strong>No look-ahead.</strong> A projection for a week only uses information available before that week&apos;s kickoff. All backtests are walk-forward.</li>
          <li><strong>Earn every feature.</strong> An idea only enters the model if it lowers error on seasons it wasn&apos;t fitted on, with the test written down <em>before</em> running it.</li>
          <li><strong>Holdout discipline.</strong> Developed on 2018–2023, validated once on 2024, final test once on 2025.</li>
          <li><strong>Significance, not just wins.</strong> Comparisons use a paired bootstrap on per-player errors, resampling whole weeks so that players in the same week aren&apos;t treated as independent.</li>
        </ul>
      </section>

      <section className="reveal space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">Results on held-out seasons (Big 60 vs the baseline)</h2>
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-[11px] uppercase tracking-wider text-subtle border-b border-line">
              <tr><th className="px-3 py-2">Test</th><th className="px-3 py-2 text-right">Baseline MAE</th><th className="px-3 py-2 text-right">Model MAE</th><th className="px-3 py-2 text-right">p-value</th><th className="px-3 py-2 text-right">Weeks won</th></tr>
            </thead>
            <tbody>
              <tr className="border-t border-line"><td className="px-3 py-2">2024 validation (one time)</td><td className="px-3 py-2 text-right num">6.506</td><td className="px-3 py-2 text-right num font-semibold">6.349</td><td className="px-3 py-2 text-right num">0.002</td><td className="px-3 py-2 text-right num">15 of 18</td></tr>
              <tr className="border-t border-line"><td className="px-3 py-2">2025 final test (one time, the live model)</td><td className="px-3 py-2 text-right num">6.589</td><td className="px-3 py-2 text-right num font-semibold">6.295</td><td className="px-3 py-2 text-right num">&lt; 0.001</td><td className="px-3 py-2 text-right num">16 of 18</td></tr>
            </tbody>
          </table>
        </div>
        <p className="text-sm text-subtle">
          A lower MAE (average miss in fantasy points) is better. These tests are against our own baseline, because
          past ESPN or Yahoo projections aren&apos;t freely available. Comparison with a real platform (Sleeper) starts
          live in 2026: see the Big 60 scoreboard.
        </p>
      </section>

      <section className="reveal space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">What didn&apos;t work</h2>
        <p className="text-sm text-subtle">Tested properly and rejected. We keep these because a model that only reports its successes can&apos;t be trusted.</p>
        <ul className="divide-y divide-line card text-sm">
          {REJECTED.map(([idea, why]) => (
            <li key={idea} className="px-4 py-2.5"><span className="font-medium">{idea}</span><span className="text-subtle">: {why}</span></li>
          ))}
        </ul>
      </section>

      <section className="reveal space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">Known limitations</h2>
        <ul className="list-disc pl-5 space-y-1">
          <li>News that breaks minutes before kickoff may be missed. Those players are handled by the inactive rule in grading, the same for every source.</li>
          <li>Players with no NFL history (most rookies before their first game) get no projection. If one is in a platform&apos;s top 60, he is dropped from both sides and the count is published.</li>
          <li>Questionable players are projected as if they will play their usual role.</li>
          <li>Sleeper&apos;s projections endpoint is part of its public API but isn&apos;t listed in its documentation. We use it under Sleeper&apos;s non-commercial API terms and publish only our error statistics.</li>
        </ul>
      </section>

      <section className="reveal space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">Data</h2>
        <p>
          Player stats, snap counts, schedules, betting lines, rosters and injury reports come from{" "}
          <a className="underline" href="https://github.com/nflverse">nflverse</a> (CC BY 4.0). Projections refresh
          automatically every day and every 3 hours Thursday–Sunday, and each game&apos;s projection is locked at
          kickoff for grading.
        </p>
      </section>
    </article>
  );
}
