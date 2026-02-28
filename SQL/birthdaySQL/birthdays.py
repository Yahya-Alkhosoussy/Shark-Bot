import sqlite3

from exceptions.exceptions import FormatError, ItemNotFound

conn = sqlite3.connect(r"databases/birthdays.db")
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS birthdays
                    (id INTEGER PRIMARY KEY, name TEXT UNIQUE, discord_id BIGINT NOT NULL UNIQUE, birthday TEXT NOT NULL, custom_gif_index INTEGER)""")  # noqa: E501

cur.execute("""CREATE TABLE IF NOT EXISTS birthday_gifs
                        (id INTEGER PRIMARY KEY, link TEXT UNIQUE, custom BOOL NOT NULL)""")
cur.execute("""CREATE TABLE IF NOT EXISTS birthday_messages
                        (id INTEGER PRIMARY KEY, message TEXT UNIQUE)""")

conn.commit()


def add_birthday(username: str, user_id: int, birthday: str):
    try:
        cur.execute(
            "INSERT OR IGNORE INTO birthdays (name, discord_id, birthday, custom_gif_index) VALUES (?, ?, ?, ?)",
            (username, user_id, birthday, None),
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
        cur.execute("INSERT OR IGNORE INTO birthday_gifs (link, custom) VALUES (?, ?)", (link, False))
        conn.commit()
    except sqlite3.OperationalError:
        raise FormatError("Gif could not be added", 1006)


def add_custom_gif(ID: int, link: str, username: str):
    try:
        cur.execute("INSERT OR IGNORE INTO birthday_gifs (id, link, custom) VALUES (?, ?)", (ID, link, True))
        cur.execute("UPDATE birthdays SET custom_gif_index=? WHERE name=?", (ID, username))
    except sqlite3.OperationalError:
        raise FormatError("Could not add gif", 1006)
    conn.commit()


def get_number_of_gifs() -> int:
    cur.execute("SELECT COUNT(id) FROM birthday_gifs WHERE custom=0")
    return cur.fetchone()[0]


def get_gif(index: int) -> str:
    try:
        cur.execute("SELECT link FROM birthday_gifs WHERE rowid=? AND custom=0", (index,))
    except Exception:
        raise ItemNotFound("Gif not found!", 1007)
    return cur.fetchone()[0]


def get_custom_gifs(index: int) -> str:
    try:
        cur.execute("SELECT link FROM birthday_gifs WHERE id=?", (index,))
    except Exception:
        raise ItemNotFound("Gif not found", 1007)
    return cur.fetchone()[0]


def get_all_gifs() -> list[str]:
    cur.execute("SELECT link FROM birthday_gifs")
    return cur.fetchall()


def remove_gif(link: str):
    try:
        cur.execute("DELETE FROM birthday_gifs WHERE link=?", (link,))
        conn.commit()
    except sqlite3.OperationalError:
        raise ItemNotFound("Link not found!", 1007)


def add_birthday_message(message: str):
    try:
        cur.execute("INSERT OR IGNORE INTO birthday_messages (message) VALUES (?)", (message,))
        conn.commit()
    except sqlite3.OperationalError:
        raise FormatError("Something went wrong while adding the message", 1002)


def get_birthday_message(index: int) -> str:
    try:
        cur.execute("SELECT message FROM birthday_messages WHERE id=?", (index,))
        return cur.fetchone()[0]
    except sqlite3.OperationalError:
        raise ItemNotFound("Could not get birthday message", 1008)


def get_number_of_messages() -> int:
    cur.execute("SELECT COUNT(id) FROM birthday_messages")
    return cur.fetchone()[0]


def get_all_birthday_messages() -> list[str]:
    cur.execute("SELECT message FROM birthday_messages")
    return cur.fetchall()


def add_custom_message(ID: int, message: str):
    try:
        cur.execute("INSERT OR IGNORE INTO birthday_messages (id, message) VALUES (?, ?)", (ID, message))
    except sqlite3.OperationalError:
        raise FormatError("Could not add custom message", 1009)
    conn.commit()


def remove_message(message: str):
    try:
        cur.execute("DELETE FROM birthday_messages WHERE message=?", (message,))
        conn.commit()
    except sqlite3.OperationalError:
        raise ItemNotFound("Could not find message in database", 1008)


def has_custom_gif(username: str) -> int | None:
    cur.execute("SELECT custom_gif_index FROM birthdays WHERE name=?", (username,))
    return cur.fetchone()[0]
