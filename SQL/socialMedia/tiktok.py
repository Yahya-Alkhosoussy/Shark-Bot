import sqlite3

conn = sqlite3.connect("databases/social media/tiktok.db")
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS tiktok_videos
            (
                id INTEGER PRIMARY KEY,
                link TEXT UNIQUE
            )
            """)


def add_link(link: str, video_id: int):
    cur.execute("INSERT OR IGNORE INTO tiktok_videos (link, id) VALUES (?, ?)", (link, id))
    conn.commit()


def check_if_link_exists(link: str) -> bool:
    cur.execute("SELECT COUNT(id) FROM tiktok_videos WHERE link=?", (link,))
    count = cur.fetchone()[0]
    if count != 0:
        return False
    return True
