import logging
import sqlite3
from enum import Enum

import exceptions.exceptions as ex
from SQL.sharkGames.sharkGameSQL import check_currency, remove_coins

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
                price INTEGER,
                catch_chance INTEGER
            )""")


def set_up_shop():
    ""
    baits_to_prices: dict[str, list[int]] = {
        "chum": [15, 35],
        "bait_ball": [30, 35],
        "mackerel": [45, 35],
        "stingray": [60, 35],
        "barracuda": [75, 35],
    }
    tup: list[tuple] = [(name, bait[0], bait[1]) for name, bait in baits_to_prices.items()]
    cur.executemany("INSERT OR IGNORE INTO baits_shop (name, price, catch_chance) VALUES (?, ?, ?)", tup)
    conn.commit()


set_up_shop()


def add_to_shop(bait: str, price: int):
    try:
        cur.execute("INSERT OR IGNORE INTO baits_shop (name, price, catch_chance) VALUES (?, ?, 35)", (bait, price))
    except sqlite3.OperationalError as e:
        raise Exception(f"Ran into an error trying to update the shop: {e}")
    conn.commit()


def update_shop_prices(bait: str, price: int):
    try:
        cur.execute("UPDATE baits_shop SET price=? WHERE name=?", (price, bait))
    except sqlite3.OperationalError as e:
        raise Exception(f"Ran into an error trying to update the shop: {e}")
    conn.commit()


def get_baits(username: str):
    """
    Returns available baits and the number of uses left.

    :param str username: Description
    :return: Tuple containing (available_baits: list[str], uses_per_bait: list[int])
    """
    baits: dict[int, str] = {1: "chum", 2: "bait ball", 3: "mackerel", 4: "stingray", 5: "barracuda"}
    all_baits = []
    try:
        all_baits.extend(
            cur.execute("SELECT chum, bait_ball, mackerel, stingray, barracuda FROM baits WHERE username=?", (username,))
        )
    except sqlite3.OperationalError as e:
        raise Exception(f"Ran into an error trying to get the baits: {e}")

    available_baits: list[str] = []
    uses_per_bait: list[int] = []
    try:
        for i in range(len(all_baits[0])):
            if all_baits[0][i] > 0:
                available_baits.append(baits[i + 1])
                uses_per_bait.append(all_baits[0][i])
    except IndexError as e:
        raise e
    return available_baits, uses_per_bait


def baits_in_shop() -> list[tuple[str, int]]:
    """
    Returns the names and prices of the baits in the shop
    """
    baits: list[tuple[str, int]] = [
        (name.replace("_", " "), price) for name, price in cur.execute("SELECT name, price FROM baits_shop").fetchall()
    ]
    return baits


class baitTypes(Enum):
    CHUM = 1
    BAIT_BALL = 2
    MACKEREL = 3
    STINGRAY = 4
    BARRACUDA = 5
    CHUM_5X = 6
    BAIT_BALL_5X = 7
    MACKEREL_5X = 8
    STINGRAY_5X = 9
    BARRACUDA_5X = 10


def add_fish_caught(username: str, size: str, rarity: str):
    if isinstance(check_user_is_in_baits(username), bool):
        match size:
            case "large":
                match rarity:
                    case "common":
                        cur.execute("UPDATE fish SET large_common_fish = large_common_fish + 1 WHERE username = ?", (username,))
                    case "shiny":
                        cur.execute("UPDATE fish SET large_shiny_fish = large_shiny_fish + 1 WHERE username = ?", (username,))
                    case "legendary":
                        cur.execute(
                            "UPDATE fish SET large_legendary_fish = large_legendary_fish + 1 WHERE username = ?", (username,)
                        )
            case "medium":
                match rarity:
                    case "common":
                        cur.execute(
                            "UPDATE fish SET medium_common_fish = medium_common_fish + 1 WHERE username = ?", (username,)
                        )
                    case "shiny":
                        cur.execute("UPDATE fish SET medium_shiny_fish = medium_shiny_fish + 1 WHERE username = ?", (username,))
                    case "legendary":
                        cur.execute(
                            "UPDATE fish SET medium_legendary_fish = medium_legendary_fish + 1 WHERE username = ?", (username,)
                        )
            case "small":
                match rarity:
                    case "common":
                        cur.execute("UPDATE fish SET small_common_fish = small_common_fish + 1 WHERE username = ?", (username,))
                    case "shiny":
                        cur.execute("UPDATE fish SET small_shiny_fish = small_shiny_fish + 1 WHERE username = ?", (username,))
                    case "legendary":
                        cur.execute(
                            "UPDATE fish SET small_legendary_fish = small_legendary_fish + 1 WHERE username = ?", (username,)
                        )

    conn.commit()


def get_fish_caught(username: str):
    cur.execute("SELECT * FROM fish WHERE username=?", (username,))
    row = cur.fetchone()
    return row


def check_user_is_in_baits(username: str) -> bool | str:
    cur.execute("SELECT EXISTS(SELECT 1 FROM baits WHERE username = ?)", (username,))
    exists = cur.fetchone()[0]  # Returns 1 if exists, 0 if not
    if exists:
        return True
    else:
        cur.execute("INSERT OR IGNORE INTO baits (username) VALUES (?)", (username,))
        cur.execute("INSERT OR IGNORE INTO fish (username) VALUES (?)", (username,))
        conn.commit()
        return f"Added {username} to baits table"


def buy_baits(username: str, bait: int):
    """
    Allows Users to buy baits from a selection of baits

    :param str username: This is the user's discord username. It is needed for the SQL tables.
    :param int bait: This is the number correlated to the bait the user is attempting to buy.

    :return: Tuple containing (success: bool, bait_bought: str | None, reason: str | None)
    :rtype: tuple
    """
    coins = check_currency(username)
    bait_bought: str = ""
    bundle: bool = False
    reason: str
    success = True
    fail = False
    match bait:
        case baitTypes.CHUM.value:
            bait_bought = "chum"
        case baitTypes.CHUM_5X.value:
            bait_bought = "chum"
            bundle = True
        case baitTypes.BAIT_BALL.value:
            bait_bought = "bait_ball"
        case baitTypes.BAIT_BALL_5X.value:
            bait_bought = "bait_ball"
            bundle = True
        case baitTypes.MACKEREL.value:
            bait_bought = "mackerel"
        case baitTypes.MACKEREL_5X.value:
            bait_bought = "mackerel"
            bundle = True
        case baitTypes.STINGRAY.value:
            bait_bought = "stingray"
        case baitTypes.STINGRAY_5X.value:
            bait_bought = "stingray"
            bundle = True
        case baitTypes.BARRACUDA.value:
            bait_bought = "barracuda"
        case baitTypes.BARRACUDA_5X.value:
            bait_bought = "barracuda"
            bundle = True
        case _:
            logging.error(f"[BAIT SQL] {bait} could not be found when prompted by {username}")
            raise ex.ItemNotFound("Bait not found!!", 1001)

    logging.info(f"[BAITS SQL] user ({username}) has selected a bait to buy (name={bait_bought}, bundle={bundle})")

    price = cur.execute("SELECT price FROM baits_shop WHERE name=?", (bait_bought,)).fetchone()[0]

    if coins < price:
        reason = "Not enough coins!!"
        return fail, None, reason

    remove_coins(username=username, coins_to_remove=price)

    amount = 1 if not bundle else 5
    cur.execute(f"UPDATE baits SET {bait_bought} = {bait_bought} + ? WHERE username = ?", (amount, username))
    conn.commit()
    bait_bought = bait_bought.replace("_", " ")
    return success, bait_bought, None


def use_bait(username: str, bait: str):

    cur.execute(f"UPDATE baits SET {bait.replace(' ', '_')}= {bait.replace(' ', '_')} - 1 WHERE username = ?", (username,))
    conn.commit()
