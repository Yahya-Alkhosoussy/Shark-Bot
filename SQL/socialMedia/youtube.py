import sqlite3

conn = sqlite3.connect("databases/social media/youtube.db")
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS videos
    (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        handle TEXT NOT NULL,
        video_title TEXT NOT NULL,
        video_id INTEGER NOT NULL,
        video_url TEXT UNIQUE NOT NULL,
        UNIQUE (video_title, video_id)
    )
    """
)


def add_video(youtube_handle: str, title: str, id: int, url: str):
    cur.execute(
        "INSERT OR IGNORE INTO videos (handle, video_title, video_id, video_url) VALUES (?, ?, ?, ?)",
        (youtube_handle, title, id, url),
    )
    conn.commit()


def is_video_existing(url: str) -> bool:
    cur.execute("SELECT COUNT(*) FROM videos WHERE video_url=?", (url,))
    if cur.fetchone()[0] != 0:
        return True
    return False


def get_youtube_handles() -> list[str]:
    cur.execute("SELECT handle FROM videos")
    return cur.fetchall()


def get_video_title(id: int) -> str:
    cur.execute("SELECT video_title FROM videos WHERE video_id=?", (id,))
    return cur.fetchone()[0]


def get_video_url(id: int) -> str:
    cur.execute("SELECT video_url FROM videos WHERE video_id=?", (id,))
    return cur.fetchone()[0]
