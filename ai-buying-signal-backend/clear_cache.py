import asyncio
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified
from app.models import UnifiedSignalModel
from app.core.database import SyncSessionLocal

def clear():
    db = SyncSessionLocal()
    signals = db.scalars(select(UnifiedSignalModel)).all()
    count = 0
    for s in signals:
        if s.metadata_ and "deep_qualification_result" in s.metadata_:
            s.metadata_.pop("deep_qualification_result")
            s.metadata_.pop("ai_reasoning", None)
            flag_modified(s, "metadata_")
            count += 1
    db.commit()
    print(f"Cleared cache for {count} signals")

if __name__ == "__main__":
    clear()
