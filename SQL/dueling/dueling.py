import sqlite3

from exceptions.exceptions import ItemNotFound

conn = sqlite3.connect("databases/dueling.db")
cur = conn.cursor()

cur.execute("PRAGMA foreign_keys = ON")


cur.execute("""CREATE TABLE IF NOT EXISTS stances
            (
                name TEXT,
                stance_id INTEGER PRIMARY KEY,
                description TEXT,
                style TEXT
            )""")  # style refers to aggressive, defensive, balanced, or counters

cur.execute("""CREATE TABLE IF NOT EXISTS stance_matchups
            (
                attacker_stance_id  INTEGER REFERENCES stances(stance_id),
                defender_stance_id  INTEGER REFERENCES stances(stance_id),
                hit_chance          INTEGER, -- base % to land a hit
                counter_chance      INTEGER, -- base % to counter
                damage_modifier     REAL, -- e.g. 1.2x damage if this matchup favours attack or 0.8x damage if this matchup favours defense
                PRIMARY KEY (attacker_stance_id, defender_stance_id)
            )""")  # noqa: E501

cur.execute("""CREATE TABLE IF NOT EXISTS player_stances
            (
                player_id INTEGER REFERENCES players(player_id),
                stance_id INTEGER REFERENCES stances(stance_id),
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                hit_chance_bonus INTEGER DEFAULT 0, -- earned through progression
                counter_chance_bonus INTEGER DEFAULT 0, -- earned through progression
                times_used INTEGER DEFAULT 0,
                times_won  INTEGER DEFAULT 0,
                PRIMARY KEY(player_id, stance_id)
            )""")

cur.execute("""CREATE TABLE IF NOT EXISTS weapons
            (
                name TEXT, -- weapon name
                damage INTEGER, -- weapon damage
                weapon_id INTEGER, -- Id for references
                weapon_type TEXTS DEFAULT "sword", -- only swords for now
                durability INTEGER, -- durability, breaks after a certain amount of hits
                crit_chance REAL,  -- chance to land a critical hit
                crit_damage_multi REAL, -- critical damage multiplier
                defective_chance REAL, -- chance for a hit to be defective
                defective_damag_multi REAL, -- defective hit multiplier
                PRIMARY KEY(name, weapon_id)
            )""")

cur.execute("""CREATE TABLE IF NOT EXISTS player_weapons
            (
                player_id INTEGER REFERENCES players(player_id),
                weapons_id INTEGER REFERENCES weapons(weapon_id),
                current_durability INTEGER,
                times_used INTEGER,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                max_level INTEGER,
                damage_bonus INTEGER DEFAULT 0, -- earned through use and level ups
                PRIMARY KEY(player_id, weapons_id)
            )""")

cur.execute(""""CREATE TABLE IF NOT EXISTS players
            (
                name TEXT UNIQUE NOT NULL,
                player_id INTEGER PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                xp_to_next_level INTEGER DEFAULT 30,
                level INTEGER DEFAULT 1,
                total_wins INTEGER DEFAULT 0,
                total_duels INTEGER DEFAULT 0,
                default_stance_id INTEGER REFERENCES stances(stance_id),
                default_weapon_id INTEGER REFERENCES weapons(weapon_id)
            )""")

cur.execute("""CREATE TABLE IF NOT EXISTS stance_school
            (
                school_id INTEGER PRIMARY KEY,
                stance_id INTEGER REFERENCES stances(stance_id),
                xp INTEGER DEFAULT 0, -- xp needed to learn stance
                enroll_cost INTEGER,
                player_level_req INTEGER DEFAULT 1, -- level required to be able to learn that stance
                prereq_stance_id INTEGER REFERENCES stances(stance_id), -- prerequisit to learning that stance.
            )""")


# For the players table:
def is_user_in_table(discord_id: int) -> bool:
    cur.execute("SELECT COUNT(*) FROM players WHERE player_id=?", (discord_id,))
    is_existing = cur.fetchone()[0]
    if is_existing:
        return True
    return False


def add_user(username: str, discord_id: int) -> bool:
    if is_user_in_table(discord_id):
        return False
    try:
        cur.execute("INSERT OR IGNORE INTO players (name, player_id) VALUES (?, ?)", (username, discord_id))
        conn.commit()
        return True
    except sqlite3.OperationalError as e:
        raise e


