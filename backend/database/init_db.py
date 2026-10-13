import sys
import os

# Add project root to python path to allow running as a script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import engine, Base
from backend.database.models import *  # Import all models so they are registered on Base

def run_init_db():
    print("Creating all tables in the database...")
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created / verified.")

if __name__ == "__main__":
    run_init_db()
