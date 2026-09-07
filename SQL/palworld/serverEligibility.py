from datetime import datetime, timedelta
from pathlib import Path
from sqlite3 import connect

if not Path("databases/palworld").exists():
    Path("databases/palworld").mkdir()

conn = connect("databases/palworld/eligibility.db")

conn.execute(
    """CREATE TABLE IF NOT EXISTS users
    (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        eligible BOOLEAN DEFAULT 0,
        num_of_msgs INTEGER DEFAULT 0,
        follow_start TEXT DEFAULT 0
    )"""
)

conn.commit()


def add_user(twitch_username: str, eligible: bool, follow_start: datetime, num_of_msgs: int | None = None):
    if not num_of_msgs:
        num_of_msgs = 0

    follow_start_str = datetime.strftime(follow_start, r"%Y-%m-%s %H:%M:%S")

    conn.execute(
        "INSERT OR IGNORE INTO users (username, eligible, num_of_msgs, follow_start) VALUES (?, ?, ?, ?)",
        (twitch_username, eligible, num_of_msgs, follow_start_str),
    )
    conn.commit()


def add_to_num_of_msgs(twitch_username: str):
    conn.execute("UPDATE users SET num_of_msgs=num_of_msgs+1 WHERE username=?", (twitch_username,))
    conn.commit()


def check_eligibility(twitch_username: str):
    cur = conn.execute("SELECT eligible FROM users WHERE username=?", (twitch_username,))
    result = cur.fetchone()[0]
    if result:
        return True
    cur = conn.execute("SELECT num_of_msgs, follow_start FROM users WHERE username=?", (twitch_username,))
    result = cur.fetchone()
    if result[0] >= 10 and timedelta(7) > datetime.now() - datetime.strptime(result[1], r"%Y-%m-%s %H:%M:%S"):
        conn.execute("UPDATE eligible=1 WHERE username=?", (twitch_username,))
        conn.commit()
        return True
    return False
