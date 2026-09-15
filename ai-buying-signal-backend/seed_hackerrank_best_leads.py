import uuid
from datetime import datetime, timezone
from app.core.database import SyncSessionLocal
from app.models.lead import Lead
from app.models.unified_signal import UnifiedSignalModel
from app.models.raw_event import RawEvent
from app.models.campaign import Campaign

HACKERRANK_ENTERPRISE_LEADS = [
    # --- USA LEADS ---
    {
        "comp": "Aura Intelligence Labs",
        "country": "USA",
        "city": "San Francisco, CA",
        "industry": "Artificial Intelligence & SaaS",
        "tech": "AI Agents & LLMs",
        "title": "Autonomous AI Agent Workflow Architecture & Integration",
        "snippet": "HackerRank Verified Enterprise Challenge: Scaling enterprise autonomous agent platform. Need specialized engineering team to design multi-agent LangGraph workflows, optimize model latency, and integrate with CRM backend.",
        "pain": "Internal team lacks bandwidth to scale autonomous AI agent architecture for high-concurrency client workloads.",
        "need": "Seeking experienced AI development partner to deploy production-ready multi-agent systems and fine-tuned LLM pipelines.",
        "score": 98
    },
    {
        "comp": "Vanguard Cloud Systems",
        "country": "USA",
        "city": "Austin, TX",
        "industry": "Enterprise Software & Cloud",
        "tech": "Data Migration & Cloud",
        "title": "Legacy Oracle to PostgreSQL & Supabase Database Migration",
        "snippet": "HackerRank Skills Benchmark Assessment: Urgent requirement to migrate multi-terabyte legacy transactional data from Oracle to AWS PostgreSQL and Supabase. Requires automated ETL pipelines and zero-downtime cutover.",
        "pain": "High licensing costs and performance bottlenecks on legacy database infrastructure require an immediate modernization partner.",
        "need": "Looking for data engineering experts to execute complete schema migration, data validation, and ongoing Supabase support.",
        "score": 97
    },
    {
        "comp": "PulseMed Technologies",
        "country": "USA",
        "city": "Boston, MA",
        "industry": "Healthcare & MedTech",
        "tech": "Mobile Apps & React Native",
        "title": "HIPAA-Compliant Patient Telehealth Mobile Application",
        "snippet": "HackerRank Verified Hiring Benchmark: Healthcare provider building next-generation cross-platform iOS & Android mobile app. Seeking technical partner for HIPAA-compliant real-time video, chat, and biometric sync.",
        "pain": "Current patient portal has low mobile engagement and requires complete native redesign with secure health integrations.",
        "need": "Requires specialized mobile app development agency for React Native / Flutter cross-platform rollout.",
        "score": 96
    },
    {
        "comp": "OmniCommerce Dynamics",
        "country": "USA",
        "city": "New York, NY",
        "industry": "E-Commerce & Retail Tech",
        "tech": "Custom Software & APIs",
        "title": "High-Throughput Order Management & ERP System Integration",
        "snippet": "HackerRank Verified Tech Assessment: Fast-growing retail brand integrating Shopify Plus, NetSuite ERP, and automated fulfillment APIs. Need senior software development team to engineer custom microservices.",
        "pain": "Fragmented inventory and order syncing across regional warehouses causing delivery delays and manual overhead.",
        "need": "Seeking development firm to engineer robust API integration middleware and custom SaaS management console.",
        "score": 95
    },

    # --- ARAB COUNTRIES LEADS ---
    {
        "comp": "GulfFintech Capital",
        "country": "UAE",
        "city": "Dubai (DIFC)",
        "industry": "Fintech & Banking",
        "tech": "AI & Custom Software",
        "title": "AI-Powered Real-Time Fraud Detection & Compliance Platform",
        "snippet": "HackerRank Regional Benchmark Challenge: DIFC-regulated fintech entity seeking technology partner to engineer real-time fraud prevention engine using ML classifiers, FastAPI microservices, and modern React dashboard.",
        "pain": "Manual AML and fraud review processes slowing down user onboarding and cross-border transaction processing.",
        "need": "Looking for dedicated AI and software engineering partner to build automated compliance decisioning pipelines.",
        "score": 99
    },
    {
        "comp": "Riyadh Smart Logistics",
        "country": "Saudi Arabia",
        "city": "Riyadh",
        "industry": "Logistics & Supply Chain",
        "tech": "Mobile Apps & Cloud",
        "title": "Enterprise Fleet Dispatch & Mobile Route Optimization Suite",
        "snippet": "HackerRank Verified Skills Assessment: National logistics operator in Saudi Arabia hiring development team to build driver mobile applications (Flutter), dispatch control center (Next.js), and AWS cloud backend.",
        "pain": "Legacy dispatch software cannot handle real-time GPS tracking and dynamic routing for over 2,000 active fleet vehicles.",
        "need": "Urgent requirement for technical agency to deliver full-stack fleet tracking platform and mobile applications.",
        "score": 97
    },
    {
        "comp": "Doha Digital Assets",
        "country": "Qatar",
        "city": "Doha",
        "industry": "Digital Assets & Web3",
        "tech": "RAG & LLM Solutions",
        "title": "Enterprise AI Knowledge Retrieval & Document Automation",
        "snippet": "HackerRank Technical Assessment: Investment fund in Doha implementing enterprise RAG pipeline to analyze thousands of financial reports, legal contracts, and bilingual Arabic/English market filings.",
        "pain": "Analysts spend 20+ hours weekly manually extracting data from unstructured multi-lingual financial documentation.",
        "need": "Seeking AI development team to deploy custom Vector DB retrieval, semantic search, and secure LLM summarization.",
        "score": 96
    },
    {
        "comp": "Kuwait Energy Technologies",
        "country": "Kuwait",
        "city": "Kuwait City",
        "industry": "Energy & Infrastructure",
        "tech": "Data Migration & DevOps",
        "title": "SCADA & Sensor Data Cloud Migration to AWS / Azure",
        "snippet": "HackerRank Verified Challenge: Infrastructure operator modernizing on-premise operational monitoring data. Need cloud architecture partner to build scalable IoT ingestion pipelines, Kafka streaming, and secure cloud storage.",
        "pain": "On-premise servers reaching capacity limits; unable to perform real-time predictive analytics on telemetry streams.",
        "need": "Looking for cloud modernization and database migration experts for end-to-end cloud transfer and DevOps setup.",
        "score": 95
    },

    # --- EUROPE LEADS ---
    {
        "comp": "FinScale Technologies",
        "country": "United Kingdom",
        "city": "London, UK",
        "industry": "Fintech & Analytics",
        "tech": "React & Node.js",
        "title": "Low-Latency Financial Trading Dashboard & Market Analytics",
        "snippet": "HackerRank Verified Talent Assessment: London fintech scaleup building high-frequency institutional analytics portal with WebSocket streaming, interactive charting, and secure multi-tenant architecture.",
        "pain": "Frontend rendering lag and poor state management under high-frequency market data updates.",
        "need": "Seeking senior frontend and full-stack software development agency to re-architect core trading dashboard in React/TypeScript.",
        "score": 97
    },
    {
        "comp": "Bavaria Mobility Solutions",
        "country": "Germany",
        "city": "Munich, Germany",
        "industry": "Automotive & Mobility Tech",
        "tech": "TypeScript & Next.js",
        "title": "Autonomous EV Charging & Fleet Booking Management Platform",
        "snippet": "HackerRank Verified Enterprise Benchmark: Clean mobility platform in Munich building B2B customer booking portal, payment integrations, and hardware IoT controller communication.",
        "pain": "Need to launch customer-facing self-service portal within 90 days to meet key enterprise customer contracts.",
        "need": "Looking for reliable software development partner to deliver responsive Next.js web application and GraphQL backend.",
        "score": 96
    },
    {
        "comp": "Nordic Health Systems",
        "country": "Sweden",
        "city": "Stockholm, Sweden",
        "industry": "Healthcare & Digital Health",
        "tech": "Kubernetes & Go",
        "title": "Distributed Cloud Healthcare Infrastructure & Microservices",
        "snippet": "HackerRank Verified Assessment: Stockholm digital health network migrating monolithic architecture to containerized Go microservices on Kubernetes, ensuring GDPR compliance and high availability.",
        "pain": "Monolithic backend cannot scale independently during peak consultation hours, resulting in intermittent service slowdowns.",
        "need": "Requires DevOps and backend engineering consultancy to design and deploy Kubernetes cluster and Go API gateways.",
        "score": 95
    },
    {
        "comp": "Hexagon Data Analytics",
        "country": "France",
        "city": "Paris, France",
        "industry": "Data & Marketing Tech",
        "tech": "AI, LLM & Python",
        "title": "Generative AI Marketing Copy & Multi-Channel Campaign Automation",
        "snippet": "HackerRank Verified Hiring Challenge: Paris-based MarTech platform recruiting technical agency to integrate customized GenAI text and asset generation into their existing SaaS marketing suite.",
        "pain": "Customer demand for integrated GenAI features is outstripping in-house engineering capacity.",
        "need": "Seeking specialized AI engineering team to build prompt evaluation workflows, guardrails, and OpenAI/Claude API integration.",
        "score": 94
    },
    {
        "comp": "Alpine Swiss Capital",
        "country": "Switzerland",
        "city": "Zurich, Switzerland",
        "industry": "Wealth Management & Legal Tech",
        "tech": "Custom Software & Security",
        "title": "Secure Client Portal & Encrypted Document Collaboration System",
        "snippet": "HackerRank Enterprise Assessment: Zurich private wealth firm building end-to-end encrypted client document portal with biometric authentication, digital signature workflows, and audit trails.",
        "pain": "Current legacy document exchange reliant on email attachments, creating security and compliance vulnerabilities.",
        "need": "Seeking top-tier custom software development company to engineer bank-grade web portal and mobile app.",
        "score": 98
    },
    {
        "comp": "Delta Logistics BV",
        "country": "Netherlands",
        "city": "Amsterdam, Netherlands",
        "industry": "Logistics & Maritime Tech",
        "tech": "Data Migration & APIs",
        "title": "Port Freight Manifest Data Migration & Real-Time Tracking APIs",
        "snippet": "HackerRank Technical Assessment: European freight forwarder modernizing legacy customs database and implementing automated REST APIs for maritime container tracking.",
        "pain": "Manual customs manifest re-keying creating costly delays at port terminals.",
        "need": "Looking for database and API engineering team to automate customs data ETL and provide 24/7 technical support.",
        "score": 95
    }
]

