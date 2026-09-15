from app.core.database import sync_engine, Base
# Import all models to ensure they are registered with Base.metadata
import app.models.lead
import app.models.unified_signal
import app.models.campaign
import app.models.raw_event
import app.models.company
import app.models.discovery_job
import app.models.source
import app.models.source_health
import app.models.service_catalog
from sqlalchemy.orm import Session
from app.core.database import sync_engine

def seed_services():
    from app.models.service_catalog import CompanyService
    with Session(sync_engine) as db:
        if db.query(CompanyService).first() is not None:
            print("Services already seeded.")
            return

        target_services = [
            "Custom Software Development", "Web Application Development", 
            "Mobile App Development", "SaaS Development", "MVP Development", 
            "AI Application Development", "AI Agents", "Business Process Automation", 
            "API Development", "API Integration", "Cloud Application Development", 
            "Legacy System Modernization", "Software Product Development", 
            "Dedicated Development Teams", "Technical Consulting"
        ]
        
        excluded_services = [
            "SEO", "Social Media Marketing", "Content Writing", "Meta Ads", 
            "Google Ads", "PPC", "Influencer Marketing", "Video Editing", 
            "Video Creation", "Voice Acting", "Graphic Design", "Recruitment", 
            "Accounting", "Legal Services", "Real Estate Services", "General Virtual Assistant work"
        ]
        
        for ts in target_services:
            db.add(CompanyService(name=ts, is_excluded=False))
            
        for es in excluded_services:
            db.add(CompanyService(name=es, is_excluded=True))
            
        db.commit()
        print("Successfully seeded CompanyService catalog.")

def init_db():
    Base.metadata.create_all(sync_engine)
    print("Successfully created all database tables in SQLite.")
    seed_services()

if __name__ == "__main__":
    init_db()
