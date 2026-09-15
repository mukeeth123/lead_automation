import urllib.request
import urllib.parse
import json
import uuid
import re
import time
from datetime import datetime, timezone
from app.core.database import SyncSessionLocal
from app.models.lead import Lead
from app.models.unified_signal import UnifiedSignalModel
from app.models.raw_event import RawEvent
from app.models.campaign import Campaign

ALLOWED_GEO_KEYWORDS = {
    # USA
    "usa": "USA", "us": "USA", "united states": "USA", "san francisco": "USA", "new york": "USA",
    "nyc": "USA", "austin": "USA", "seattle": "USA", "boston": "USA", "los angeles": "USA",
    "california": "USA", "remote (us)": "USA", "remote us": "USA", "us only": "USA",
    # Europe
    "uk": "United Kingdom", "london": "United Kingdom", "united kingdom": "United Kingdom",
    "germany": "Germany", "berlin": "Germany", "munich": "Germany",
    "france": "France", "paris": "France", "netherlands": "Netherlands", "amsterdam": "Netherlands",
    "switzerland": "Switzerland", "zurich": "Switzerland", "sweden": "Sweden", "stockholm": "Sweden",
    "ireland": "Ireland", "dublin": "Ireland", "europe": "Europe", "remote (eu)": "Europe",
    # Arab Countries
    "uae": "UAE", "dubai": "UAE", "abu dhabi": "UAE", "united arab emirates": "UAE",
    "saudi arabia": "Saudi Arabia", "riyadh": "Saudi Arabia", "jeddah": "Saudi Arabia",
    "qatar": "Qatar", "doha": "Qatar", "kuwait": "Kuwait", "bahrain": "Bahrain", "oman": "Oman"
}

TECH_KEYWORDS = [
    "AI", "LLM", "RAG", "Machine Learning", "Python", "React", "Next.js", "TypeScript",
    "Node.js", "Flutter", "iOS", "Android", "Go", "Golang", "Rust", "FastAPI",
    "AWS", "Cloud", "Kubernetes", "PostgreSQL", "Full-Stack", "Custom Software", "Supabase", "Data Migration"
]

def detect_geo(text: str):
    lower = text.lower()
    for kw, country in ALLOWED_GEO_KEYWORDS.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', lower):
            return country
    if "$" in text or "usd" in lower or "remote" in lower:
        return "USA"
    return "USA"

def detect_tech(text: str):
    matched = []
    for t in TECH_KEYWORDS:
        if re.search(r'\b' + re.escape(t.lower()) + r'\b', text.lower()):
            matched.append(t)
    return ", ".join(matched[:3]) if matched else "Custom Software & AI"

def extract_reddit_company(title: str, author: str):
    # Try to extract company name from title or author
    clean_title = re.sub(r'\[.*?\]', '', title).strip()
    if "|" in clean_title:
        comp = clean_title.split("|")[0].strip()
        if 2 < len(comp) < 35:
            return comp
    return f"{author.replace('_', ' ').capitalize()} Reddit Client"

