import type { Metadata } from "next";
import Link from "next/link";
import { leaderboard, accuracyEdge, PLATFORM_LABEL, type WeekResult, type PositionResult, type Highlight } from "@/lib/data";

export const metadata: Metadata = {
  title: "Big 60 scoreboard: FantasyQuant vs Sleeper",
  description: "Weekly accuracy scoreboard: FantasyQuant's full-PPR projections vs Sleeper's on Sleeper's own top 60 players, locked at kickoff and graded on actual points. Every week is published.",
  alternates: { canonical: "/big60" },
};

const ORDER = ["sleeper", "baseline"];

function record(weeks: WeekResult[]) {
  const w = weeks.filter((x) => x.winner === "ours").length, l = weeks.filter((x) => x.winner === "platform").length;
  const t = weeks.length - w - l;
  return `${w}–${l}${t ? `–${t}` : ""}`;
}

export default async function Big60() {
  const { weeks, positions, highlights } = await leaderboard();
  const platforms = [...new Set([...ORDER, ...weeks.map((w) => w.platform)])].filter((p) => weeks.some((w) => w.platform === p));
  return (
    <div className="space-y-8">
      <section className="space-y-4 fade-up">
        <p className="text-sm font-medium text-accent">Scoreboard</p>
        <h1 className="text-4xl sm:text-5xl font-semibold tracking-tight"><span className="gradient-text">The Big 60</span>, every week.</h1>
        <div className="text-sm text-subtle max-w-3xl space-y-2">
          <p>
            Every week we go head-to-head with each source <em>on its own turf</em>: the 60 players <strong className="text-foreground">it</strong>{" "}
            ranks highest before kickoff (top 10 QB, 20 RB, 20 WR, 10 TE). Both sides&apos; projections are locked at
            each game&apos;s kickoff. After the games, the side whose projections were closer to the actual full-PPR
            points wins the week. We publish every week, including the ones we lose.
          </p>
          <p>
            <strong className="text-foreground">How to read it:</strong> the <strong className="text-foreground">average miss</strong> is
            how many fantasy points a projection was off by, on average, across the 60 players (statisticians call
            this MAE). If a player was projected for 15 and scored 20, that projection missed by 5. Lower is better.{" "}
            <strong className="text-foreground">&quot;% more accurate&quot;</strong> compares the two average misses: missing by 6.2 points instead of
            6.5 makes us 4% more accurate that week.
          </p>
          <p>
            Players ruled inactive at kickoff are removed for every source alike. Results can change for 10 days after
            a week because of NFL stat corrections.
          </p>
        </div>
      </section>
      {platforms.length === 0 ? (
        <div className="card p-8 text-center fade-up delay-2">
          <p className="text-xl font-semibold tracking-tight">First results coming soon</p>
          <p className="text-subtle mt-2 max-w-md mx-auto text-sm">
            The first live results (week 9 of 2026, against Sleeper and our simple-average baseline) appear once the
            NFL&apos;s week-9 stats are final, around Tuesday, Nov 10.
          </p>
        </div>
      ) : (
        platforms.map((p) => <Platform key={p} platform={p} weeks={weeks.filter((w) => w.platform === p)}
          positions={positions.filter((x) => x.platform === p)}
          highlights={p === "sleeper" ? highlights.filter((h) => h.platform === p) : []} />)
      )}
      <section className="reveal rounded-2xl bg-muted p-6 text-sm text-subtle max-w-3xl space-y-2">
        <p><strong className="text-foreground">Who are we comparing against?</strong></p>
        <p>
          <strong className="text-foreground">{PLATFORM_LABEL.sleeper}</strong>: Sleeper&apos;s public weekly
          projections, collected under Sleeper&apos;s API terms for non-commercial use. To grade everyone on identical
          scoring, their projected stat lines are re-scored with the same PPR rules as ours and the actual points
          (e.g. −2 per interception). We show only the error statistics, never their projections.
        </p>
        <p>
          <strong className="text-foreground">{PLATFORM_LABEL.baseline}</strong>: a recency-weighted average of each
          player&apos;s past fantasy points. It is the bar any model must clear. Beating it is necessary, not impressive.
        </p>
      </section>
    </div>
  );
}

function Edge({ value }: { value: number }) {
  const r = Math.round(Math.abs(value) * 10) / 10;
  if (r === 0) return <span className="text-subtle">Even</span>;
  return value > 0
    ? <span className="text-good">{r}% more accurate</span>
    : <span className="text-bad">{r}% less accurate</span>;
}

