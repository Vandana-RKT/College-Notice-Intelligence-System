import os
import sqlite3

DATABASE = os.path.join("instance", "cnis.db")

def get_db_connection():
    os.makedirs("instance", exist_ok=True)
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

def initialize_database():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'student'))
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            notice_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT,
            pdf_filename TEXT NOT NULL,
            extracted_text TEXT,
            extracted_details TEXT,
            summary TEXT,
            status TEXT DEFAULT 'pending'
                CHECK(status IN ('pending', 'published')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            published_at TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS checklist (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            notice_id INTEGER NOT NULL,
            task_name TEXT NOT NULL,
            is_completed INTEGER DEFAULT 0,
            FOREIGN KEY(student_id) REFERENCES users(user_id),
            FOREIGN KEY(notice_id) REFERENCES notices(notice_id),
            UNIQUE(student_id, notice_id, task_name)
        )
    """)
    connection.commit()
    connection.close()
