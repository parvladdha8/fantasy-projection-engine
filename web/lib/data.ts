// Read-only data access to Supabase's public REST API. The publishable key can only READ the public tables
// (Row Level Security; see db/supabase_security.sql). Sleeper's projections are never readable through it.
import { cacheLife } from "next/cache";

export type Projection = {
  player_id: string; game_id: string; season: number; week: number; player_name: string; position: string;
  team: string; median: number; floor: number; ceiling: number; baseline: number | null; explanation: string | null;
};
export type Run = { run_id: string; started_at: string; finished_at: string | null; status: string };
export type WeekResult = {
  platform: string; season: number; week: number; n_pool: number; n_scored: number; n_dropped_no_ours: number;
  n_inactive: number; mae_ours: number; mae_platform: number; rmse_ours: number; rmse_platform: number;
  spearman_ours: number | null; spearman_platform: number | null; winner: "ours" | "platform" | "tie"; computed_at: string;
};
export type PositionResult = { platform: string; season: number; week: number; position: string; n: number; mae_ours: number; mae_platform: number };
export type Frozen = { source: string; player_id: string; game_id: string; season: number; week: number; projected: number; kickoff: string };
export type Actual = { player_id: string; game_id: string; season: number; week: number; points_ppr: number };

async function query<T>(path: string): Promise<T[]> {
  const url = process.env.SUPABASE_URL, key = process.env.SUPABASE_PUBLISHABLE_KEY;
  if (!url || !key || key.startsWith("PASTE_")) throw new Error("Supabase settings missing (SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY).");
  const res = await fetch(`${url}/rest/v1/${path}`, { headers: { apikey: key, Authorization: `Bearer ${key}` } });
  if (!res.ok) throw new Error(`Supabase ${res.status} for ${path.split("?")[0]}`);
  return res.json();
}

export async function latestProjections(): Promise<{ run: Run | null; rows: Projection[] }> {
  "use cache";
  cacheLife("minutes");
  const [run] = await query<Run>("runs?status=eq.ok&order=started_at.desc&limit=1");
  if (!run) return { run: null, rows: [] };
  const rows = await query<Projection>(`projections?run_id=eq.${encodeURIComponent(run.run_id)}&order=median.desc&limit=2000`);
  return { run, rows };
}

export async function playerHistory(playerId: string): Promise<{ frozen: Frozen[]; actuals: Actual[] }> {
  "use cache";
  cacheLife("minutes");
  const id = encodeURIComponent(playerId);
  const [frozen, actuals] = await Promise.all([
    query<Frozen>(`frozen_projections?player_id=eq.${id}&source=eq.ours&order=kickoff.desc&limit=40`),
    query<Actual>(`actuals?player_id=eq.${id}&limit=40`),
  ]);
  return { frozen, actuals };
}

export async function leaderboard(): Promise<{ weeks: WeekResult[]; positions: PositionResult[] }> {
  "use cache";
  cacheLife("minutes");
  const [weeks, positions] = await Promise.all([
    query<WeekResult>("leaderboard_weekly?order=season.desc,week.desc&limit=500"),
    query<PositionResult>("leaderboard_position?order=season.desc,week.desc&limit=2000"),
  ]);
  return { weeks, positions };
}

export const PLATFORM_LABEL: Record<string, string> = {
  sleeper: "Sleeper (projections by RotoWire)",
  baseline: "Simple average (our baseline)",
};

export function formatPT(iso: string): string {
  return new Intl.DateTimeFormat("en-US", {
    timeZone: "America/Los_Angeles", weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
  }).format(new Date(iso)) + " PT";
}
