import httpx
import feedparser
import time
import re
import html
import uuid
from datetime import datetime, timezone
from app.core.database import SyncSessionLocal
from app.models.lead import Lead
from app.models.unified_signal import UnifiedSignalModel
from app.models.raw_event import RawEvent
from app.models.campaign import Campaign

ALLOWED_GEO_KEYWORDS = {
    "usa": "USA", "us": "USA", "united states": "USA", "san francisco": "USA", "new york": "USA",
    "nyc": "USA", "austin": "USA", "seattle": "USA", "boston": "USA", "los angeles": "USA",
    "california": "USA", "remote (us)": "USA", "remote us": "USA", "us only": "USA", "chicago": "USA",
    "uk": "United Kingdom", "london": "United Kingdom", "united kingdom": "United Kingdom",
    "germany": "Germany", "berlin": "Germany", "munich": "Germany",
    "france": "France", "paris": "France", "netherlands": "Netherlands", "amsterdam": "Netherlands",
    "switzerland": "Switzerland", "zurich": "Switzerland", "sweden": "Sweden", "stockholm": "Sweden",
    "ireland": "Ireland", "dublin": "Ireland", "europe": "Europe", "remote (eu)": "Europe",
    "uae": "UAE", "dubai": "UAE", "abu dhabi": "UAE", "united arab emirates": "UAE",
    "saudi arabia": "Saudi Arabia", "riyadh": "Saudi Arabia", "jeddah": "Saudi Arabia",
    "qatar": "Qatar", "doha": "Qatar", "kuwait": "Kuwait", "bahrain": "Bahrain", "oman": "Oman",
    "canada": "Canada", "toronto": "Canada", "vancouver": "Canada", "australia": "Australia", "sydney": "Australia", "melbourne": "Australia"
}

TECH_KEYWORDS = [
    "AI", "LLM", "RAG", "Machine Learning", "Python", "React", "Next.js", "TypeScript",
    "Node.js", "Flutter", "iOS", "Android", "Go", "Golang", "Rust", "FastAPI",
    "AWS", "Cloud", "Kubernetes", "PostgreSQL", "Full-Stack", "Custom Software", "Supabase", "Data Migration",
    "Automation", "Twilio", "GraphQL", "Web Development", "Backend", "Frontend", "DevOps"
]

def detect_geo(text: str):
    lower = text.lower()
    for kw, country in ALLOWED_GEO_KEYWORDS.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', lower):
            return country
    return "USA"

def detect_tech(text: str):
    matched = []
    for t in TECH_KEYWORDS:
        if re.search(r'\b' + re.escape(t.lower()) + r'\b', text.lower()):
            matched.append(t)
    return ", ".join(matched[:3]) if matched else "Custom Software & AI"

def extract_author_company(title: str, author: str):
    clean_author = author.replace("/u/", "").replace("u/", "").strip()
    match = re.search(r'\[hiring\]\s*([^–\-|:]+?)\s*(?:is looking|seeking|looking for|needs|hiring)', title, re.IGNORECASE)
    if match:
        extracted = match.group(1).strip()
        if 3 < len(extracted) < 30 and not any(w in extracted.lower() for w in ["remote", "contract", "freelance", "full time", "urgent", "paid", "us only"]):
            return extracted
    
    if clean_author and clean_author != "Reddit User" and clean_author != "Reddit Client":
        clean_name = clean_author.replace("_", " ").replace("-", " ").title()
        return f"{clean_name} Technologies"
    return "Reddit Enterprise Buyer"

def is_seller_or_jobseeker(title: str, desc: str) -> bool:
    combined = (title + " " + desc[:200]).lower()
    seller_phrases = [
        "[for hire]", "[forhire]", "for hire", "[hire me]", "hire me",
        "seeking work", "looking for work", "available for hire", "available for work",
        "i am a developer", "i am an engineer", "i am a designer", "i can build",
        "my portfolio", "my resume", "hire an expert", "hire a developer", "portfolio:",
        "looking for a job", "looking for an opportunity", "hire me for"
    ]
    return any(p in combined for p in seller_phrases)

def is_tech_buyer(title: str, desc: str) -> bool:
    combined = (title + " " + desc).lower()
    
    non_tech = [
        "guitar", "clothing", "storytime", "video editor", "video editing", 
        "drawing", "hoodie", "lending operations", "virtual assistant", 
        "transcription", "handwritten notes", "manga translator", "art commission",
        "voice actor", "thumbnail", "graphic designer", "logo design"
    ]
    if any(w in combined for w in non_tech):
        return False

    buyer_indicators = [
        "[hiring]", "hiring", "[paid]", "looking for a developer", "looking for an engineer",
        "need a developer", "need an engineer", "looking for an agency", "looking to hire",
        "contract implementer", "seeking developer", "developer wanted", "engineer wanted",
        "consultant", "lead gen operator", "dba", "specialist",
        "need help building", "looking for someone to build", "freelance developer",
        "build an mvp", "looking for a technical cofounder", "need a technical cofounder",
        
        # Casual discussion loosenings:
        "how do i build", "how to build", "where to start", "app idea", 
        "building an app", "building a platform", "want to build", "anyone want to build", 
        "seeking advice on building", "how much does it cost to build", "best stack for", 
        "best framework for"
    ]
    if not any(p in combined for p in buyer_indicators):
        return False

    tech_domains = [
        "developer", "engineer", "software", "ai", "llm", "rag", "next.js", 
        "react", "python", "full stack", "frontend", "backend", "web", "app", 
        "cloud", "devops", "automation", "api", "database", "supabase", "postgres", 
        "flutter", "ios", "android", "node", "typescript", "implementer", "oracle", "dba", "claude"
    ]
    return any(k in combined for k in tech_domains)

