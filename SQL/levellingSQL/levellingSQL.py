import sqlite3, logging
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
        info.extend(row) # breaks to tuple into individual indicies

    level_up = False

    if info[indicies.EXP.value] >= info[indicies.UNTIL_NEXT_LEVEL.value]:
        level_up = True
        info[indicies.LEVEL.value] += 1
        info[indicies.EXP.value] = 0
        info[indicies.UNTIL_NEXT_LEVEL.value] += calculate_xp_needed(username=username)
        cur.execute(f"UPDATE level SET level={info[indicies.LEVEL.value]} WHERE username='{username}'")
        cur.execute(f"UPDATE level SET exp={info[indicies.EXP.value]} WHERE username='{username}'")
        cur.execute(f"UPDATE level SET until_next_level={info[indicies.UNTIL_NEXT_LEVEL.value]} WHERE username='{username}'")
    connection.commit() # pushes changes to database

    return level_up

def calculate_xp_needed(username: str) -> int:
    """
    This function is to calculate the XP needed for the next level
    
    :param username: The user's username
    :type username: str
    """
    level, xp_needed = cur.execute("SELECT level, until_next_level FROM level WHERE username=?", (username,)).fetchone()


    if level >= 0 and level <= 4:
        xp_needed += 10
    elif level > 4 and level <= 8:
        xp_needed += 20
    elif level > 8 and level <= 12:
        xp_needed += 30
    elif level > 12 and level <= 16:
        xp_needed += 40
    elif level > 16 and level <= 20:
        xp_needed += 50
    elif level > 20 and level <= 24:
        xp_needed += 60
    elif level > 24 and level <= 28:
        xp_needed += 70
    elif level > 28 and level <= 32:
        xp_needed += 80
    elif level > 32 and level <= 36:
        xp_needed += 90
    elif level > 36 and level % 4 == 0:
        xp_needed += 100

    return xp_needed
"""
The result of the function above:
30
40
50
60
70
90
110
130
150
180
210
240
270
310
350
390
430
480
530
580
630
690
750
810
870
940
1010
1080
1150
1230
1310
1390
1470
1560
1650
1740
1830
1830
1830
1830
1930
1930
1930
1930
2030
2030
2030
2030
2130
2130
2130
2130
2230
2230
2230
2230
2330
2330
2330
2330
2430
2430
2430
2430
2530
2530
2530
2530
2630
2630
2630
2630
2730
2730
2730
2730
2830
2830
2830
2830
2930
2930
2930
2930
3030
3030
3030
3030
3130
3130
3130
3130
3230
3230
3230
3230
3330
3330
3330
3330
"""

def get_info(username: str):
    """
    Docstring for get_info
    
    :param username: The user's username
    :type username: str
    """
    
    info = []
    for row in cur.execute("SELECT * FROM level WHERE username=?", (username,)):
        info.extend(row)
    
    return info[indicies.LEVEL.value], info[indicies.EXP.value], info[indicies.UNTIL_NEXT_LEVEL.value], get_rank(username=username)
    


def add_user(username: str):
    """
    Docstring for add_user
    
    :param username: The user's username
    :type username: str
    """
    rows: tuple = (username, 0, 0, 30)
    cur.execute(f"INSERT OR IGNORE INTO level (username, level, exp, until_next_level) VALUES (?, ?, ?, ?)", rows)
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
    for row in cur.execute(f"SELECT * FROM level WHERE username=?", (username,)):
        info.extend(row) # breaks to tuple into individual indicies
    
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

    rank = cur.execute("SELECT COUNT(*) + 1 FROM level WHERE level > ? OR (level = ? AND exp > ?)", (level, level, exp)).fetchone()[0]
    return rank


def get_leaderboard():
    rows = []
    for row in cur.execute("SELECT username, level FROM level ORDER BY level DESC, exp DESC"):
        rows.extend(row)
    return rows

# add_user("spiderbyte2007")
# add_to_level("spiderbyte2007", False, 2)
# add_user("spider")
# add_to_level("spider", False, 2)
# add_to_level("spider", False, 2)
# print(get_leaderboard())

connection.commit() # pushes changes to database