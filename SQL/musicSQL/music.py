import sqlite3
from pathlib import Path

conn = sqlite3.connect(Path("databases/music.db"))
cur = conn.cursor()

cur.execute(
    """CREATE TABLE IF NOT EXISTS music
    (
        id INTEGER PRIMARY KEY,
        song_and_author TEXT,
        song_url TEXT,
        added_by INTEGER
    )"""
)


def add_song(song_name: str, song_url: str, requested_by: int):
    cur.execute(
        "INSERT OR IGNORE INTO music (song_and_author, song_url, added_by) VALUES (?, ?, ?)",
        (song_name, song_url, requested_by),
    )
    conn.commit()


def remove_song(song_name: str):
    cur.execute("DELETE FROM music WHERE song_and_author=?", (song_name))
    conn.commit()


def clear_queue():
    cur.execute("DELETE FROM music")
    conn.commit()


def get_song() -> tuple[str, str, int]:
    cur.execute("SELECT song_and_author, song_url, added_by FROM music ORDER BY ID ASC")
    result = cur.fetchone()
    return result
