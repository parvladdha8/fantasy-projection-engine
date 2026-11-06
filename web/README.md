# FantasyQuant website

Next.js 16 site that shows the live projections, player breakdowns, the Big 60 scoreboard, "The idea" and the methodology.
It reads Supabase's public REST API with the **publishable** key (read-only through Row Level Security; Sleeper's data is
not readable with it). Data pages refresh every minute; design changes go live when pushed to GitHub (Vercel rebuilds).

Local preview: `export PATH=~/.local/node/bin:$PATH && npm run dev`, then open http://localhost:3000.
Settings: `web/.env.local` (git-ignored) with `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY`; on Vercel, the same two
as Environment Variables.
