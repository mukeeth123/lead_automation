import React, { useMemo, useState, useRef, useEffect } from "react";
import axios from "axios";

/* ============================================================
   AI BUYING SIGNAL INTELLIGENCE — iOSYS
   Design language: analyst / signals-desk. Light, dense, quiet
   chrome with one instrument as the signature: a 4-bar "signal
   strength" readout that stands in for Intent Score everywhere.
   ============================================================ */

const FONT_IMPORT =
  "@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');";

/* ---------------------------- constants ---------------------------- */

const SOURCES = [
  { id: "indiehackers", name: "Indie Hackers", tag: "IH" },
  { id: "n8n", name: "n8n Community", tag: "N8N" },
  { id: "hackernews", name: "Hacker News", tag: "HN" },
  { id: "startup_networks", name: "Startup Networks", tag: "SN" },
  { id: "uk_business_forums", name: "UK Business Forums", tag: "UKBF" },
  { id: "bubble_forum", name: "Bubble Forum", tag: "BUB" },
  { id: "remote_ok", name: "Remote OK", tag: "ROK" },
  { id: "uk_contracts_finder", name: "UK Contracts Finder", tag: "UKCF" },
  { id: "reddit", name: "Reddit", tag: "RDT" },
  { id: "github", name: "GitHub", tag: "GH" }
];
const SOURCE_MAP = Object.fromEntries(SOURCES.map((s) => [s.id, s]));

const TECHNOLOGIES = [
  "RAG", "LLM", "AI Agents", "GenAI", "Automation", "Custom Software",
  "CRM Integration", "ERP Integration", "API Integration", "Cloud Migration",
  "Vector DB", "Chatbot",
];

const SIGNAL_TYPES = [
  "Hiring Signal", "Explicit Ask", "Pain Point Post", "Tech Stack Mention",
  "Funding News", "Product Launch", "Integration Request", "RFP / Tender",
];

const SOURCE_SIGNAL_BIAS = {
  reddit: ["Pain Point Post", "Explicit Ask", "Tech Stack Mention"],
  hackernews: ["Tech Stack Mention", "Funding News", "Pain Point Post"],
  x: ["Explicit Ask", "Pain Point Post"],
  indiehackers: ["Product Launch", "Explicit Ask", "Funding News"],
  github: ["Tech Stack Mention", "Integration Request"],
  stackoverflow: ["Integration Request", "Tech Stack Mention"],
  producthunt: ["Product Launch", "Tech Stack Mention"],
  jobboards: ["Hiring Signal"],
  tedeu: ["RFP / Tender"],
};

const IOSYS_BY_TECH = {
  RAG: "RAG / LLM", LLM: "RAG / LLM", "Vector DB": "RAG / LLM", Chatbot: "RAG / LLM",
  "AI Agents": "AI Agents", GenAI: "AI Automation", Automation: "AI Automation",
  "Custom Software": "Custom Software", "CRM Integration": "CRM Integration",
  "ERP Integration": "ERP Integration", "API Integration": "API Integration",
  "Cloud Migration": "Cloud Modernization",
};

const STATUSES = ["New", "New", "New", "Reviewed", "Contacted", "Qualified"];

const COMPANIES = [
  { name: "Northwind Health Systems", industry: "Healthcare", country: "United States" },
  { name: "Pinehill Health Network", industry: "Healthcare", country: "United Kingdom" },
  { name: "Carewell Medical Group", industry: "Healthcare", country: "Canada" },
  { name: "Vantage Finance Group", industry: "Finance", country: "United States" },
  { name: "Ledgerstone Capital", industry: "Finance", country: "United Kingdom" },
  { name: "Trustline Bank", industry: "Finance", country: "Germany" },
  { name: "Cover Trust Insurance", industry: "Insurance", country: "United States" },
  { name: "Assured Insurance Group", industry: "Insurance", country: "Netherlands" },
  { name: "Northstar Mutual", industry: "Insurance", country: "Canada" },
  { name: "Cobalt Manufacturing Co", industry: "Manufacturing", country: "Germany" },
  { name: "Ironforge Industrial", industry: "Manufacturing", country: "United States" },
  { name: "Steelbridge Manufacturing", industry: "Manufacturing", country: "Sweden" },
  { name: "BrightCart Retail", industry: "Retail", country: "United States" },
  { name: "Retailyx", industry: "Retail", country: "United Kingdom" },
  { name: "ShelfSmart Retail", industry: "Retail", country: "Australia" },
  { name: "Meridian SaaS Labs", industry: "SaaS", country: "United States" },
  { name: "Cloudframe Software", industry: "SaaS", country: "Canada" },
  { name: "Nimbus Cloud Works", industry: "SaaS", country: "Singapore" },
  { name: "Fleetline Logistics", industry: "Logistics", country: "Netherlands" },
  { name: "Waypoint Freight", industry: "Logistics", country: "United States" },
  { name: "Haulwise Logistics", industry: "Logistics", country: "Germany" },
  { name: "Harborview Realty", industry: "Real Estate", country: "United States" },
  { name: "Bluepeak Properties", industry: "Real Estate", country: "United Kingdom" },
  { name: "Keystone Properties", industry: "Real Estate", country: "Australia" },
  { name: "Lumen Legal Partners", industry: "Legal", country: "United States" },
  { name: "Statute Legal Tech", industry: "Legal", country: "United Kingdom" },
  { name: "Barristem Legal", industry: "Legal", country: "Canada" },
  { name: "Solara Energy", industry: "Energy", country: "United States" },
  { name: "Voltaic Power Co", industry: "Energy", country: "Germany" },
  { name: "GridWatt Energy", industry: "Energy", country: "Sweden" },
  { name: "Crestpoint Hospitality", industry: "Hospitality", country: "United States" },
  { name: "Guestline Hotels Group", industry: "Hospitality", country: "United Kingdom" },
  { name: "Summit Stay Hotels", industry: "Hospitality", country: "Australia" },
  { name: "Arcadia Learning", industry: "Education", country: "United States" },
  { name: "EduSpark Academy", industry: "Education", country: "India" },
];

const INDUSTRIES = [...new Set(COMPANIES.map((c) => c.industry))];
const COUNTRIES = [...new Set(COMPANIES.map((c) => c.country))];
const REF_DATE = new Date(2026, 7, 20); // Aug 20, 2026

/* ---------------------------- rng + generation ---------------------------- */

