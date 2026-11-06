"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import type { Projection } from "@/lib/data";

const POSITIONS = ["All", "QB", "RB", "WR", "TE"] as const;

export default function ProjectionsTable({ rows }: { rows: Projection[] }) {
  const [pos, setPos] = useState<(typeof POSITIONS)[number]>("All");
  const [q, setQ] = useState("");
  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return rows.filter(
      (r) => (pos === "All" || r.position === pos) &&
        (!needle || r.player_name.toLowerCase().includes(needle) || r.team.toLowerCase() === needle),
    );
  }, [rows, pos, q]);
  const scaleMax = Math.max(...rows.map((r) => r.ceiling), 1);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex rounded-lg border border-line p-0.5" role="tablist" aria-label="Position">
          {POSITIONS.map((p) => (
            <button key={p} role="tab" aria-selected={pos === p} onClick={() => setPos(p)}
              className={`rounded-md px-3 py-1.5 text-sm ${pos === p ? "bg-foreground text-background" : "hover:bg-muted"}`}>
              {p}
            </button>
          ))}
        </div>
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search player or team (e.g. KC)"
          className="min-w-0 flex-1 rounded-lg border border-line bg-background px-3 py-2 text-sm" aria-label="Search" />
      </div>
      <div className="overflow-x-auto rounded-lg border border-line">
        <table className="w-full text-sm">
          <thead className="bg-muted text-left text-xs uppercase tracking-wide text-subtle">
            <tr>
              <th className="px-3 py-2 w-10">#</th>
              <th className="px-3 py-2">Player</th>
              <th className="px-3 py-2 text-right" title="10th percentile: a bad week">Floor</th>
              <th className="px-3 py-2 text-right" title="Our projection: half the time he scores more, half the time less">Median</th>
              <th className="px-3 py-2 text-right" title="90th percentile: a great week">Ceiling</th>
              <th className="px-3 py-2 hidden sm:table-cell w-48">Range</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((r, i) => (
              <tr key={`${r.player_id}-${r.game_id}`} className="border-t border-line hover:bg-muted/60">
                <td className="px-3 py-2 text-subtle num">{i + 1}</td>
                <td className="px-3 py-2">
                  <Link href={`/player/${r.player_id}`} className="font-medium hover:underline">{r.player_name}</Link>
                  <span className="ml-2 text-xs text-subtle">{r.position} · {r.team}</span>
                </td>
                <td className="px-3 py-2 text-right num text-subtle">{r.floor.toFixed(1)}</td>
                <td className="px-3 py-2 text-right num font-semibold">{r.median.toFixed(1)}</td>
                <td className="px-3 py-2 text-right num text-subtle">{r.ceiling.toFixed(1)}</td>
                <td className="px-3 py-2 hidden sm:table-cell">
                  <div className="relative h-2 rounded bg-muted" aria-hidden>
                    <div className="absolute h-2 rounded bg-accent/30"
                      style={{ left: `${(r.floor / scaleMax) * 100}%`, width: `${((r.ceiling - r.floor) / scaleMax) * 100}%` }} />
                    <div className="absolute h-2 w-0.5 bg-accent" style={{ left: `${(r.median / scaleMax) * 100}%` }} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {shown.length === 0 && <p className="p-4 text-sm text-subtle">No players match.</p>}
      </div>
    </div>
  );
}
