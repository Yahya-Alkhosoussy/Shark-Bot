import sqlite3
from collections import namedtuple
from enum import Enum

import discord

conn = sqlite3.connect("databases/roles.db")
cur = conn.cursor()
Emoji_Result = namedtuple(
    "EmojiResult",
    ("roleName", "roleId", "guildName", "guildId", "roleSetName", "emojiName", "emojiIsAnimated", "discordEmojiId"),
)
emojiResults: list[Emoji_Result] = []
# Create the table
cur.execute("""CREATE TABLE IF NOT EXISTS emojis
                        (id INTEGER PRIMARY KEY, animated BOOLEAN, name TEXT UNIQUE, discord_id BIGINT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS guilds
                        (id INTEGER PRIMARY KEY, name TEXT UNIQUE, guild_id INTEGER)""")
cur.execute("""CREATE TABLE IF NOT EXISTS roleSets
                        (id INTEGER PRIMARY KEY, name TEXT UNIQUE)""")
cur.execute("""CREATE TABLE IF NOT EXISTS roles
                        (id INTEGER PRIMARY KEY, name TEXT UNIQUE, role_id INTEGER, emoji_id INTEGER, guild_id INTEGER, roleSet_ID INTEGER)""")  # noqa: E501


class indicies(Enum):
    ROLE = 0
    GUILD = 1
    MESSAGE = 2
    ID = 3


SQL_QUERY = r"""SELECT
    r.role_id,
    r.name as roleName,
    g.name as guildName,
    g.guild_id as guildId,
    rs.name as roleSetName,
    e.name as emojiName,
    e.animated as emojiIsAnimated,
    e.discord_id as discordEmojiId
FROM
    roles as r
INNER JOIN
    roleSets AS rs
    ON r.roleSet_ID = rs.id
INNER JOIN
    guilds as g
    ON r.guild_id = g.id
INNER JOIN
    emojis AS e
    ON r.emoji_id = e.id
"""


def put_emoji_in_table(animated: bool, emoji_name: str, discord_id: int | None) -> int:
    """
    Puts emoji in the SQL table and returns the emoji ID
    """
    cur.execute(
        "INSERT OR IGNORE INTO emojis (animated, name, discord_id) VALUES (?, ?, ?)", (animated, emoji_name, discord_id)
    )
    conn.commit()

    return cur.execute("SELECT id FROM emojis WHERE name=?", (emoji_name,)).fetchone()[0]


def put_guild_in_table(guild_name: str, guild_id: int | None = None) -> int:
    """
    Puts Guild in the SQL table and returns the guild ID
    """
    if guild_id is not None:
        cur.execute("INSERT OR IGNORE INTO guilds (name, guild_id) VALUES (?, ?)", (guild_name, guild_id))
        conn.commit()
    return cur.execute("SELECT id FROM guilds WHERE name = ?", (guild_name,)).fetchone()[0]


def put_role_set_in_table(role_set_name: str) -> int:
    """
    Puts role set in the SQL table and returns the role set ID
    """
    cur.execute("INSERT OR IGNORE INTO roleSets (name) VALUES (?)", (role_set_name,))
    conn.commit()
    return cur.execute("SELECT id FROM roleSets WHERE name = ?", (role_set_name,)).fetchone()[0]


def put_role_in_table(role_name: str, role_id: int, emoji_table_id: int, guild_table_id: int, role_set_table_id: int):
    cur.execute(
        "INSERT OR IGNORE INTO roles (name, role_id, emoji_id, guild_id, roleSet_ID) VALUES (?, ?, ?, ?, ?)",
        (role_name, role_id, emoji_table_id, guild_table_id, role_set_table_id),
    )
    conn.commit()


def fill_emoji_map() -> dict[int, dict[str, dict[discord.PartialEmoji, int]]]:
    emojiMap: dict[int, dict[str, dict[discord.PartialEmoji, int]]] = {}
    cur.row_factory = sqlite3.Row
    results = cur.execute(SQL_QUERY).fetchall()
    for result in results:
        emojiResults.append(
            Emoji_Result(
                roleName=result["roleName"],
                roleId=result["role_id"],
                guildName=result["guildName"],
                roleSetName=result["roleSetName"],
                emojiName=result["emojiName"],
                emojiIsAnimated=result["emojiIsAnimated"],
                discordEmojiId=result["discordEmojiId"],
                guildId=result["guildId"],
            )
        )

    for r in emojiResults:
        if r.guildId not in emojiMap.keys():
            emojiMap[r.guildId] = {}
        if r.roleSetName not in emojiMap[r.guildId].keys():
            emojiMap[r.guildId][r.roleSetName] = {}
        if r.discordEmojiId:
            emojiMap[r.guildId][r.roleSetName][
                discord.PartialEmoji.from_str(f"<{'a' if r.emojiIsAnimated else ''}:{r.emojiName}:{r.discordEmojiId}>")
            ] = r.roleId
        else:
            emojiMap[r.guildId][r.roleSetName][discord.PartialEmoji.from_str(r.emojiName)] = r.roleId
    return emojiMap


# print(f"emojiResults has {len(emojiResults)} items")
# print(emojiMap)
"""
emojis table:
  fields: id(int) <primary_key>, animated(bool), name(string), discord_id(bigint)
  example: [(1, False, 💻, NULL), (2, False, "Zerotwodrinkbyliliiet112", 1318361002072604692)]

guilds table:
  fields: id(int) <primary_key>, name(string)

roleSets table:
  fields: id(int) <primary_key>, name(string)

roles table:
  fields: id(int) <primary_key>, name(string), roleId(int), emojiId(int), guildId(int), roleSetId(int)
"""


def get_guilds() -> tuple[list[str], list[int]]:
    """Returns guild name and guild ID"""
    cur.execute("SELECT name, guild_id FROM guilds")

    rows = cur.fetchall()
    names, ids = [], []
    for row in rows:
        names.append(row[0])
        ids.append(row[1])
    return names, ids


def add_role(
    role_name: str,
    role_id: int,
    role_emoji_name: str,
    is_emoji_animated: bool,
    role_emoji_id: int | None,
    role_set_name: str,
    guild_name: str,
) -> bool:
    try:
        emoji_id = put_emoji_in_table(animated=is_emoji_animated, emoji_name=role_emoji_name, discord_id=role_emoji_id)
        roleSet_id = put_role_set_in_table(role_set_name)
        guild_table_id = put_guild_in_table(guild_name=guild_name)
        put_role_in_table(role_name, role_id, emoji_id, guild_table_id, roleSet_id)
    except sqlite3.OperationalError as e:
        raise e
    return True
