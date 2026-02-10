import logging
import sqlite3

logging
conn = sqlite3.connect("databases/fishing")
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
                stringray INTEGER DEFAULT 0,
                barracuda INTEGER DEFAULT 0
            )""")

cur.execute("""CREATE TABLE IF NOT EXISTS baits_shop
            (
                name TEXT PRIMARY KEY,
                price REAL
            )""")


def set_up_shop():
    ""
