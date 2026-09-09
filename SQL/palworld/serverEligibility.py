from datetime import datetime, timedelta
from pathlib import Path
from sqlite3 import connect

from aiosqlite import connect as aconnect

if not Path("databases/palworld").exists():
    Path("databases/palworld").mkdir()

db_path = Path("databases/palworld/eligibility.db")

conn = connect(db_path)

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


async def add_user(twitch_username: str, eligible: bool, follow_start: datetime, num_of_msgs: int | None = None):
    if not num_of_msgs:
        num_of_msgs = 0

    follow_start_str = datetime.strftime(follow_start, r"%Y-%m-%d %H:%M:%S")
    async with aconnect(db_path) as conn:
        await conn.execute(
            "INSERT OR IGNORE INTO users (username, eligible, num_of_msgs, follow_start) VALUES (?, ?, ?, ?)",
            (twitch_username, eligible, num_of_msgs, follow_start_str),
        )
        await conn.commit()


async def check_if_in_table(twitch_username: str):
    async with aconnect(db_path) as conn:
        cur = await conn.execute("SELECT COUNT(*) FROM users WHERE username=?", (twitch_username,))
        result = await cur.fetchone()
        if result is None:
            return False
        if result[0] > 0:
            return True
        return False


async def add_to_num_of_msgs(twitch_username: str):
    async with aconnect(db_path) as conn:
        await conn.execute("UPDATE users SET num_of_msgs=num_of_msgs+1 WHERE username=?", (twitch_username,))
        await conn.commit()


async def check_eligibility(twitch_username: str):
    async with aconnect(db_path) as conn:
        cur = await conn.execute("SELECT eligible FROM users WHERE username=?", (twitch_username,))
        result = await cur.fetchone()
        if result is None:
            return False
        if result[0]:
            return True

        cur = await conn.execute("SELECT num_of_msgs, follow_start FROM users WHERE username=?", (twitch_username,))
        result = await cur.fetchone()

        if result is None:
            return False
        if timedelta(40) > datetime.now() - datetime.strptime(result[1], r"%Y-%m-%d %H:%M:%S"):
            await conn.execute("UPDATE eligible=1 WHERE username=?", (twitch_username,))
            await conn.commit()
            return True

        if result[0] >= 10 and timedelta(7) > datetime.now() - datetime.strptime(result[1], r"%Y-%m-%d %H:%M:%S"):
            await conn.execute("UPDATE eligible=1 WHERE username=?", (twitch_username,))
            await conn.commit()
            return True
        return False
