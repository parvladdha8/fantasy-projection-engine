import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site";

// Open to every search engine and AI answer engine (GPTBot, ClaudeBot, PerplexityBot, Google-Extended, ...):
// being cited by AI assistants is part of how people find the site.
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: "*", allow: "/" }],
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  };
}
