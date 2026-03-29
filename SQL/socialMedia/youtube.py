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
        video_id TEXT NOT NULL,
        video_url TEXT UNIQUE NOT NULL,
        UNIQUE (video_title, video_id)
    )
    """
)


def add_video(youtube_handle: str, title: str, id: str, url: str):
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


def get_youtube_handles() -> set[str]:
    cur.execute("SELECT handle FROM videos")
    handles: set[str] = set(cur.fetchall())
    return handles


def get_video_title(id: str) -> str:
    cur.execute("SELECT video_title FROM videos WHERE video_id=?", (id,))
    return cur.fetchone()[0]


def get_video_url(id: str) -> str:
    cur.execute("SELECT video_url FROM videos WHERE video_id=?", (id,))
    return cur.fetchone()[0]


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # So it would always run from the most parent directory and avoid import errors
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    import utils.socials.youtubeCore.youtube as y

    items = y.get_video_items(youtube_handle="sharkocalypse")

    for item in items:
        add_video("sharkocalypse", item.snippet.title, item.snippet.resourceId.videoId, item.snippet.url)
