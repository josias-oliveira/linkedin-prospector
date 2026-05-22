import sqlite3
from dataclasses import asdict
from datetime import datetime
from scraper import LinkedInProfile


DB_PATH = "prospects.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prospects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            title TEXT,
            company TEXT,
            location TEXT,
            about TEXT,
            profile_url TEXT UNIQUE,
            recent_post TEXT,
            short_message TEXT,
            long_message TEXT,
            status TEXT DEFAULT 'novo',
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_prospect(profile: LinkedInProfile, messages: dict = None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT OR IGNORE INTO prospects
        (name, title, company, location, about, profile_url, recent_post,
         short_message, long_message, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'novo', ?)
    """, (
        profile.name,
        profile.title,
        profile.company,
        profile.location,
        profile.about,
        profile.profile_url,
        profile.recent_post,
        messages.get("short_message", "") if messages else "",
        messages.get("long_message", "") if messages else "",
        datetime.now().isoformat(),
    ))
    conn.commit()
    conn.close()


def update_status(profile_url: str, status: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE prospects SET status = ? WHERE profile_url = ?",
        (status, profile_url),
    )
    conn.commit()
    conn.close()


def update_messages(profile_url: str, short: str, long: str):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE prospects SET short_message = ?, long_message = ? WHERE profile_url = ?",
        (short, long, profile_url),
    )
    conn.commit()
    conn.close()


def clear_all_prospects():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM prospects")
    conn.commit()
    conn.close()


def get_all_prospects():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM prospects ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