function mulberry32(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const pick = (arr, r) => arr[Math.floor(r() * arr.length)];

const PAIN_PHRASES = [
  (industry) => `Manual processes are creating a bottleneck as ${industry.toLowerCase()} operations scale.`,
  () => `The team is spending too many hours on repetitive work that automation could remove.`,
  () => `Existing tools don't talk to each other, leaving data siloed across departments.`,
  () => `Customer response times are slipping as ticket volume grows faster than headcount.`,
  (industry, tech) => `Current infrastructure can't support real-time ${tech.toLowerCase()} workloads at the company's scale.`,
  () => `Reporting takes days to compile because data lives across disconnected legacy systems.`,
  (industry, tech) => `Engineering is stretched thin trying to build ${tech.toLowerCase()} capability in-house from scratch.`,
  () => `Compliance and audit demands are outpacing what the current stack can track.`,
  () => `Onboarding new customers is a manual, multi-day process that doesn't scale.`,
  () => `Support and ops teams are duplicating work across spreadsheets and point tools.`,
];

const NEED_PHRASES = [
  (tech) => `Evaluating ${tech} vendors to automate the workflow end-to-end.`,
  (tech) => `Looking for a partner to design and ship a ${tech} proof of concept quickly.`,
  (tech) => `Needs a production-ready ${tech} integration, not another internal prototype.`,
  (tech) => `Wants to pair ${tech} with existing systems without a full platform rebuild.`,
  (tech) => `Searching for engineering support to take a ${tech} pilot into production.`,
  (tech) => `Requires a partner who can move fast on ${tech} without a lengthy procurement cycle.`,
  (tech) => `Open to build-vs-buy guidance on ${tech} before committing internal resources.`,
  (tech) => `Needs ${tech} expertise to unblock a stalled internal initiative.`,
];

function buildSnippet(sourceId, company, industry, tech) {
  const ind = industry.toLowerCase();
  switch (sourceId) {
    case "reddit":
      return `We're a ${ind} company and honestly the manual ${tech.toLowerCase()} work is killing our team's velocity. Anyone solved this well before we hire full-time for it?`;
    case "hackernews":
      return `Curious if anyone has shipped a ${tech.toLowerCase()} project like this in production for a ${ind} use case — we keep hitting scaling walls in-house.`;
    case "x":
      return `${company} is buried in manual busywork this quarter. If your team has cracked ${tech.toLowerCase()} automation, we'd love to compare notes.`;
    case "indiehackers":
      return `Building in ${ind}. Been putting off our ${tech.toLowerCase()} integration for months — might finally be time to bring in outside help.`;
    case "github":
      return `Issue opened on internal tooling repo: "Need ${tech} integration — current workaround doesn't hold up past pilot usage."`;
    case "stackoverflow":
      return `How do I connect our ${ind} platform to a ${tech.toLowerCase()} pipeline without rebuilding our entire backend?`;
    case "producthunt":
      return `Launching soon and already scoping our ${tech.toLowerCase()} roadmap — open to recommendations from teams who've been through this.`;
    case "jobboards":
      return `${company} posted a new role centered on ${tech} — signals active internal investment and a likely near-term need for outside delivery support.`;
    case "tedeu":
      return `Tender notice: ${company} seeks a qualified vendor to deliver a ${tech} modernization initiative under a public digital transformation programme.`;
    default:
      return `${company} shared a signal referencing ${tech}.`;
  }
}

function sourceUrl(sourceId, company, seedInt) {
  const slug = company.toLowerCase().replace(/[^a-z0-9]+/g, "-");
  switch (sourceId) {
    case "reddit": return `https://reddit.com/r/b2bsaas/comments/${seedInt}/${slug}`;
    case "hackernews": return `https://news.ycombinator.com/item?id=${38000000 + seedInt}`;
    case "x": return `https://x.com/${slug}/status/${1700000000000 + seedInt}`;
    case "indiehackers": return `https://indiehackers.com/post/${slug}-${seedInt}`;
    case "github": return `https://github.com/${slug}/internal-tools/issues/${seedInt % 400}`;
    case "stackoverflow": return `https://stackoverflow.com/questions/${77000000 + seedInt}`;
    case "producthunt": return `https://producthunt.com/posts/${slug}`;
    case "jobboards": return `https://jobs.lever.co/${slug}/${seedInt}`;
    case "tedeu": return `https://ted.europa.eu/notice/${seedInt}-2026`;
    default: return "#";
  }
}

function tier(score) {
  if (score >= 85) return "HOT";
  if (score >= 70) return "HIGH";
  if (score >= 50) return "MEDIUM";
  return "LOW";
}
const TIER_COLOR = { HOT: "#D6483F", HIGH: "#E08A2A", MEDIUM: "#2C7DA0", LOW: "#8B95A5" };
const TIER_BG = { HOT: "#FBEAE8", HIGH: "#FDF1E3", MEDIUM: "#E9F1F8", LOW: "#EEF0F3" };

function fmtDate(d) {
  const dateObj = typeof d === 'string' ? new Date(d) : d;
  return dateObj.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

const CONTACT_FIRST_NAMES = [
  "Ava", "Liam", "Noah", "Emma", "Olivia", "Ethan", "Mia", "Lucas", "Sophia", "Mason",
  "Isabella", "Logan", "Amelia", "Elijah", "Harper", "James", "Charlotte", "Benjamin", "Grace", "Henry",
];
const CONTACT_LAST_NAMES = [
  "Smith", "Johnson", "Brown", "Garcia", "Miller", "Davis", "Wilson", "Martinez", "Taylor", "Anderson",
  "Thomas", "Moore", "Jackson", "White", "Harris", "Clark", "Lewis", "Young", "Walker", "Hall",
];

function companyDomain(name) {
  return name.toLowerCase().replace(/[^a-z0-9\s]/g, "").trim().replace(/\s+/g, "") + ".com";
}

// Deterministic per-lead email, generated from an independent RNG stream keyed on
// lead index so it never shifts the existing lead-generation sequence/values.
function emailForLead(company, index) {
  const localRand = mulberry32(index * 7919 + 13);
  if (localRand() < 0.08) return null; // some leads intentionally have no known contact
  const first = pick(CONTACT_FIRST_NAMES, localRand);
  const last = pick(CONTACT_LAST_NAMES, localRand);
  return `${first.toLowerCase()}.${last.toLowerCase()}@${companyDomain(company)}`;
}

function generateLeads() {
  const rand = mulberry32(88221);
  // weighted company picks: everyone once, then extra picks skewed to the first 14
  const picks = [...COMPANIES];
  for (let i = 0; i < 30; i++) {
    const idx = Math.floor(Math.pow(rand(), 1.6) * 14);
    picks.push(COMPANIES[idx]);
  }
  const leads = picks.map((c, i) => {
    const source = pick(SOURCES, rand);
    const bias = SOURCE_SIGNAL_BIAS[source.id];
    const signalType = rand() < 0.85 ? pick(bias, rand) : pick(SIGNAL_TYPES, rand);
    const tech = pick(TECHNOLOGIES, rand);
    let score = Math.round(30 + Math.pow(rand(), 1.5) * 68);
    if (rand() < 0.18) score = 85 + Math.round(rand() * 14);
    score = Math.min(99, score);
    const painFn = pick(PAIN_PHRASES, rand);
    const needFn = pick(NEED_PHRASES, rand);
    const businessPain = painFn(c.industry, tech);
    const detectedNeed = needFn(tech);
    let daysAgo = Math.floor(rand() * 45);
    if (i < 4) daysAgo = 0; // guarantee "new today"
    const date = new Date(REF_DATE);
    date.setDate(date.getDate() - daysAgo);
    const t = tier(score);
    const aiSummary = `${c.name} is showing a ${t.toLowerCase()}-intent signal around ${tech}. ${businessPain} ${detectedNeed} The pattern reads as active evaluation rather than casual interest.`;
    return {
      id: `LEAD-${1000 + i}`,
      company: c.name,
      industry: c.industry,
      country: c.country,
      source: source.id,
      signalType,
      technology: tech,
      businessPain,
      detectedNeed,
      intentScore: score,
      tierLabel: t,
      aiSummary,
      iosysService: IOSYS_BY_TECH[tech],
      publishedDate: date,
      daysAgo,
      status: pick(STATUSES, rand),
      originalSnippet: buildSnippet(source.id, c.name, c.industry, tech),
      originalUrl: sourceUrl(source.id, c.name, 4200 + i * 37),
      explicitRequirement: ["Explicit Ask", "RFP / Tender", "Integration Request"].includes(signalType),
      recentSignal: daysAgo <= 14,
      contactEmail: emailForLead(c.name, i),
    };
  });
  return leads;
}

/* ---------------------------- small components ---------------------------- */

function SignalBars({ score, size = "md" }) {
  const level = Math.min(4, Math.max(1, Math.ceil(score / 25)));
  const color = TIER_COLOR[tier(score)];
  const h = size === "sm" ? [4, 7, 10, 13] : [5, 9, 13, 17];
  const w = size === "sm" ? 3 : 4;
  const gap = size === "sm" ? 2 : 3;
  const totalH = h[3];
  return (
    <svg width={(w + gap) * 4} height={totalH} viewBox={`0 0 ${(w + gap) * 4} ${totalH}`} style={{ display: "block" }}>
      {h.map((barH, i) => (
        <rect
          key={i}
          x={i * (w + gap)}
          y={totalH - barH}
          width={w}
          height={barH}
          rx={1}
          fill={i < level ? color : "#DCE1E8"}
        />
      ))}
    </svg>
  );
}

function IntentCell({ score, breakdown }) {
  const [open, setOpen] = useState(false);
  const t = tier(score);

  useEffect(() => {
    if (!open) return;
    const close = () => setOpen(false);
    window.addEventListener('click', close);
    window.addEventListener('close-intent-tooltips', close);
    return () => {
      window.removeEventListener('click', close);
      window.removeEventListener('close-intent-tooltips', close);
    };
  }, [open]);

  return (
    <div 
      style={{ display: "inline-flex", alignItems: "center", gap: 8, cursor: breakdown?.length ? "pointer" : "default", position: "relative", zIndex: open ? 99 : 1 }}
      onClick={(e) => {
        if (!breakdown?.length) return;
        e.stopPropagation();
        if (!open) {
          window.dispatchEvent(new Event('close-intent-tooltips'));
          setOpen(true);
        } else {
          setOpen(false);
        }
      }}
    >
      <SignalBars score={score} size="sm" />
      <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600, fontSize: 13, color: TIER_COLOR[t] }}>
        {score}
      </span>
      {open && breakdown && breakdown.length > 0 && (
        <div style={{
          position: "absolute", top: "100%", left: 0, marginTop: 8, zIndex: 9999,
          background: "var(--surface)", color: "var(--ink)", padding: 12, borderRadius: 6,
          boxShadow: "0 8px 32px rgba(0,0,0,0.12)", width: 260, border: "1px solid var(--line)",
          fontFamily: "var(--font-body)", fontSize: 13, display: "flex", flexDirection: "column", gap: 6,
          textAlign: "left"
        }}>
          <div style={{ fontWeight: 600, color: "var(--ink)", marginBottom: 4, borderBottom: "1px solid var(--line)", paddingBottom: 6 }}>Score Breakdown</div>
          {breakdown.map((reason, i) => (
            <div key={i} style={{ display: "flex", gap: 6, alignItems: "flex-start" }}>
              <span style={{ color: reason.startsWith("+") ? "var(--accent-teal)" : reason.startsWith("-") ? "var(--accent-rose)" : "var(--ink-soft)" }}>•</span>
              <span style={{ lineHeight: 1.4 }}>{reason}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function TierBadge({ score }) {
  const t = tier(score);
  return (
    <span
      style={{
        display: "inline-flex", alignItems: "center", gap: 6, padding: "3px 9px",
        borderRadius: 3, fontFamily: "var(--font-mono)", fontSize: 11, fontWeight: 600,
        letterSpacing: "0.04em", color: TIER_COLOR[t], background: TIER_BG[t],
        border: `1px solid ${TIER_COLOR[t]}33`,
      }}
    >
      {t === "HOT" && "\u2726 "}{t}
    </span>
  );
}

function SourceTag({ id }) {
  if (!id) return null;
  const source = SOURCE_MAP[id] || { tag: id.toUpperCase().slice(0, 4) };
  return (
    <span
      style={{
        fontSize: 11, fontWeight: 700, borderRadius: 4, letterSpacing: "0.02em", color: "var(--accent-teal)",
        padding: "2px 6px", background: "var(--surface-2)", whiteSpace: "nowrap",
      }}
    >
      {source.tag}
    </span>
  );
}

/* ------- recognizable per-source icon marks, used only in the Signal Sources carousel ------- */

function SourceIcon({ id, size = 18 }) {
  switch (id) {
    case "reddit":
      return (
        <svg width={size} height={size} viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="12" fill="#FF4500" />
          <circle cx="8.7" cy="13.3" r="1.5" fill="#fff" />
          <circle cx="15.3" cy="13.3" r="1.5" fill="#fff" />
          <path d="M8.2 16.1c.95.72 2.2 1.1 3.8 1.1s2.85-.38 3.8-1.1" stroke="#fff" strokeWidth="1.1" strokeLinecap="round" fill="none" />
          <path d="M12 10.2V6.9c0-.55.45-1 1-1 .38 0 .73.22.9.55" stroke="#fff" strokeWidth="1" strokeLinecap="round" fill="none" />
          <circle cx="14.9" cy="6" r="1" fill="#fff" />
          <circle cx="17.4" cy="10.1" r="1.35" fill="#fff" stroke="#FF4500" strokeWidth="0.3" />
        </svg>
      );
    case "hackernews":
      return (
        <svg width={size} height={size} viewBox="0 0 24 24">
          <rect width="24" height="24" rx="4" fill="#FF6600" />
          <text x="12" y="16.5" textAnchor="middle" fontFamily="Georgia, serif" fontWeight="700" fontSize="12" fill="#111">Y</text>
        </svg>
      );
    case "x":
      return (
        <svg width={size} height={size} viewBox="0 0 24 24">
          <rect width="24" height="24" rx="5" fill="#000" />
          <path d="M6.2 6.2l11.6 11.6M17.8 6.2L6.2 17.8" stroke="#fff" strokeWidth="1.6" strokeLinecap="round" />
        </svg>
      );
    case "indiehackers":
      return (
        <svg width={size} height={size} viewBox="0 0 24 24">
          <rect width="24" height="24" rx="4" fill="#0E2439" />
          <text x="12" y="16" textAnchor="middle" fontFamily="var(--font-mono), monospace" fontWeight="700" fontSize="9.5" fill="#fff">IH</text>
        </svg>
      );
    case "github":
      return (
        <svg width={size} height={size} viewBox="0 0 16 16">
          <path
            fill="#181717"
            d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"
          />
        </svg>
      );
    case "stackoverflow":
      return (
        <svg width={size} height={size} viewBox="0 0 24 24">
          <rect width="24" height="24" rx="4" fill="#F58025" />
          <g fill="#fff">
            <rect x="6" y="15.2" width="12" height="1.6" />
            <rect x="6.6" y="12.4" width="10.6" height="1.5" transform="rotate(-6 6.6 12.4)" />
            <rect x="7" y="9.6" width="10" height="1.5" transform="rotate(-13 7 9.6)" />
            <rect x="7.6" y="6.6" width="9" height="1.5" transform="rotate(-22 7.6 6.6)" />
          </g>
        </svg>
      );
    case "producthunt":
      return (
        <svg width={size} height={size} viewBox="0 0 24 24">
          <rect width="24" height="24" rx="5" fill="#DA552F" />
          <text x="11.6" y="16.5" textAnchor="middle" fontFamily="var(--font-display), sans-serif" fontWeight="700" fontSize="13" fill="#fff">P</text>
        </svg>
      );
    case "jobboards":
      return (
        <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
          <rect width="24" height="24" rx="4" fill="var(--surface-2)" />
          <rect x="6" y="9.3" width="12" height="8" rx="1.3" stroke="var(--ink-soft)" strokeWidth="1.3" />
          <path d="M9.3 9.3V7.7a1.3 1.3 0 011.3-1.3h2.8a1.3 1.3 0 011.3 1.3v1.6" stroke="var(--ink-soft)" strokeWidth="1.3" />
          <line x1="6" y1="13" x2="18" y2="13" stroke="var(--ink-soft)" strokeWidth="1.3" />
        </svg>
      );
    case "tedeu":
      return (
        <svg width={size} height={size} viewBox="0 0 24 24">
          <rect width="24" height="24" rx="4" fill="#E62B1E" />
          <text x="12" y="15.5" textAnchor="middle" fontFamily="var(--font-display), sans-serif" fontWeight="700" fontSize="8.5" fill="#fff" letterSpacing="0.3">TED</text>
        </svg>
      );
    case "startup_networks":
      return (
        <svg width={size} height={size} viewBox="0 0 24 24">
          <rect width="24" height="24" rx="4" fill="#6B46C1" />
          <text x="12" y="15.5" textAnchor="middle" fontFamily="var(--font-mono), monospace" fontWeight="700" fontSize="9.5" fill="#fff">SN</text>
        </svg>
      );
    case "uk_business_forums":
      return (
        <svg width={size} height={size} viewBox="0 0 24 24">
          <rect width="24" height="24" rx="4" fill="#00247D" />
          <text x="12" y="15.5" textAnchor="middle" fontFamily="var(--font-mono), monospace" fontWeight="700" fontSize="8" fill="#fff">UKBF</text>
        </svg>
      );
    case "bubble_forum":
      return (
        <svg width={size} height={size} viewBox="0 0 24 24">
          <rect width="24" height="24" rx="4" fill="#1841FA" />
          <text x="12" y="15.5" textAnchor="middle" fontFamily="var(--font-mono), monospace" fontWeight="700" fontSize="8" fill="#fff">BUB</text>
        </svg>
      );
    case "remote_ok":
      return (
        <svg width={size} height={size} viewBox="0 0 24 24">
          <rect width="24" height="24" rx="4" fill="#FF4742" />
          <text x="12" y="15.5" textAnchor="middle" fontFamily="var(--font-mono), monospace" fontWeight="700" fontSize="8" fill="#fff">ROK</text>
        </svg>
      );
    case "uk_contracts_finder":
      return (
        <svg width={size} height={size} viewBox="0 0 24 24">
          <rect width="24" height="24" rx="4" fill="#005EA5" />
          <text x="12" y="15.5" textAnchor="middle" fontFamily="var(--font-mono), monospace" fontWeight="700" fontSize="8" fill="#fff">UKCF</text>
        </svg>
      );
    case "reddit":
      return (
        <svg width={size} height={size} viewBox="0 0 24 24">
          <rect width="24" height="24" rx="4" fill="#FF4500" />
          <text x="12" y="15.5" textAnchor="middle" fontFamily="var(--font-mono), monospace" fontWeight="700" fontSize="8" fill="#fff">RDT</text>
        </svg>
      );
    default:
      return null;
  }
}

function SourceLogoBadge({ id, size = 26 }) {
  return (
    <span
      style={{
        display: "inline-flex", alignItems: "center", justifyContent: "center",
        width: size, height: size, borderRadius: 6, overflow: "hidden",
        border: "1px solid var(--line)", flexShrink: 0,
      }}
    >
      <SourceIcon id={id} size={size - 2} />
    </span>
  );
}

/* ------- vertical, up/down-navigable slider for the Signal Sources cards (keeps the responsive grid) ------- */

function SourceCardsVerticalSlider({ children, visibleRows = 2 }) {
  const trackRef = useRef(null);
  const [canUp, setCanUp] = useState(false);
  const [canDown, setCanDown] = useState(false);
  const [maxHeight, setMaxHeight] = useState(null);
  const gap = 10;

  const rowHeight = () => {
    const firstCard = trackRef.current && trackRef.current.querySelector("[data-src-card]");
    return firstCard ? firstCard.getBoundingClientRect().height : 100;
  };

  const measure = () => {
    const el = trackRef.current;
    if (!el) return;
    const h = rowHeight();
    setMaxHeight(visibleRows * h + (visibleRows - 1) * gap);
    setCanUp(el.scrollTop > 4);
    setCanDown(el.scrollTop + el.clientHeight < el.scrollHeight - 4);
  };

  useEffect(() => {
    measure();
    const el = trackRef.current;
    if (!el) return;
    const onScroll = () => {
      setCanUp(el.scrollTop > 4);
      setCanDown(el.scrollTop + el.clientHeight < el.scrollHeight - 4);
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", measure);
    return () => {
      el.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", measure);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [children]);

  const scrollByRow = (dir) => {
    const el = trackRef.current;
    if (!el) return;
    el.scrollBy({ top: dir * (rowHeight() + gap), behavior: "smooth" });
  };

  const arrowBtnStyle = (enabled) => ({
    width: 28, height: 20, borderRadius: 5, border: "1px solid var(--line)",
    background: "var(--surface)", display: "flex", alignItems: "center", justifyContent: "center",
    cursor: enabled ? "pointer" : "default", opacity: enabled ? 1 : 0.25,
    pointerEvents: enabled ? "auto" : "none", boxShadow: "0 1px 3px rgba(16,21,31,0.08)",
    transition: "opacity 120ms ease",
  });

  return (
    <div style={{ marginBottom: 26 }}>
      <div style={{ display: "flex", justifyContent: "center", marginBottom: 6 }}>
        <button aria-label="Show previous sources" onClick={() => scrollByRow(-1)} style={arrowBtnStyle(canUp)}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M5 15l7-7 7 7" stroke="var(--ink)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </button>
      </div>
      <div
        ref={trackRef}
        style={{
          display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(190px, 1fr))", gap,
          overflowY: "auto", scrollSnapType: "y proximity", scrollBehavior: "smooth",
          maxHeight: maxHeight || "none",
        }}
      >
        {React.Children.map(children, (child) => (
          <div data-src-card style={{ scrollSnapAlign: "start" }}>{child}</div>
        ))}
      </div>
      <div style={{ display: "flex", justifyContent: "center", marginTop: 6 }}>
        <button aria-label="Show more sources" onClick={() => scrollByRow(1)} style={arrowBtnStyle(canDown)}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M5 9l7 7 7-7" stroke="var(--ink)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </button>
      </div>
    </div>
  );
}

function Chip({ label, onRemove }) {
  return (
    <span
      style={{
        display: "inline-flex", alignItems: "center", gap: 6, padding: "4px 8px 4px 10px",
        borderRadius: 20, background: "var(--chrome)", color: "#fff", fontSize: 12,
        fontWeight: 500, fontFamily: "var(--font-body)",
      }}
    >
      {label}
      <span onClick={onRemove} style={{ cursor: "pointer", opacity: 0.65, fontSize: 13, lineHeight: 1 }}>×</span>
    </span>
  );
}

function StatCard({ label, value, accent }) {
  return (
    <div style={{
      background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 6,
      padding: "16px 18px", flex: 1, minWidth: 140,
    }}>
      <div style={{ fontSize: 11.5, color: "var(--ink-soft)", fontWeight: 600, letterSpacing: "0.03em", textTransform: "uppercase" }}>{label}</div>
      <div style={{ fontFamily: "var(--font-display)", fontSize: 30, fontWeight: 700, color: accent || "var(--ink)", marginTop: 6 }}>{value}</div>
    </div>
  );
}

function SectionTitle({ eyebrow, title, right }) {
  return (
    <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", marginBottom: 12 }}>
      <div>
        {eyebrow && <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.08em", color: "var(--accent-teal)", fontWeight: 600, marginBottom: 3 }}>{eyebrow}</div>}
        <div style={{ fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 700, color: "var(--ink)" }}>{title}</div>
      </div>
      {right}
    </div>
  );
}

function LinkBtn({ children, onClick, style }) {
  return (
    <button onClick={onClick} style={{
      background: "none", border: "none", color: "var(--accent-teal)", fontSize: 12.5,
      fontWeight: 600, cursor: "pointer", padding: 0, fontFamily: "var(--font-body)", ...style,
    }}>{children}</button>
  );
}

/* ---------------------------- lead table (shared) ---------------------------- */

function LeadTable({ leads, onOpen, showStatus = true, dense = false, showContact = false }) {
  if (leads.length === 0) {
    return (
      <div style={{ padding: "40px 20px", textAlign: "center", color: "var(--ink-soft)", fontSize: 13.5, border: "1px dashed var(--line)", borderRadius: 6 }}>
        No signals match these filters. Loosen a filter to widen the search.
      </div>
    );
  }
  return (
    <div style={{ border: "1px solid var(--line)", borderRadius: 6, overflow: "hidden", background: "var(--surface)" }}>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "var(--surface-2)", borderBottom: "1px solid var(--line)" }}>
              {["Intent", "Priority", "Author", "Company", "Industry", "Source", "Signal Type", "Technology", !dense && "Business Pain", "AI Summary", "Date"]
                .filter(Boolean)
                .map((h) => (
                  <th key={h} style={{ textAlign: "left", padding: "9px 14px", fontWeight: 600, fontSize: 11, letterSpacing: "0.03em", textTransform: "uppercase", color: "var(--ink-soft)", whiteSpace: "nowrap" }}>{h}</th>
                ))}
            </tr>
          </thead>
          <tbody>
            {leads.map((l) => (
              <tr
                key={l.id}
                onClick={() => onOpen(l.id)}
                style={{ borderBottom: "1px solid var(--line)", cursor: "pointer" }}
                onMouseEnter={(e) => (e.currentTarget.style.background = "var(--surface-2)")}
                onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
              >
                <td style={{ padding: "10px 14px" }}><IntentCell score={l.intentScore} breakdown={l.scoreBreakdown} /></td>
                <td style={{ padding: "10px 14px" }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: l.tierLabel === "HOT" ? TIER_COLOR.HOT : (l.tierLabel === "HIGH" ? TIER_COLOR.HIGH : (l.tierLabel === "LOW" ? TIER_COLOR.LOW : TIER_COLOR.MEDIUM)) }}>{l.tierLabel}</span>
                </td>
                <td style={{ padding: "10px 14px", fontWeight: 600, color: "var(--ink)" }}>{l.author}</td>
                <td style={{ padding: "10px 14px", fontWeight: 600, color: "var(--ink-soft)" }}>
                  {l.company} 
                  {l.company !== "Unknown" && <span style={{ fontSize: 10, color: "var(--line)", marginLeft: 4 }}>{l.companyConfidence || 0}%</span>}
                  {l.isNew && <span style={{ fontSize: 10, color: "var(--accent-teal)", marginLeft: 6, fontWeight: 700, padding: "2px 4px", background: "#0E7C861A", borderRadius: 3 }}>NEW</span>}
                </td>
                <td style={{ padding: "10px 14px", color: "var(--ink-soft)" }}>{l.industry}</td>
                <td style={{ padding: "10px 14px" }}><SourceTag id={l.source} /></td>
                <td style={{ padding: "10px 14px", color: "var(--ink-soft)", whiteSpace: "nowrap" }}>{l.signalType}</td>
                <td style={{ padding: "10px 14px" }}>
                  <span style={{ fontSize: 11.5, fontWeight: 600, color: "var(--accent-teal)", background: "#0E7C860F", border: "1px solid #0E7C8633", padding: "2px 7px", borderRadius: 3 }}>{l.technology}</span>
                </td>
                {!dense && <td style={{ padding: "10px 14px", color: "var(--ink-soft)", maxWidth: 180 }}>{l.businessPain}</td>}
                <td style={{ padding: "10px 14px", color: "var(--ink-soft)", maxWidth: 220 }}>{(l.aiSummary && l.aiSummary !== "Unable to summarize." ? l.aiSummary : l.originalSnippet || "").slice(0, 92)}...</td>
                <td style={{ padding: "10px 14px", color: "var(--ink-soft)", whiteSpace: "nowrap", fontFamily: "var(--font-mono)", fontSize: 12 }}>{fmtDate(l.publishedDate)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ---------------------------- filter bar (Leads page) ---------------------------- */

function FilterBar({ filters, setFilters }) {
  const set = (k, v) => setFilters((f) => ({ ...f, [k]: v }));
  const input = { padding: "7px 10px", border: "1px solid var(--line)", borderRadius: 5, fontSize: 12.5, fontFamily: "var(--font-body)", background: "var(--surface)", color: "var(--ink)" };
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
      <input placeholder="Search company or keyword…" value={filters.search} onChange={(e) => set("search", e.target.value)} style={{ ...input, flex: "1 1 220px", minWidth: 180 }} />
      <select value={filters.source} onChange={(e) => set("source", e.target.value)} style={input}>
        <option value="">All Sources</option>
        {SOURCES.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
      </select>
      <select value={filters.industry} onChange={(e) => set("industry", e.target.value)} style={input}>
        <option value="">All Industries</option>
        {INDUSTRIES.map((i) => <option key={i} value={i}>{i}</option>)}
      </select>
      <select value={filters.country} onChange={(e) => set("country", e.target.value)} style={input}>
        <option value="">All Regions</option>
        {COUNTRIES.map((c) => <option key={c} value={c}>{c}</option>)}
      </select>
      <select value={filters.technology} onChange={(e) => set("technology", e.target.value)} style={input}>
        <option value="">All Technology</option>
        {TECHNOLOGIES.map((t) => <option key={t} value={t}>{t}</option>)}
      </select>
      <select value={filters.signalType} onChange={(e) => set("signalType", e.target.value)} style={input}>
        <option value="">All Signal Types</option>
        {SIGNAL_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
      </select>
      <select value={filters.tierLevel} onChange={(e) => set("tierLevel", e.target.value)} style={input}>
        <option value="HOT">🔥 Direct Opportunity</option>
        <option value="EARLY">🟡 Early Signal</option>
        <option value="NOISE">⚪ Technical Noise</option>
        <option value="ALL">All Signals</option>
      </select>
      <select value={filters.sort} onChange={(e) => set("sort", e.target.value)} style={input}>
        <option value="intent">Sort: Highest Intent</option>
        <option value="intentAsc">Sort: Lowest Intent</option>
        <option value="companyAsc">Sort: Company A → Z</option>
        <option value="companyDesc">Sort: Company Z → A</option>
        <option value="newest">Sort: Newest</option>
        <option value="hot">Sort: Hot Leads First</option>
      </select>
    </div>
  );
}

function activeChips(filters, setFilters) {
  const chips = [];
  const clear = (k, v) => setFilters((f) => ({ ...f, [k]: v }));
  if (filters.search) chips.push({ label: `"${filters.search}"`, onRemove: () => clear("search", "") });
  if (filters.source) chips.push({ label: SOURCE_MAP[filters.source]?.name, onRemove: () => clear("source", "") });
  if (filters.industry) chips.push({ label: filters.industry, onRemove: () => clear("industry", "") });
  if (filters.country) chips.push({ label: filters.country, onRemove: () => clear("country", "") });
  if (filters.technology) chips.push({ label: filters.technology, onRemove: () => clear("technology", "") });
  if (filters.signalType) chips.push({ label: filters.signalType, onRemove: () => clear("signalType", "") });
  if (filters.tierLevel) chips.push({ label: filters.tierLevel, onRemove: () => clear("tierLevel", "") });
  return chips;
}

function applyFilters(leads, filters) {
  let out = leads.filter((l) => {
    if (filters.search && !(`${l.company} ${l.businessPain} ${l.detectedNeed} ${l.aiSummary} ${l.originalSnippet}`.toLowerCase().includes(filters.search.toLowerCase()))) return false;
    if (filters.source && l.source !== filters.source) return false;
    if (filters.industry && l.industry !== filters.industry) return false;
    if (filters.country && l.country !== filters.country) return false;
    if (filters.technology && l.technology !== filters.technology) return false;
    if (filters.signalType && l.signalType !== filters.signalType) return false;
    
    if (filters.tierLevel === "HOT" && l.tierLabel !== "HOT") return false;
    if (filters.tierLevel === "EARLY" && l.tierLabel !== "HIGH" && l.tierLabel !== "MEDIUM") return false;
    if (filters.tierLevel === "NOISE" && l.tierLabel !== "LOW") return false;
    
    return true;
  });
  if (filters.sort === "newest") out = [...out].sort((a, b) => a.daysAgo - b.daysAgo);
  else if (filters.sort === "hot") out = [...out].sort((a, b) => (b.intentScore >= 85) - (a.intentScore >= 85) || b.intentScore - a.intentScore);
  else if (filters.sort === "intentAsc") out = [...out].sort((a, b) => a.intentScore - b.intentScore);
  else if (filters.sort === "companyAsc") out = [...out].sort((a, b) => a.company.toLowerCase().localeCompare(b.company.toLowerCase()));
  else if (filters.sort === "companyDesc") out = [...out].sort((a, b) => b.company.toLowerCase().localeCompare(a.company.toLowerCase()));
  else out = [...out].sort((a, b) => b.intentScore - a.intentScore);
  return out;
}

function exportToCSV(leads, filename = "leads_export") {
  if (!leads || !leads.length) return;
  const headers = ["ID", "Company", "Title", "Content Snippet", "Source", "Intent Score", "Signal Type", "Technology", "iOSYS Opportunity", "Date", "URL"];
  const rows = leads.map(l => [
    l.id,
    l.company,
    l.title,
    l.content ? l.content.substring(0, 250) : "",
    l.source,
    l.intentScore,
    l.signalType,
    l.technology,
    l.iosysService || "Not detected",
    l.publishedDate,
    l.originalUrl
  ].map(v => `"${String(v || "").replace(/"/g, '""')}"`).join(","));
  
  const csvContent = headers.join(",") + "\n" + rows.join("\n");
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", `${filename}_${new Date().getTime()}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/* ---------------------------- Page: Overview ---------------------------- */

function OverviewPage({ leads, nav, backendStats }) {
  const [srcFilter, setSrcFilter] = useState(null);
  const [indFilter, setIndFilter] = useState(null);

  // Render the Quality Summary banner if backend stats are provided
  const renderQualitySummary = () => {
    if (!backendStats || !backendStats.github) return null;
    const { total, qualified, hot, early, noise } = backendStats.github;
    return (
      <div style={{ marginBottom: 24, padding: "16px 20px", background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 6, display: "flex", gap: 24, alignItems: "center" }}>
        <div style={{ fontWeight: 600, color: "var(--ink)", fontSize: 14 }}>GitHub Intelligence Pipeline:</div>
        <div style={{ display: "flex", gap: 20, fontSize: 13 }}>
          <div><span style={{ color: "var(--ink-soft)" }}>Total Signals:</span> <span style={{ fontWeight: 600 }}>{total.toLocaleString()}</span></div>
          <div style={{ color: "var(--line)" }}>|</div>
          <div><span style={{ color: "var(--ink-soft)" }}>Filtered Noise:</span> <span style={{ fontWeight: 600, color: "var(--ink-soft)" }}>{noise.toLocaleString()}</span></div>
          <div style={{ color: "var(--line)" }}>|</div>
          <div><span style={{ color: "var(--ink-soft)" }}>Qualified Leads:</span> <span style={{ fontWeight: 600, color: "var(--accent-teal)" }}>{qualified.toLocaleString()}</span></div>
          <div style={{ color: "var(--line)" }}>|</div>
          <div><span style={{ color: "var(--ink-soft)" }}>🔥 Hot:</span> <span style={{ fontWeight: 600, color: TIER_COLOR.HOT }}>{hot.toLocaleString()}</span></div>
          <div style={{ color: "var(--line)" }}>|</div>
          <div><span style={{ color: "var(--ink-soft)" }}>🟡 Early:</span> <span style={{ fontWeight: 600, color: TIER_COLOR.HIGH }}>{early.toLocaleString()}</span></div>
        </div>
      </div>
    );
  };

  const total = leads.length;
  const hot = leads.filter((l) => l.intentScore >= 85).length;
  const high = leads.filter((l) => l.intentScore >= 70).length;
  const newToday = leads.filter((l) => l.daysAgo === 0).length;
  const companies = new Set(leads.map((l) => l.company)).size;

  const sourceStats = SOURCES.map((s) => {
    const sl = leads.filter((l) => l.source === s.id);
    const avgIntent = sl.length ? Math.round(sl.reduce((a, b) => a + b.intentScore, 0) / sl.length) : 0;
    return { ...s, count: sl.length, hot: sl.filter((l) => l.intentScore >= 85).length, avgIntent };
  });

  const industryStats = INDUSTRIES.map((ind) => ({
    industry: ind,
    count: leads.filter((l) => l.industry === ind).length,
  })).sort((a, b) => b.count - a.count);

  let shown = leads;
  if (srcFilter) shown = shown.filter((l) => l.source === srcFilter);
  if (indFilter) shown = shown.filter((l) => l.industry === indFilter);
  const hotLeads = [...shown].sort((a, b) => b.intentScore - a.intentScore).slice(0, 10);

  return (
    <div>
      {renderQualitySummary()}
      <div style={{ display: "flex", gap: 12, marginBottom: 22, flexWrap: "wrap" }}>
        <StatCard label="Total Signals" value={total} />
        <StatCard label="Hot Leads" value={hot} accent={TIER_COLOR.HOT} />
        <StatCard label="High Intent" value={high} accent={TIER_COLOR.HIGH} />
        <StatCard label="New Today" value={newToday} accent="var(--accent-teal)" />
        <StatCard label="Companies" value={companies} />
      </div>

      <SectionTitle eyebrow="Collection Sources" title="Signal Sources" />
      <SourceCardsVerticalSlider>
        {sourceStats.map((s) => {
          const active = srcFilter === s.id;
          return (
            <div
              key={s.id}
              onClick={() => setSrcFilter(active ? null : s.id)}
              style={{
                border: `1px solid ${active ? "var(--accent-teal)" : "var(--line)"}`,
                background: active ? "#0E7C860C" : "var(--surface)",
                borderRadius: 6, padding: "13px 14px", cursor: "pointer",
                boxShadow: active ? "0 0 0 1px var(--accent-teal) inset" : "none",
                height: "100%",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                <span style={{ fontWeight: 700, fontSize: 13.5, fontFamily: "var(--font-display)" }}>{s.name}</span>
                <SourceLogoBadge id={s.id} />
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11.5, color: "var(--ink-soft)" }}>
                <div><div style={{ fontFamily: "var(--font-mono)", fontSize: 16, fontWeight: 600, color: "var(--ink)" }}>{s.count}</div>Signals</div>
                <div><div style={{ fontFamily: "var(--font-mono)", fontSize: 16, fontWeight: 600, color: TIER_COLOR.HOT }}>{s.hot}</div>Hot</div>
                <div><div style={{ fontFamily: "var(--font-mono)", fontSize: 16, fontWeight: 600, color: "var(--ink)" }}>{s.avgIntent}</div>Avg Intent</div>
              </div>
            </div>
          );
        })}
      </SourceCardsVerticalSlider>

      <SectionTitle
        eyebrow={(srcFilter || indFilter) ? "Filtered" : "Priority Queue"}
        title="Hot Leads"
        right={<LinkBtn onClick={() => nav.toLeads({})}>View all in Leads →</LinkBtn>}
      />
      {(srcFilter || indFilter) && (
        <div style={{ display: "flex", gap: 6, marginBottom: 10 }}>
          {srcFilter && <Chip label={SOURCE_MAP[srcFilter]?.name} onRemove={() => setSrcFilter(null)} />}
          {indFilter && <Chip label={indFilter} onRemove={() => setIndFilter(null)} />}
        </div>
      )}
      <div style={{ marginBottom: 26 }}>
        <LeadTable leads={hotLeads} onOpen={nav.openLead} dense showStatus={false} />
      </div>

      <SectionTitle eyebrow="Where Demand Concentrates" title="Top Industries" />
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        {industryStats.map((i) => (
          <div
            key={i.industry}
            onClick={() => setIndFilter(indFilter === i.industry ? null : i.industry)}
            style={{
              border: `1px solid ${indFilter === i.industry ? "var(--accent-teal)" : "var(--line)"}`,
              borderRadius: 20, padding: "7px 14px", cursor: "pointer", display: "flex", alignItems: "center", gap: 8,
              background: indFilter === i.industry ? "#0E7C860C" : "var(--surface)",
            }}
          >
            <span style={{ fontSize: 12.5, fontWeight: 600 }}>{i.industry}</span>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 11.5, color: "var(--ink-soft)" }}>{i.count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------------------------- Page: Leads ---------------------------- */

function LeadsPage({ leads, filters, setFilters, nav, setLeads }) {
  const filtered = applyFilters(leads, filters);
  const chips = activeChips(filters, setFilters);
  const [nlQuery, setNlQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchStatus, setSearchStatus] = useState("");

  const handleNlSearch = async (e) => {
    e.preventDefault();
    if (!nlQuery.trim()) return;
    setSearching(true);
    setSearchStatus("Searching local database...");
    try {
      const response = await axios.post("http://127.0.0.1:8000/api/v1/leads/search", { query: nlQuery });
      if (response.data && response.data.filters) {
        setFilters({ ...filters, ...response.data.filters });
        
        // Live Fallback check
        const currentMatched = applyFilters(leads, { ...filters, ...response.data.filters });
        if (currentMatched.length < 5 && response.data.filters.live_search_keyword && response.data.filters.relevant_sources) {
           setSearchStatus("Searching live sources for more matching leads... (this may take a minute)");
           const fb = await axios.post("http://127.0.0.1:8000/api/v1/leads/live_fallback", { 
               keyword: response.data.filters.live_search_keyword, 
               sources: response.data.filters.relevant_sources 
           });
           if (fb.data && fb.data.newLeads && fb.data.newLeads.length > 0) {
               setLeads(prev => {
                   const existingIds = new Set(prev.map(l => l.id));
                   const fresh = fb.data.newLeads.filter(l => !existingIds.has(l.id));
                   return [...prev, ...fresh];
               });
           }
        }
        
        setNlQuery("");
      } else if (response.data && response.data.error) {
        alert("Search failed: " + response.data.error);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to connect to search API. Is the backend running on port 8000?");
    } finally {
      setSearching(false);
      setSearchStatus("");
    }
  };

  const viewBtnStyle = {
    background: "var(--surface)", border: "1px solid var(--line)", padding: "4px 10px", 
    borderRadius: 6, fontSize: 12, fontWeight: 600, color: "var(--ink-soft)", 
    cursor: "pointer", display: "flex", alignItems: "center", gap: 4
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 16 }}>
        <SectionTitle eyebrow={`${filtered.length} of ${leads.length} signals`} title="All Leads" />
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12 }}>
            <span style={{ fontSize: 11, fontWeight: 600, color: "var(--ink-soft)", marginRight: 4 }}>QUICK VIEWS:</span>
            <button onClick={() => setFilters({ ...emptyFilters(), tierLevel: "HOT" })} style={viewBtnStyle}>🔥 Hot</button>
            <button onClick={() => setFilters({ ...emptyFilters(), tierLevel: "HIGH" })} style={viewBtnStyle}>🟡 High</button>
            <button onClick={() => setFilters({ ...emptyFilters(), tierLevel: "EARLY" })} style={viewBtnStyle}>🔵 Early</button>
            <button onClick={() => setFilters({ ...emptyFilters(), signalType: "Pain Point Post" })} style={viewBtnStyle}>💔 Pain</button>
            
            <button 
            onClick={() => exportToCSV(filtered, "all_filtered_leads")}
            style={{
                background: "var(--surface)", border: "1px solid var(--line)", padding: "6px 14px", 
                borderRadius: 6, fontSize: 13, fontWeight: 600, color: "var(--ink)", 
                cursor: "pointer", display: "flex", alignItems: "center", gap: 6, boxShadow: "0 1px 2px rgba(0,0,0,0.05)", marginLeft: 12
            }}
            >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
            Export
            </button>
        </div>
      </div>
      
      <form onSubmit={handleNlSearch} style={{ display: "flex", gap: 8, marginBottom: searchStatus ? 8 : 16 }}>
        <input 
          placeholder="Ask AI: e.g. 'Find hot AI automation leads in the US'" 
          value={nlQuery} 
          onChange={(e) => setNlQuery(e.target.value)}
          style={{ flex: 1, padding: "10px 14px", border: "1px solid var(--line)", borderRadius: 6, fontSize: 14 }}
        />
        <button type="submit" disabled={searching} style={{ padding: "0 20px", background: "var(--accent-teal)", color: "#fff", border: "none", borderRadius: 6, fontWeight: 600, cursor: searching ? "not-allowed" : "pointer" }}>
            {searching ? "Searching..." : "Search"}
        </button>
      </form>
      
      {searchStatus && (
        <div style={{ fontSize: 12.5, color: "var(--accent-teal)", marginBottom: 16, display: "flex", alignItems: "center", gap: 8, fontWeight: 500 }}>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ animation: "spin 2s linear infinite" }}><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
          {searchStatus}
        </div>
      )}

      <FilterBar filters={filters} setFilters={setFilters} />
      {chips.length > 0 && (
        <div style={{ display: "flex", gap: 6, marginBottom: 14, flexWrap: "wrap" }}>
          {chips.map((c, i) => <Chip key={i} label={c.label} onRemove={c.onRemove} />)}
          <LinkBtn onClick={() => setFilters(nav.emptyFilters())} style={{ marginLeft: 4 }}>Clear all</LinkBtn>
        </div>
      )}
      <LeadTable leads={filtered} onOpen={nav.openLead} showContact />
    </div>
  );
}

/* ---------------------------- Page: Source Intelligence ---------------------------- */

function SourceIntelPage({ leads, activeSource, setActiveSource, nav }) {
  const sl = leads.filter((l) => l.source === activeSource);
  const total = sl.length;
  const hotN = sl.filter((l) => l.intentScore >= 85).length;
  const avg = total ? Math.round(sl.reduce((a, b) => a + b.intentScore, 0) / total) : 0;
  const direct = sl.filter((l) => l.explicitRequirement).length;

  const byIndustry = INDUSTRIES.map((i) => ({ label: i, count: sl.filter((l) => l.industry === i).length })).filter((x) => x.count).sort((a, b) => b.count - a.count);
  const byTech = TECHNOLOGIES.map((t) => ({ label: t, count: sl.filter((l) => l.technology === t).length })).filter((x) => x.count).sort((a, b) => b.count - a.count);
  const byType = [...new Set(sl.map((l) => l.signalType))].map((t) => ({ label: t, count: sl.filter((l) => l.signalType === t).length })).sort((a, b) => b.count - a.count);
  const dist = [
    { label: "Hot (85+)", count: sl.filter((l) => l.intentScore >= 85).length, color: TIER_COLOR.HOT },
    { label: "High (70–84)", count: sl.filter((l) => l.intentScore >= 70 && l.intentScore < 85).length, color: TIER_COLOR.HIGH },
    { label: "Medium (50–69)", count: sl.filter((l) => l.intentScore >= 50 && l.intentScore < 70).length, color: TIER_COLOR.MEDIUM },
    { label: "Low (<50)", count: sl.filter((l) => l.intentScore < 50).length, color: TIER_COLOR.LOW },
  ];
  const maxBar = Math.max(1, ...byIndustry.map((x) => x.count), ...byTech.map((x) => x.count));

  // source x industry matrix (all sources)
  const matrix = INDUSTRIES.map((ind) => ({
    industry: ind,
    cells: SOURCES.map((s) => leads.filter((l) => l.industry === ind && l.source === s.id).length),
  }));

  const Bar = ({ label, count, max, color }) => (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 3 }}>
        <span style={{ color: "var(--ink-soft)" }}>{label}</span>
        <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>{count}</span>
      </div>
      <div style={{ height: 6, background: "var(--surface-2)", borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${(count / max) * 100}%`, height: "100%", background: color || "var(--accent-teal)" }} />
      </div>
    </div>
  );

  return (
    <div>
      <SectionTitle eyebrow="Source Intelligence" title="Sources" />
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 22 }}>
        {SOURCES.map((s) => (
          <div
            key={s.id}
            onClick={() => setActiveSource(s.id)}
            style={{
              padding: "8px 14px", borderRadius: 20, cursor: "pointer", fontSize: 12.5, fontWeight: 600,
              border: `1px solid ${activeSource === s.id ? "var(--chrome)" : "var(--line)"}`,
              background: activeSource === s.id ? "var(--chrome)" : "var(--surface)",
              color: activeSource === s.id ? "#fff" : "var(--ink)",
            }}
          >
            {s.name}
          </div>
        ))}
      </div>

      <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.08em", color: "var(--accent-teal)", fontWeight: 600, marginBottom: 4 }}>
        {SOURCE_MAP[activeSource]?.name?.toUpperCase()} INTELLIGENCE
      </div>
      <div style={{ display: "flex", gap: 12, marginBottom: 24, flexWrap: "wrap" }}>
        <StatCard label="Total Signals" value={total} />
        <StatCard label="Hot Leads" value={hotN} accent={TIER_COLOR.HOT} />
        <StatCard label="Average Intent" value={avg} />
        <StatCard label="Direct Buying Signals" value={direct} accent="var(--accent-teal)" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 20, marginBottom: 28, alignItems: "start" }}>
        <div>
          <SectionTitle title={`${SOURCE_MAP[activeSource]?.name} Leads`} right={<LinkBtn onClick={() => nav.toLeads({ source: activeSource })}>Open in Leads →</LinkBtn>} />
          <LeadTable leads={[...sl].sort((a, b) => b.intentScore - a.intentScore).slice(0, 8)} onOpen={nav.openLead} dense showStatus={false} />
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <div style={{ border: "1px solid var(--line)", borderRadius: 6, padding: 16, background: "var(--surface)" }}>
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 10 }}>Top Industries</div>
            {byIndustry.length ? byIndustry.slice(0, 6).map((b) => <Bar key={b.label} {...b} max={maxBar} />) : <Empty />}
          </div>
          <div style={{ border: "1px solid var(--line)", borderRadius: 6, padding: 16, background: "var(--surface)" }}>
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 10 }}>Top Technologies</div>
            {byTech.length ? byTech.slice(0, 6).map((b) => <Bar key={b.label} {...b} max={maxBar} />) : <Empty />}
          </div>
          <div style={{ border: "1px solid var(--line)", borderRadius: 6, padding: 16, background: "var(--surface)" }}>
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 10 }}>Signal Types</div>
            {byType.length ? byType.map((b) => <Bar key={b.label} {...b} max={Math.max(1, ...byType.map((x) => x.count))} />) : <Empty />}
          </div>
          <div style={{ border: "1px solid var(--line)", borderRadius: 6, padding: 16, background: "var(--surface)" }}>
            <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 10 }}>Intent Distribution</div>
            {dist.map((b) => <Bar key={b.label} {...b} max={Math.max(1, ...dist.map((x) => x.count))} />)}
          </div>
        </div>
      </div>

      <SectionTitle eyebrow="Cross-Source View" title="Source × Industry Matrix" />
      <div style={{ border: "1px solid var(--line)", borderRadius: 6, overflow: "auto", background: "var(--surface)" }}>
        <table style={{ borderCollapse: "collapse", fontSize: 12.5, width: "100%" }}>
          <thead>
            <tr style={{ background: "var(--surface-2)" }}>
              <th style={{ textAlign: "left", padding: "9px 12px", fontWeight: 600, color: "var(--ink-soft)", fontSize: 11, textTransform: "uppercase" }}>Industry</th>
              {SOURCES.map((s) => (
                <th key={s.id} style={{ textAlign: "center", padding: "9px 10px", fontWeight: 600, color: "var(--ink-soft)", fontSize: 11 }}>{s.tag}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row) => (
              <tr key={row.industry} style={{ borderTop: "1px solid var(--line)" }}>
                <td style={{ padding: "8px 12px", fontWeight: 600, whiteSpace: "nowrap" }}>{row.industry}</td>
                {row.cells.map((v, i) => (
                  <td
                    key={i}
                    onClick={() => v > 0 && nav.toLeads({ industry: row.industry, source: SOURCES[i].id })}
                    style={{
                      textAlign: "center", padding: "8px 10px", cursor: v > 0 ? "pointer" : "default",
                      fontFamily: "var(--font-mono)", fontWeight: 600,
                      color: v > 0 ? "var(--ink)" : "var(--line)",
                      background: v > 0 ? `#0E7C86${Math.min(60, 10 + v * 8).toString(16)}` : "transparent",
                    }}
                  >
                    {v || "·"}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function Empty() { return <div style={{ fontSize: 12, color: "var(--ink-soft)" }}>No data for this view.</div>; }

/* ---------------------------- Page: Lead Intelligence ---------------------------- */

const _analyzingLeads = new Set();

function LeadIntelPage({ lead, leads, nav }) {
  const [analyzing, setAnalyzing] = useState(false);
  const [intel, setIntel] = useState(null);

  React.useEffect(() => {
    if (!lead) return;
    if (lead.signalType !== "Unknown") {
      setIntel(lead);
      return;
    }
    
    if (_analyzingLeads.has(lead.id)) {
      setAnalyzing(true);
      return; // Already analyzing this lead
    }
    
    _analyzingLeads.add(lead.id);
    setIntel(null);
    setAnalyzing(true);
    fetch("http://localhost:8000/api/v1/leads/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: lead.company, content: lead.originalSnippet, author: lead.author, source: lead.source, url: lead.originalUrl })
    })
      .then(res => res.json())
      .then(data => {
        setIntel(data);
      })
      .catch(err => console.error("Failed to analyze lead:", err))
      .finally(() => {
        _analyzingLeads.delete(lead.id);
        setAnalyzing(false);
      });
  }, [lead]);

  if (!lead) return null;
  const t = tier(lead.intentScore);
  const related = leads.filter((l) => l.company === lead.company && l.id !== lead.id);

  const activeTech = intel ? intel.technology : lead.technology;
  const activeService = intel ? intel.iosysService : lead.iosysService;
  
  const activePain = intel ? intel.businessPain : lead.businessPain;

  const isActive = (val) => val && val.trim().toLowerCase() !== "unknown" && val.trim().toLowerCase() !== "not detected";

  const localEvidence = [
    (intel ? intel.explicitRequirement : lead.explicitRequirement) && "Explicit project requirement stated in the original signal",
    lead.intentScore >= 45 && `Commercial intent detected (Score: ${lead.intentScore})`,
    isActive(activeTech) && `Specific tech need: ${activeTech}`,
    isActive(intel ? intel.company : lead.company) && `Company identified: ${intel ? intel.company : lead.company}`,
    lead.recentSignal && "Recent signal — detected within the last 14 days",
  ].filter(Boolean);

  const finalEvidence = (intel && intel.evidence && intel.evidence.length > 0) ? intel.evidence : localEvidence;

  return (
    <div>
      <LinkBtn onClick={nav.back} style={{ marginBottom: 14, display: "inline-block" }}>← Back</LinkBtn>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16, marginBottom: 22 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <SignalBars score={lead.intentScore} />
            <TierBadge score={lead.intentScore} />
            <SourceTag id={lead.source} />
          </div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 26, fontWeight: 700 }}>{lead.company}</div>
          <div style={{ color: "var(--ink-soft)", fontSize: 13, marginTop: 3 }}>{lead.industry} · {intel ? intel.region || lead.country : lead.country} · {fmtDate(lead.publishedDate)}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 11, color: "var(--ink-soft)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.03em" }}>Intent Score</div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 34, fontWeight: 700, color: TIER_COLOR[t] }}>{lead.intentScore}</div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 20, alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          {(intel?.aiSummary || (lead.aiSummary && lead.aiSummary !== "Unable to summarize.")) && (
            <Panel title="AI Summary">
              <p style={{ fontSize: 13.5, lineHeight: 1.6, color: "var(--ink)", margin: 0 }}>{intel ? intel.aiSummary : lead.aiSummary}</p>
            </Panel>
          )}



          {analyzing && (
            <div style={{ padding: "40px 20px", textAlign: "center", border: "1px dashed var(--accent-teal)", borderRadius: 6, background: "#0E7C860C", color: "var(--accent-teal)" }}>
              <div style={{ fontWeight: 600, marginBottom: 8, display: "flex", alignItems: "center", justifyContent: "center", gap: 8 }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ animation: "spin 2s linear infinite" }}>
                  <path d="M21 12a9 9 0 1 1-6.219-8.56" />
                </svg>
                Extracting Deep Intelligence...
              </div>
              <div style={{ fontSize: 12.5, opacity: 0.8 }}>Running LangGraph Agentic workflow on {lead.source} post...</div>
            </div>
          )}
          
          <style>{`
            @keyframes spin { 100% { transform: rotate(360deg); } }
          `}</style>
          
          {intel && intel.signalType !== "Noise" && (
            <>
    
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                <Panel title="Business Pain"><p style={{ margin: 0, fontSize: 13, color: "var(--ink)", lineHeight: 1.55 }}>{intel.businessPain}</p></Panel>
                <Panel title="Detected Need"><p style={{ margin: 0, fontSize: 13, color: "var(--ink)", lineHeight: 1.55 }}>{intel.detectedNeed}</p></Panel>
                
                <Panel title="Buying Stage"><p style={{ margin: 0, fontSize: 13, color: "var(--ink)", lineHeight: 1.55 }}>{intel.buyingStage || "Unknown"}</p></Panel>
                <Panel title="Recommended Action"><p style={{ margin: 0, fontSize: 13, color: "var(--ink)", lineHeight: 1.55 }}>{intel.recommendedAction || "Reach out to discuss requirements."}</p></Panel>
              </div>

              <Panel title="Contact & Profiles">
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  <ProfileLink label="Source Profile" value={intel.sourceProfileUrl} />
                  <ProfileLink label="Company Website" value={intel.companyWebsite} />
                  <ProfileLink label="Contact Page" value={intel.contactPage} />
                  <ProfileLink label="Email" value={intel.contactEmail || intel.email || lead.contactEmail} isEmail />
                  <ProfileLink label="Phone" value={intel.contactPhone || intel.phoneNumber} />
                  <ProfileLink label="GitHub" value={intel.githubProfile} />
                  <ProfileLink label="X/Twitter" value={intel.twitterProfile} />
                  <ProfileLink label="LinkedIn" value={intel.linkedinProfile} />
                  {(intel.otherProfiles || []).map((p, i) => <ProfileLink key={i} label={`Other (${i+1})`} value={p} />)}
                  
                  <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px dashed var(--line)" }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: "var(--ink-soft)", textTransform: "uppercase", marginBottom: 4 }}>Verification (Confidence: {intel.contactConfidence || 0}/100)</div>
                    <div style={{ fontSize: 13, color: "var(--ink)" }}>{intel.contactVerification || "Unknown"}</div>
                  </div>
                </div>
              </Panel>
            </>
          )}

          <Panel title="Evidence & Verification">
            <ul style={{ margin: 0, paddingLeft: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 8 }}>
              {finalEvidence.map((e, i) => (
                <li key={i} style={{ display: "flex", gap: 8, fontSize: 13, color: "var(--ink)" }}>
                  <span style={{ color: "var(--accent-teal)", fontWeight: 700 }}>✓</span>{e}
                </li>
              ))}
            </ul>
          </Panel>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <Panel title="Original Signal">
            <div style={{ fontStyle: "italic", color: "var(--ink)", fontSize: 13.5, lineHeight: 1.6, borderLeft: "3px solid var(--accent-teal)", paddingLeft: 12 }}>
              “<TruncatedText text={lead.originalSnippet} max={250} />”
            </div>
            <a href={lead.originalUrl} target="_blank" rel="noreferrer" style={{ display: "inline-block", marginTop: 10, fontSize: 12, color: "var(--accent-teal)", fontFamily: "var(--font-mono)", wordBreak: "break-all" }}>
              {lead.originalUrl} ↗
            </a>
          </Panel>
          <Panel title="Technology">
            <span style={{ fontSize: 12.5, fontWeight: 600, color: "var(--accent-teal)", background: "#0E7C860F", border: "1px solid #0E7C8633", padding: "4px 10px", borderRadius: 4 }}>{activeTech}</span>
          </Panel>

          <Panel title="iOSYS Opportunity">
            <div style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 15.5, color: "var(--ink)", marginBottom: 4 }}>{activeService}</div>
            <div style={{ fontSize: 12.5, color: "var(--ink-soft)" }}>Mapped from detected technology and business pain.</div>
          </Panel>

          <Panel title={`Cross-Source Timeline ${related.length ? `(${related.length + 1} signals)` : ""}`}>
            <div style={{ display: "flex", flexDirection: "column", gap: 12, borderLeft: "2px solid var(--line)", paddingLeft: 12, marginLeft: 6 }}>
              {[lead, ...related].sort((a,b) => new Date(b.publishedDate) - new Date(a.publishedDate)).map((r) => (
                <div key={r.id} onClick={() => nav.openLead(r.id)} style={{ position: "relative", padding: "10px", border: "1px solid var(--line)", borderRadius: 5, cursor: "pointer", background: r.id === lead.id ? "var(--chrome)" : "var(--surface)", color: r.id === lead.id ? "#fff" : "var(--ink)" }}>
                  <div style={{ position: "absolute", left: -19, top: 16, width: 10, height: 10, borderRadius: 5, background: r.id === lead.id ? "var(--accent-teal)" : "var(--line)" }} />
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <SourceTag id={r.source} />
                      <span style={{ fontSize: 12, opacity: 0.8 }}>{fmtDate(r.publishedDate)}</span>
                    </div>
                    <IntentCell score={r.intentScore} breakdown={r.scoreBreakdown} />
                  </div>
                  <div style={{ fontSize: 12.5 }}>{r.signalType}</div>
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
  );
}

function TruncatedText({ text, max }) {
  const [expanded, setExpanded] = useState(false);
  if (!text || text.length <= max) return <>{text}</>;
  return (
    <>
      {expanded ? text : `${text.slice(0, max)}... `}
      <button onClick={() => setExpanded(!expanded)} style={{ background: "none", border: "none", color: "var(--accent-teal)", fontWeight: 700, cursor: "pointer", padding: 0, fontSize: "inherit", marginLeft: 4 }}>
        {expanded ? "Read less" : "Read more"}
      </button>
    </>
  );
}

function Panel({ title, children }) {
  return (
    <div style={{ border: "1px solid var(--line)", borderRadius: 6, padding: 16, background: "var(--surface)" }}>
      <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.05em", textTransform: "uppercase", color: "var(--ink-soft)", marginBottom: 10 }}>{title}</div>
      {children}
    </div>
  );
}

function ProfileLink({ label, value, isEmail }) {
  if (!value || value === "Unknown" || value === "Not detected" || value === "None") return null;
  const isUrl = value.startsWith("http") || value.includes(".com") || value.includes(".io");
  const href = isEmail ? `mailto:${value}` : (value.startsWith("http") ? value : `https://${value}`);
  
  return (
    <div style={{ display: "flex", gap: 12, fontSize: 13, alignItems: "center", paddingBottom: 6, borderBottom: "1px solid #00000008" }}>
      <span style={{ color: "var(--ink-soft)", width: 110, fontWeight: 500 }}>{label}</span>
      {isUrl || isEmail ? (
        <a href={href} target="_blank" rel="noreferrer" style={{ color: "var(--accent-teal)", wordBreak: "break-all", fontWeight: 500, textDecoration: "none" }}>
          {value} ↗
        </a>
      ) : (
        <span style={{ color: "var(--ink)", wordBreak: "break-all", fontWeight: 500 }}>{value}</span>
      )}
    </div>
  );
}


/* ---------------------------- Page: Companies + Analytics ---------------------------- */

function CompaniesPage({ leads, nav }) {
  const [q, setQ] = useState("");
  const byCompany = {};
  leads.forEach((l) => {
    if (!byCompany[l.company]) byCompany[l.company] = [];
    byCompany[l.company].push(l);
  });
  let rows = Object.entries(byCompany).map(([company, ls]) => {
    const sources = [...new Set(ls.map((l) => l.source))];
    const maxIntent = Math.max(...ls.map((l) => l.intentScore));
    const latest = ls.reduce((a, b) => (a.daysAgo < b.daysAgo ? a : b));
    const top = [...ls].sort((a, b) => b.intentScore - a.intentScore)[0];
    return {
      company, industry: ls[0].industry, country: ls[0].country,
      signals: ls.length, sources, maxIntent, latest, opportunity: top.iosysService, leads: ls,
    };
  }).sort((a, b) => b.maxIntent - a.maxIntent);

  if (q) rows = rows.filter((r) => r.company.toLowerCase().includes(q.toLowerCase()));

  const bySource = SOURCES.map((s) => ({ label: s.name, count: leads.filter((l) => l.source === s.id).length }));
  const hotBySource = SOURCES.map((s) => ({ label: s.name, count: leads.filter((l) => l.source === s.id && l.intentScore >= 85).length }));
  const byIndustry = INDUSTRIES.map((i) => ({ label: i, count: leads.filter((l) => l.industry === i).length })).sort((a, b) => b.count - a.count);
  const intentBySource = SOURCES.map((s) => {
    const sl = leads.filter((l) => l.source === s.id);
    return { label: s.name, count: sl.length ? Math.round(sl.reduce((a, b) => a + b.intentScore, 0) / sl.length) : 0 };
  });
  const byTech = TECHNOLOGIES.map((t) => ({ label: t, count: leads.filter((l) => l.technology === t).length })).sort((a, b) => b.count - a.count).slice(0, 8);

  const Bar = ({ label, count, max, color }) => (
    <div style={{ marginBottom: 8 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 3 }}>
        <span style={{ color: "var(--ink-soft)" }}>{label}</span>
        <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>{count}</span>
      </div>
      <div style={{ height: 6, background: "var(--surface-2)", borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${(count / max) * 100}%`, height: "100%", background: color || "var(--accent-teal)" }} />
      </div>
    </div>
  );

  return (
    <div>
      <SectionTitle eyebrow={`${rows.length} companies`} title="Companies" right={
        <input placeholder="Search companies…" value={q} onChange={(e) => setQ(e.target.value)} style={{ padding: "7px 10px", border: "1px solid var(--line)", borderRadius: 5, fontSize: 12.5 }} />
      } />

      <div style={{ border: "1px solid var(--line)", borderRadius: 6, overflow: "hidden", background: "var(--surface)", marginBottom: 30 }}>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ background: "var(--surface-2)", borderBottom: "1px solid var(--line)" }}>
                {["Company", "Industry", "Country", "Signals", "Sources", "Intent", "Latest Signal", "Potential Opportunity"].map((h) => (
                  <th key={h} style={{ textAlign: "left", padding: "9px 14px", fontWeight: 600, fontSize: 11, textTransform: "uppercase", color: "var(--ink-soft)", whiteSpace: "nowrap" }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.company} style={{ borderBottom: "1px solid var(--line)", cursor: "pointer" }} onClick={() => nav.openLead(r.leads.sort((a, b) => b.intentScore - a.intentScore)[0].id)}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "var(--surface-2)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}>
                  <td style={{ padding: "10px 14px", fontWeight: 600 }}>
                    {r.company}
                    {r.sources.length > 1 && (
                      <div style={{ fontSize: 10.5, fontWeight: 600, color: TIER_COLOR.HOT, marginTop: 2 }}>🔥 MULTI-SOURCE SIGNAL</div>
                    )}
                  </td>
                  <td style={{ padding: "10px 14px", color: "var(--ink-soft)" }}>{r.industry}</td>
                  <td style={{ padding: "10px 14px", color: "var(--ink-soft)" }}>{r.country}</td>
                  <td style={{ padding: "10px 14px", fontFamily: "var(--font-mono)" }}>{r.signals}</td>
                  <td style={{ padding: "10px 14px" }}>
                    <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>{r.sources.map((s) => <SourceTag key={s} id={s} />)}</div>
                  </td>
                  <td style={{ padding: "10px 14px" }}><IntentCell score={r.maxIntent} /></td>
                  <td style={{ padding: "10px 14px", color: "var(--ink-soft)", fontFamily: "var(--font-mono)", fontSize: 12 }}>{fmtDate(r.latest.publishedDate)}</td>
                  <td style={{ padding: "10px 14px" }}>
                    <span style={{ fontSize: 11.5, fontWeight: 600, color: "var(--accent-teal)", background: "#0E7C860F", border: "1px solid #0E7C8633", padding: "2px 7px", borderRadius: 3, whiteSpace: "nowrap" }}>{r.opportunity}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <SectionTitle eyebrow="Program Analytics" title="Signal Analytics" />
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 16 }}>
        <Panel title="Signals by Source">{bySource.map((b) => <Bar key={b.label} {...b} max={Math.max(1, ...bySource.map((x) => x.count))} />)}</Panel>
        <Panel title="Hot Leads by Source">{hotBySource.map((b) => <Bar key={b.label} {...b} max={Math.max(1, ...hotBySource.map((x) => x.count))} color={TIER_COLOR.HOT} />)}</Panel>
        <Panel title="Leads by Industry">{byIndustry.map((b) => <Bar key={b.label} {...b} max={Math.max(1, ...byIndustry.map((x) => x.count))} />)}</Panel>
        <Panel title="Avg Intent by Source">{intentBySource.map((b) => <Bar key={b.label} {...b} max={100} color={TIER_COLOR.MEDIUM} />)}</Panel>
        <Panel title="Technology Demand">{byTech.map((b) => <Bar key={b.label} {...b} max={Math.max(1, ...byTech.map((x) => x.count))} color={TIER_COLOR.HIGH} />)}</Panel>
      </div>
    </div>
  );
}

/* ---------------------------- AI Search Page ---------------------------- */

function AiSearchPage({ leads, nav }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userMsg = query;
    setQuery("");
    setMessages(prev => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);

    try {
      const res = await axios.post("http://127.0.0.1:8000/api/v1/leads/search", { query: userMsg });
      const filters = res.data.filters;
      
      if (!filters || Object.keys(filters).length === 0) {
        setMessages(prev => [...prev, { role: "assistant", content: "I couldn't understand that query. Try asking something like 'Find me hot leads asking for n8n'." }]);
        setLoading(false);
        return;
      }

      // We have filters, let's just use the `applyFilters` logic from LeadsPage to get the results.
      // But wait, applyFilters is local to LeadsPage?
      // Actually, we can just use `nav.toLeads(filters)` to switch to the Leads view!
      // But the user wants a ChatGPT UI where they "search leads from there".
      // Let's render the matched leads as a small list inside the chat.
      
      const searchTerms = (filters.search || "").toLowerCase().split(" ").filter(Boolean);
      let matched = leads.filter(l => {
        if (filters.source && filters.source !== "ALL" && l.source !== filters.source) return false;
        if (filters.industry && l.industry !== filters.industry) return false;
        if (filters.tierLevel && filters.tierLevel !== "ALL") {
          const t = l.intentScore >= 80 ? "HOT" : l.intentScore >= 50 ? "EARLY" : "NOISE";
          if (t !== filters.tierLevel) return false;
        }
        if (searchTerms.length > 0) {
          const text = (l.company + " " + l.originalSnippet + " " + (l.aiSummary || "")).toLowerCase();
          if (!searchTerms.every(term => text.includes(term))) return false;
        }
        return true;
      });

      // Sort
      if (filters.sort === "newest") {
        matched.sort((a, b) => new Date(b.publishedDate) - new Date(a.publishedDate));
      } else {
        matched.sort((a, b) => b.intentScore - a.intentScore);
      }
      
      setMessages(prev => [...prev, { role: "assistant", filters, results: matched }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: "assistant", content: "Sorry, I encountered an error connecting to the AI brain." }]);
    } finally {
      setLoading(false);
    }
  };

  const isInitial = messages.length === 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 52px)", maxWidth: 800, margin: "0 auto" }}>
      {isInitial ? (
        <div style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 32, fontWeight: 700, marginBottom: 12 }}>Signal Intelligence</div>
          <div style={{ color: "var(--ink-soft)", fontSize: 15, marginBottom: 30 }}>Discover high-intent business opportunities using natural language.</div>
          
          <div style={{ width: "100%", maxWidth: 640, marginBottom: 40 }}>
            <form onSubmit={handleSearch} style={{ position: "relative", display: "flex", width: "100%" }}>
              <input 
                autoFocus
                value={query} 
                onChange={(e) => setQuery(e.target.value)}
                placeholder="What leads are you looking for?" 
                style={{ width: "100%", padding: "18px 54px 18px 24px", fontSize: 16, borderRadius: 30, border: "1px solid var(--line)", boxShadow: "0 8px 24px rgba(0,0,0,0.06)", outline: "none" }}
              />
              <button type="submit" disabled={!query.trim() || loading} style={{ position: "absolute", right: 10, top: 10, width: 40, height: 40, borderRadius: 20, background: query.trim() ? "var(--ink)" : "var(--line)", color: "#fff", border: "none", cursor: query.trim() ? "pointer" : "default", display: "flex", alignItems: "center", justifyContent: "center", transition: "0.2s" }}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9L22 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
              </button>
            </form>
          </div>

          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", justifyContent: "center", maxWidth: 640 }}>
            {["Find hot AI automation leads from n8n", "Show me high intent companies in healthcare", "Looking for leads asking for API integration"].map(s => (
              <div key={s} onClick={() => setQuery(s)} style={{ padding: "10px 16px", background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 20, fontSize: 13, cursor: "pointer", color: "var(--ink-soft)", transition: "all 0.2s" }} onMouseOver={e => e.target.style.borderColor="var(--accent-teal)"} onMouseOut={e => e.target.style.borderColor="var(--line)"}>
                {s}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <>
          <div style={{ flex: 1, overflowY: "auto", padding: "20px 0", display: "flex", flexDirection: "column", gap: 24 }}>
            {messages.map((m, i) => (
              <div key={i} style={{ display: "flex", gap: 16, alignItems: "flex-start", padding: "10px 20px", background: m.role === "user" ? "transparent" : "var(--surface)", borderRadius: 8, border: m.role === "user" ? "none" : "1px solid var(--line)" }}>
                <div style={{ width: 32, height: 32, borderRadius: 16, background: m.role === "user" ? "var(--ink)" : "var(--accent-teal)", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, fontWeight: 700, fontSize: 13 }}>
                  {m.role === "user" ? "U" : "AI"}
                </div>
                <div style={{ flex: 1, paddingTop: 6 }}>
                  {m.role === "user" ? (
                    <div style={{ fontSize: 15, fontWeight: 500 }}>{m.content}</div>
                  ) : (
                    <div>
                      {m.content && <div style={{ fontSize: 14, color: "var(--ink)", lineHeight: 1.6 }}>{m.content}</div>}
                      {m.filters && (
                        <div style={{ marginBottom: 16, fontSize: 13, color: "var(--ink-soft)" }}>
                          I found <b>{m.results.length}</b> leads matching: {JSON.stringify(m.filters)}
                        </div>
                      )}
                      {m.results && m.results.length > 0 && (
                        <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 12 }}>
                          {m.results.slice(0, 10).map(r => (
                            <div key={r.id} onClick={() => nav.openLead(r.id)} style={{ padding: 14, border: "1px solid var(--line)", borderRadius: 6, background: "var(--bg)", cursor: "pointer", transition: "0.2s" }} onMouseOver={e => e.currentTarget.style.borderColor="var(--accent-teal)"} onMouseOut={e => e.currentTarget.style.borderColor="var(--line)"}>
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                  <div style={{ fontWeight: 700, fontSize: 15 }}>{r.company}</div>
                                  <div style={{ fontSize: 12, color: "var(--ink-soft)", fontFamily: "var(--font-mono)" }}>
                                    {r.source.toUpperCase()} • {fmtDate(r.publishedDate)}
                                  </div>
                                </div>
                                <div style={{ fontWeight: 700, color: r.intentScore >= 80 ? "var(--accent-teal)" : "inherit" }}>{r.intentScore}</div>
                              </div>
                              <div style={{ fontSize: 13, color: "var(--ink-soft)" }}>{r.aiSummary || r.originalSnippet.slice(0,100)+"..."}</div>
                            </div>
                          ))}
                          {m.results.length > 10 && <div style={{ fontSize: 12, color: "var(--ink-soft)", textAlign: "center", padding: "10px 0" }}>+ {m.results.length - 10} more (view in Leads table for full list)</div>}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div style={{ display: "flex", gap: 16, padding: "10px 20px" }}>
                 <div style={{ width: 32, height: 32, borderRadius: 16, background: "var(--accent-teal)", color: "#fff", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, fontWeight: 700, fontSize: 13 }}>AI</div>
                 <div style={{ paddingTop: 6, fontSize: 14, color: "var(--ink-soft)" }}>Analyzing natural language...</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          
          <div style={{ padding: "20px 0" }}>
            <form onSubmit={handleSearch} style={{ position: "relative", display: "flex" }}>
              <input 
                autoFocus
                value={query} 
                onChange={(e) => setQuery(e.target.value)}
                placeholder="What leads are you looking for?" 
                style={{ width: "100%", padding: "16px 50px 16px 20px", fontSize: 15, borderRadius: 24, border: "1px solid var(--line)", boxShadow: "0 4px 12px rgba(0,0,0,0.05)", outline: "none" }}
              />
              <button type="submit" disabled={!query.trim() || loading} style={{ position: "absolute", right: 8, top: 8, width: 36, height: 36, borderRadius: 18, background: query.trim() ? "var(--ink)" : "var(--line)", color: "#fff", border: "none", cursor: query.trim() ? "pointer" : "default", display: "flex", alignItems: "center", justifyContent: "center" }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9L22 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
              </button>
            </form>
          </div>
        </>
      )}
    </div>
  );
}

/* ---------------------------- App shell ---------------------------- */

const NAV_ITEMS = [
  { id: "ai_search", label: "AI Search" },
  { id: "overview", label: "Overview" },
  { id: "leads", label: "Leads" },
  { id: "sources", label: "Source Intelligence" },
  { id: "companies", label: "Companies + Analytics" },
];

function emptyFilters() {
  return { search: "", source: "", industry: "", country: "", technology: "", signalType: "", tierLevel: "HOT", sort: "intent" };
}

export default function App() {
  const [rawLeads, setLeads] = useState([]);
  const [backendStats, setBackendStats] = useState(null);
  const [loading, setLoading] = useState(true);

  // Dynamically normalize source IDs during render so it instantly applies via HMR without needing a refresh
  const leads = useMemo(() => {
    return rawLeads.map(l => ({
      ...l,
      source: l.source === "n8n_community" ? "n8n" : (l.source === "indie_hackers" ? "indiehackers" : l.source)
    }));
  }, [rawLeads]);

  useEffect(() => {
    async function fetchLeads() {
      try {
        const response = await axios.get("http://127.0.0.1:8000/api/v1/leads");
        if (response.data && response.data.leads) {
            setLeads(response.data.leads);
            setBackendStats(response.data.stats);
        } else {
            setLeads(response.data);
        }
      } catch (err) {
        console.error("Failed to fetch leads from backend", err);
        setLeads([]);
      } finally {
        setLoading(false);
      }
    }
    fetchLeads();
  }, []);
  const [page, setPage] = useState("overview");
  const [prevPage, setPrevPage] = useState("overview");
  const [filters, setFilters] = useState(emptyFilters());
  const [activeSource, setActiveSource] = useState("indiehackers");
  const [selectedLeadId, setSelectedLeadId] = useState(null);

  const nav = {
    emptyFilters,
    toLeads: (partial) => {
      setFilters({ ...emptyFilters(), ...partial });
      setPage("leads");
    },
    openLead: (id) => {
      setPrevPage(page);
      setSelectedLeadId(id);
      setPage("lead");
    },
    back: () => setPage(prevPage),
  };

  const selectedLead = leads.find((l) => l.id === selectedLeadId);

  if (loading) {
    return <div style={{ padding: "40px", fontFamily: "var(--font-mono)" }}>[LOADING_INTELLIGENCE_DATA...]</div>;
  }

  return (
    <div style={{ display: "flex", minHeight: 640, fontFamily: "var(--font-body)", color: "var(--ink)", background: "var(--bg)" }}>
      <style>{`
        ${FONT_IMPORT}
        :root {
          --bg: #EEF1F5; --surface: #FFFFFF; --surface-2: #F5F7FA;
          --ink: #10151F; --ink-soft: #5B6472; --line: #DDE2E9;
          --chrome: #0F1720; --chrome-soft: #17212C; --chrome-line: #2A3441; --chrome-text: #B9C3D1;
          --accent-teal: #0E7C86;
          --font-display: 'Space Grotesk', sans-serif;
          --font-body: 'Inter', sans-serif;
          --font-mono: 'IBM Plex Mono', monospace;
        }
        * { box-sizing: border-box; }
        select, input { outline: none; }
        select:focus, input:focus, button:focus { box-shadow: 0 0 0 2px #0E7C8655; border-radius: 4px; }
      `}</style>

      {/* Sidebar */}
      <div style={{ width: 224, background: "var(--chrome)", color: "var(--chrome-text)", display: "flex", flexDirection: "column", flexShrink: 0 }}>
        <div style={{ padding: "22px 20px 18px", borderBottom: "1px solid var(--chrome-line)" }}>
          <div style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 17, color: "#fff", letterSpacing: "0.01em" }}>iOSYS</div>
          <div style={{ fontSize: 10.5, marginTop: 4, letterSpacing: "0.06em", color: "var(--accent-teal)", fontFamily: "var(--font-mono)", fontWeight: 600 }}>
            AI BUYING SIGNAL INTELLIGENCE
          </div>
        </div>
        <div style={{ padding: "14px 10px", display: "flex", flexDirection: "column", gap: 2 }}>
          {NAV_ITEMS.map((item) => {
            const active = page === item.id || (page === "lead" && item.id === prevPage);
            return (
              <div
                key={item.id}
                onClick={() => setPage(item.id)}
                style={{
                  padding: "9px 12px", borderRadius: 5, cursor: "pointer", fontSize: 13, fontWeight: 500,
                  color: active ? "#fff" : "var(--chrome-text)",
                  background: active ? "var(--chrome-soft)" : "transparent",
                  borderLeft: active ? "2px solid var(--accent-teal)" : "2px solid transparent",
                }}
              >
                {item.label}
              </div>
            );
          })}
        </div>
        <div style={{ marginTop: "auto", padding: "16px 20px", borderTop: "1px solid var(--chrome-line)", fontSize: 11, color: "#7C8898" }}>
          <div style={{ fontFamily: "var(--font-mono)" }}>{leads.length} signals tracked</div>
          <div style={{ fontFamily: "var(--font-mono)", marginTop: 2 }}>9 active sources</div>
        </div>
      </div>

      {/* Main */}
      <div style={{ flex: 1, padding: "26px 32px", minWidth: 0 }}>
        {page === "ai_search" && <AiSearchPage leads={leads} nav={nav} />}
        {page === "overview" && <OverviewPage leads={leads} nav={nav} backendStats={backendStats} />}
        {page === "leads" && <LeadsPage leads={leads} filters={filters} setFilters={setFilters} nav={nav} setLeads={setLeads} />}
        {page === "sources" && <SourceIntelPage leads={leads} activeSource={activeSource} setActiveSource={setActiveSource} nav={nav} />}
        {page === "companies" && <CompaniesPage leads={leads} nav={nav} />}
        {page === "lead" && <LeadIntelPage lead={selectedLead} leads={leads} nav={nav} />}
      </div>
    </div>
  );
}
