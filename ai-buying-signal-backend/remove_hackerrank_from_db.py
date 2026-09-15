from app.core.database import SyncSessionLocal
from app.models.unified_signal import UnifiedSignalModel
from app.models.lead import Lead

def remove_hackerrank():
    db = SyncSessionLocal()
    print(">>> Removing all HackerRank signals and leads from DB...")
    signals = db.query(UnifiedSignalModel).filter(UnifiedSignalModel.source.in_(['hackerrank', 'HackerRank'])).all()
    count = 0
    for sig in signals:
        db.query(Lead).filter(Lead.signal_id == sig.signal_id).delete()
        db.delete(sig)
        count += 1
    db.commit()
    print(f"[DONE] Successfully removed {count} HackerRank records from DB.")
    db.close()

if __name__ == '__main__':
    remove_hackerrank()