function Platform({ platform, weeks, positions, highlights }: { platform: string; weeks: WeekResult[]; positions: PositionResult[]; highlights: Highlight[] }) {
  const label = PLATFORM_LABEL[platform] ?? platform;
  const season = weeks[0].season;
  const thisSeason = weeks.filter((w) => w.season === season);
  const avg = (k: "mae_ours" | "mae_platform") => thisSeason.reduce((s, w) => s + w[k], 0) / thisSeason.length;
  const seasonEdge = accuracyEdge(avg("mae_ours"), avg("mae_platform"));
  const hlWeeks = [...new Set(highlights.map((h) => `${h.season}-${h.week}`))];
  return (
    <section className="reveal space-y-3">
      <h2 className="text-2xl font-semibold tracking-tight">vs {label}</h2>
      <dl className="grid gap-3 grid-cols-3">
        <div className="card p-4">
          <dt className="text-[12px] text-subtle">{season} record (weeks won–lost)</dt>
          <dd className="num text-2xl sm:text-3xl font-semibold tracking-tight mt-1">{record(thisSeason)}</dd>
        </div>
        <div className="card p-4">
          <dt className="text-[12px] text-subtle">Accuracy this season</dt>
          <dd className="text-lg sm:text-2xl font-semibold tracking-tight mt-1"><Edge value={seasonEdge} /></dd>
        </div>
        <div className="card p-4">
          <dt className="text-[12px] text-subtle">Average miss (ours vs theirs)</dt>
          <dd className="num text-lg sm:text-2xl font-semibold tracking-tight mt-1">{avg("mae_ours").toFixed(2)} <span className="text-subtle font-normal text-base">vs {avg("mae_platform").toFixed(2)} pts</span></dd>
        </div>
      </dl>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-[11px] uppercase tracking-wider text-subtle border-b border-line">
            <tr>
              <th className="px-3 py-2">Week</th>
              <th className="px-3 py-2 text-right" title="Average miss in fantasy points (MAE)">Our avg miss</th>
              <th className="px-3 py-2 text-right" title="Average miss in fantasy points (MAE)">Their avg miss</th>
              <th className="px-3 py-2">Winner</th>
              <th className="px-3 py-2">Accuracy</th>
              <th className="px-3 py-2 text-right hidden sm:table-cell" title="Rank correlation with actual points (higher is better)">Spearman (ours / theirs)</th>
              <th className="px-3 py-2 text-right hidden md:table-cell">QB / RB / WR / TE (ours − theirs)</th>
              <th className="px-3 py-2 text-right hidden md:table-cell" title="Scored players; players removed as inactive; pool players we had no projection for">Scored · inactive · no proj.</th>
            </tr>
          </thead>
          <tbody>
            {weeks.map((w) => {
              const pos = Object.fromEntries(positions.filter((x) => x.week === w.week && x.season === w.season).map((x) => [x.position, x.mae_ours - x.mae_platform]));
              return (
                <tr key={`${w.season}-${w.week}`} className="border-t border-line">
                  <td className="px-3 py-2">{w.season} wk {w.week}</td>
                  <td className="px-3 py-2 text-right num font-semibold">{w.mae_ours.toFixed(2)}</td>
                  <td className="px-3 py-2 text-right num">{w.mae_platform.toFixed(2)}</td>
                  <td className={`px-3 py-2 ${w.winner === "ours" ? "text-good" : w.winner === "platform" ? "text-bad" : "text-subtle"}`}>
                    {w.winner === "ours" ? "Us" : w.winner === "platform" ? "Them" : "Tie"}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap"><Edge value={accuracyEdge(w.mae_ours, w.mae_platform)} /></td>
                  <td className="px-3 py-2 text-right num hidden sm:table-cell text-subtle">
                    {w.spearman_ours?.toFixed(2) ?? "–"} / {w.spearman_platform?.toFixed(2) ?? "–"}
                  </td>
                  <td className="px-3 py-2 text-right num hidden md:table-cell text-subtle">
                    {["QB", "RB", "WR", "TE"].map((k) => (pos[k] === undefined ? "–" : (pos[k] > 0 ? "+" : "") + pos[k].toFixed(1))).join(" / ")}
                  </td>
                  <td className="px-3 py-2 text-right num hidden md:table-cell text-subtle">{w.n_scored} · {w.n_inactive} · {w.n_dropped_no_ours}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-subtle">Average miss = how many fantasy points a projection was off by, on average (MAE; lower is better). Position columns: negative = we missed by less.</p>
      {hlWeeks.map((key, i) => {
        const hs = highlights.filter((h) => `${h.season}-${h.week}` === key);
        const [s, wk] = key.split("-");
        return (
          <details key={key} open={i === 0} className="card p-5 group">
            <summary className="cursor-pointer list-none font-semibold flex items-center justify-between">
              <span>Week {wk} biggest wins and losses{s !== String(season) ? ` (${s})` : ""}</span>
              <span aria-hidden className="text-subtle transition-transform group-open:rotate-45">+</span>
            </summary>
            <p className="text-xs text-subtle mt-1">Biggest wins: players where our projection beat {label.split(" (")[0]}&apos;s by the most. Biggest losses: where theirs beat ours by the most. Names only; we never publish their projections.</p>
            <div className="grid gap-4 sm:grid-cols-2 mt-4">
              {(["win", "loss"] as const).map((kind) => (
                <div key={kind}>
                  <h3 className={`text-sm font-semibold ${kind === "win" ? "text-good" : "text-bad"}`}>{kind === "win" ? "Biggest wins" : "Biggest losses"}</h3>
                  <ol className="mt-2 space-y-1 text-sm">
                    {hs.filter((h) => h.kind === kind).map((h) => (
                      <li key={h.rank} className="flex gap-2">
                        <span className="num text-subtle w-4">{h.rank}.</span>
                        <Link href={`/player/${encodeURIComponent(h.player_id)}`} className="hover:underline">{h.player_name}</Link>
                        <span className="text-subtle">{h.position}</span>
                      </li>
                    ))}
                  </ol>
                </div>
              ))}
            </div>
          </details>
        );
      })}
    </section>
  );
}
