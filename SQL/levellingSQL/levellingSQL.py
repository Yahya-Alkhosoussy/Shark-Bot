import logging
import sqlite3
from enum import Enum

# ====== Logging ======
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="a")
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)

connection = sqlite3.connect("databases/leveling_shark.db")
cur = connection.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS level
                        (username TEXT PRIMARY KEY, level INTEGER, exp INTEGER, until_next_level INTEGER)""")


class indicies(Enum):
    USERNAME = 0
    LEVEL = 1
    EXP = 2
    UNTIL_NEXT_LEVEL = 3


def check_level(username: str):
    """
    Docstring for check_level

    :param username: The user's username
    :type username: str

    :return level_up: Whether or not the user has levelled up
    """
    info = []
    for row in cur.execute("SELECT * FROM level WHERE username=?", (username,)):
        info.extend(row)  # breaks to tuple into individual indicies

    level_up = False

    if info[indicies.EXP.value] >= info[indicies.UNTIL_NEXT_LEVEL.value]:
        level_up = True
        info[indicies.LEVEL.value] += 1
        info[indicies.EXP.value] = 0
        info[indicies.UNTIL_NEXT_LEVEL.value] = calculate_xp_needed(username=username)
        cur.execute(f"UPDATE level SET level={info[indicies.LEVEL.value]} WHERE username='{username}'")
        cur.execute(f"UPDATE level SET exp={info[indicies.EXP.value]} WHERE username='{username}'")
        cur.execute(f"UPDATE level SET until_next_level={info[indicies.UNTIL_NEXT_LEVEL.value]} WHERE username='{username}'")
    connection.commit()  # pushes changes to database

    return level_up


def calculate_xp_needed(username: str) -> int:
    """
    This function is to calculate the XP needed for the next level

    :param username: The user's username
    :type username: str
    """
    xp_needed = cur.execute("SELECT until_next_level FROM level WHERE username=?", (username,)).fetchone()[0]

    xp_needed += 50

    return xp_needed


def get_info(username: str):
    """
    Docstring for get_info

    :param username: The user's username
    :type username: str
    """

    info = []
    for row in cur.execute("SELECT * FROM level WHERE username=?", (username,)):
        info.extend(row)

    return (
        info[indicies.LEVEL.value],
        info[indicies.EXP.value],
        info[indicies.UNTIL_NEXT_LEVEL.value],
        get_rank(username=username),
    )


def add_user(username: str):
    """
    Docstring for add_user

    :param username: The user's username
    :type username: str
    """
    rows: tuple = (username, 0, 0, 50)
    cur.execute("INSERT OR IGNORE INTO level (username, level, exp, until_next_level) VALUES (?, ?, ?, ?)", rows)
    connection.commit()
    if cur.rowcount > 0:
        logging.info(f"[LEVELING SYSTEM] {username} was added to the leveling database")
        return True
    return False


def add_to_level(username: str, boost: bool, boost_amount: int):
    """
    Docstring for add_to_level

    :param username: The user's username
    :type username: str
    :param boost: Whether or not a boost event is active
    :type boost: bool
    :param boost_amount: How much is the boosted amount
    :type boost_amount: int
    """
    info = []
    for row in cur.execute("SELECT * FROM level WHERE username=?", (username,)):
        info.extend(row)  # breaks to tuple into individual indicies

    if not boost:
        info[indicies.EXP.value] += 2
    else:
        info[indicies.EXP.value] += 2 * boost_amount

    cur.execute(f"UPDATE level SET exp={info[indicies.EXP.value]} WHERE username=?", (username,))
    connection.commit()


def get_rank(username: str):
    data = cur.execute("SELECT level, exp FROM level WHERE username=?", (username,)).fetchone()

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
        # cur.execute(f"UPDATE level SET level=0 WHERE username='{row[indicies.USERNAME.value]}'")
    print(levels_gained)
    print(exp_gained)
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


reset_levels()

# add_user("spiderbyte2007")
# add_to_level("spiderbyte2007", False, 2)
# add_user("spider")
# add_to_level("spider", False, 2)
# add_to_level("spider", False, 2)
# print(get_leaderboard())

connection.commit()  # pushes changes to database
