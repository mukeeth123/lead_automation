from app.core.database import SyncSessionLocal
from app.models.lead import Lead
from app.models.unified_signal import UnifiedSignalModel
from app.models.raw_event import RawEvent
from sqlalchemy import select

db = SyncSessionLocal()
try:
    sources_to_delete = ["producthunt", "weworkremotely", "remotive", "himalayas", "startup_networks"]
    
    # Find unified signals to delete
    signals = db.execute(select(UnifiedSignalModel).where(UnifiedSignalModel.source.in_(sources_to_delete))).scalars().all()
    signal_ids = [s.signal_id for s in signals]
    raw_event_ids = [s.raw_event_id for s in signals]
    
    # Delete Leads
    if signal_ids:
        db.query(Lead).filter(Lead.signal_id.in_(signal_ids)).delete(synchronize_session=False)
    
    # Delete Signals
    if signal_ids:
        db.query(UnifiedSignalModel).filter(UnifiedSignalModel.signal_id.in_(signal_ids)).delete(synchronize_session=False)
        
    # Delete Raw Events
    if raw_event_ids:
        db.query(RawEvent).filter(RawEvent.id.in_(raw_event_ids)).delete(synchronize_session=False)
        
    db.commit()
    print(f"Deleted {len(signals)} leads from unwanted sources.")
except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()
