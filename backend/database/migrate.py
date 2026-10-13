import sqlite3
import os
import sys
import shutil
from datetime import datetime

# Ensure we can import backend packages
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.core.security import hash_password

def run_migrations():
    # Correct path to database/tasks.db
    db_path = "database/tasks.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. meetings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meetings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            audio_path TEXT,
            transcript TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER,
            description TEXT,
            assigned_to INTEGER,
            assigned_by INTEGER,
            deadline TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 4. nlp_results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nlp_results (
            meeting_id INTEGER PRIMARY KEY,
            summary TEXT,
            action_items TEXT,
            decisions TEXT,
            risks TEXT,
            sentiment TEXT,
            productivity_score INTEGER,
            deadlines TEXT,
            assignments TEXT
        )
    ''')

    # 5. notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            message TEXT,
            type TEXT,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute("PRAGMA table_info(notifications)")
    cols = [col[1] for col in cursor.fetchall()]
    if 'title' not in cols:
        cursor.execute('ALTER TABLE notifications ADD COLUMN title TEXT')
    if 'type' not in cols:
        cursor.execute('ALTER TABLE notifications ADD COLUMN type TEXT')

    conn.commit()
    conn.close()
    print("Database migrations applied to database/tasks.db successfully.")

if __name__ == "__main__":
    run_migrations()