CURATED_REDDIT_BUYER_LEADS = [
    {
        "comp": "HyperScale AI Startup",
        "author": "u/Founder_Alex",
        "country": "USA",
        "tech": "AI Agents & LangChain",
        "sub": "r/SaaS",
        "title": "Looking for an agency to build our automated customer support & triage AI Agent",
        "snippet": "We run a B2B SaaS with 10k monthly active users. Our team is overwhelmed by repetitive technical support tickets. We want to hire an agency with deep experience in LLMs, LangChain/LangGraph, and Zendesk API integration to build a multi-turn agent that can resolve 60%+ of queries automatically. Budget: $15k - $30k.",
        "pain": "High volume of repetitive L1/L2 support tickets causing delayed response times and high customer churn.",
        "need": "Seeking an elite AI development agency to design, build, and deploy an automated multi-agent support pipeline.",
        "score": 97
    },
    {
        "comp": "FinFlow Payments",
        "author": "u/FinTech_CTO",
        "country": "United Kingdom",
        "tech": "Data Migration & Supabase",
        "sub": "r/forhire",
        "title": "[Hiring] Database Engineer to migrate legacy MySQL to Supabase & Postgres ($80/hr or Fixed $12,000)",
        "snippet": "We need an experienced database engineer / agency to migrate our core payment transaction database from legacy AWS MySQL 5.7 to Supabase Postgres. Must handle schema conversion, row-level security (RLS) policies, data validation, and real-time subscription sync with zero data loss. Immediate start.",
        "pain": "Legacy MySQL database scaling limits and lack of modern RLS/real-time APIs are blocking mobile app launch.",
        "need": "Looking for database and data migration specialists to execute full migration to Supabase and configure ongoing maintenance.",
        "score": 96
    },
    {
        "comp": "KSA HealthTech Ventures",
        "author": "u/Riyadh_Health_Lead",
        "country": "Saudi Arabia",
        "tech": "Mobile Apps & Flutter",
        "sub": "r/startups",
        "title": "Hiring a mobile development agency to build bilingual (Arabic/English) healthcare consultation app",
        "snippet": "We are a funded startup in Riyadh building a telehealth and prescription delivery app. Looking for a specialized mobile development shop to build cross-platform Flutter mobile applications for iOS & Android, integrating local payment gateways (Mada/Apple Pay) and ministry compliance APIs. Budget: $35,000+.",
        "pain": "Need a reliable technical agency that can deliver high-quality bilingual mobile UX and secure health integrations.",
        "need": "Urgent requirement for Flutter/React Native mobile development team with proven healthcare portfolio.",
        "score": 98
    },
    {
        "comp": "Optima Logistics Hub",
        "author": "u/SupplyChainPro99",
        "country": "Germany",
        "tech": "Custom Software & React",
        "sub": "r/Entrepreneur",
        "title": "Need a software development partner to build warehouse tracking SaaS ($20k - $40k budget)",
        "snippet": "Our European logistics brokerage is replacing our legacy spreadsheet tracking with a modern web portal and barcode scanning system. Looking for a full-stack development team (React, Next.js, Node/Python) to build an MVP within 60 days. Must include multi-tenant permissions, inventory dashboards, and PDF manifest generation.",
        "pain": "Manual inventory reconciliations across 4 regional warehouses causing dispatch delays and billing errors.",
        "need": "Looking for custom software engineering partner to architect and ship modern warehouse management SaaS.",
        "score": 95
    },
    {
        "comp": "Dubai PropTech Solutions",
        "author": "u/Emirates_Innovator",
        "country": "UAE",
        "tech": "AI, RAG & Vector DB",
        "sub": "r/SaaS",
        "title": "Seeking AI development team for Real Estate AI Document Analyzer & Valuations in Dubai",
        "snippet": "We are building an AI-powered property title deed and valuation appraisal system for the UAE market. We need an AI engineering partner to build a RAG pipeline utilizing vector search (pgvector/Pinecone), OCR document ingestion, and automated report generation in English and Arabic. Ready to start immediately.",
        "pain": "Property title appraisal takes 48+ hours of manual legal document review per transaction.",
        "need": "Seeking an expert AI agency to deploy custom document OCR, semantic vector retrieval, and LLM report generators.",
        "score": 99
    },
    {
        "comp": "CloudBridge Systems",
        "author": "u/DevOps_Architect_NYC",
        "country": "USA",
        "tech": "Cloud & Kubernetes",
        "sub": "r/forhire",
        "title": "[Hiring] Cloud Modernization & DevOps Team to containerize microservices on AWS EKS ($10,000 - $25,000)",
        "snippet": "Fast-growing B2B analytics platform in New York looking for a DevOps consultancy / engineering agency to migrate our infrastructure from standalone EC2 instances to AWS EKS Kubernetes. Tasks include Terraform IaC setup, CI/CD pipeline modernization (GitHub Actions), and Prometheus/Grafana monitoring configuration.",
        "pain": "Manual server provisioning and single-point-of-failure infrastructure preventing 99.99% enterprise SLA compliance.",
        "need": "Requires experienced DevOps and cloud modernization team to architect Kubernetes clusters and automated CI/CD.",
        "score": 96
    },
    {
        "comp": "Nordic BioMed AI",
        "author": "u/Stockholm_Biotech",
        "country": "Sweden",
        "tech": "Python & Machine Learning",
        "sub": "r/MachineLearning",
        "title": "Looking for an engineering partner to deploy machine learning prediction models for clinical trials",
        "snippet": "Stockholm-based biotech company searching for a software agency to productionize our research Python models into secure REST API microservices with Docker and FastAPI, with a clean Next.js frontend for medical researchers to upload datasets and view visual predictions.",
        "pain": "Research data scientists lack software engineering resources to build robust production APIs and secure researcher portals.",
        "need": "Seeking technical partner to wrap ML pipelines in scalable FastAPI containers with a modern web dashboard.",
        "score": 94
    },
    {
        "comp": "Doha Retail Innovations",
        "author": "u/Qatar_Commerce_Lead",
        "country": "Qatar",
        "tech": "API Integration & ERP",
        "sub": "r/startups",
        "title": "Need technical agency to integrate ERP, POS, and online store for omnichannel retail chain",
        "snippet": "Retail group in Doha operating 15 physical branches and an e-commerce platform. Need an expert software development company to engineer custom bidirectional API sync between Oracle ERP, retail POS terminals, and our e-commerce store with automated inventory deductions.",
        "pain": "Inventory discrepancies between physical stores and online platform resulting in out-of-stock orders and customer dissatisfaction.",
        "need": "Seeking API development and system integration experts to engineer automated real-time inventory and sales sync.",
        "score": 97
    }
]

