from backend.database import SessionLocal
from backend.models.user import User, UserRole
from backend.core.security import hash_password

def seed():
    db = SessionLocal()
    # Clear and reseed or just add missing
    users = [
        {"username": "admin", "password": "admin123", "role": UserRole.ADMIN},
        {"username": "manager", "password": "manager123", "role": UserRole.MANAGER},
        {"username": "employee", "password": "employee123", "role": UserRole.EMPLOYEE}
    ]
    for u in users:
        existing = db.query(User).filter(User.username == u["username"]).first()
        if existing:
            db.delete(existing)
        db.add(User(
            username=u["username"], 
            password_hash=hash_password(u["password"]), 
            role=u["role"]
        ))
    db.commit()
    db.close()
    print("Seed complete.")

if __name__ == "__main__":
    seed()
