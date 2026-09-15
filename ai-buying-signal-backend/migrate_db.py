from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.lead import Lead
from app.models.unified_signal import UnifiedSignalModel
from app.models.campaign import Campaign

# Source SQLite
sqlite_engine = create_engine("sqlite:///./test.db")
SqliteSession = sessionmaker(bind=sqlite_engine)

# Target MySQL
mysql_engine = create_engine("mysql+pymysql://root:root@localhost:3306/ai_buying_signal")
MysqlSession = sessionmaker(bind=mysql_engine)

def migrate():
    sqlite_db = SqliteSession()
    mysql_db = MysqlSession()
    
    # Migrate Campaigns
    campaigns = sqlite_db.query(Campaign).all()
    for c in campaigns:
        mysql_db.merge(c)
    
    # Migrate Signals
    signals = sqlite_db.query(UnifiedSignalModel).all()
    for s in signals:
        mysql_db.merge(s)
        
    # Migrate Leads
    leads = sqlite_db.query(Lead).all()
    for l in leads:
        mysql_db.merge(l)
        
    mysql_db.commit()
    print(f"Migrated {len(campaigns)} campaigns, {len(signals)} signals, and {len(leads)} leads.")
    sqlite_db.close()
    mysql_db.close()

if __name__ == "__main__":
    migrate()
