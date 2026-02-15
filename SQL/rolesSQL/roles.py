import sqlite3
from collections import namedtuple
from enum import Enum

import discord

conn = sqlite3.connect("databases/roles.db")
cur = conn.cursor()
Emoji_Result = namedtuple(
    "EmojiResult", ("roleName", "roleId", "guildName", "roleSetName", "emojiName", "emojiIsAnimated", "discordEmojiId")
)
emojiResults: list[Emoji_Result] = []
# Create the table
cur.execute("""CREATE TABLE IF NOT EXISTS emojis
                        (id INTEGER PRIMARY KEY, animated BOOLEAN, name TEXT, discord_id BIGINT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS guilds
                        (id INTEGER PRIMARY KEY, name TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS roleSets
                        (id INTEGER PRIMARY KEY, name TEXT)""")
cur.execute("""CREATE TABLE IF NOT EXISTS roles
                        (id INTEGER PRIMARY KEY, name TEXT, role_id INTEGER, emoji_id INTEGER, guild_id INTEGER, roleSet_ID INTEGER)""")  # noqa: E501


class indicies(Enum):
    ROLE = 0
    GUILD = 1
    MESSAGE = 2
    ID = 3


# Set up for emojis table
roles_test_server = ["🩵", "❤️", "💚"]
roles_test_server_emoji_ids = [None, None, None]
roles_name_test_server = ["blue", "red", "green"]
roles_test_server_ids = [1422681663342903438, 1428757018792956085, 1428757052993437767]
roles_test_server_messages = ["colour", "general", "test"]
roles_test_server_messages_ids = [1463681052278263880, 1463681055084118017, 1463681059236614144]
roles_shark_squad = ["🎆", "💌", "🍀", "<:Zerotwodrinkbyliliiet112:1318361002072604692>"]

