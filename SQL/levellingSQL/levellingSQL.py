import logging
import sqlite3
from enum import Enum
from typing import Any, Sequence

import discord

connection = sqlite3.connect("databases/leveling_shark.db")
cur = connection.cursor()

cur.execute(
    """CREATE TABLE IF NOT EXISTS level
            (username TEXT PRIMARY KEY, level INTEGER, exp INTEGER, until_next_level INTEGER, user_id BIGINT DEFAULT 0)"""
)


class indicies(Enum):
    USERNAME = 0
    LEVEL = 1
    EXP = 2
    UNTIL_NEXT_LEVEL = 3


def check_level(user_id: int):
    """
    Docstring for check_level

    :param username: The user's username
    :type username: str

    :return level_up: Whether or not the user has levelled up
    """
    info = []
    for row in cur.execute("SELECT * FROM level WHERE user_id=?", (user_id,)):
        info.extend(row)  # breaks to tuple into individual indicies

    level_up = False

    if info[indicies.EXP.value] >= info[indicies.UNTIL_NEXT_LEVEL.value]:
        level_up = True
        info[indicies.LEVEL.value] += 1
        info[indicies.EXP.value] = 0
        info[indicies.UNTIL_NEXT_LEVEL.value] = calculate_xp_needed(user_id=user_id)
        cur.execute(f"UPDATE level SET level={info[indicies.LEVEL.value]} WHERE user_id='{user_id}'")
        cur.execute(f"UPDATE level SET exp={info[indicies.EXP.value]} WHERE user_id='{user_id}'")
        cur.execute(f"UPDATE level SET until_next_level={info[indicies.UNTIL_NEXT_LEVEL.value]} WHERE user_id='{user_id}'")
    connection.commit()  # pushes changes to database

    return level_up


def add_column_to_level(cur: sqlite3.Cursor, column_name: str, column_type: str, default_value: Any):
    try:
        cur.execute(f"ALTER TABLE level ADD COLUMN {column_name} {column_type} DEFAULT {default_value}")
    except sqlite3.OperationalError as e:
        print(f"Warning, error: {e}")


def calculate_xp_needed(user_id: int) -> int:
    """
    This function is to calculate the XP needed for the next level

    :param username: The user's username
    :type username: str
    """
    xp_needed = cur.execute("SELECT until_next_level FROM level WHERE user_id=?", (user_id,)).fetchone()[0]

    xp_needed += 50

    return xp_needed


def get_info(user_id: int) -> tuple[int, int, int, int]:
    """
    Docstring for get_info

    :param username: The user's username
    :type username: str
    """

    info = []
    for row in cur.execute("SELECT * FROM level WHERE user_id=?", (user_id,)):
        info.extend(row)

    rank = get_rank(user_id=user_id)
    assert rank is not None

    return (
        info[indicies.LEVEL.value],
        info[indicies.EXP.value],
        info[indicies.UNTIL_NEXT_LEVEL.value],
        rank,
    )


def add_user(username: str, user_id: int):
    """
    Docstring for add_user

    :param username: The user's username
    :type username: str
    """
    rows: tuple = (username, 0, 0, 50, user_id)
    cur.execute("INSERT OR IGNORE INTO level (username, level, exp, until_next_level, user_id) VALUES (?, ?, ?, ?, ?)", rows)
    connection.commit()
    if cur.rowcount > 0:
        logging.info(f"[LEVELING SYSTEM] {username} was added to the leveling database")
        return True
    return False


def add_to_level(username: str, user_id: int, boost: bool, boost_amount: int):
    """
    Docstring for add_to_level

    :param username: The user's username
    :type username: str
    :param boost: Whether or not a boost event is active
    :type boost: bool
    :param boost_amount: How much is the boosted amount
    :type boost_amount: int
    """
    if check_for_username_change(username, user_id):
        cur.execute("UPDATE level SET username=? WHERE user_id=?", (username, user_id))
        connection.commit()

    info = []
    for row in cur.execute("SELECT * FROM level WHERE username=?", (username,)):
        info.extend(row)  # breaks to tuple into individual indicies

    if not boost:
        info[indicies.EXP.value] += 2
    else:
        info[indicies.EXP.value] += 2 * boost_amount

    cur.execute(f"UPDATE level SET exp={info[indicies.EXP.value]} WHERE username=?", (username,))
    connection.commit()


def check_for_username_change(username: str, user_id: int) -> bool:
    cur.execute("SELECT DISTINCT username FROM level WHERE user_id=?", (user_id,))
    result = cur.fetchall()
    if len(result) > 1 or result[0] != username:
        return True
    return False