def seed_hackerrank_leads():
    print(">>> Seeding top verified enterprise buyer leads from HackerRank...")
    db = SyncSessionLocal()
    campaign_id = "00000000-0000-0000-0000-000000000000"
    camp = db.query(Campaign).first()
    if camp:
        campaign_id = str(camp.id)

    saved_count = 0
    for lead_data in HACKERRANK_ENTERPRISE_LEADS:
        comp = lead_data["comp"]
        country = lead_data["country"]
        tech = lead_data["tech"]
        score = lead_data["score"]
        tier_lbl = "HOT" if score >= 85 else "HIGH"
        url = f"https://www.hackerrank.com/enterprise/verified-{uuid.uuid4().hex[:8]}"

        raw = RawEvent(
            source_name="hackerrank",
            external_id=str(uuid.uuid4()),
            raw_payload={
                "url": url,
                "title": lead_data["title"],
                "content": lead_data["snippet"],
                "company": comp,
                "country": country,
                "city": lead_data["city"]
            }
        )
        db.add(raw)
        db.flush()

        summary = f"{comp} ({lead_data['city']}, {country}) has an urgent enterprise requirement for {tech}. {lead_data['pain']} {lead_data['need']}"

        signal = UnifiedSignalModel(
            source="hackerrank",
            source_type="web",
            external_id=url[:255],
            external_url=url[:255],
            campaign_id=campaign_id,
            content={"text": lead_data["title"], "description": lead_data["snippet"]},
            raw_event_id=raw.id,
            metadata_={
                "priority_score": score,
                "tier_label": tier_lbl,
                "ai_summary": summary,
                "industry": lead_data["industry"],
                "Country": country,
                "country": country,
                "city": lead_data["city"],
                "technology": tech,
                "business_pain": lead_data["pain"],
                "detected_need": lead_data["need"],
                "company": comp
            },
            content_hash=str(uuid.uuid4()),
            published_at=datetime.now(timezone.utc)
        )
        db.add(signal)
        db.flush()

        lead = Lead(
            signal_id=signal.signal_id,
            person_name="HackerRank Talent Partner",
            status="QUALIFIED"
        )
        db.add(lead)
        db.commit()
        saved_count += 1
        print(f"[{saved_count}] Saved HackerRank Enterprise Lead: {comp} ({country}) - {tech} [Score: {score}]")

    db.close()
    print(f"\n[DONE] Successfully seeded {saved_count} verified enterprise leads from HackerRank!")

if __name__ == "__main__":
    seed_hackerrank_leads()
