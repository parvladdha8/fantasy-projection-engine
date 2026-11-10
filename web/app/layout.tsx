import type { Metadata } from "next";
import Link from "next/link";
import Script from "next/script";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { SITE_URL, SITE_NAME, TAGLINE, SITE_DESCRIPTION, jsonLd } from "@/lib/site";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: `${SITE_NAME} | ${TAGLINE}`, template: `%s · ${SITE_NAME}` },
  description: SITE_DESCRIPTION,
  applicationName: SITE_NAME,
  keywords: ["fantasy football projections", "PPR projections", "weekly fantasy rankings", "floor and ceiling",
    "fantasy football accuracy", "start sit", "FantasyQuant"],
  authors: [{ name: "Parv Laddha" }],
  openGraph: { type: "website", siteName: SITE_NAME, url: SITE_URL, title: `${SITE_NAME} | ${TAGLINE}`, description: SITE_DESCRIPTION },
  twitter: { card: "summary", title: `${SITE_NAME} | ${TAGLINE}`, description: SITE_DESCRIPTION },
  robots: { index: true, follow: true },
};

// Who publishes the site and what it is, in schema.org terms (read by search engines and AI assistants).
const SITE_LD = {
  "@context": "https://schema.org",
  "@graph": [
    { "@type": "WebSite", "@id": `${SITE_URL}/#website`, url: SITE_URL, name: SITE_NAME, description: SITE_DESCRIPTION,
      publisher: { "@id": `${SITE_URL}/#org` }, inLanguage: "en-US" },
    { "@type": "Organization", "@id": `${SITE_URL}/#org`, name: SITE_NAME, url: SITE_URL, slogan: TAGLINE,
      founder: { "@type": "Person", name: "Parv Laddha" },
      sameAs: ["https://github.com/parvladdha8/fantasy-projection-engine", "https://www.instagram.com/parv_laddha/"] },
  ],
};

const NAV = [
  { href: "/", label: "Projections" },
  { href: "/big60", label: "Scoreboard" },
  { href: "/idea", label: "The idea" },
  { href: "/methodology", label: "Methodology" },
];

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body suppressHydrationWarning className="min-h-full flex flex-col bg-background text-foreground">
        <header className="glass sticky top-0 z-50 border-b border-line/70">
          <div className="mx-auto max-w-5xl px-4 h-12 flex items-center justify-between gap-3">
            <Link href="/" className="font-semibold tracking-tight text-[17px]">
              Fantasy<span className="text-accent">Quant</span>
            </Link>
            <nav className="flex gap-0.5 overflow-x-auto text-[13px] text-subtle -mr-2">
              {NAV.map((n) => (
                <Link key={n.href} href={n.href}
                  className="whitespace-nowrap rounded-full px-3 py-1.5 transition-colors hover:text-foreground hover:bg-muted">
                  {n.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-10 sm:py-14">{children}</main>
        <footer className="border-t border-line text-xs text-subtle bg-muted/40">
          <div className="mx-auto max-w-5xl px-4 py-6 space-y-2">
            <p>
              <span className="font-semibold text-foreground">FantasyQuant</span> · Non-commercial fantasy football
              research. Every projection is locked at kickoff and graded after the games, including the weeks we lose.
              Code, methodology and every result, including failures:{" "}
              <a className="underline" href="https://github.com/parvladdha8/fantasy-projection-engine">GitHub</a>.
            </p>
            <p>
              NFL data from <a className="underline" href="https://github.com/nflverse">nflverse</a> (CC BY 4.0).
              Comparison projections from Sleeper (supplied by RotoWire); only our error statistics are shown, never
              their projections. Not affiliated with the NFL, Sleeper or RotoWire.
            </p>
          </div>
        </footer>
        {/* Vercel Web Analytics: cookie-free visitor counts (enable in Vercel dashboard → Analytics) */}
        <Script src="/_vercel/insights/script.js" strategy="afterInteractive" />
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLd(SITE_LD) }} />
      </body>
    </html>
  );
}
