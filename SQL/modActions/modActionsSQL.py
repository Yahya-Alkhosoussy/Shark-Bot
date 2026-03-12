import sqlite3
from datetime import datetime

conn = sqlite3.connect(r"databases/twitch_stuff")
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS bans
            (
                id PRIMARY KEY,
                streamer TEXT,
                banned_user TEXT,
                reason TEXT,
                mod_that_banned_them TEXT,
                when_banned TEXT,
                UNIQUE(streamer, banned_user)
            )""")

cur.execute("""CREATE TABLE IF NOT EXISTS timeouts
            (
                id PRIMARY KEY,
                streamer TEXT,
                timed_out_user TEXT,
                reason TEXT,
                mod_that_timed_them_out TEXT,
                duration INTEGER,
                when_timed_out TEXT
            )""")


def add_ban(streamer: str, user: str, reason: str | None, mod: str, when: datetime):
    when_str = when.strftime(r"%Y-%m-%d %H:%M")
    cur.execute(
        "INSERT OR IGNORE INTO bans (streamer, banned_user, reason, mod_that_banned_them, when_banned) VALUES (?, ?, ?, ?, ?)",
        (streamer, user, reason, mod, when_str),
    )


def add_timeout(streamer: str, user: str, reason: str | None, mod: str, when: datetime, duration: int):
    when_str = when.strftime(r"%Y-%m-%d %H:%M")
    cur.execute(
        """INSERT OR IGNORE INTO timeouts (streamer, time_out_user, reason, mod_that_timed_them_out, duration, when_timed_out)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (streamer, user, reason, mod, duration, when_str),
    )


def get_bans(amount: int | None = None) -> list[tuple[str, str, str, str, str]]:
    cur.execute("SELECT * FROM bans ORDER BY when_banned DESC")
    rows = cur.fetchall()
    if amount is None:
        return rows

    to_return: list[tuple[str, str, str, str, str]] = []
    i = 0
    for row in rows:
        if i != amount:
            to_return.append(row)
            i += 1
        else:
            break
    return to_return


def get_timeouts(amount: int | None = None) -> list[tuple[str, str, str, str, int, str]]:
    cur.execute("SELECT * FROM timeouts ORDER BY when_timed_out DESC")
    rows = cur.fetchall()
    if amount is None:
        return rows

    to_return: list[tuple[str, str, str, str, int, str]] = []
    i = 0
    for row in rows:
        if i != amount:
            to_return.append(row)
            i += 1
        else:
            break
    return to_return


def get_streamers() -> set[str]:
    cur.execute("SELECT streamer FROM bans")
    ban_rows = cur.fetchall()
    cur.execute("SELECT streamer FROM timeouts")
    timeout_rows = cur.fetchall()

    ban_set = set(ban_rows)
    timeout_set = set(timeout_rows)

    return ban_set | timeout_set
