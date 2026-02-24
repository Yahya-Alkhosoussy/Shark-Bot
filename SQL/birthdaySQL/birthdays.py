import sqlite3

conn = sqlite3.connect(r"databases/birthdays.db")
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS birthdays
                        (id INTEGER PRIMARY KEY, name TEXT UNIQUE, discord_id BIGINT NOT NULL, birthday TEXT NOT NULL)""")


def add_birthday(username: str, user_id: int, birthday: str):
    try:
        cur.execute(
            "INSERT OR IGNORE INTO birthdays (name, discord_id, birthday) VALUES (?, ?, ?)", (username, user_id, birthday)
        )
        conn.commit()
    except sqlite3.OperationalError as e:
        raise e


def get_birthdays() -> tuple[list[int], list[str]]:
    cur.execute("SELECT discord_id, birthday FROM birthdays")
    rows = cur.fetchall()
    ids: list[int] = []
    birthdays: list[str] = []
    for row in rows:
        ids.append(row[0])
        birthdays.append(row[1])

    return ids, birthdays
