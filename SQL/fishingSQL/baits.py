import logging
import sqlite3
from pathlib import Path

from utils.fishing import FishingConfig

config = FishingConfig(Path(r"fishing\fishing.yaml"))
logging
conn = sqlite3.connect("databases/fishing.db")
cur = conn.cursor()

# Initialise table if it does not exist
cur.execute("""CREATE TABLE IF NOT EXISTS fish
            (
                username TEXT PRIMARY KEY,
                large_common_fish INTEGER DEFAULT 0,
                large_shiny_fish INTEGER DEFAULT 0,
                large_legendary_fish INTEGER DEFAULT 0,
                medium_common_fish INTEGER DEFAULT 0,
                medium_shiny_fish INTEGER DEFAULT 0,
                medium_legendary_fish INTEGER DEFAULT 0,
                small_common_fish INTEGER DEFAULT 0,
                small_shiny_fish INTEGER DEFAULT 0,
                small_legendary_fish INTEGER DEFAULT 0
            )""")

cur.execute("""CREATE TABLE IF NOT EXISTS baits
            (
                username TEXT PRIMARY KEY,
                chum INTEGER DEFAULT 0,
                bait_ball INTEGER DEFAULT 0,
                mackerel INTEGER DEFAULT 0,
                stingray INTEGER DEFAULT 0,
                barracuda INTEGER DEFAULT 0
            )""")

cur.execute("""CREATE TABLE IF NOT EXISTS baits_shop
            (
                name TEXT PRIMARY KEY,
                price REAL
            )""")


def set_up_shop():
    ""
    baits_to_prices = config.baits
    tup: list[tuple] = [(name, bait[2]) for name, bait in baits_to_prices]
    cur.executemany("INSERT OR IGNORE INTO baits_shop (name, price) VALUES (?, ?)", tup)
    conn.commit()


def get_baits(username: str):
    """
    Returns available baits and the number of uses left.

    :param username: Description
    :type username: str
    """
    baits: dict[int, str] = {1: "chum", 2: "bait ball", 3: "mackerel", 4: "stingray", 5: "barracuda"}
    all_baits = []
    try:
        all_baits.extend(
            cur.execute("SELECT chum, bait_ball, mackerel, stingray, barracuda FROM baits WHERE username=?", (username,))
        )
    except sqlite3.OperationalError as e:
        raise e

    available_baits = []
    for i in range(len(all_baits[0])):
        if all_baits[0][i] > 0:
            available_baits.append(baits[i + 1])

    return available_baits


cur.execute("INSERT OR IGNORE INTO baits (username, chum, mackerel) VALUES (?, ?, ?)", ("spiderbyte2007", 2, 15))
get_baits("spiderbyte2007")
