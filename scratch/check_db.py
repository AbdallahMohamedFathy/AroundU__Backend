from src.core.database import SessionLocal
from src.models.notification import Notification
from src.models.user import User

db = SessionLocal()
try:
    notif_count = db.query(Notification).count()
    user_count = db.query(User).count()
    owner_count = db.query(User).filter(User.role == 'OWNER').count()
    print(f"Total Notifications: {notif_count}")
    print(f"Total Users: {user_count}")
    print(f"Total Owners: {owner_count}")
    
    if notif_count > 0:
        latest = db.query(Notification).order_by(Notification.created_at.desc()).first()
        print(f"Latest Notification: {latest.title} for user {latest.user_id} at {latest.created_at}")
finally:
    db.close()
