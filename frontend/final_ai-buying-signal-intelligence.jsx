import React, { useMemo, useState, useRef, useEffect } from "react";

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
  { id: "reddit", name: "Reddit", tag: "RDT" },
  { id: "hackernews", name: "Hacker News", tag: "HN" },
  { id: "x", name: "X", tag: "X" },
  { id: "indiehackers", name: "Indie Hackers", tag: "IH" },
  { id: "github", name: "GitHub", tag: "GH" },
  { id: "stackoverflow", name: "Stack Overflow", tag: "SO" },
  { id: "producthunt", name: "Product Hunt", tag: "PH" },
  { id: "jobboards", name: "Job Boards", tag: "JB" },
  { id: "tedeu", name: "TED EU", tag: "TED" },
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
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
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

function IntentCell({ score }) {
  const t = tier(score);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <SignalBars score={score} size="sm" />
      <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600, fontSize: 13, color: TIER_COLOR[t] }}>
        {score}
      </span>
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
  return (
    <span
      style={{
        fontFamily: "var(--font-mono)", fontSize: 10.5, fontWeight: 600, letterSpacing: "0.04em",
        color: "var(--ink-soft)", border: "1px solid var(--line)", borderRadius: 3,
        padding: "2px 6px", background: "var(--surface-2)", whiteSpace: "nowrap",
      }}
    >
      {SOURCE_MAP[id].tag}
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
              {["Intent", "Company", showContact && "Contact", "Industry", "Source", "Signal Type", "Technology", !dense && "Business Pain", "AI Summary", "Date", showStatus && "Status"]
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
                <td style={{ padding: "10px 14px" }}><IntentCell score={l.intentScore} /></td>
                <td style={{ padding: "10px 14px", fontWeight: 600, color: "var(--ink)" }}>{l.company}</td>
                {showContact && (
                  <td style={{ padding: "10px 14px", color: "var(--ink-soft)", fontFamily: "var(--font-mono)", fontSize: 12, maxWidth: 190, overflowWrap: "anywhere", wordBreak: "break-word", whiteSpace: "normal", lineHeight: 1.4 }}>
                    {l.contactEmail || "—"}
                  </td>
                )}
                <td style={{ padding: "10px 14px", color: "var(--ink-soft)" }}>{l.industry}</td>
                <td style={{ padding: "10px 14px" }}><SourceTag id={l.source} /></td>
                <td style={{ padding: "10px 14px", color: "var(--ink-soft)", whiteSpace: "nowrap" }}>{l.signalType}</td>
                <td style={{ padding: "10px 14px" }}>
                  <span style={{ fontSize: 11.5, fontWeight: 600, color: "var(--accent-teal)", background: "#0E7C860F", border: "1px solid #0E7C8633", padding: "2px 7px", borderRadius: 3 }}>{l.technology}</span>
                </td>
                {!dense && <td style={{ padding: "10px 14px", color: "var(--ink-soft)", maxWidth: 220 }}>{l.businessPain}</td>}
                <td style={{ padding: "10px 14px", color: "var(--ink-soft)", maxWidth: 260 }}>{l.aiSummary.slice(0, 92)}…</td>
                <td style={{ padding: "10px 14px", color: "var(--ink-soft)", whiteSpace: "nowrap", fontFamily: "var(--font-mono)", fontSize: 12 }}>{fmtDate(l.publishedDate)}</td>
                {showStatus && (
                  <td style={{ padding: "10px 14px" }}>
                    <span style={{ fontSize: 11.5, fontWeight: 600, color: "var(--ink-soft)", background: "var(--surface-2)", border: "1px solid var(--line)", padding: "2px 7px", borderRadius: 3, whiteSpace: "nowrap" }}>{l.status}</span>
                  </td>
                )}
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
      <select value={filters.minIntent} onChange={(e) => set("minIntent", Number(e.target.value))} style={input}>
        <option value={0}>Any Intent</option>
        <option value={50}>50+</option>
        <option value={70}>70+</option>
        <option value={85}>85+ Hot</option>
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
  if (filters.source) chips.push({ label: SOURCE_MAP[filters.source].name, onRemove: () => clear("source", "") });
  if (filters.industry) chips.push({ label: filters.industry, onRemove: () => clear("industry", "") });
  if (filters.country) chips.push({ label: filters.country, onRemove: () => clear("country", "") });
  if (filters.technology) chips.push({ label: filters.technology, onRemove: () => clear("technology", "") });
  if (filters.signalType) chips.push({ label: filters.signalType, onRemove: () => clear("signalType", "") });
  if (filters.minIntent) chips.push({ label: `Intent ${filters.minIntent}+`, onRemove: () => clear("minIntent", 0) });
  return chips;
}

function applyFilters(leads, filters) {
  let out = leads.filter((l) => {
    if (filters.search && !(`${l.company} ${l.businessPain} ${l.detectedNeed}`.toLowerCase().includes(filters.search.toLowerCase()))) return false;
    if (filters.source && l.source !== filters.source) return false;
    if (filters.industry && l.industry !== filters.industry) return false;
    if (filters.country && l.country !== filters.country) return false;
    if (filters.technology && l.technology !== filters.technology) return false;
    if (filters.signalType && l.signalType !== filters.signalType) return false;
    if (filters.minIntent && l.intentScore < filters.minIntent) return false;
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

/* ---------------------------- Page: Overview ---------------------------- */

function OverviewPage({ leads, nav }) {
  const [srcFilter, setSrcFilter] = useState(null);
  const [indFilter, setIndFilter] = useState(null);

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
          {srcFilter && <Chip label={SOURCE_MAP[srcFilter].name} onRemove={() => setSrcFilter(null)} />}
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

function LeadsPage({ leads, filters, setFilters, nav }) {
  const filtered = applyFilters(leads, filters);
  const chips = activeChips(filters, setFilters);
  return (
    <div>
      <SectionTitle eyebrow={`${filtered.length} of ${leads.length} signals`} title="All Leads" />
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
        {SOURCE_MAP[activeSource].name.toUpperCase()} INTELLIGENCE
      </div>
      <div style={{ display: "flex", gap: 12, marginBottom: 24, flexWrap: "wrap" }}>
        <StatCard label="Total Signals" value={total} />
        <StatCard label="Hot Leads" value={hotN} accent={TIER_COLOR.HOT} />
        <StatCard label="Average Intent" value={avg} />
        <StatCard label="Direct Buying Signals" value={direct} accent="var(--accent-teal)" />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: 20, marginBottom: 28, alignItems: "start" }}>
        <div>
          <SectionTitle title={`${SOURCE_MAP[activeSource].name} Leads`} right={<LinkBtn onClick={() => nav.toLeads({ source: activeSource })}>Open in Leads →</LinkBtn>} />
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

function LeadIntelPage({ lead, leads, nav }) {
  if (!lead) return null;
  const t = tier(lead.intentScore);
  const related = leads.filter((l) => l.company === lead.company && l.id !== lead.id);

  const evidence = [
    lead.explicitRequirement && "Explicit requirement stated in the original signal",
    "Clear business pain identified",
    `Technology requirement: ${lead.technology}`,
    lead.recentSignal && "Recent signal — detected within the last 14 days",
    `Strong fit for iOSYS ${lead.iosysService}`,
  ].filter(Boolean);

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
          <div style={{ color: "var(--ink-soft)", fontSize: 13, marginTop: 3 }}>{lead.industry} · {lead.country} · {fmtDate(lead.publishedDate)}</div>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 11, color: "var(--ink-soft)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.03em" }}>Intent Score</div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 34, fontWeight: 700, color: TIER_COLOR[t] }}>{lead.intentScore}</div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr", gap: 20, alignItems: "start" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <Panel title="Original Signal">
            <div style={{ fontStyle: "italic", color: "var(--ink)", fontSize: 13.5, lineHeight: 1.6, borderLeft: "3px solid var(--accent-teal)", paddingLeft: 12 }}>
              “{lead.originalSnippet}”
            </div>
            <a href={lead.originalUrl} target="_blank" rel="noreferrer" style={{ display: "inline-block", marginTop: 10, fontSize: 12, color: "var(--accent-teal)", fontFamily: "var(--font-mono)", wordBreak: "break-all" }}>
              {lead.originalUrl} ↗
            </a>
          </Panel>

          <Panel title="AI Summary">
            <p style={{ fontSize: 13.5, lineHeight: 1.6, color: "var(--ink)", margin: 0 }}>{lead.aiSummary}</p>
          </Panel>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            <Panel title="Business Pain"><p style={{ margin: 0, fontSize: 13, color: "var(--ink)", lineHeight: 1.55 }}>{lead.businessPain}</p></Panel>
            <Panel title="Detected Need"><p style={{ margin: 0, fontSize: 13, color: "var(--ink)", lineHeight: 1.55 }}>{lead.detectedNeed}</p></Panel>
          </div>

          <Panel title="Why This Is A Lead">
            <ul style={{ margin: 0, paddingLeft: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 8 }}>
              {evidence.map((e, i) => (
                <li key={i} style={{ display: "flex", gap: 8, fontSize: 13, color: "var(--ink)" }}>
                  <span style={{ color: "var(--accent-teal)", fontWeight: 700 }}>✓</span>{e}
                </li>
              ))}
            </ul>
            <div style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid var(--line)", display: "flex", gap: 16, flexWrap: "wrap" }}>
              {["Budget unknown", "Timeline unknown", "Decision maker unknown"].map((u) => (
                <span key={u} style={{ fontSize: 11.5, color: "var(--ink-soft)", fontFamily: "var(--font-mono)" }}>○ {u}</span>
              ))}
            </div>
          </Panel>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <Panel title="Technology">
            <span style={{ fontSize: 12.5, fontWeight: 600, color: "var(--accent-teal)", background: "#0E7C860F", border: "1px solid #0E7C8633", padding: "4px 10px", borderRadius: 4 }}>{lead.technology}</span>
          </Panel>

          <Panel title="iOSYS Opportunity">
            <div style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 15.5, color: "var(--ink)", marginBottom: 4 }}>{lead.iosysService}</div>
            <div style={{ fontSize: 12.5, color: "var(--ink-soft)" }}>Mapped from detected technology and business pain.</div>
          </Panel>

          <Panel title={`Related Signals ${related.length ? `(${related.length})` : ""}`}>
            {related.length === 0 && <div style={{ fontSize: 12.5, color: "var(--ink-soft)" }}>No other signals detected for this company yet.</div>}
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {related.map((r) => (
                <div key={r.id} onClick={() => nav.openLead(r.id)} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 10px", border: "1px solid var(--line)", borderRadius: 5, cursor: "pointer" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <SourceTag id={r.source} />
                    <span style={{ fontSize: 12.5, color: "var(--ink)" }}>{r.signalType}</span>
                  </div>
                  <IntentCell score={r.intentScore} />
                </div>
              ))}
            </div>
          </Panel>
        </div>
      </div>
    </div>
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

