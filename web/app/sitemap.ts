import type { MetadataRoute } from "next";
import { latestProjections } from "@/lib/data";
import { SITE_URL } from "@/lib/site";

// Every page search engines should know about, including one page per projected player.
export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const pages: MetadataRoute.Sitemap = [
    { url: `${SITE_URL}/`, changeFrequency: "daily", priority: 1 },
    { url: `${SITE_URL}/big60`, changeFrequency: "weekly", priority: 0.9 },
    { url: `${SITE_URL}/idea`, changeFrequency: "monthly", priority: 0.7 },
    { url: `${SITE_URL}/methodology`, changeFrequency: "monthly", priority: 0.7 },
  ];
  try {
    const { run, rows } = await latestProjections();
    const lastModified = run ? new Date(run.started_at) : undefined;
    for (const r of rows) {
      pages.push({ url: `${SITE_URL}/player/${encodeURIComponent(r.player_id)}`, lastModified, changeFrequency: "daily", priority: 0.5 });
    }
  } catch {
    // Database unreachable: still serve the main pages rather than an error.
  }
  return pages;
}