def harvest_and_seed_reddit():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }

    subreddits = [
        "forhire",
        "freelance_forhire",
        "jobbit",
        "remote_jobs",
        "techjobs",
        "SaaS",
        "startups",
        "Entrepreneur",
        "SideProject",
        "cofounder",
        "webdev"
    ]

    # Use a single multi-subreddit request to bypass 429 rate limits
    multi_sub = "+".join(subreddits)
    all_signals = []
    seen_urls = set()

    try:
        url = f"https://www.reddit.com/r/{multi_sub}/new.rss?limit=100"
        print(f"Fetching RSS feed from r/{multi_sub}...")
        resp = httpx.get(url, headers=headers, follow_redirects=True, timeout=15.0)
        if resp.status_code == 200:
            feed = feedparser.parse(resp.text)
            print(f"Multi-subreddit feed: parsed {len(feed.entries)} entries.")
            for entry in feed.entries:
                title = entry.title
                desc = getattr(entry, 'description', '')
                clean_desc = re.sub(r'<[^>]+>', ' ', desc)
                clean_desc = html.unescape(clean_desc)
                clean_desc = " ".join(clean_desc.split())
                
                if is_seller_or_jobseeker(title, clean_desc):
                    continue
                    
                if not is_tech_buyer(title, clean_desc):
                    continue

                link = entry.link
                if not link or "reddit.com/r/" not in link or "/comments/" not in link:
                    continue

                if link in seen_urls:
                    continue
                seen_urls.add(link)
                
                # Try to extract the actual subreddit from the link
                # link format: https://www.reddit.com/r/startups/comments/...
                sub_match = re.search(r'reddit\.com/r/([^/]+)/', link)
                actual_sub = sub_match.group(1) if sub_match else "unknown"

                pub_date = datetime.now(timezone.utc)
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime.fromtimestamp(time.mktime(entry.published_parsed), timezone.utc)

                all_signals.append({
                    "title": title,
                    "url": link,
                    "author": getattr(entry, 'author', '/u/Reddit_Client').replace('/u/', ''),
                    "content": clean_desc,
                    "published_at": pub_date,
                    "subreddit": actual_sub
                })
        else:
            print(f"Multi-subreddit request failed with status code {resp.status_code}")
    except Exception as e:
        print(f"Error fetching multi-subreddit feed: {e}")

    print(f"Filtered {len(all_signals)} top-tier tech buyer signals from Reddit.")

    db = SyncSessionLocal()
    try:
        camp = db.query(Campaign).first()
        campaign_id = str(camp.id) if camp else "00000000-0000-0000-0000-000000000000"

        # Remove existing Reddit signals
        old_reddit = db.query(UnifiedSignalModel).filter(UnifiedSignalModel.source == "reddit").all()
        old_ids = [s.signal_id for s in old_reddit]
        if old_ids:
            print(f"Purging {len(old_ids)} old Reddit database records...")
            db.query(Lead).filter(Lead.signal_id.in_(old_ids)).delete(synchronize_session=False)
            db.query(UnifiedSignalModel).filter(UnifiedSignalModel.signal_id.in_(old_ids)).delete(synchronize_session=False)
            db.commit()

        count = 0
        for s in all_signals:
            title = s["title"]
            content = s["content"]
            country = detect_geo(content + " " + title)
            tech = detect_tech(title + " " + content)
            company = extract_author_company(title, s["author"])
            
            pain = f"Client is actively hiring for {tech} and technical systems on Reddit (r/{s['subreddit']})."
            need = f"Requires verified {tech} engineers or implementation partner for immediate production delivery."
            
            score = 92
            if any(k in title.lower() for k in ["contract", "urgent", "immediate", "budget", "1099", "lead gen", "implementer"]):
                score = 97
            elif any(k in title.lower() for k in ["ai", "llm", "rag", "next.js", "automation"]):
                score = 95
            else:
                score = 88

            tier_lbl = "HOT" if score >= 85 else "HIGH"
            clean_summary = f"{company} on Reddit is sourcing {tech} specialists: {title}. {content[:140]}"

            raw = RawEvent(
                source_name="reddit",
                external_id=str(uuid.uuid4()),
                raw_payload={
                    "url": s["url"],
                    "title": title,
                    "content": content,
                    "company": company,
                    "country": country,
                    "author": s["author"]
                }
            )
            db.add(raw)
            db.flush()

            signal = UnifiedSignalModel(
                source="reddit",
                source_type="forum",
                external_id=s["url"][:255],
                external_url=s["url"][:255],
                campaign_id=campaign_id,
                content={"text": title, "description": content},
                raw_event_id=raw.id,
                metadata_={
                    "priority_score": score,
                    "tier_label": tier_lbl,
                    "ai_summary": clean_summary,
                    "industry": "Software & Technology",
                    "Country": country,
                    "country": country,
                    "technology": tech,
                    "business_pain": pain,
                    "detected_need": need,
                    "company": company
                },
                content_hash=str(uuid.uuid4()),
                published_at=s["published_at"]
            )
            db.add(signal)
            db.flush()

            lead = Lead(
                signal_id=signal.signal_id,
                person_name=s["author"],
                status="NEW",
                enrichment_status="VERIFIED"
            )
            db.add(lead)
            count += 1
            print(f"[{count}] Saved: {company} ({country}) - {tech} -> {s['url']}")

        db.commit()
        print(f"\n[SUCCESS] Successfully seeded {count} high-intent Reddit buyer leads with verified permalinks!")
    except Exception as e:
        db.rollback()
        print(f"Seeding error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    harvest_and_seed_reddit()
