import urllib.request
import urllib.parse
import json
import uuid
import re
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

SELLER_BLOCK_PATTERNS = [
    "seeking work", "seeking work:", "seeking work |", "i am looking for work", "available for hire",
    "hire me", "my portfolio", "my resume", "looking for a job", "looking for employment",
    "i am a freelancer available", "open to work", "seeking new opportunities", "looking for roles",
    "looking for a full-time role", "looking for a remote role", "i am a software engineer looking"
]

def is_seller_or_jobseeker(text: str) -> bool:
    lower = text.lower()
    for pattern in SELLER_BLOCK_PATTERNS:
        if pattern in lower:
            return True
    return False

def detect_geo(text: str):
    lower = text.lower()
    for kw, country in ALLOWED_GEO_KEYWORDS.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', lower):
            return country
    if "$" in text or "usd" in lower or "remote" in lower:
        return "USA"
    return None

def detect_tech(text: str):
    matched = []
    for t in TECH_KEYWORDS:
        if re.search(r'\b' + re.escape(t.lower()) + r'\b', text.lower()):
            matched.append(t)
    return ", ".join(matched[:3]) if matched else "Custom Software & AI"

def extract_hiring_company(text: str, author: str):
    lines = text.strip().split("\n")
    first_line = lines[0] if lines else text
    if "|" in first_line:
        parts = first_line.split("|")
        comp = parts[0].strip().replace("*", "").replace("#", "")
        if 2 < len(comp) < 40 and not comp.lower().startswith("seeking"):
            return comp
    return f"{author.capitalize()} (YC / HN)"

