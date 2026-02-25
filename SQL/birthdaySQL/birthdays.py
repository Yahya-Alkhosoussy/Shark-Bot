import sqlite3

from exceptions.exceptions import FormatError

conn = sqlite3.connect(r"databases/birthdays.db")
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS birthdays
                    (id INTEGER PRIMARY KEY, name TEXT UNIQUE, discord_id BIGINT NOT NULL UNIQUE, birthday TEXT NOT NULL)""")

cur.execute("""CREATE TABLE IF NOT EXISTS birthday_gifs
                        (id INTEGER PRIMARY KEY, link TEXT UNIQUE)""")

conn.commit()


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


def edit_birthday(username: str, new_birthday: str):
    cur.execute("UPDATE birthdays SET birthday=? WHERE name=?", (new_birthday, username))
    conn.commit()


def add_gif_to_table(link: str):
    try:
        cur.execute("INSERT OR IGNORE INTO birthday_gifs (link) VALUES (?)", (link,))
        conn.commit()
    except sqlite3.OperationalError:
        raise FormatError("Gif could not be added", 1006)


def get_number_of_gifs() -> int:
    cur.execute("SELECT COUNT(id) FROM birthday_gifs")
    return cur.fetchone()[0]


def get_gif(index) -> str:
    try:
        cur.execute("SELECT link FROM birthday_gifs WHERE id=?", (index,))
    except Exception as e:
        print(e)
    return cur.fetchone()[0]