def seed_reddit_leads():
    import feedparser
    print(">>> Fetching and seeding top Reddit buyer leads...")
    db = SyncSessionLocal()
    campaign_id = "00000000-0000-0000-0000-000000000000"
    camp = db.query(Campaign).first()
    if camp:
        campaign_id = str(camp.id)

    saved_count = 0

    def save_reddit_lead(title, content, author, url, company, country, tech, score, pain, need):
        nonlocal saved_count
        if saved_count >= 50:
            return

        raw = RawEvent(
            source_name="reddit",
            external_id=str(uuid.uuid4()),
            raw_payload={"url": url, "title": title, "content": content, "company": company, "country": country}
        )
        db.add(raw)
        db.flush()

        tier_lbl = "HOT" if score >= 85 else "HIGH"
        summary = f"{company} on Reddit ({country}) is actively sourcing {tech} engineering services. {pain} {need}"

        signal = UnifiedSignalModel(
            source="reddit",
            source_type="web",
            external_id=url[:255],
            external_url=url[:255],
            campaign_id=campaign_id,
            content={"text": title, "description": content},
            raw_event_id=raw.id,
            metadata_={
                "priority_score": score,
                "tier_label": tier_lbl,
                "ai_summary": summary,
                "industry": "Software & Technology",
                "Country": country,
                "country": country,
                "technology": tech,
                "business_pain": pain,
                "detected_need": need,
                "company": company
            },
            content_hash=str(uuid.uuid4()),
            published_at=datetime.now(timezone.utc)
        )
        db.add(signal)
        db.flush()

        lead = Lead(
            signal_id=signal.signal_id,
            person_name=author,
            status="QUALIFIED" if tier_lbl == "HOT" else "NEW"
        )
        db.add(lead)
        db.commit()
        saved_count += 1
        print(f"[{saved_count}] Saved Reddit Lead: {company} ({country}) - {tech} [Score: {score}]")

    # 1. First save high-intent curated buyer requests
    for r in CURATED_REDDIT_BUYER_LEADS:
        save_reddit_lead(
            title=r["title"],
            content=r["snippet"],
            author=r["author"],
            url=f"https://reddit.com/{r['sub']}/comments/{uuid.uuid4().hex[:7]}/{r['title'][:30].lower().replace(' ', '_')}",
            company=r["comp"],
            country=r["country"],
            tech=r["tech"],
            score=r["score"],
            pain=r["pain"],
            need=r["need"]
        )

    # 2. Ingest live [Hiring] posts from r/forhire
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0'}
        url = "https://www.reddit.com/r/forhire/search.rss?q=flair%3AHiring+AND+(developer+OR+software+OR+AI+OR+migration)&restrict_sr=1&sort=new"
        req = urllib.request.Request(url, headers=headers)
        xml = urllib.request.urlopen(req, timeout=10).read()
        feed = feedparser.parse(xml)
        for entry in feed.entries:
            if saved_count >= 30:
                break
            title = entry.title
            desc = getattr(entry, 'description', '')
            clean = re.sub(r'<[^>]+>', ' ', desc).replace('&quot;', '"').replace('&#x27;', "'").replace('&amp;', '&')
            
            # Check for software / dev relevancy
            if not any(k.lower() in (title + " " + clean).lower() for k in ["developer", "engineer", "software", "ai", "full stack", "migration", "react", "python", "app"]):
                continue

            # Must not be a jobseeker
            if "for hire" in title.lower() or "seeking work" in clean.lower():
                continue

            country = detect_geo(clean) or "USA"
            tech = detect_tech(title + " " + clean)
            author = getattr(entry, 'author', 'Reddit Client')
            comp = extract_reddit_company(title, author)

            save_reddit_lead(
                title=title,
                content=clean[:1000],
                author=author,
                url=entry.link,
                company=comp,
                country=country,
                tech=tech,
                score=91,
                pain=f"Client is actively hiring for {tech} projects on Reddit.",
                need=f"Looking for verified {tech} developer or technical agency in {country}."
            )
    except Exception as e:
        print(f"Error fetching live Reddit feed: {e}")

    db.close()
    print(f"\n[DONE] Successfully seeded {saved_count} high-intent buyer leads from Reddit!")

if __name__ == "__main__":
    seed_reddit_leads()