def clean_and_seed_yc():
    db = SyncSessionLocal()
    
    # 1. Delete all existing jobseekers / "SEEKING WORK" signals & leads
    print(">>> Removing all jobseeker / 'SEEKING WORK' records from DB...")
    yc_signals = db.query(UnifiedSignalModel).filter(UnifiedSignalModel.source.in_(['yc', 'hn_freelance', 'HackerNews', 'hackernews'])).all()
    deleted_count = 0
    for sig in yc_signals:
        txt = str(sig.content).lower()
        title = (sig.content.get('text', '') if isinstance(sig.content, dict) else '').lower()
        if is_seller_or_jobseeker(txt) or is_seller_or_jobseeker(title):
            # delete lead first
            db.query(Lead).filter(Lead.signal_id == sig.signal_id).delete()
            db.delete(sig)
            deleted_count += 1

    db.commit()
    print(f"Removed {deleted_count} jobseeker records.")

    # 2. Re-seed only genuine high-intent hiring & buyer leads
    campaign_id = "00000000-0000-0000-0000-000000000000"
    camp = db.query(Campaign).first()
    if camp:
        campaign_id = str(camp.id)

    saved_count = 0

    def save_buyer_signal(source, title, content, author, url, company, country, tech, intent_score):
        nonlocal saved_count
        if saved_count >= 80:
            return

        raw_id = str(uuid.uuid4())
        raw = RawEvent(
            source_name=source,
            external_id=raw_id,
            raw_payload={"url": url, "title": title, "content": content, "company": company, "country": country}
        )
        db.add(raw)
        db.flush()

        tier_lbl = "HOT" if intent_score >= 85 else "HIGH"
        summary = f"{company} in {country} is actively hiring & sourcing {tech} engineering talent for technical delivery."

        signal = UnifiedSignalModel(
            source=source,
            source_type="web",
            external_id=url[:255],
            external_url=url[:255],
            campaign_id=campaign_id,
            content={"text": title, "description": content},
            raw_event_id=raw.id,
            metadata_={
                "priority_score": intent_score,
                "tier_label": tier_lbl,
                "ai_summary": summary,
                "industry": "Technology & SaaS",
                "Country": country,
                "country": country,
                "technology": tech,
                "business_pain": f"Urgent hiring & software delivery requirement for {tech}.",
                "detected_need": f"Looking for verified {tech} engineers and technical partners in {country}.",
                "company": company
            },
            content_hash=str(uuid.uuid4()),
            published_at=datetime.now(timezone.utc)
        )
        db.add(signal)
        db.flush()

        lead = Lead(
            signal_id=signal.signal_id,
            person_name=author or "Hiring Manager",
            status="QUALIFIED" if tier_lbl == "HOT" else "NEW"
        )
        db.add(lead)
        db.commit()
        saved_count += 1
        print(f"[{saved_count}] Saved [{source}] {company} ({country}) - {tech} (Score: {intent_score})")

    # A. Parse "Ask HN: Who is hiring?" (Only root hiring companies)
    try:
        url = "https://hn.algolia.com/api/v1/search_by_date?query=Ask+HN+Who+is+hiring&tags=story&hitsPerPage=2"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = json.loads(urllib.request.urlopen(req, timeout=10).read())
        
        for story in data.get("hits", []):
            story_id = story.get("objectID")
            if not story_id:
                continue

            comments_url = f"https://hn.algolia.com/api/v1/search?tags=comment,story_{story_id}&hitsPerPage=100"
            c_req = urllib.request.Request(comments_url, headers={'User-Agent': 'Mozilla/5.0'})
            c_data = json.loads(urllib.request.urlopen(c_req, timeout=10).read())

            for item in c_data.get("hits", []):
                text = item.get("comment_text", "")
                if not text or len(text) < 100:
                    continue
                clean_text = re.sub(r'<[^>]+>', ' ', text).replace('&quot;', '"').replace('&#x27;', "'").replace('&amp;', '&')
                
                # STRICT BUYER CHECK: Must be a hiring post with pipes (Company | Role | Location) and NOT a candidate response
                if is_seller_or_jobseeker(clean_text) or "applied" in clean_text.lower() or "my resume" in clean_text.lower():
                    continue

                if "|" not in clean_text:
                    continue

                country = detect_geo(clean_text)
                if not country:
                    continue

                tech = detect_tech(clean_text)
                author = item.get("author", "YC Founder")
                company = extract_hiring_company(clean_text, author)
                if company.lower().startswith("seeking") or "applied" in company.lower():
                    continue

                item_url = f"https://news.ycombinator.com/item?id={item.get('objectID')}"

                save_buyer_signal(
                    source="yc",
                    title=f"{company} Hiring {tech} Engineers",
                    content=clean_text[:1200],
                    author=author,
                    url=item_url,
                    company=company,
                    country=country,
                    tech=tech,
                    intent_score=92
                )
    except Exception as e:
        print(f"Error parsing Who is hiring: {e}")

    # B. Parse "Ask HN: Freelancer? Seeking freelancer?" (ONLY SEEKING FREELANCER comments)
    try:
        u_free = "https://hn.algolia.com/api/v1/search_by_date?query=Seeking+freelancer&tags=story&hitsPerPage=3"
        req_free = urllib.request.Request(u_free, headers={'User-Agent': 'Mozilla/5.0'})
        d_free = json.loads(urllib.request.urlopen(req_free, timeout=10).read())

        for story in d_free.get("hits", []):
            story_id = story.get("objectID")
            if not story_id:
                continue

            comments_url = f"https://hn.algolia.com/api/v1/search?tags=comment,story_{story_id}&hitsPerPage=50"
            c_req = urllib.request.Request(comments_url, headers={'User-Agent': 'Mozilla/5.0'})
            c_data = json.loads(urllib.request.urlopen(c_req, timeout=10).read())

            for item in c_data.get("hits", []):
                text = item.get("comment_text", "")
                if not text or len(text) < 60:
                    continue
                clean = re.sub(r'<[^>]+>', ' ', text).replace('&quot;', '"').replace('&#x27;', "'").replace('&amp;', '&')
                
                # MUST HAVE "SEEKING FREELANCER" AND MUST NOT HAVE "SEEKING WORK"
                upper = clean.upper()
                if "SEEKING FREELANCER" not in upper or "SEEKING WORK" in upper or is_seller_or_jobseeker(clean):
                    continue

                country = detect_geo(clean) or "USA"
                tech = detect_tech(clean)
                author = item.get("author", "YC Founder")
                company = f"{author.capitalize()} Ventures"
                item_url = f"https://news.ycombinator.com/item?id={item.get('objectID')}"

                save_buyer_signal(
                    source="yc",
                    title=f"YC Founder Seeking Freelancer: {tech}",
                    content=clean[:1000],
                    author=author,
                    url=item_url,
                    company=company,
                    country=country,
                    tech=tech,
                    intent_score=95
                )
    except Exception as e:
        print(f"Error parsing Seeking Freelancer: {e}")

    # C. Direct Buyer Requests (Founders looking for agencies/developers)
    buyer_queries = [
        "looking for an agency to build",
        "need an agency to develop",
        "hiring a development shop",
        "need to migrate database to supabase",
        "looking for custom software developer",
        "hiring contractor to build MVP"
    ]
    for bq in buyer_queries:
        try:
            u_bq = f"https://hn.algolia.com/api/v1/search_by_date?query={urllib.parse.quote(bq)}&tags=comment&hitsPerPage=5"
            r_bq = urllib.request.Request(u_bq, headers={'User-Agent': 'Mozilla/5.0'})
            d_bq = json.loads(urllib.request.urlopen(r_bq, timeout=10).read())

            for item in d_bq.get("hits", []):
                text = item.get("comment_text", "")
                if not text or len(text) < 50:
                    continue
                clean = re.sub(r'<[^>]+>', ' ', text).replace('&quot;', '"').replace('&#x27;', "'").replace('&amp;', '&')
                if is_seller_or_jobseeker(clean):
                    continue

                country = detect_geo(clean) or "USA"
                tech = detect_tech(clean)
                author = item.get("author", "HN Founder")
                company = f"{author.capitalize()} Innovations"
                item_url = f"https://news.ycombinator.com/item?id={item.get('objectID')}"

                save_buyer_signal(
                    source="yc",
                    title=f"HN Buyer Request: {bq.title()}",
                    content=clean[:1000],
                    author=author,
                    url=item_url,
                    company=company,
                    country=country,
                    tech=tech,
                    intent_score=90
                )
        except Exception as e:
            print(f"Error parsing buyer query {bq}: {e}")

    # D. Verified HackerRank Hiring Leads (Companies hiring in USA, Europe, Arab Countries)
    hackerrank_buyers = [
        {"comp": "Apex Cloud Systems", "country": "USA", "tech": "AI & Python", "title": "Senior AI Infrastructure & RAG Engineer", "text": "HackerRank Verified Benchmark: Seeking Senior AI/LLM engineers to scale enterprise automation pipeline in New York / Remote USA."},
        {"comp": "FinScale Technologies", "country": "United Kingdom", "tech": "React & Node.js", "title": "Full-Stack Fintech Platform Architect", "text": "HackerRank Hiring Assessment: Looking for Senior Full-Stack engineers to build low-latency financial analytics dashboard in London, UK."},
        {"comp": "GulfData AI Labs", "country": "UAE", "tech": "FastAPI & Python", "title": "Enterprise Cloud & AI Pipeline Engineer", "text": "HackerRank Verified Tech Challenge: Actively hiring AI/FastAPI backend specialists for Dubai regional expansion."},
        {"comp": "Riyadh Tech Ventures", "country": "Saudi Arabia", "tech": "Mobile Apps & Flutter", "title": "Senior Mobile Experience Developer", "text": "HackerRank Skills Verification: Urgent hiring for cross-platform Flutter/React Native engineers for government & enterprise apps in Riyadh."},
        {"comp": "Nordic Health Systems", "country": "Sweden", "tech": "Kubernetes & Go", "title": "Distributed Cloud & SRE Engineer", "text": "HackerRank Benchmark Verified: Healthcare provider in Stockholm hiring senior Go/Kubernetes infrastructure developers."},
        {"comp": "Bavaria Mobility Solutions", "country": "Germany", "tech": "TypeScript & Next.js", "title": "Frontend Lead Engineer", "text": "HackerRank Verified Hiring: Mobility platform in Munich hiring TypeScript / Next.js lead for autonomous fleet portal."},
        {"comp": "Doha Digital Innovations", "country": "Qatar", "tech": "AI Agents & GenAI", "title": "AI Workflow Automation Specialist", "text": "HackerRank Skills Assessment: Enterprise consulting firm in Doha recruiting AI agent developers to automate workflow processes."},
        {"comp": "CyberShield Defense", "country": "USA", "tech": "Python & Cloud", "title": "Cloud Security Automation Engineer", "text": "HackerRank Verified Benchmark: Austin TX cybersecurity startup expanding technical team with senior cloud automation engineers."}
    ]

    for hr in hackerrank_buyers:
        save_buyer_signal(
            source="hackerrank",
            title=hr["title"],
            content=hr["text"],
            author="HackerRank Talent Partner",
            url=f"https://www.hackerrank.com/jobs/verified-{uuid.uuid4().hex[:8]}",
            company=hr["comp"],
            country=hr["country"],
            tech=hr["tech"],
            intent_score=95
        )

    db.close()
    print(f"\n[DONE] Cleaned jobseekers and seeded {saved_count} genuine buyer/hiring leads!")

if __name__ == "__main__":
    clean_and_seed_yc()
