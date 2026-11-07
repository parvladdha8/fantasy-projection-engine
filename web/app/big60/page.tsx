import type { Metadata } from "next";
import { leaderboard, PLATFORM_LABEL, type WeekResult, type PositionResult } from "@/lib/data";

export const metadata: Metadata = { title: "Big 60 scoreboard" };

const ORDER = ["sleeper", "baseline"];

function record(weeks: WeekResult[]) {
  const w = weeks.filter((x) => x.winner === "ours").length, l = weeks.filter((x) => x.winner === "platform").length;
  const t = weeks.length - w - l;
  return `${w}–${l}${t ? `–${t}` : ""}`;
}

export default async function Big60() {
  const { weeks, positions } = await leaderboard();
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
            points (lower average miss, MAE) wins the week. We publish every week, including the ones we lose.
          </p>
          <p>
            Players ruled inactive at kickoff are removed for every source alike. Results can change for 10 days after
            a week because of NFL stat corrections. One week is noise; judge us on the season.
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
          positions={positions.filter((x) => x.platform === p)} />)
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

function Platform({ platform, weeks, positions }: { platform: string; weeks: WeekResult[]; positions: PositionResult[] }) {
  const label = PLATFORM_LABEL[platform] ?? platform;
  const season = weeks[0].season;
  const thisSeason = weeks.filter((w) => w.season === season);
  const avg = (k: "mae_ours" | "mae_platform") => thisSeason.reduce((s, w) => s + w[k], 0) / thisSeason.length;
  return (
    <section className="reveal space-y-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-2xl font-semibold tracking-tight">vs {label}</h2>
        <p className="text-sm"><span className="text-subtle">{season} record: </span><span className="num font-semibold text-base">{record(thisSeason)}</span>
          <span className="text-subtle"> · season MAE </span><span className="num">{avg("mae_ours").toFixed(2)}</span>
          <span className="text-subtle"> vs </span><span className="num">{avg("mae_platform").toFixed(2)}</span></p>
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-[11px] uppercase tracking-wider text-subtle border-b border-line">
            <tr>
              <th className="px-3 py-2">Week</th>
              <th className="px-3 py-2 text-right">Our MAE</th>
              <th className="px-3 py-2 text-right">Their MAE</th>
              <th className="px-3 py-2">Winner</th>
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
      <p className="text-xs text-subtle">MAE = average absolute miss in fantasy points over the scored pool (lower is better). Position columns: negative = we missed by less.</p>
    </section>
  );
}
