# Draft: permission request to Sleeper (Parv sends this; not sent by Claude)

**To:** the licensing address on https://docs.sleeper.com/ (the page hides it from automated readers; open the page in a browser and copy it from the line "For commercial use of the Sleeper API, please reach out to us directly at …")
**Subject:** Permission request: non-commercial projection-accuracy leaderboard using Sleeper projections

---

Hi Sleeper team,

My name is Parv. I'm a high school student building a non-commercial research project: a weekly full-PPR fantasy football projection model that publicly grades its own accuracy.

Each week, the site compares projections head-to-head on a fixed pool of players chosen *before* kickoff: the platform's own top 10 QBs, 20 RBs, 20 WRs and 10 TEs by projected points. After the games, it publishes the error (MAE) for both sides, including the weeks we lose. The goal is an honest, pre-registered accuracy test, not a competing product.

I'd like to include Sleeper's weekly player projections as one of the benchmarks. That would mean:

- **What we collect:** a snapshot of Sleeper's weekly projections for NFL players, at most a few times per week and once at each game's kickoff (far below your 1,000-calls-per-minute guideline).
- **What we publish:** only Sleeper's projected points for the 60 benchmark players each week, next to their actual points and our projections, with clear attribution to Sleeper and a link to your site. We would not republish your full projection set or any other Sleeper data.
- **Non-commercial:** the site has no ads, payments, sponsorships or user accounts. The code and methodology are public.

The projections endpoint isn't in your public API documentation, so I wanted to ask before using it rather than assume. Is this use acceptable to you? If you'd prefer different limits (frequency, what is shown, attribution wording), I'm happy to follow them. If the answer is no, I'll leave Sleeper out of the leaderboard.

Thank you for your time,
Parv
[optional: link to the project's GitHub repo once it's public]
