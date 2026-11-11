"use client";

import Link from "next/link";
import { useMemo, useRef, useState } from "react";

import { injuryBadge } from "@/lib/injury";

// Compact row sent to the browser: [player_id, name, position, team, floor, median, ceiling, injury status, chance of
// playing] (numbers to 1 decimal; injury fields null for players not on an injury report).
export type Row = [string, string, string, string, number, number, number, string | null, number | null];

const TONE = { bad: "bg-bad/15 text-bad", warn: "bg-amber-500/15 text-amber-600 dark:text-amber-400", info: "bg-muted text-subtle" };

const POSITIONS = ["All", "QB", "RB", "WR", "TE"] as const;

export default function ProjectionsTable({ data }: { data: Row[] }) {
  const rows = useMemo(() => data.map(([player_id, player_name, position, team, floor, median, ceiling, injury_status, p_play]) =>
    ({ player_id, player_name, position, team, floor, median, ceiling, injury_status, badge: injuryBadge(injury_status, p_play) })), [data]);
  const [pos, setPos] = useState<(typeof POSITIONS)[number]>("All");
  const [q, setQ] = useState("");
  const [page, setPage] = useState(0);
  const top = useRef<HTMLDivElement>(null);
  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return rows.filter(
      (r) => (pos === "All" || r.position === pos) &&
        (!needle || r.player_name.toLowerCase().includes(needle) || r.team.toLowerCase() === needle),
    );
  }, [rows, pos, q]);
  const scaleMax = Math.max(...rows.map((r) => r.ceiling), 1);
  const PER_PAGE = 30;
  const pages = Math.max(1, Math.ceil(shown.length / PER_PAGE));
  const current = Math.min(page, pages - 1);
  const visible = shown.slice(current * PER_PAGE, (current + 1) * PER_PAGE);
  const go = (n: number) => {
    setPage(n);
    top.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const idx = POSITIONS.indexOf(pos);

  return (
    <div ref={top} className="scroll-mt-20 space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        {/* Segmented control with a sliding selection pill. */}
        <div className="relative grid grid-cols-5 rounded-full bg-muted p-1 sm:w-80" role="tablist" aria-label="Position">
          <span aria-hidden className="absolute inset-y-1 left-1 rounded-full bg-surface shadow-sm transition-transform duration-300 ease-out"
            style={{ width: "calc((100% - 0.5rem) / 5)", transform: `translateX(${idx * 100}%)` }} />
          {POSITIONS.map((p) => (
            <button key={p} role="tab" aria-selected={pos === p} onClick={() => { setPos(p); setPage(0); }}
              className={`relative z-10 rounded-full py-1.5 text-[13px] font-medium transition-colors ${pos === p ? "text-foreground" : "text-subtle hover:text-foreground"}`}>
              {p}
            </button>
          ))}
        </div>
        <div className="relative flex-1">
          <svg aria-hidden viewBox="0 0 20 20" className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-subtle" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="9" cy="9" r="6" /><path d="m14 14 4 4" strokeLinecap="round" />
          </svg>
          <input value={q} onChange={(e) => { setQ(e.target.value); setPage(0); }} placeholder="Search a player or team (e.g. KC)"
            className="w-full rounded-full bg-muted pl-10 pr-4 py-2 text-[14px] outline-none ring-accent/40 transition focus:bg-surface focus:ring-2"
            aria-label="Search" />
        </div>
      </div>
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-[14px]">
            <thead className="text-left text-[11px] uppercase tracking-wider text-subtle">
              <tr className="border-b border-line">
                <th className="px-4 py-3 w-10 font-medium">#</th>
                <th className="px-4 py-3 font-medium">Player</th>
                <th className="px-3 py-3 text-right font-medium" title="10th percentile: a bad week">Floor</th>
                <th className="px-3 py-3 text-right font-medium" title="Our projection: half the time he scores more, half less">Median</th>
                <th className="px-3 py-3 text-right font-medium" title="90th percentile: a great week">Ceiling</th>
                <th className="px-4 py-3 hidden sm:table-cell w-52 font-medium">Range</th>
              </tr>
            </thead>
            <tbody key={`${pos}-${current}`}>
              {visible.map((r, i) => (
                <tr key={r.player_id} className="group border-t border-line/60 first:border-t-0 transition-colors hover:bg-muted/60">
                  <td className="px-4 py-2.5 text-subtle num text-[13px]">{current * PER_PAGE + i + 1}</td>
                  <td className="px-4 py-2.5">
                    <Link href={`/player/${r.player_id}`} className="font-medium group-hover:text-accent transition-colors">{r.player_name}</Link>
                    <span className="ml-2 text-[12px] text-subtle">{r.position} · {r.team}</span>
                    {r.badge && (
                      <span title={`${r.injury_status ?? ""}. Projection assumes he plays.`}
                        className={`ml-2 inline-block whitespace-nowrap rounded-full px-2 py-0.5 text-[11px] font-medium ${TONE[r.badge.tone]}`}>
                        {r.badge.label}
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-right num text-subtle">{r.floor.toFixed(1)}</td>
                  <td className="px-3 py-2.5 text-right num font-semibold">{r.median.toFixed(1)}</td>
                  <td className="px-3 py-2.5 text-right num text-subtle">{r.ceiling.toFixed(1)}</td>
                  <td className="px-4 py-2.5 hidden sm:table-cell">
                    <div className="relative h-1.5 rounded-full bg-muted" aria-hidden>
                      <div className="grow-x absolute h-1.5 rounded-full bg-gradient-to-r from-accent/25 to-accent/60"
                        style={{ left: `${(r.floor / scaleMax) * 100}%`, width: `${((r.ceiling - r.floor) / scaleMax) * 100}%`, animationDelay: `${Math.min(i, 20) * 25}ms` }} />
                      <div className="absolute -top-0.5 h-2.5 w-2.5 -translate-x-1/2 rounded-full border-2 border-surface bg-accent shadow"
                        style={{ left: `${(r.median / scaleMax) * 100}%` }} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {shown.length === 0 && <p className="p-5 text-sm text-subtle">No players match.</p>}
      </div>
      {pages > 1 && (
        <nav className="flex items-center justify-between gap-3" aria-label="Pages">
          <button onClick={() => go(current - 1)} disabled={current === 0}
            className="rounded-full bg-muted px-5 py-2 text-[13px] font-medium transition hover:bg-line disabled:opacity-40 disabled:hover:bg-muted">
            ← Previous
          </button>
          <span className="num text-[13px] text-subtle">
            {current * PER_PAGE + 1}–{Math.min((current + 1) * PER_PAGE, shown.length)} of {shown.length}
          </span>
          <button onClick={() => go(current + 1)} disabled={current >= pages - 1}
            className="rounded-full bg-accent px-5 py-2 text-[13px] font-medium text-white transition hover:opacity-90 disabled:opacity-40">
            Next →
          </button>
        </nav>
      )}
    </div>
  );
}