def add_win(discord_id: int):
    try:
        cur.execute("UPDATE players SET total_wins = total_wins + 1 WHERE player_id=?", (discord_id,))
        cur.execute("UPDATE players SET total_duels = total_duels + 1 WHERE player_id=?", (discord_id,))
        conn.commit()
    except sqlite3.OperationalError as e:
        raise e


def add_loss(discord_id: int):
    try:
        cur.execute("UPDATE players SET total_duels = total_duels + 1 WHERE player_id=?", (discord_id,))
        conn.commit()
    except sqlite3.OperationalError as e:
        raise e


def add_xp(discord_id: int, xp_added: int):
    try:
        cur.execute("UPDATE players SET xp = xp + ? WHERE player_id=?", (xp_added, discord_id))
        conn.commit()
    except sqlite3.OperationalError as e:
        raise e


def add_level(discord_id: int):
    cur.execute(
        "UPDATE players SET level = level + 1, xp = 0, xp_to_next_level = xp_to_next_level + 40 WHERE player_id=?",
        (discord_id,),
    )
    conn.commit()


def add_default_stance(stance_id: int, discord_id: int):
    try:
        cur.execute("UPDATE players SET default_stance_id = ? WHERE player_id=?", (stance_id, discord_id))
        conn.commit()
    except sqlite3.OperationalError as e:
        raise e


def add_default_weapon(weapon_id: int, discord_id: int):
    try:
        cur.execute("UPDATE players SET default_weapon_id = ? WHERE player_id=?", (weapon_id, discord_id))
        conn.commit()
    except sqlite3.OperationalError as e:
        raise e


def get_stat(discord_id: int, stat: str) -> int | str:
    match stat:
        case "xp":
            cur.execute("SELECT xp FROM players WHERE player_id=?", (discord_id,))
            return cur.fetchone()[0]
        case "level":
            cur.execute("SELECT level FROM players WHERE player_id=?", (discord_id,))
            return cur.fetchone()[0]
        case "wins":
            cur.execute("SELECT total_wins FROM players WHERE player_id=?", (discord_id,))
            return cur.fetchone()[0]
        case "duels":
            cur.execute("SELECT total_duels FROM players WHERE player_id=?", (discord_id,))
            return cur.fetchone()[0]
        case "default stance":
            cur.execute("SELECT default_stance_id FROM players WHERE player_id=?", (discord_id,))
            stance_id = cur.fetchone()[0]
            cur.execute("SELECT name FROM stances WHERE stance_id=?", (stance_id,))
            return cur.fetchone()[0]
        case "default weapon":
            cur.execute("SELECT default_weapon_id FROM players WHERE player_id=?", (discord_id,))
            weapon_id = cur.fetchone()[0]
            cur.execute("SELECT name FROM weapons WHERE weapon_id=?", (weapon_id,))
            return cur.fetchone()[0]
        case _:
            raise ItemNotFound(f"Could not find {stat} in the player database", 1012)


# stances table:
def add_stance(name: str, description: str, style: str) -> None:
    cur.execute("INSERT OR IGNORE INTO stances (name, description, style) VALUES (?, ?, ?)", (name, description, style))
    conn.commit()


def get_stance_id(name: str) -> int:
    cur.execute("SELECT stance_id WHERE name=?", (name,))
    return cur.fetchone()[0]


def get_stance_info(stance_id: int, info: str) -> str:
    match info:
        case "description":
            cur.execute("SELECT description FROM stances WHERE stance_id=?", (stance_id,))
            return cur.fetchone()[0]
        case "style":
            cur.execute("SELECT style FROM stances WHERE stance_id=?", (stance_id,))
            return cur.fetchone()[0]
        case _:
            raise ItemNotFound(f"Could not find {info} in the stances database", 1012)


# stance match up:
def add_stance_matchup(stance_id_1: int, stance_id_2: int, hit_chance: int, counter_chance: int, damage_modifer: int):
    cur.execute(
        """INSERT OR IGNORE INTO stance_matchups
                (attacker_stance_id, defender_stance_id, hit_chance, counter_chance, damage_modifier)
                VALUES (?, ?, ?, ?, ?)
        """,
        (stance_id_1, stance_id_2, hit_chance, counter_chance, damage_modifer),
    )
    conn.commit()


