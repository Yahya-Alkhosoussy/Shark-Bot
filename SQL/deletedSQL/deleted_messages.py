import sqlite3
from datetime import datetime, timedelta

from exceptions.exceptions import ItemNotFound

conn = sqlite3.connect("databases/deleted_messages.db")
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS deleted
    (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        display_name TEXT,
        user_id BIGINT NOT NULL,
        message_content TEXT,
        image_path TEXT,
        channel_id BIGINT,
        deleted_at TEXT
    )
    """
)


def add_deleted_message(
    username: str,
    user_id: int,
    channel_id: int,
    message_content: str,
    deleted_at: datetime,
    image_path: str | None = None,
    display_name: str | None = None,
):
    check_for_username_or_display_name_change(username, display_name, user_id)
    cur.execute(
        """INSERT OR IGNORE INTO deleted
        (
            username,
            user_id,
            channel_id,
            message_content,
            deleted_at,
            image_path,
            display_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (username, user_id, channel_id, message_content, deleted_at.strftime(r"%Y-%m-%d %H:%M:%S"), image_path, display_name),
    )

    conn.commit()


def get_user_id(username: str) -> int:
    cur.execute("SELECT user_id FROM deleted WHERE username=?", (username,))
    result = cur.fetchone()
    if result is None:
        cur.execute("SELECT user_id FROM deleted WHERE display_name=?", (username,))
        result = cur.fetchone()
        if result is None:
            raise ItemNotFound("Could not find user ID", 1012)
    return result[0]


def get_deleted_messages(user_id: int, time: datetime):

    cur.execute("SELECT message_content, image_path, deleted_at FROM deleted WHERE user_id=?", (user_id,))
    results = cur.fetchall()
    messages: list[str] = []
    image_paths: list[str | None] = []
    deleted_at: list[str] = []
    for result in results:
        _deleted_at = result[2]
        if time - datetime.strptime(_deleted_at, r"%Y-%m-%d %H:%M:%S") <= timedelta(7):
            messages.append(result[0])
            image_paths.append(result[1])
            deleted_at.append(_deleted_at)

    return messages, image_paths, deleted_at


def check_for_username_or_display_name_change(new_username: str, new_display_name: str | None, user_id: int):
    cur.execute("SELECT username, display_name FROM deleted WHERE user_id=?", (user_id,))
    results = cur.fetchone()
    username = results[0]
    display_name = results[1]

    if username != new_username:
        cur.execute("UPDATE deleted SET username=? WHERE user_id=?", (new_username, user_id))
    if display_name != new_display_name:
        cur.execute("UPDATE deleted SET display_name=? WHERE user_id=?", (new_display_name, user_id))

    conn.commit()
