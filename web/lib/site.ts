// Site-wide facts used for search-engine and AI-answer-engine metadata (SEO / AEO / GEO).
// Keep these in sync with the published results (paper/results_test_2025.md).

export const SITE_URL = "https://www.fantasyquant.app";
export const SITE_NAME = "FantasyQuant";
export const TAGLINE = "Projections that grade themselves in public";
export const SITE_DESCRIPTION =
  "Free weekly full-PPR fantasy football projections with a floor, median and ceiling for every player, built with " +
  "economics and statistics methods and graded publicly every week against Sleeper's projections.";

// Questions people ask search engines and AI assistants, answered in self-contained sentences.
// Shown on the home page and published as FAQPage structured data, so the two always match.
export const FAQ: [string, string][] = [
  ["What is FantasyQuant?",
    "FantasyQuant is a free website that publishes weekly full-PPR fantasy football projections for every relevant QB, RB, WR and TE. Each player gets a floor, median and ceiling, and every projection's accuracy is graded publicly after the games."],
  ["How accurate are FantasyQuant's projections?",
    "On the 2025 season, which was held out and never used to build the model, FantasyQuant's projections missed by 6.30 fantasy points per player on average versus 6.59 for a weighted average of past points: 4.5% less error (p < 0.001), winning 16 of 18 weeks. Live 2026 results against Sleeper are published weekly on the Big 60 scoreboard."],
  ["What is the Big 60 scoreboard?",
    "Each week, FantasyQuant is compared with Sleeper's projections on the 60 players Sleeper ranks highest before kickoff (top 10 QBs, 20 RBs, 20 WRs and 10 TEs). Both sets of projections are locked at kickoff, and whichever has the lower average miss (MAE) against actual full-PPR points wins the week."],
  ["What do floor, median and ceiling mean?",
    "The median is the projection: half the time the player scores more, half the time less. The floor is the 10th percentile (a bad week) and the ceiling is the 90th percentile (a great week). In the 2025 test, 82.7% of outcomes landed between the floor and ceiling, close to the 80% target."],
  ["How are the projections calculated?",
    "Each projection multiplies a player's expected opportunities (targets, carries, pass attempts) by his expected points per opportunity. Both are shrunk toward league averages with empirical Bayes so small samples don't overreact, adjusted with team implied points from betting lines, and converted to a median. Every step is shown on each player's page."],
  ["How often are the projections updated?",
    "Projections update automatically every morning and every 3 hours from Thursday to Sunday, so injury news and roster changes are included. Players ruled Out are removed. Each game's projections are locked at kickoff for grading."],
  ["What scoring format does FantasyQuant use?",
    "Full PPR (point per reception): 1 point per reception, 0.1 per rushing or receiving yard, 6 per rushing or receiving touchdown, 0.04 per passing yard, 4 per passing touchdown, 2 per two-point conversion and −2 per interception or fumble lost."],
  ["Is FantasyQuant free?",
    "Yes. FantasyQuant is a free, non-commercial research project with no sign-up. The code, methodology and every test result, including ideas that failed, are public on GitHub."],
];

/** JSON for a <script type="application/ld+json"> tag; escapes "<" so text can't close the tag. */
export function jsonLd(data: unknown): string {
  return JSON.stringify(data).replace(/</g, "\\u003c");
}