def update_hit_chance(stance_id_1: int, stance_id_2: int, hit_chance: int):
    cur.execute(
        "UPDATE stance_matchups SET hit_chance=? WHERE attacker_stance_id=? AND defender_stance_id=?",
        (hit_chance, stance_id_1, stance_id_2),
    )
    conn.commit()


def update_counter_chance(stance_id_1: int, stance_id_2: int, counter_chance: int):
    cur.execute(
        "UPDATE stance_matchups SET counter_chance=? WHERE attacker_stance_id=? AND defender_stance_id=?",
        (counter_chance, stance_id_1, stance_id_2),
    )
    conn.commit()


def update_damage_modifier(stance_id_1: int, stance_id_2: int, modifier: float):
    cur.execute(
        "UPDATE stance_matchups SET damage_modifier=? WHERE attacker_stance_id=? AND defender_stance_id=?",
        (modifier, stance_id_1, stance_id_2),
    )
    conn.commit()


def get_matchup_info(stance_id_1: int, stance_id_2: int):
    "Returns hit chance, counter chance and damage modifier for any stance matchup"
    cur.execute(
        "SELECT hit_chance, counter_chance, damage_modifier FROM stance_matchups WHERE attacker_stance_id=? AND defender_stance_id=?",  # noqa: E501
        (stance_id_1, stance_id_2),
    )
    return cur.fetchall()


# Player stances
def add_player_stance(
    player_id: int, stance_id: int, hit_chance_bonus: int | None = None, counter_chance_bonus: int | None = None
):
    if hit_chance_bonus and counter_chance_bonus:
        cur.execute(
            """INSERT OR IGNORE INTO player_stances (player_id, stance_id, hit_chance_bonus, counter_chance_bonus)
                        VALUES (?, ?, ?, ?)""",
            (player_id, stance_id, hit_chance_bonus, counter_chance_bonus),
        )
    elif hit_chance_bonus:
        cur.execute(
            "INSERT OR IGNORE INTO player_stances (player_id, stance_id, hit_chance_bonus) VALUES (?, ?, ?)",
            (player_id, stance_id, hit_chance_bonus),
        )
    elif counter_chance_bonus:
        cur.execute(
            "INSERT OR IGNORE INTO player_stances (player_id, stance_id, counter_chance_bonus) VALUES (?, ?, ?)",
            (player_id, stance_id, counter_chance_bonus),
        )
    else:
        cur.execute(
            "INSERT OR IGNORE INTO player_stances (player_id, stance_id) VALUES (?, ?)",
            (player_id, stance_id),
        )
    conn.commit()


def update_hit_chance_bonus(player_id: int, stance_id: int, hit_chance_bonus: int):
    cur.execute(
        "UPDATE player_stances SET hit_chance_bonus=? WHERE player_id=? AND stance_id=?",
        (hit_chance_bonus, player_id, stance_id),
    )
    conn.commit()


def update_counter_chance_bonus(player_id: int, stance_id: int, counter_chance_bonus: int):
    cur.execute(
        "UPDATE player_stances SET counter_chance_bonus=? WHERE player_id=? AND stance_id=?",
        (counter_chance_bonus, player_id, stance_id),
    )
    conn.commit()


def get_stance_level(player_id: int, stance_id: int):
    "Returns the XP and Level associated with a stance"
    cur.execute("SELECT level, xp FROM player_stances WHERE player_id=? AND stance_id=?", (player_id, stance_id))
    return cur.fetchall()


def get_stance_bonuses(player_id: int, stance_id: int):
    "Returns both hit chance bonus and counter chance bonus"
    cur.execute(
        "SELECT hit_chance_bonus, counter_chance_bonus FROM player_stances WHERE player_id=? AND stance_id=?",
        (player_id, stance_id),
    )
    return cur.fetchall()


def get_wins_and_uses(player_id: int, stance_id: int):
    "Returns wins and times used for a stance"
    cur.execute("SELECT times_won, times_used FROM player_stances WHERE player_id=? AND stance_id=?", (player_id, stance_id))
    return cur.fetchall()
