import type { Metadata } from "next";

export const metadata: Metadata = { title: "The idea" };

const DIFFERENT = [
  ["A range, not just a number", "Every player gets a floor, median and ceiling. We check that the range is honest: in our 2025 test, 82.7% of outcomes landed inside the 10th–90th percentile band (target ≈ 80%)."],
  ["You can see the working", "Each projection shows every step from the player's recent average to the final number, so you can disagree with a specific step instead of a black box."],
  ["Graded in public, losses included", "Each week's projections are locked at kickoff and scored afterwards against the actual points, side by side with Sleeper's, on Sleeper's own top 60. A losing week is published like a winning one."],
  ["Failed ideas are published too", "Prime-time games, weather, opponent strength and Week 1 effects all sound smart. We tested each one properly, none of them helped, so none of them are in the model, and we say so."],
  ["Tests written before results", "Every idea's test and pass/fail rule were written down before it was run. That stops the most common trap in sports analytics: trying things until something looks good by luck."],
];

export default function Idea() {
  return (
    <article className="max-w-3xl space-y-14 text-[15px] leading-relaxed">
      <header className="space-y-4 fade-up">
        <p className="text-sm font-medium text-accent">The idea</p>
        <h1 className="text-4xl sm:text-5xl font-semibold leading-[1.08] tracking-tight"><span className="gradient-text">Fantasy projections</span> built like an economics paper</h1>
        <p className="text-subtle">
          Most fantasy projections ask you to trust them. This project tries to earn it: every number comes from a
          model whose parts were tested on seasons it never saw, and the whole thing is graded in public every week.
        </p>
      </header>

      <section className="reveal space-y-3">
        <h2 className="text-2xl font-semibold tracking-tight">Why I built it</h2>
        <p>
          A fantasy projection is a forecast, and forecasting is something economists have thought hard about: how
          to separate signal from noise, how to avoid fooling yourself, and how to prove a forecast is actually good.
          I wanted to see what happens when you apply those habits to fantasy football: start from the simplest
          sensible forecast, add an idea only if it beats that forecast on data it wasn&apos;t built on, and keep a
          public scorecard.
        </p>
      </section>

      <section className="reveal space-y-3">
        <h2 className="text-2xl font-semibold tracking-tight">What&apos;s different here</h2>
        <ul className="grid gap-3 sm:grid-cols-2">
          {DIFFERENT.map(([t, d]) => (
            <li key={t} className="card p-5 transition-transform duration-300 hover:-translate-y-0.5">
              <div className="font-semibold">{t}</div>
              <p className="text-sm text-subtle mt-1">{d}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="reveal space-y-4">
        <h2 className="text-2xl font-semibold tracking-tight">The statistics and econometrics, in plain English</h2>

        <div className="space-y-2">
          <h3 className="font-semibold">1. Opportunity × efficiency</h3>
          <p>
            Fantasy points are a product: <strong>how many chances a player gets</strong> (targets, carries, pass
            attempts) times <strong>how much each chance is worth</strong>. The two behave very differently. Volume
            is stable: a player&apos;s role carries over from week to week. Efficiency is mostly noise: a receiver who
            scores twice on four catches won&apos;t keep doing that. Modelling them separately lets us trust the
            stable part and be sceptical of the noisy part.
          </p>
        </div>

        <div className="space-y-2">
          <h3 className="font-semibold">2. Shrinkage (empirical Bayes)</h3>
          <p>
            Small samples lie. The fix is to blend each player&apos;s own record with the league average for his
            position, trusting his record more the more evidence he has:
          </p>
          <p className="rounded-2xl bg-muted px-4 py-3 font-mono text-sm">
            efficiency = (his points + k × league rate) ÷ (his opportunities + k)
          </p>
          <p>
            <em>k</em> acts like a number of &quot;imaginary&quot; league-average plays. It isn&apos;t picked by
            hand; it is chosen by testing which value forecasts best on later seasons. For receivers it came out at{" "}
            <strong>100 targets</strong>. So a receiver with 50 recent targets is pulled two-thirds of the way toward
            the league rate, while one with 300 targets is pulled only a quarter of the way. This is the same idea
            economists use when ranking hospitals or teachers from small samples.
          </p>
        </div>

        <div className="space-y-2">
          <h3 className="font-semibold">3. The betting market as information</h3>
          <p>
            Sportsbooks&apos; point totals and spreads are some of the best public forecasts in sports, because
            people bet real money against them. They give each team&apos;s <strong>implied points</strong>: a team
            favoured by 3 in a game with a total of 47 is expected to score (47 + 3) ÷ 2 = 25. Teams expected to
            score more run more plays (more volume), and every touch is worth more in a shootout (more efficiency).
            We tested this with a <strong>placebo</strong>: with the lines shuffled between games, only a small gain
            remained (from the extra model structure). The real lines improved accuracy significantly beyond that,
            so the gain comes from genuine information in the market.
          </p>
        </div>

        <div className="space-y-2">
          <h3 className="font-semibold">4. Median, not mean</h3>
          <p>
            Fantasy scores are skewed. A few 40-point explosions pull a player&apos;s <em>average</em> above his{" "}
            <em>typical</em> week. If you want the number that misses by the least on average (the leaderboard&apos;s
            metric), the right target is the <strong>median</strong>. A per-position correction fitted by least
            absolute deviations (the regression that targets medians instead of means) does exactly that, and it
            improved accuracy significantly.
          </p>
        </div>

        <div className="space-y-2">
          <h3 className="font-semibold">5. Floor and ceiling (quantile regression)</h3>
          <p>
            The floor and ceiling are the 10th and 90th percentiles, estimated with quantile regression on past
            seasons. Players whose scores have swung more in the past get wider ranges than steady ones, even at the
            same median.
          </p>
        </div>

        <div className="space-y-2">
          <h3 className="font-semibold">6. Testing like a forecaster</h3>
          <ul className="list-disc pl-5 space-y-1">
            <li><strong>Walk-forward.</strong> To test a season, the model is fitted only on seasons before it, exactly as it would have been used in real time.</li>
            <li><strong>Untouched holdouts.</strong> Built on 2018–2023, validated once on 2024, final test once on 2025.</li>
            <li><strong>Significance.</strong> A win counts only if a paired bootstrap says it is unlikely to be luck. It resamples whole weeks, because players in the same week share game conditions.</li>
            <li><strong>Placebos.</strong> Every idea is also tested with a fake version (labels moved to random games). If the fake helps too, the idea isn&apos;t real.</li>
          </ul>
        </div>
      </section>

      <section className="reveal space-y-3">
        <h2 className="text-2xl font-semibold tracking-tight">What the model looks at</h2>
        <ul className="list-disc pl-5 space-y-1">
          <li>Snap counts, targets, carries and pass attempts, recency-weighted, with zero-snap games counted honestly</li>
          <li>Points per target, per carry and per pass attempt, shrunk toward the position&apos;s league rate</li>
          <li>Team implied points and expected margin from betting lines</li>
          <li>Official injury designations (players ruled Out are removed)</li>
          <li>Each player&apos;s current team from weekly rosters, so trades and signings are picked up</li>
        </ul>
        <p className="text-sm text-subtle">
          And what it deliberately ignores, because testing showed it didn&apos;t help: prime-time games, weather,
          opponent defence rankings, Week 1 effects and late-season trends. Details are on the Methodology page.
        </p>
      </section>

      <section className="reveal card p-5 space-y-1">
        <h2 className="text-2xl font-semibold tracking-tight">Who&apos;s behind it</h2>
        <p>
          Built by <strong>Parv Laddha</strong>, a student interested in economics and statistics. Questions or
          feedback: Instagram{" "}
          <a className="underline" href="https://www.instagram.com/parv_laddha/">@parv_laddha</a>.
        </p>
      </section>
    </article>
  );
}
