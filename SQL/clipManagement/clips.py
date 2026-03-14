import sqlite3
from typing import overload

from utils.pullingFromTwitch import is_live

conn = sqlite3.connect("databases/clips.db")
cur = conn.cursor()

cur.execute("""CREATE IF NOT EXISTS clip_channels
            (discord_id INTEGER PRIMARY KEY, username TEXT, dms BOOLEAN NOT NULL, channel_id INTEGER)""")

cur.execute("""CREATE IF NOT EXISTS is_live
            (discord_id INTEGER PRIMARY KEY, username TEXT, user TEXT, is_live BOOLEAN)""")


def add_user(discord_id: int, user: str, username: str, dms: bool, channel_id: int | None = None):
    cur.execute(
        "INSERT OR IGNORE INTO clip_channels (discord_id, username, dms, channel_id) VALUES (?, ?, ?, ?)",
        (discord_id, username, dms, channel_id),
    )
    live = is_live(user, username)
    cur.execute(
        "INSERT OR IGNORE INTO is_live (discord_id, username, user, is_live) VALUES (?, ?, ?)",
        (discord_id, username, user, live),
    )
    conn.commit()


@overload
def check_live(id: int) -> bool: ...


@overload
def check_live(id: str) -> bool: ...


def check_live(id: int | str) -> bool:
    if isinstance(id, int):
        cur.execute("SELECT is_live FROM is_live WHERE discord_id=?", (id,))
    else:
        cur.execute("SELECT is_live FROM is_live WHERE username=?", (id,))
    return bool(cur.fetchone()[0])


@overload
def update_live(id: int) -> bool: ...


@overload
def update_live(id: str) -> bool: ...


def update_live(id: int | str) -> bool:
    if isinstance(id, int):
        cur.execute("SELECT username, user, is_live FROM is_live WHERE discord_id=?", (id,))
        username, user, live = cur.fetchall()
        new_live = is_live(user, username)
        if live != new_live:
            cur.execute("UPDATE is_live SET is_live=? WHERE discord_id=?", (new_live, id))
            conn.commit()
            return True

        return False
    else:
        cur.execute("SELECT user, is_live FROM is_live WHERE username=?", (id,))
        user, live = cur.fetchall()
        new_live = is_live(user, id)
        if live != new_live:
            cur.execute("UPDATE is_live SET is_live=? WHERE username=?", (new_live, id))
            conn.commit()
            return True

        return False


def get_channel(discord_id: int) -> int:
    cur.execute("SELECT dms FROM clip_channels WHERE discord_id=?", (discord_id,))
    dms = cur.fetchone()[0]

    if dms:
        return 1

    cur.execute("SELECT channel_id FROM clip_channels WHERE discord_id=?", (discord_id,))

    return cur.fetchone()[0]


def get_users() -> tuple[list[str], list[int]]:
    cur.execute("SELECT username, discord_id FROM clip_channels")
    rows = cur.fetchall()

    usernames: list[str] = []
    discord_ids: list[int] = []

    for row in rows:
        usernames.append(row[0])
        discord_ids.append(row[1])

    return usernames, discord_ids


def get_discord_id(username: str) -> int:
    cur.execute("SELECT discord_id FROM clip_channels WHERE username=?", (username,))
    return cur.fetchone()[0]


def get_nick(username: str) -> str:
    cur.execute("SELECT user FROM is_live WHERE username=?", (username,))
    return cur.fetchone()[0]
