import { latestProjections, formatPT } from "@/lib/data";
import ProjectionsTable from "./projections-table";

export default async function Home() {
  const { run, rows } = await latestProjections();
  const week = rows[0]?.week;
  return (
    <div className="space-y-6">
      <section className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">
          {week ? `Week ${week} projections` : "Projections"} <span className="text-subtle font-normal">· full PPR</span>
        </h1>
        <p className="text-sm text-subtle max-w-3xl">
          <strong className="text-foreground">Median</strong> is our projection: half the time a player scores more,
          half the time less. <strong className="text-foreground">Floor</strong> and{" "}
          <strong className="text-foreground">ceiling</strong> are the 10th and 90th percentiles, so about 8 in 10 weeks
          land between them (82.7% did in our 2025 test). Click a player to see how his number was built.
        </p>
        {run && (
          <p className="text-xs text-subtle">
            Updated {formatPT(run.started_at)}. Refreshed daily and every 3 hours Thursday–Sunday. Each game&apos;s
            projection is locked at kickoff for grading.
          </p>
        )}
      </section>
      {rows.length ? (
        <ProjectionsTable rows={rows.map((r) => ({ ...r, explanation: null, baseline: null }))} />
      ) : (
        <p className="text-subtle">No projections published yet.</p>
      )}
    </div>
  );
}
