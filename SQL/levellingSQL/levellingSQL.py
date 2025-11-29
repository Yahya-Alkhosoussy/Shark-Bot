import sqlite3
from enum import Enum
connection = sqlite3.connect("databases/leveling_shark.db")
cur = connection.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS level
                        (username text PRIMARY KEY, level real, exp real, until_next_level real)""")

class indicies(Enum):
    USERNAME = 0
    LEVEL = 1
    EXP = 2
    UNTIL_NEXT_LEVEL = 3

def check_level(username: str):
    info = []
    for row in cur.execute(f"SELECT * FROM level WHERE username='{username}'"):
        info.extend(row) # breaks to tuple into individual indicies

    if info[indicies.EXP.value] == info[indicies.UNTIL_NEXT_LEVEL.value]:
        info[indicies.LEVEL.value] += 1
        info[indicies.EXP.value] = 0
        info[indicies.UNTIL_NEXT_LEVEL.value] += 20
        cur.execute(f"UPDATE level SET level={info[indicies.LEVEL.value]} WHERE username='{username}'")
        cur.execute(f"UPDATE level SET exp={info[indicies.EXP.value]} WHERE username='{username}'")
        cur.execute(f"UPDATE level SET until_next_level={info[indicies.UNTIL_NEXT_LEVEL.value]} WHERE username='{username}'")
    connection.commit() # pushes changes to database

    return info

def add_user(username: str):
    rows: tuple = [(username, 0, 0, 50)]
    cur.executemany(f"INSERT OR IGNORE INTO level VALUES (?, ?, ?, ?)", rows)

def add_to_level(username: str):
    info = []
    for row in cur.execute(f"SELECT * FROM level WHERE username='{username}'"):
        info.extend(row) # breaks to tuple into individual indicies
    
    info[indicies.EXP.value] += 2

    cur.execute(f"UPDATE level SET exp={info[indicies.EXP.value]} WHERE username='{username}'")
    connection.commit()

    result = check_level(username)
    return result

def get_leaderboard():
    rows = []
    for row in cur.execute("SELECT username, level FROM level ORDER BY level DESC, exp DESC"):
        rows.extend(row)
    return rows

# add_user("spiderbyte2007")
# print(add_to_level("spiderbyte2007"))
# add_user("spider")
# print(add_to_level("spider"))
print(get_leaderboard())

connection.commit() # pushes changes to database