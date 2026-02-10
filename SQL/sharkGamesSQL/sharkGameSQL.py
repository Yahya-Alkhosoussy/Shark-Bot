import datetime as dt
import json
import logging
import sqlite3
from enum import Enum

with open("listofsharks.json", "r", encoding="utf-8") as file:
    list_of_sharks: dict = json.load(file)

total = []
# Build rows as tuples of scalars (name, fact)
# total = [(name, (info or {})["fact"]) for name, info in list_of_sharks.items()]

for shark in list_of_sharks:
    emoji = list_of_sharks.setdefault(shark, {})["emoji"]
    fact = list_of_sharks.setdefault(shark, {})["fact"]
    weight = list_of_sharks.setdefault(shark, {})["weight"]
    temp = (shark, fact, emoji, weight)
    total.append(temp)

# connection to database
connection = sqlite3.connect("databases/shark_game.db")
# cursor that allows us to perform SQL queries
cursor = connection.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS sharks
                        (name text PRIMARY KEY, fact text, emoji text, weight real, rarity INTEGER)""")  # real is a float

# rows: tuple = [(name, fact, emoji, weight) for name, fact, emoji, weight in total]

# cursor.executemany("INSERT OR IGNORE INTO sharks VALUES (?, ?, ?, ?, ?)", rows)


class SharkRarity(Enum):
    VERY_COMMON = 1
    COMMON = 2
    UNCOMMON = 3
    RARE = 4
    ULTRA_RARE = 5


class NetTypes(Enum):
    LEATHER_NET = 1
    GOLD_NET = 2
    TITANIUM_NET = 3
    NET_OF_DOOM = 4
    LEATHER_NET_5 = 5
    GOLD_NET_5 = 6
    TITANIUM_NET_5 = 7
    NET_OF_DOOM_5 = 8


def get_names_of_sharks():
    full = []
    for row in cursor.execute("""SELECT name FROM sharks"""):
        full.append(row[0])

    return full


def get_something(name: str, thing: str):
    full: list = []

    for row in cursor.execute(f"SELECT {thing} FROM sharks WHERE name = '{name}'"):
        full.append(row)
    return full


def get_all_facts(name: str):
    """
    :param name: The name of the shark
    :type name: str
    :return: Returns all facts about a certain shark
    :rtype: tuple
    """
    return cursor.execute("SELECT * FROM sharks WHERE name = ?", (name,)).fetchone()


def create_dex(username: str, shark_name: str, when_caught: str, net_used: str, rarity: str, net_uses: int):
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS '{username} dex'
                                (shark text, time text, fact text, weight real, net text, coins real, rarity text, level INTEGER, net_uses INTEGER)""")
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS '{username} nets'
                                ('rope net' BOOLEAN, 'leather net' BOOLEAN, 'gold net' BOOLEAN, 'titanium net' BOOLEAN, 'net of doom' BOOLEAN, time text)""")
    fact = get_something(shark_name, "fact")
    weight = get_something(shark_name, "weight")
    net_type: str = net_used
    coins = check_currency(username)
    coins = 0 if coins is None else coins
    level = 0
    current_time = dt.datetime.now()
    time_caught: str = f"{current_time.date()} {current_time.hour}"
    row: tuple = (shark_name, when_caught, fact[0][0], weight[0][0], net_type, coins, rarity, level, net_uses)
    cursor.execute(f"INSERT OR IGNORE INTO '{username} dex' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
    # Check if row exists
    row_count = cursor.execute(f"SELECT COUNT(*) FROM '{username} nets'").fetchone()[0]
    if row_count == 0:
        cursor.execute(
            f"INSERT INTO '{username} nets' VALUES (?, ?, ?, ?, ?, ?)", (True, False, False, False, False, time_caught)
        )
        connection.commit()
    connection.commit()


def fish_caught(username: str, rarity: str):
    cursor.execute(f"""CREATE TABLE IF NOT EXISTS '{username} fish'
                                (trash INTEGER, common INTEGER, shiny INTEGER, legendary INTEGER)""")

    old = cursor.execute(f"SELECT * FROM '{username} fish'")

    trash, common, shiny, legendary = [], [], [], []

    for item in old:
        trash.append(item[0])
        common.append(item[1])
        shiny.append(item[2])
        legendary.append(item[3])

    if trash:  # the code only runs if trash is not empty
        match rarity:
            case "trash":
                last = trash[-1]
                last += 1
                cursor.execute(f"UPDATE '{username} fish' SET trash = ?", (last,))
            case "common":
                last = common[-1]
                last += 1
                cursor.execute(f"UPDATE '{username} fish' SET common = ?", (last,))
            case "shiny":
                last = shiny[-1]
                last += 1
                cursor.execute(f"UPDATE '{username} fish' SET shiny = ?", (last,))
            case "legendary":
                last = legendary[-1]
                last += 1
                cursor.execute(f"UPDATE '{username} fish' SET legendary = ?", (last,))
    else:
        row = (0, 0, 0, 0)
        cursor.execute(f"INSERT INTO '{username} fish' VALUES (?, ?, ?, ?)", row)
        match rarity:
            case "trash":
                row = (1, 0, 0, 0)
            case "common":
                row = (0, 1, 0, 0)
            case "shiny":
                row = (0, 0, 1, 0)
            case "legendary":
                row = (0, 0, 0, 1)
        cursor.execute(f"UPDATE '{username} fish' SET trash = ?, common = ?, shiny = ?, legendary = ?", row)
    connection.commit()


def get_dex(username: str):
    full = []
    try:
        for row in cursor.execute(f"SELECT * FROM '{username} dex'"):
            full.append(row)
    except sqlite3.OperationalError:
        full = None
    return full


def add_column_to_shark_db(column_name: str, column_type, default_value):
    # 1) List shark table
    try:
        cursor.execute(f"""
                   ALTER TABLE sharks
                   ADD COLUMN {column_name} {column_type} DEFAULT {default_value};
                   """)
    except sqlite3.OperationalError as e:
        print(f"Warning, error {e}")

    connection.commit()


def remove_column_to_shark_db(column_name: str):
    try:
        cursor.execute(f"""
                   ALTER TABLE sharks
                   DROP COLUMN {column_name} ;
                   """)
    except sqlite3.OperationalError as e:
        print(f"Warning, error {e}")


# remove_column_to_shark_db("net_uses")
# print("column, net_uses removed")


def add_rarity():
    shark_rarity_level_2 = [
        "Sand Tiger Shark",
        "Tiger Shark",
        "Broadnose Sevengill Shark",
        "Epaulette Shark",
        "Whitespotted Bamboo Shark",
        "Sharptooth Lemon Shark",
        "Oceanic Whitetip Shark",
        "Silky Shark",
        "Galapagos Shark",
        "Crocodile Shark",
        "Sand Devil",
        "Bahamas Sawshark",
        "Longfin Mako Shark",
        "Bigeye Thresher Shark",
        "Bluntnose Sixgill Shark",
        "Starry Catshark",
    ]
    shark_rarity_level_3 = [
        "Basking Shark",
        "Frilled Shark",
        "Angel Shark",
        "Porbeagle Shark",
        "Pacific Sleeper Shark",
        "Great Lanternshark",
        "Nervous Shark",
        "Little Sleeper Shark",
        "Crying Izak",
        "Kitefin Shark",
    ]
    shark_rarity_level_4 = [
        "Mollisquama parini",
        "Mollisquama mississippiensis",
        "Frog Shark",
        "Goblin Shark",
        "Megamouth Shark",
        "Greenland Shark",
        "Gulper Shark",
        "Whale Shark",
        "Pygmy Shark",
        "Cookiecutter Shark",
    ]
    shark_rarity_level_5 = [
        "Akmonistion",
        "Falcatus falcatus",
        "Xenacanth",
        "Stethacanthus",
        "Edestid",
        "Helicoprion",
        "Bandringa",
        "Megalodon",
    ]

    def set_rarity(names, rarity):
        if not names:  # check if the list is empty
            return
        placeholders = ", ".join("?" for _ in names)  # creates (?, ?, ?)
        query = f"UPDATE sharks SET rarity = ? WHERE name IN ({placeholders});"
        cursor.execute(query, (rarity, *names))
        print(f"done for {names} where rarity is {rarity}")

    set_rarity(shark_rarity_level_2, 2)
    set_rarity(shark_rarity_level_3, 3)
    set_rarity(shark_rarity_level_4, 4)
    set_rarity(shark_rarity_level_5, 5)


# add_rarity()


def get_shark_names(rarity: SharkRarity):
    temp = cursor.execute("SELECT name FROM sharks WHERE rarity = ?", (rarity.value,))

    names = []
    for item in temp:
        names.append(item[0])
    return names


def add_column_to_dex(column_name: str, column_type, default):
    # 1) list all user tables:
    cursor.execute("""
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
    table_names = [row[0] for row in cursor.fetchall()]

    # 2) keep only tables that follow your pattern
    dex_tables = [t for t in table_names if t.endswith(" dex")]

    # 3) Alter each
    for t in dex_tables:
        try:
            cursor.execute(f"""ALTER TABLE '{t}' ADD COLUMN {column_name} {column_type} DEFAULT {default};""")
        except sqlite3.OperationalError as e:
            print(f"Skipping {t}: {e}")


