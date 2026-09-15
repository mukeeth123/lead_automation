import sys
from app.core.database import SyncSessionLocal
from app.models.service_catalog import CompanyService
from app.models.unified_signal import UnifiedSignalModel
from sqlalchemy.orm.attributes import flag_modified

def update_catalog_and_clear_rejections():
    db = SyncSessionLocal()
    
    # 1. New Core Services for IOSYS
    new_services = [
        {"name": "Data Migration & Database Engineering", "description": "Database migrations, ETL pipelines, Zoho to Supabase, SQL/NoSQL transfers, and cloud data architecture.", "keywords": ["migration", "database", "supabase", "zoho", "postgres", "sql", "etl", "data migration"]},
        {"name": "Cloud Modernization & DevOps", "description": "AWS, Azure, GCP infrastructure, Docker, Kubernetes, CI/CD, and scalable cloud deployments.", "keywords": ["cloud", "aws", "azure", "gcp", "devops", "kubernetes", "docker"]},
        {"name": "AI, LLM & AI Agent Solutions", "description": "Custom LLM integrations, RAG systems, Autonomous AI Agents, LangChain, and AI automation.", "keywords": ["ai", "llm", "rag", "gpt", "agents", "machine learning", "automation"]},
        {"name": "API & System Integration", "description": "Seamless integration between CRM, ERP, payment gateways, third-party platforms, and custom REST/GraphQL APIs.", "keywords": ["api", "integration", "crm", "erp", "webhook", "zapier"]},
        {"name": "Custom Software & SaaS Development", "description": "End-to-end full-stack web and mobile application engineering from MVP to enterprise scale.", "keywords": ["software", "saas", "mvp", "web", "mobile", "app", "react", "python", "node"]}
    ]

    for s_data in new_services:
        existing = db.query(CompanyService).filter(CompanyService.name == s_data["name"]).first()
        if not existing:
            service = CompanyService(
                name=s_data["name"],
                description=s_data["description"],
                keywords=s_data["keywords"],
                is_excluded=False
            )
            db.add(service)
            print(f"Added service: {s_data['name']}")

    db.commit()

    # 2. Clear old negative cached qualification results so they freshly qualify with the full catalog
    signals = db.query(UnifiedSignalModel).all()
    cleared_count = 0
    for sig in signals:
        if sig.metadata_ and "deep_qualification_result" in sig.metadata_:
            qual = sig.metadata_["deep_qualification_result"]
            # If it was marked as not a match / rejected, remove it so it recalculates with the new catalog
            if not qual.get("service_match", False) or qual.get("lead_status") == "REJECTED":
                del sig.metadata_["deep_qualification_result"]
                flag_modified(sig, "metadata_")
                cleared_count += 1

    db.commit()
    print(f"Cleared {cleared_count} outdated negative qualification caches.")
    db.close()

if __name__ == "__main__":
    update_catalog_and_clear_rejections()
