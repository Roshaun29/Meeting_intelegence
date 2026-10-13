from pathlib import Path

from backend.database import Base, engine
from backend.models import meeting, notification, task, nlp_result, user  # noqa: F401


def initialize_database() -> None:
    Path("storage/uploads").mkdir(parents=True, exist_ok=True)
    Path("data/audio").mkdir(parents=True, exist_ok=True)
    Path("data/transcripts").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    
    from backend.database import SessionLocal
    from backend.models.user import User
    from backend.core.security import hash_password

    db = SessionLocal()
    users_to_seed = [
        {"username": "admin", "password": "admin123", "role": "admin"},
        {"username": "manager", "password": "manager123", "role": "manager"},
        {"username": "employee", "password": "employee123", "role": "employee"}
    ]
    for u in users_to_seed:
        if not db.query(User).filter_by(username=u["username"]).first():
            db.add(User(username=u["username"], password_hash=hash_password(u["password"]), role=u["role"]))
    db.commit()
    db.close()


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully with seeded users.")
