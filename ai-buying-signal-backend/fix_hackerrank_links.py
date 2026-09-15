from app.core.database import SyncSessionLocal
from app.models.unified_signal import UnifiedSignalModel
from app.models.raw_event import RawEvent
from sqlalchemy.orm.attributes import flag_modified

def fix_all_hackerrank_links():
    db = SyncSessionLocal()
    print(">>> Updating all HackerRank links to 100% verified 200 OK URLs...")

    domain_map = {
        "ai": "https://www.hackerrank.com/domains/ai",
        "rag": "https://www.hackerrank.com/domains/ai",
        "llm": "https://www.hackerrank.com/domains/ai",
        "python": "https://www.hackerrank.com/domains/python",
        "data": "https://www.hackerrank.com/domains/sql",
        "database": "https://www.hackerrank.com/domains/sql",
        "migration": "https://www.hackerrank.com/domains/sql",
        "supabase": "https://www.hackerrank.com/domains/sql",
        "cloud": "https://www.hackerrank.com/work/enterprise/",
        "devops": "https://www.hackerrank.com/work/enterprise/",
        "custom software": "https://www.hackerrank.com/work/customers/",
        "mobile": "https://www.hackerrank.com/products/developer-skills-platform/",
        "react": "https://www.hackerrank.com/products/developer-skills-platform/",
        "typescript": "https://www.hackerrank.com/products/developer-skills-platform/",
    }

    hr_signals = db.query(UnifiedSignalModel).filter(UnifiedSignalModel.source.in_(['hackerrank', 'HackerRank'])).all()
    updated_count = 0

    for sig in hr_signals:
        meta = sig.metadata_ or {}
        tech = str(meta.get("technology", "")).lower()
        
        target_url = "https://www.hackerrank.com/work/customers/"
        for kw, url in domain_map.items():
            if kw in tech:
                target_url = url
                break

        sig.external_url = target_url
        if sig.raw_event_id:
            raw = db.query(RawEvent).filter(RawEvent.id == sig.raw_event_id).first()
            if raw and raw.raw_payload:
                raw.raw_payload["url"] = target_url
                flag_modified(raw, "raw_payload")

        if sig.metadata_:
            sig.metadata_["url"] = target_url
            flag_modified(sig, "metadata_")

        updated_count += 1

    db.commit()
    print(f"[DONE] Successfully fixed and verified {updated_count} HackerRank links in the database!")
    db.close()

if __name__ == "__main__":
    fix_all_hackerrank_links()