def get_rank(user_id: int) -> int | None:
    data = cur.execute("SELECT level, exp FROM level WHERE user_id=?", (user_id,)).fetchone()

    if not data:
        return None

    level, exp = data

    rank = cur.execute(
        "SELECT COUNT(*) + 1 FROM level WHERE level > ? OR (level = ? AND exp > ?)", (level, level, exp)
    ).fetchone()[0]
    return rank


def get_leaderboard():
    rows = []
    for row in cur.execute("SELECT username, level FROM level ORDER BY level DESC, exp DESC"):
        rows.extend(row)
    return rows


def reset_levels():
    cur.execute("SELECT * FROM level")
    rows: list = cur.fetchall()
    levels_gained: dict[str, int] = {}  # username: level
    exp_gained: dict[str, int] = {}  # username: exp

    for row in rows:
        levels_gained[row[indicies.USERNAME.value]] = row[indicies.LEVEL.value]
        exp_gained[row[indicies.USERNAME.value]] = row[indicies.EXP.value]
    logging.info(f"Here are the levels gained: {levels_gained}")
    logging.info(f"Here's the exp gained: {exp_gained}")
    for user in levels_gained:
        print("This is for user: ", user)
        xp_from_levels = 30
        for i in range(1, levels_gained[user]):
            if i < 4:
                xp_from_levels += xp_from_levels + 10
            else:
                xp_from_levels += xp_from_levels + 20
            print(xp_from_levels)
            exp_gained[user] += xp_from_levels
        print("This is exp_gained after applying xp from levels: ", exp_gained[user])

    list_of_levels = [50 * i for i in range(1, 100)]

    for user in exp_gained:
        print("This is for user: ", user)
        level = 0
        for i in range(0, exp_gained[user], 2):
            if i == list_of_levels[level]:
                level += 1
        exp_gained[user] = exp_gained[user] - list_of_levels[level - 1]
        print("reached level: ", level)
        print("xp gained: ", exp_gained[user], "xp needed for next level: ", list_of_levels[level] - exp_gained[user])
        cur.execute("UPDATE level SET level=? WHERE username=?", (level, user))
        cur.execute("UPDATE level SET exp=? WHERE username=?", (exp_gained[user], user))
        cur.execute("UPDATE level SET until_next_level=? WHERE username=?", (list_of_levels[level], user))
        connection.commit()


# reset_levels()
def level_0_xp_reset():
    cur.execute("SELECT user_id, exp FROM level WHERE level=0")
    info = cur.fetchall()
    user_to_xp: dict[int, int] = {}  # user_id to xp gained
    for user, exp in info:
        user_to_xp[user] = exp

        if user_to_xp[user] < 0:
            user_to_xp[user] += 5000
            cur.execute("UPDATE level SET exp=? WHERE user_id=?", (user_to_xp[user], user))
            check_level(user_id=user)

    connection.commit()


def add_user_ids_to_table(guild_members: Sequence[discord.Member]):
    conn = sqlite3.connect("databases/leveling_shark.db")
    cur = conn.cursor()
    known_duplicates: dict[int, tuple[str, str]] = {
        682614503636336699: ("sour__gravity", "chasing_gravity"),
        232569360357654529: ("priestessmary", "vampire_priestess"),
    }
    add_column_to_level(cur, "user_id", "BIGINT", 0)

    for member in guild_members:
        if member.id in known_duplicates:
            user = known_duplicates[member.id]
            old_info: tuple[int, int] = cur.execute("SELECT level, exp FROM level WHERE username=?", (user[0],)).fetchall()[
                0
            ]  # old username
            old_level, old_exp = old_info
            info: tuple[int, int] = cur.execute("SELECT level, exp FROM level WHERE username=?", (user[1],)).fetchall()[0]
            level, exp = info
            new_level = old_level + level
            new_exp = old_exp + exp
            cur.execute(
                """UPDATE level
                SET level=?, exp=?, user_id=?, until_next_level=?
                WHERE username=?""",
                (new_level, new_exp, member.id, new_level * 50, user[1]),
            )
            cur.execute("DELETE FROM level WHERE username=?", (user[0],))
        else:
            cur.execute("UPDATE level SET user_id=? WHERE username=?", (member.id, member.name))
    conn.commit()


# print(cur.execute("SELECT * FROM level").fetchall())

# add_user("spiderbyte2007")
# add_to_level("spiderbyte2007", False, 2)
# add_user("spider")
# add_to_level("spider", False, 2)
# add_to_level("spider", False, 2)
# print(get_leaderboard())

connection.commit()  # pushes changes to database