SQL_QUERY = r"""SELECT
    r.role_id,
    r.name as roleName,
    g.name as guildName,
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
i = 0
for emoji in roles_test_server:
    cur.execute(
        "INSERT OR IGNORE INTO emojis (animated, name, discord_id) VALUES (?, ?, ?)",
        (False, emoji, roles_test_server_emoji_ids[i]),
    )
    emoji_id = cur.execute(
        "SELECT id FROM emojis WHERE name = ? AND discord_id = ?", (emoji, roles_test_server_emoji_ids[i])
    ).fetchone()[0]

    cur.execute("INSERT OR IGNORE INTO guilds (name) VALUES (?)", ("test server",))
    guild_id = cur.execute("SELECT id FROM guilds WHERE name = ?", ("test server",)).fetchone()[0]

    cur.execute("INSERT OR IGNORE INTO roleSets (name) VALUES (?)", (roles_test_server_messages[i],))
    roleSetID = cur.execute("SELECT id FROM roleSets WHERE name = ?", (roles_test_server_messages[i])).fetchone()[0]

    cur.execute(
        "INSERT OR IGNORE INTO roles (name, role_id, emoji_id, guild_id, roleSet_ID) VALUES (?, ?, ?, ?, ?)",
        (roles_name_test_server[i], roles_test_server_ids[i], emoji_id, guild_id, roleSetID),
    )
    i += 1

cur.row_factory = sqlite3.Row
results = cur.execute(SQL_QUERY).fetchall()
print(f"Query returned {len(results)} rows")
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
        )
    )

emojiMap: dict[str, dict[str, dict[discord.PartialEmoji, int]]] = {}
for r in emojiResults:
    if r.guildName not in emojiMap.keys():
        emojiMap[r.guildName] = {}
    if r.roleSetName not in emojiMap[r.guildName].keys():
        emojiMap[r.guildName][r.roleSetName] = {}
    if r.discordEmojiId:
        emojiMap[r.guildName][r.roleSetName][
            discord.PartialEmoji.from_str(f"<{'a' if r.emojiIsAnimated else ''}:{r.emojiName}:{r.discordEmojiId}>")
        ] = r.roleId
    else:
        emojiMap[r.guildName][r.roleSetName][discord.PartialEmoji.from_str(r.emojiName)] = r.roleId

print(f"emojiResults has {len(emojiResults)} items")
print(emojiMap)
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


def get_roles(guild_name: str):
    ""
    results = cur.execute("SELECT role, role_message FROM roles WHERE guild=?", (guild_name,)).fetchall()

    roles, role_message = [], []
    for result in results:
        roles.append(result[0])
        role_message.append(result[1])

    i = 0
    for role in roles:
        print(role, ": ", len(role))
        print(role_message[i])
        i += 1


"""
 gids["test server"]: {
            "colour": {
                discord.PartialEmoji(name='🩵'): roles["colour"]["cyan"]
            },
            "general": {
                discord.PartialEmoji(name='❤️'): roles["general"]["red"]
            },
            "test": {
                discord.PartialEmoji(name='❤️'): roles["test"]["green"]
            },
        },
        gids["shark squad"]: {
            "birthdays": {
                discord.PartialEmoji(name='🎆'): roles["birthdays"]["January babies"],
                discord.PartialEmoji(name='💌'): roles["birthdays"]["February babies"],
                discord.PartialEmoji(name='🍀'): roles["birthdays"]["March babies"],
                discord.PartialEmoji(name='🪺'): roles["birthdays"]["April babies"],
                discord.PartialEmoji(name='🌥️'): roles["birthdays"]["May babies"],
                discord.PartialEmoji(name='🌞'): roles["birthdays"]["June babies"],
                discord.PartialEmoji(name='🗽'): roles["birthdays"]["July babies"],
                discord.PartialEmoji(name='🌤️'): roles["birthdays"]["August babies"],
                discord.PartialEmoji(name='🍂'): roles["birthdays"]["September babies"],
                discord.PartialEmoji(name='👻'): roles["birthdays"]["October babies"],
                discord.PartialEmoji(name='🦃'): roles["birthdays"]["November babies"],
                discord.PartialEmoji(name='🎅'): roles["birthdays"]["December babies"],
            },
            "general": {
                discord.PartialEmoji(name='🎮'): roles["general"]["shark games"],
                discord.PartialEmoji(name='❗'): roles["general"]["shark update"],
                discord.PartialEmoji(name='💻'): roles["general"]["discord bot update"],
                '<:Zerotwodrinkbyliliiet112:1318361002072604692>': roles["general"]["dyslexxik updates"],
                discord.PartialEmoji(name='🎫'): roles["general"]["shark movie ticket"],
            },
            "backpack": {
                discord.PartialEmoji(name='🦸'): roles["backpacks and sherpas"]["marvel rivals backpack"],
                discord.PartialEmoji(name='🧙‍♀️'): roles["backpacks and sherpas"]["TFD backpack"],
                discord.PartialEmoji(name='🧟'): roles["backpacks and sherpas"]["monster hunter backpack"],
                discord.PartialEmoji(name='🥷'): roles["backpacks and sherpas"]["warframe backpack"],
                discord.PartialEmoji(name='🏰'): roles["backpacks and sherpas"]["elden ring backpack"],
                discord.PartialEmoji(name='🤺'): roles["backpacks and sherpas"]["nightreign backpack"],
                discord.PartialEmoji(name='🔫'): roles["backpacks and sherpas"]["Destiney Backpack"],
                '<a:animateduwu:1279478093278609491>': roles["backpacks and sherpas"]["DNA backpack"],
                '<:Zerotwosurprisedbyliliiet112:1318361087833538631>': roles["backpacks and sherpas"]["ZZZ backpack"],
            },
            "sherpa": {
                discord.PartialEmoji(name='🦸'): roles["backpacks and sherpas"]["marvel rivals sherpa"],
                discord.PartialEmoji(name='🧙‍♀️'): roles["backpacks and sherpas"]["TFD sherpa"],
                discord.PartialEmoji(name='🧟'): roles["backpacks and sherpas"]["monster hunter sherpa"],
                discord.PartialEmoji(name='🥷'): roles["backpacks and sherpas"]["warframe sherpa"],
                discord.PartialEmoji(name='🏰'): roles["backpacks and sherpas"]["elden ring sherpa"],
                discord.PartialEmoji(name='🤺'): roles["backpacks and sherpas"]["nightreign sherpa"],
                discord.PartialEmoji(name='🔫'): roles["backpacks and sherpas"]["Destiney Sherpa"],
                '<a:animateduwu:1279478093278609491>': roles["backpacks and sherpas"]["DNA sherpa"],
                '<:Zerotwosurprisedbyliliiet112:1318361087833538631>': roles["backpacks and sherpas"]["ZZZ sherpa"],
            },
            "friend": {
                discord.PartialEmoji(name='🦸'): roles["friend"]["Marvel Rivals"],
                discord.PartialEmoji(name='🧙‍♀️'): roles["friend"]["TFD"],
                discord.PartialEmoji(name='🧟'): roles["friend"]["Monster Hunter"],
                discord.PartialEmoji(name='🥷'): roles["friend"]["Warframe"],
                discord.PartialEmoji(name='🏰'): roles["friend"]["Elden Ring"],
                discord.PartialEmoji(name='🤺'): roles["friend"]["Nightreign"],
                discord.PartialEmoji(name='🔫'): roles["friend"]["Destiney"],
                '<a:animateduwu:1279478093278609491>': roles["friend"]["DNA"],
                '<:Zerotwosurprisedbyliliiet112:1318361087833538631>': roles["friend"]["ZZZ"],
                '<:hello:1446858982403739689>': roles["friend"]["Gaming Friend"]"""