/* ---------------------------- App shell ---------------------------- */

const NAV_ITEMS = [
  { id: "overview", label: "Overview" },
  { id: "leads", label: "Leads" },
  { id: "sources", label: "Source Intelligence" },
  { id: "companies", label: "Companies + Analytics" },
];

function emptyFilters() {
  return { search: "", source: "", industry: "", country: "", technology: "", signalType: "", minIntent: 0, sort: "intent" };
}

export default function App() {
  const leads = useMemo(() => generateLeads(), []);
  const [page, setPage] = useState("overview");
  const [prevPage, setPrevPage] = useState("overview");
  const [filters, setFilters] = useState(emptyFilters());
  const [activeSource, setActiveSource] = useState("reddit");
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
        {page === "overview" && <OverviewPage leads={leads} nav={nav} />}
        {page === "leads" && <LeadsPage leads={leads} filters={filters} setFilters={setFilters} nav={nav} />}
        {page === "sources" && <SourceIntelPage leads={leads} activeSource={activeSource} setActiveSource={setActiveSource} nav={nav} />}
        {page === "companies" && <CompaniesPage leads={leads} nav={nav} />}
        {page === "lead" && <LeadIntelPage lead={selectedLead} leads={leads} nav={nav} />}
      </div>
    </div>
  );
}