def remove_column_to_dex(column_name: str):
    # 1) list all user tables:
    cursor.execute("""
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
    table_names = [row[0] for row in cursor.fetchall()]

    # 2) keep only tables that follow your pattern
    dex_tables = [t for t in table_names if t.endswith(" dex")]

    for t in dex_tables:
        try:
            cursor.execute(f"""
                    ALTER TABLE '{t}'
                    DROP COLUMN {column_name} ;
                    """)
            print(f"Done for {t} \n")
        except sqlite3.OperationalError as e:
            print(f"Warning, error {e}")


# remove_column_to_dex("net_uses")
# print("net uses removed")
# add_column_to_dex("net_uses", "INTEGER", 25)
# cursor.execute("DROP TABLE 'nets shop'")
# connection.commit()


def add_column_to_net(column_name: str, column_type, default):
    # 1) list all user tables:
    cursor.execute("""
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
    table_names = [row[0] for row in cursor.fetchall()]
    # 2) keep only tables that follow your pattern
    net_tables = [t for t in table_names if t.endswith(" nets")]

    # 3) Alter each
    for t in net_tables:
        try:
            cursor.execute(f"""ALTER TABLE '{t}' ADD COLUMN {column_name} {column_type} DEFAULT '{default}';""")
            print(f"done for {t}")
        except sqlite3.OperationalError as e:
            print(f"Skipping {t}: {e}")


current_time = dt.datetime.now()
# time_now: str = f"{current_time.date()} {current_time.hour - 1}"

# add_column_to_net("time", "text", time_now)
# print("added column")


def setup_net_shop():
    cursor.execute("""CREATE TABLE IF NOT EXISTS 'nets shop'
                            (net text PRIMARY KEY, price real, odds real)""")
    nets = [
        "leather net",
        "gold net",
        "titanium net",
        "net of doom",
        "leather net x 5",
        "gold net x 5",
        "titanium net x 5",
        "net of doom x 5",
    ]
    prices = [60, 140, 250, 500, 300.0, 700.0, 1250.0, 2500.0]
    odds = [25, 30, 50, 90, 25, 30, 50, 90]  # in percentage
    full = []
    for i in range(len(nets)):
        temp = (nets[i], prices[i], odds[i])
        full.append(temp)
    tup: list[tuple] = [(net, price, odd) for net, price, odd in full]
    cursor.executemany("INSERT OR IGNORE INTO 'nets shop' VALUES (?, ?, ?)", tup)
    # print(tup)
    connection.commit()


def get_nets():
    info = cursor.execute("SELECT net, price FROM 'nets shop'")
    nets = []
    prices = []
    for net, price in info:
        nets.append(net)
        prices.append(price)

    return nets, prices


# print(get_nets())
# for row in cursor.execute("SELECT net FROM 'spiderbyte2007 dex' WHERE net='leather net' ORDER BY time DESC LIMIT 1"):
# print(row[0])


def get_net_availability(username: str):
    """
    Returns available nets and returns if a net is about to break or not.

    returns:
        1. available nets
        2. about to break
        3. broken nets
        4. net uses
    """
    all_nets = []
    available_nets = ["rope net"]
    try:
        all_nets.extend(cursor.execute(f"SELECT * FROM '{username} nets' ORDER BY time DESC LIMIT 1;"))
    except sqlite3.OperationalError:
        all_nets.extend(available_nets)

    net_uses: int = 0

    about_to_break = []
    broken = []
    i = 0
    try:
        for nets in all_nets[0]:
            if nets == 0:
                i += 1
            else:
                match i:
                    case NetTypes.LEATHER_NET.value:
                        for row in cursor.execute(
                            f"SELECT net_uses FROM '{username} dex' WHERE net='leather net' ORDER BY time DESC LIMIT 1"
                        ):
                            net_uses = row[0]
                        if (
                            (net_uses <= 25 and net_uses > 21)
                            or (net_uses <= 19 and net_uses > 16)
                            or (net_uses <= 14 and net_uses > 11)
                            or (net_uses <= 9 and net_uses > 6)
                            or (net_uses <= 4 and net_uses > 1)
                        ):
                            available_nets.append("leather net")
                        elif net_uses == 21 or net_uses == 16 or net_uses == 11 or net_uses == 6 or net_uses == 1:
                            available_nets.append("leather net")
                            about_to_break.append("leather net")
                        elif net_uses == 20 or net_uses == 15 or net_uses == 10 or net_uses == 5 or net_uses == 0:
                            broken.append("leather net")
                            available_nets.append("leather net")
                            if net_uses == 0:
                                cursor.execute(f"UPDATE '{username} nets' SET 'leather net'=0")
                        else:
                            broken.append("leather net")

                    case NetTypes.GOLD_NET.value:
                        for row in cursor.execute(
                            f"SELECT net_uses FROM '{username} dex' WHERE net='gold net' ORDER BY time DESC LIMIT 1"
                        ):
                            net_uses = row[0]
                        if (
                            (net_uses <= 25 and net_uses > 21)
                            or (net_uses <= 19 and net_uses > 16)
                            or (net_uses <= 14 and net_uses > 11)
                            or (net_uses <= 9 and net_uses > 6)
                            or (net_uses <= 4 and net_uses > 1)
                        ):
                            available_nets.append("gold net")
                        elif net_uses == 21 or net_uses == 16 or net_uses == 11 or net_uses == 6 or net_uses == 1:
                            available_nets.append("gold net")
                            about_to_break.append("gold net")
                        elif net_uses == 20 or net_uses == 15 or net_uses == 10 or net_uses == 5 or net_uses == 0:
                            broken.append("gold net")
                            available_nets.append("gold net")
                            if net_uses == 0:
                                cursor.execute(f"UPDATE '{username} nets' SET 'gold net'=0")
                        else:
                            broken.append("gold net")

                    case NetTypes.TITANIUM_NET.value:
                        for row in cursor.execute(
                            f"SELECT net_uses FROM '{username} dex' WHERE net='titanium net' ORDER BY time DESC LIMIT 1"
                        ):
                            net_uses = row[0]
                        if (
                            (net_uses <= 25 and net_uses > 21)
                            or (net_uses <= 19 and net_uses > 16)
                            or (net_uses <= 14 and net_uses > 11)
                            or (net_uses <= 9 and net_uses > 6)
                            or (net_uses <= 4 and net_uses > 1)
                        ):
                            available_nets.append("titanium net")
                        elif net_uses == 21 or net_uses == 16 or net_uses == 11 or net_uses == 6 or net_uses == 1:
                            available_nets.append("titanium net")
                            about_to_break.append("titanium net")
                        elif net_uses == 20 or net_uses == 15 or net_uses == 10 or net_uses == 5 or net_uses == 0:
                            broken.append("titanium net")
                            available_nets.append("titanium net")
                            if net_uses == 0:
                                cursor.execute(f"UPDATE '{username} nets' SET 'titanium net'=0")
                        else:
                            broken.append("titanium net")

                    case NetTypes.NET_OF_DOOM.value:
                        for row in cursor.execute(
                            f"SELECT net_uses FROM '{username} dex' WHERE net='net of doom' ORDER BY time DESC LIMIT 1"
                        ):
                            net_uses = row[0]
                        if (
                            (net_uses <= 25 and net_uses > 21)
                            or (net_uses <= 19 and net_uses > 16)
                            or (net_uses <= 14 and net_uses > 11)
                            or (net_uses <= 9 and net_uses > 6)
                            or (net_uses <= 4 and net_uses > 1)
                        ):
                            available_nets.append("net of doom")
                        elif net_uses == 21 or net_uses == 16 or net_uses == 11 or net_uses == 6 or net_uses == 1:
                            available_nets.append("net of doom")
                            about_to_break.append("net of doom")
                        elif net_uses == 20 or net_uses == 15 or net_uses == 10 or net_uses == 5 or net_uses == 0:
                            broken.append("net of doom")
                            available_nets.append("net of doom")
                            if net_uses == 0:
                                cursor.execute(f"UPDATE '{username} nets' SET 'net of doom'=0")
                        else:
                            broken.append("net of doom")

                i += 1
    except sqlite3.OperationalError:
        pass

    return available_nets, about_to_break, broken, net_uses


def remove_net_use(username: str, net: str, net_uses: int):
    try:
        cursor.execute(f"""SELECT rowid FROM '{username} dex' WHERE net='{net}' ORDER BY time DESC LIMIT 1;""")
    except sqlite3.OperationalError:
        return

    row = cursor.fetchone()

    if row is not None:
        rowid = row[0]
        cursor.execute(f"UPDATE '{username} dex' SET net_uses={net_uses} WHERE rowid = {rowid}")
        connection.commit()


def is_net_available(username: str, net: str):
    nets_available: dict = {}
    all_nets = []
    try:
        all_nets.extend(cursor.execute(f"SELECT * FROM '{username} nets'"))
    except sqlite3.OperationalError:
        return False
    i = 0
    try:
        for nets in all_nets[0]:
            if nets == 0:
                i += 1
            else:
                match i:
                    case NetTypes.LEATHER_NET.value:
                        nets_available["leather net"] = True

                    case NetTypes.GOLD_NET.value:
                        nets_available["gold net"] = True

                    case NetTypes.TITANIUM_NET.value:
                        nets_available["titanium net"] = True

                    case NetTypes.NET_OF_DOOM.value:
                        nets_available["net of doom"] = True

                i += 1

    except IndexError:
        return False
    if "x 5" in net:
        net = net[:-4]
    if net in nets_available.keys():
        return True
    else:
        return False


def check_currency(username: str):
    rows = []
    try:
        for row in cursor.execute(f"SELECT coins FROM '{username} dex' ORDER BY time DESC LIMIT 1"):
            rows.append(row[0])
    except sqlite3.OperationalError:
        rows = []

    return None if not rows else rows[len(rows) - 1]


def buy_net(username: str, net: int):
    """
    Allows users to buy a net from a certain selection of nets

    Inputs:
        Username: str           This is the user's discord username that is used for the SQL tables.
        Net: int                This is the number corresponding to the net they want to buy, refer to num_to_net class for the numbers.

    Outputs:
        Successful: Bool        Was the buying of the net successful?
        net_to_buy: str | None  Returns the net that the user bought.
        reason:     str | None  Returns the reason the transaction failed.
    """

    coins = check_currency(username)

    price: list = []

    net_to_buy: str
    bundle: bool = False

    reason = ""
    success = True
    fail = False

    match net:
        case NetTypes.LEATHER_NET.value:
            net_to_buy = "leather net"
            logging.info(f"[SHARK GAME SQL] Selected net ({net_to_buy}, bundle={bundle}) for {username}")
        case NetTypes.LEATHER_NET_5.value:
            net_to_buy = "leather net"
            bundle = True
            logging.info(f"[SHARK GAME SQL] Selected net ({net_to_buy}, bundle={bundle}) for {username}")
        case NetTypes.GOLD_NET.value:
            net_to_buy = "gold net"
            logging.info(f"[SHARK GAME SQL] Selected net ({net_to_buy}, bundle={bundle}) for {username}")
        case NetTypes.GOLD_NET_5.value:
            net_to_buy = "gold net"
            bundle = True
            logging.info(f"[SHARK GAME SQL] Selected net ({net_to_buy}, bundle={bundle}) for {username}")
        case NetTypes.TITANIUM_NET.value:
            net_to_buy = "titanium net"
            logging.info(f"[SHARK GAME SQL] Selected net ({net_to_buy}, bundle={bundle}) for {username}")
        case NetTypes.TITANIUM_NET_5.value:
            net_to_buy = "titanium net"
            bundle = True
            logging.info(f"[SHARK GAME SQL] Selected net ({net_to_buy}, bundle={bundle}) for {username}")
        case NetTypes.NET_OF_DOOM.value:
            net_to_buy = "net of doom"
            logging.info(f"[SHARK GAME SQL] Selected net ({net_to_buy}, bundle={bundle}) for {username}")
        case NetTypes.NET_OF_DOOM_5.value:
            net_to_buy = "net of doom"
            bundle = True
            logging.info(f"[SHARK GAME SQL] Selected net ({net_to_buy}, bundle={bundle}) for {username}")
        case _:
            logging.info(f"[SHARK GAME SQL] {net} not found when prompted by {username}")
            reason = "I could not find the net you requested"
            return fail, None, reason  # net bought is None

    for prices in cursor.execute(f"SELECT price FROM 'nets shop' WHERE net='{net_to_buy}'"):
        price.extend(prices)

    if coins is None:
        logging.warning(f"[SHARK GAME SQL] Could not find coins for {username}")
        reason = "I could not find your coins"
        return fail, None, reason

    catches = []
    latest_catch = ""

    if coins >= price[-1]:
        current_time = dt.datetime.now()
        time_now: str = f"{current_time.date()} {current_time.hour}"
        if not is_net_available(username, net_to_buy) and not bundle:
            cursor.execute(f"UPDATE '{username} nets' SET '{net_to_buy}'=1, time='{time_now}'")
            existing = cursor.execute(f"SELECT COUNT(*) FROM '{username} dex' WHERE net='{net_to_buy}'").fetchone()[0]

            if existing > 0:
                for catch in cursor.execute(
                    f"SELECT time FROM '{username} dex' WHERE net='{net_to_buy}' ORDER BY time DESC LIMIT 1"
                ):
                    catches.extend(catch)
                latest_catch = catches[0]
                cursor.execute(f"UPDATE '{username} dex' SET net_uses=5 WHERE net='{net_to_buy}' AND time=?", (latest_catch,))
                cursor.execute(
                    f"UPDATE '{username} dex' SET coins=? WHERE time=?",
                    (
                        coins - price[-1],
                        latest_catch,
                    ),
                )
            else:
                row: tuple = (None, time_now, None, None, net_to_buy, coins - price[-1], None, None, 5)
                cursor.execute(f"INSERT INTO '{username} dex' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
            connection.commit()
            logging.info("[SHARK GAME SQL] Net bought successfully!")
            return success, net_to_buy, None  # reason
        elif not is_net_available(username, net_to_buy) and bundle:
            cursor.execute(f"UPDATE '{username} nets' SET '{net_to_buy}'=1, time='{time_now}'")

            existing = cursor.execute(f"SELECT COUNT(*) FROM '{username} dex' WHERE net='{net_to_buy}'").fetchone()[0]

            if existing > 0:
                for catch in cursor.execute(
                    f"SELECT time FROM '{username} dex' WHERE net='{net_to_buy}' ORDER BY time DESC LIMIT 1"
                ):
                    catches.extend(catch)
                latest_catch = catches[0]
                cursor.execute(f"UPDATE '{username} dex' SET net_uses=25 WHERE net='{net_to_buy}' AND time=?", (latest_catch,))
                cursor.execute(
                    f"UPDATE '{username} dex' SET coins=? WHERE time=?",
                    (
                        coins - price[-1],
                        latest_catch,
                    ),
                )
            else:
                row: tuple = (None, time_now, None, None, net_to_buy, coins - price[-1], None, None, 25)
                cursor.execute(f"INSERT INTO '{username} dex' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", row)
            connection.commit()
            logging.info(
                f"[SHARK GAME SQL] Net bought successfully by {username} and the net uses for {net_to_buy} has been set to 25 at {latest_catch}"
            )
            return success, net_to_buy, None  # reason
        elif is_net_available(username, net_to_buy):
            reason = "You already have the net"
            logging.info("[SHARK GAME SQL] Could not buy net, user already had it")
            return fail, net_to_buy, reason
    else:
        reason = "You cannot afford the net"
        return fail, net_to_buy, reason


def get_shark_rarity(shark_name: str):
    rarity = cursor.execute(f"SELECT rarity FROM sharks WHERE name='{shark_name}'")
    rare = []
    rare.extend(rarity)
    return rare[0][0]


def reward_coins(
    username: str,
    shark: bool,
    rare: str,
    shark_name: str | None = None,
    size: str | None = None,
    boost: bool = False,
    boost_amount: int = 2,
):
    retVal: int = 0
    if (shark and shark_name) and boost:
        rarity = get_shark_rarity(shark_name)
        match rare:
            case "normal":
                match rarity:
                    case 1:  # very common
                        add_coins(username, 10 * boost_amount)
                        retVal = 10 * boost_amount
                    case 2:  # common
                        add_coins(username, 15 * boost_amount)
                        retVal = 15 * boost_amount
                    case 3:  # uncommon
                        add_coins(username, 20 * boost_amount)
                        retVal = 20 * boost_amount
                    case 4:  # rare
                        add_coins(username, 25 * boost_amount)
                        retVal = 25 * boost_amount
                    case 5:  # ultra-rare
                        add_coins(username, 30 * boost_amount)
                        retVal = 30 * boost_amount
            case "shiny":
                match rarity:
                    case 1:  # very common
                        add_coins(username, 20 * boost_amount)
                        retVal = 20 * boost_amount
                    case 2:  # common
                        add_coins(username, 25 * boost_amount)
                        retVal = 25 * boost_amount
                    case 3:  # uncommon
                        add_coins(username, 30 * boost_amount)
                        retVal = 30 * boost_amount
                    case 4:  # rare
                        add_coins(username, 35 * boost_amount)
                        retVal = 35 * boost_amount
                    case 5:  # ultra-rare
                        add_coins(username, 40 * boost_amount)
                        retVal = 40 * boost_amount
            case "legendary":
                match rarity:
                    case 1:  # very common
                        add_coins(username, 30 * boost_amount)
                        retVal = 30 * boost_amount
                    case 2:  # common
                        add_coins(username, 35 * boost_amount)
                        retVal = 35 * boost_amount
                    case 3:  # uncommon
                        add_coins(username, 40 * boost_amount)
                        retVal = 40 * boost_amount
                    case 4:  # rare
                        add_coins(username, 45 * boost_amount)
                        retVal = 45 * boost_amount
                    case 5:  # ultra-rare
                        add_coins(username, 50 * boost_amount)
                        retVal = 50 * boost_amount
    elif shark and shark_name:
        rarity = get_shark_rarity(shark_name)
        match rare:
            case "normal":
                match rarity:
                    case 1:  # very common
                        add_coins(username, 10)
                        retVal = 10
                    case 2:  # common
                        add_coins(username, 15)
                        retVal = 15
                    case 3:  # uncommon
                        add_coins(username, 20)
                        retVal = 20
                    case 4:  # rare
                        add_coins(username, 25)
                        retVal = 25
                    case 5:  # ultra-rare
                        add_coins(username, 30)
                        retVal = 30
            case "shiny":
                match rarity:
                    case 1:  # very common
                        add_coins(username, 20)
                        retVal = 20
                    case 2:  # common
                        add_coins(username, 25)
                        retVal = 25
                    case 3:  # uncommon
                        add_coins(username, 30)
                        retVal = 30
                    case 4:  # rare
                        add_coins(username, 35)
                        retVal = 35
                    case 5:  # ultra-rare
                        add_coins(username, 40)
                        retVal = 40
            case "legendary":
                match rarity:
                    case 1:  # very common
                        add_coins(username, 30)
                        retVal = 30
                    case 2:  # common
                        add_coins(username, 35)
                        retVal = 35
                    case 3:  # uncommon
                        add_coins(username, 40)
                        retVal = 40
                    case 4:  # rare
                        add_coins(username, 45)
                        retVal = 45
                    case 5:  # ultra-rare
                        add_coins(username, 50)
                        retVal = 50
    elif not shark and boost:  # fish but with booster
        match rare:
            case "trash":
                add_coins(username, 1 * boost_amount)
                retVal = 1 * boost_amount
            case "normal":
                match size:
                    case "large":
                        add_coins(username, 6 * boost_amount)
                        retVal = 6 * boost_amount
                    case "medium":
                        add_coins(username, 4 * boost_amount)
                        retVal = 4 * boost_amount
                    case "small":
                        add_coins(username, 2 * boost_amount)
                        retVal = 2 * boost_amount
            case "shiny":
                match size:
                    case "large":
                        add_coins(username, 9 * boost_amount)
                        retVal = 9 * boost_amount
                    case "medium":
                        add_coins(username, 7 * boost_amount)
                        retVal = 7 * boost_amount
                    case "small":
                        add_coins(username, 5 * boost_amount)
                        retVal = 5 * boost_amount
            case "legendary":
                match size:
                    case "large":
                        add_coins(username, 14 * boost_amount)
                        retVal = 14 * boost_amount
                    case "medium":
                        add_coins(username, 12 * boost_amount)
                        retVal = 12 * boost_amount
                    case "small":
                        add_coins(username, 10 * boost_amount)
                        retVal = 10 * boost_amount
    else:  # Fish
        match rare:
            case "trash":
                add_coins(username, 1)
                retVal = 1
            case "normal":
                match size:
                    case "large":
                        add_coins(username, 6)
                        retVal = 6
                    case "medium":
                        add_coins(username, 4)
                        retVal = 4
                    case "small":
                        add_coins(username, 2)
                        retVal = 2
            case "shiny":
                match size:
                    case "large":
                        add_coins(username, 9)
                        retVal = 9
                    case "medium":
                        add_coins(username, 7)
                        retVal = 7
                    case "small":
                        add_coins(username, 5)
                        retVal = 5
            case "legendary":
                match size:
                    case "large":
                        add_coins(username, 14)
                        retVal = 14
                    case "medium":
                        add_coins(username, 12)
                        retVal = 12
                    case "small":
                        add_coins(username, 10)
                        retVal = 10
    return retVal


def fishing_odds_shark(username: str, net_used: str = "rope net"):
    try:
        if is_net_available(username, net_used):
            net = net_used
        else:
            net = "rope net"
    except sqlite3.OperationalError:
        net = "rope net"
    match net:
        case "net of doom":
            return 90
        case "titanium net":
            return 60
        case "gold net":
            return 40
        case "leather net":
            return 30
        case _:
            return 20


def fishing_odds_fish(username: str, net_used: str = "rope net"):
    try:
        if is_net_available(username, net_used):
            net = net_used
        else:
            net = "rope net"
    except sqlite3.OperationalError:
        net = "rope net"

    match net:
        case "net of doom":
            return 100
        case "titanium net":
            return 100
        case "gold net":
            return 85
        case "leather net":
            return 75
        case _:
            return 60


def get_basic_dex(username: str):
    try:
        dex: list = get_dex(username) or []
    except sqlite3.OperationalError:
        return None
    sharks_caught = []
    i = 0
    coins: int = 0
    for item in dex:
        sharks_caught.append(item[0])
        if i == len(dex) - 1:
            coins = int(item[5])
        i += 1

    sharks_caught.sort()
    count: dict[str, int] = {}
    for shark in sharks_caught:
        if shark in count:
            count[shark] += 1
        else:
            count[shark] = 1
    return count, coins


# get_basic_dex("spiderbyte2007")


def add_coins(username: str, coins_to_add: int):
    coins = check_currency(username)
    coins = coins if coins else 0

    coins += coins_to_add

    catches = []
    latest_catch = ""
    for catch in cursor.execute(f"SELECT time FROM '{username} dex' ORDER BY time DESC"):
        catches.extend(catch)
    latest_catch = catches[0]

    cursor.execute(f"UPDATE '{username} dex' SET coins=? WHERE time=?", (coins, latest_catch))

    connection.commit()


# BAIT SET UP
def setup_bait_shop():
    cursor.execute("""CREATE TABLE IF NOT EXISTS bait
                            (bait text PRIMARY KEY, price real)""")
    # baits  = ["chum", "worms", ""]
    # prices = [120]


# create_dex("spiderbyte2007", "Bull Shark", "2025-10-18")

# create_dex("harunkal", "Bull Shark", "2025-10-21", "rope net", "normal")

setup_net_shop()

# add_coins("sharktrocity", 40)

# add_coins("spiderbyte2007", 250)

# print(buy_net("spiderbyte2007", "gold net"))

# print(get_dex("spiderbyte2007"))

# print(is_net_available("harunkal", "net of doom"))

# print(get_net("spiderbyte2007"), " ", get_next_net("spiderbyte2007"))

# create_dex("spiderbyte2007", "Bull Shark", "2025-10-18")

# print(get_odds("spiderbyte2007", "gold net"))

# [print(get_net_availability("spiderbyte2007"))]

# try:
#     print(get_dex("spiderbyte"))
# except sqlite3.OperationalError:
#     print("No table exists")


# print(get_dex("spiderbyte2007"))


def add_row_to_nets():
    # 1) list all user tables:
    cursor.execute("""
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
    table_names = [row[0] for row in cursor.fetchall()]

    # 2) keep only tables that follow your pattern
    dex_tables = [t for t in table_names if t.endswith(" nets")]
    # tables = [dt2 for dt2 in table_names if dt2.endswith(" dex")]
    # 3) Alter each
    for t in dex_tables:
        i = 0
        try:
            # nets = ["leather net", "gold net", "titanium net", "net of doom"]
            time_now: str = f"{current_time.date()} {current_time.hour}"
            # catches = []
            # for catch in cursor.execute(f"SELECT time FROM '{tables[i]}' ORDER BY time DESC LIMIT 1"):
            #     catches.extend(catch)
            #     latest_catch = catches[0]
            # for net_to_buy in nets:
            # cursor.execute(f"UPDATE '{t}' SET '{net_to_buy}'=0, time='{time_now}'")
            # Check if row exists
            row_count = cursor.execute(f"SELECT COUNT(*) FROM '{t}'").fetchone()[0]
            if row_count == 0:
                cursor.execute(f"INSERT INTO '{t}' VALUES (?, ?, ?, ?, ?, ?)", (True, False, False, False, False, time_now))
                print(f"Added row for {t}")
                connection.commit()
            else:
                print(f"Skipping {t}: row already exists, there are {row_count} rows")
                # cursor.execute(f"UPDATE '{tables[i]}' SET net_uses=25 WHERE net='{net_to_buy}' AND time=?", (latest_catch,))
        except sqlite3.OperationalError as e:
            print(f"Skipping {t}: {e}")
        i += 1


def delete_all_rows_from_nets():
    cursor.execute("""
                    SELECT name
                   FROM sqlite_master
                   WHERE type='table' AND name NOT LIKE 'sqlite_%'
                   """)
    table_names = [row[0] for row in cursor.fetchall()]

    nets_tables = [t for t in table_names if t.endswith(" nets")]
    for t in nets_tables:
        cursor.execute(f"DELETE FROM '{t}'")  # To clear all existing
        print(f"Done for {t}")
    connection.commit()


# delete_all_rows_from_nets()
# add_row_to_nets()

connection.commit()  # pushes changes to database
