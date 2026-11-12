import Link from "next/link";
import { latestProjections, formatPT } from "@/lib/data";
import type { Metadata } from "next";
import ProjectionsTable, { type Row } from "./projections-table";
import { FAQ, SITE_URL, jsonLd } from "@/lib/site";

export const metadata: Metadata = { alternates: { canonical: "/" } };

const FAQ_LD = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  url: SITE_URL,
  mainEntity: FAQ.map(([q, a]) => ({ "@type": "Question", name: q, acceptedAnswer: { "@type": "Answer", text: a } })),
};

const r1 = (x: number) => Math.round(x * 10) / 10;

// Headline numbers from the one-time 2025 final test (paper/results_test_2025.md). Against our own baseline.
const STATS = [
  { value: "−0.29", unit: "pts", label: "smaller average miss than a simple average, 2025 holdout test (p < 0.001)" },
  { value: "16–2", unit: "", label: "weekly head-to-head record vs that baseline in 2025" },
  { value: "82.7%", unit: "", label: "of outcomes landed between our floor and ceiling (target 80%)" },
];

export default async function Home() {
  const { run, rows } = await latestProjections();
  const week = rows[0]?.week;
  return (
    <div className="space-y-16">
      <section className="space-y-6 pt-2 sm:pt-6">
        <p className="fade-up text-sm font-medium text-accent">Full-PPR fantasy football projections</p>
        <h1 className="fade-up delay-1 text-5xl sm:text-7xl font-semibold leading-[1.02] tracking-tight">
          <span className="gradient-text">FantasyQuant</span>
        </h1>
        <p className="fade-up delay-1 text-2xl sm:text-4xl font-semibold leading-tight tracking-tight max-w-3xl">
          Projections that grade themselves in public.
        </p>
        <p className="fade-up delay-2 text-lg sm:text-xl text-subtle max-w-2xl leading-relaxed">
          Every player gets a floor, median and ceiling. Every number shows how it was calculated. Every week, our projections
          are locked at kickoff and scored against Sleeper&apos;s, including the weeks we lose.
        </p>
        <div className="fade-up delay-3 flex flex-wrap gap-3 pt-1">
          <a href="#projections" className="rounded-full bg-accent px-5 py-2.5 text-sm font-medium text-white transition hover:opacity-90">
            {week ? `See week ${week}` : "See projections"}
          </a>
          <Link href="/idea" className="rounded-full px-5 py-2.5 text-sm font-medium text-accent transition hover:bg-muted">
            How it works →
          </Link>
        </div>
        <dl className="fade-up delay-4 grid gap-3 sm:grid-cols-3 pt-6">
          {STATS.map((s) => (
            <div key={s.value} className="card p-5">
              <dt className="sr-only">{s.label}</dt>
              <dd>
                <div className="num text-3xl font-semibold tracking-tight">
                  {s.value}<span className="text-base font-normal text-subtle"> {s.unit}</span>
                </div>
                <p className="mt-1 text-[13px] leading-snug text-subtle">{s.label}</p>
              </dd>
            </div>
          ))}
        </dl>
      </section>

      <section id="projections" className="scroll-mt-20 space-y-5">
        <div className="flex flex-wrap items-end justify-between gap-2">
          <div>
            <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight">{week ? `Week ${week}` : "This week"}</h2>
            {run && <p className="text-[13px] text-subtle mt-1">Updated {formatPT(run.started_at)} · refreshes daily, every 3 hours Thu–Sun</p>}
          </div>
          <p className="text-[13px] text-subtle max-w-sm">
            <strong className="text-foreground font-medium">Median</strong>: half the time he scores more, half less.{" "}
            <strong className="text-foreground font-medium">Floor / ceiling</strong>: a bad week and a great week (10th / 90th percentile).{" "}
            <strong className="text-foreground font-medium">Injury tags</strong>: the latest official report, or the latest news before the
            report is out (&ldquo;Trending out&rdquo; means news lists him Out or Doubtful). Projections assume the
            player plays; the % is how often players with that status have played (2018–2023). Players ruled Out are removed.
          </p>
        </div>
        {rows.length ? (
          <ProjectionsTable
            data={rows.map((r): Row => [r.player_id, r.player_name, r.position, r.team, r1(r.floor), r1(r.median), r1(r.ceiling),
              r.injury_status ?? null, r.p_play ?? null])}
          />
        ) : (
          <p className="text-subtle">No projections published yet.</p>
        )}
      </section>

      <section id="faq" className="scroll-mt-20 space-y-5 max-w-3xl">
        <h2 className="text-2xl sm:text-3xl font-semibold tracking-tight">Frequently asked questions</h2>
        <div className="card divide-y divide-line">
          {FAQ.map(([q, a]) => (
            <details key={q} className="group px-5 py-4">
              <summary className="cursor-pointer list-none font-medium flex items-center justify-between gap-4">
                <h3 className="text-[15px]">{q}</h3>
                <span aria-hidden className="text-subtle transition-transform group-open:rotate-45">+</span>
              </summary>
              <p className="mt-2 text-sm text-subtle leading-relaxed">{a}</p>
            </details>
          ))}
        </div>
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLd(FAQ_LD) }} />
      </section>
    </div>
  );
}
