import sqlite3
from utils.pullingFromTwitch import is_live
from typing import overload

conn = sqlite3.connect("databases/social media/twitch.db")
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS twitch_users
            (
                id INTEGER PRIMARY KEY,
                twitch_username TEXT UNIQUE,
                live_status BOOLEAN,
                custom_message TEXT,
                discord_id INTEGER UNIQUE
            )""")

def add_user(twitch_username: str, discord_id: int, custom_message: str):
    live_status = is_live(username=twitch_username)
    cur.execute("INSERT OR IGNORE INTO twitch_users (twitch_username, discord_id, live_status, custom_message) VALUES (?, ?, ?)", (twitch_username, discord_id, live_status, custom_message))
    conn.commit()

def get_twitch_username(discord_id: int):
    cur.execute("SELECT twitch_username FROM twitch_users WHERE discord_id=?", (discord_id,))
    return cur.fetchone()[0]

@overload
def get_live_status(id: int) -> bool: ...

@overload 
def get_live_status(id: str) -> bool: ...

def get_live_status(id: str | int) -> bool:
    if isinstance(id, int):
        cur.execute("SELECT live_status FROM twitch_users WHERE discord_id=?", (id,))
        return cur.fetchone()[0]
    cur.execute("SELECT live_status FROM twitch_users WHERE twitch_username=?", (id,))
    return cur.fetchone()[0]

def get_custom_message(twitch_username: str):
    cur.execute("SELECT custom_message FROM twitch_users WHERE twitch_username=?", (twitch_username,))
    return cur.fetchone()[0]