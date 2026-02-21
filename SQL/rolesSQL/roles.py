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


# print(config.guild_role_messages)
# Set up for emojis table
roles_test_server = ["🩵", "🧡", "❤️", "💚"]
roles_test_server_emoji_ids = [None, None, None, None]
roles_name_test_server = ["cyan", "orange", "red", "green"]
roles_test_server_ids = [1422681663342903438, 1470819205564727427, 1428757018792956085, 1428757052993437767]
roles_test_server_messages = ["colour", "colour", "general", "test"]
roles_test_server_messages_ids = [1463681052278263880, 1463681055084118017, 1463681059236614144]


birthday_roles_shark_squad_emojis = ["🎆", "💌", "🍀", "🪺", "🌥️", "🌞", "🗽", "🌤️", "🍂", "👻", "🦃", "🎅"]
birthday_roles_shark_squad_names = [
    "Janruary babies",
    "February babies",
    "March babies",
    "April babies",
    "May babies",
    "June babies",
    "July babies",
    "August babies",
    "September babies",
    "October babies",
    "November babies",
    "December babies",
]
birthday_roles_shark_squad_ids = [
    1335413563627409429,
    1335415340049371188,
    1335416311089463378,
    1335416850615504957,
    1335417252270571560,
    1335417579832873072,
    1335417607825784864,
    1335417655309369375,
    1335417694228316172,
    1335417733281480774,
    1335417768404848640,
    1335417794799341670,
]
birthday_roles_shark_squad_emoji_ids = [None, None, None, None, None, None, None, None, None, None, None, None]
birthday_roles_shark_squad_animated = [False, False, False, False, False, False, False, False, False, False, False, False]
general_roles_shark_squad_emojis = ["🎮", "❗", "💻", "Zerotwodrinkbyliliiet112", "🎫"]
general_roles_shark_squad_names = [
    "shark games",
    "shark updates",
    "discord bot updates",
    "dyslexxik updates",
    "shark movie ticket",
]
general_roles_shark_squad_ids = [
    1398962532244520992,
    1335425471810375750,
    1433791804893040743,
    1461715493034655786,
    1461715407839821918,
]
general_roles_shark_squad_emoji_ids = [None, None, None, 1318361002072604692, None]
general_roles_shark_squad_animated = [False, False, False, False, False]
friend_roles_shark_squad_emojis = [
    "🦸",
    "🧙‍♀️",
    "🧟",
    "🥷",
    "🏰",
    "🤺",
    "🔫",
    "animateduwu",
    "Zerotwosurprisedbyliliiet112",
    "hello",
]
friend_roles_shark_squad_names = [
    "Marvel Rivals Friend",
    "TFD Friend",
    "Monster Hunter Friend",
    "Warframe Friend",
    "Elden Ring Friend",
    "Nightreign Friend",
    "Destiny Friend",
    "DNA Friend",
    "ZZZ Friend",
    "Gaming Friend",
]
friend_roles_shark_squad_ids = [
    1457472384641531954,  # rivals
    1457472526312538266,  # tfd
    1457472677303554111,  # MH
    1457472769267601428,  # warframes
    1457472831507009739,  # ER
    1457472920132653199,  # Nightreign
    1457473018598260900,  # Cancer
    1459222288481255496,  # DNA
    1459230046165274735,  # ZZZ
    1467166788105142324,  # general
]
friend_roles_shark_squad_emoji_ids = [
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    1279478093278609491,
    1318361087833538631,
    1446858982403739689,
]
friend_roles_shark_squad_animated = [False, False, False, False, False, False, False, True, False, False]
backpack_roles_shark_squad_emojis = [
    "🦸",
    "🧙‍♀️",
    "🧟",
    "🥷",
    "🏰",
    "🤺",
    "🔫",
    "animateduwu",
    "Zerotwosurprisedbyliliiet112",
]
backpack_roles_shark_squad_names = [
    "Marvel Rivals Backpack",
    "TFD Backpack",
    "Monster Hunter Backpack",
    "Warframe Backpack",
    "Elden Ring Backpack",
    "Nightreign Backpack",
    "Destiny Backpack",
    "DNA Backpack",
    "ZZZ Backpack",
]
backpack_roles_shark_squad_ids = [
    1432332559731130520,  # rivals
    1432333228408307802,  # tfd
    1432333412118691881,  # MH
    1432333502883303567,  # warframes
    1432425438688575570,  # ER
    1432425674315927582,  # Nightreign
    1445833998919139460,  # Destiny
    1459222514495524985,  # DNA
    1459229849175588925,  # ZZZ
]
backpack_roles_shark_squad_emoji_ids = [
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    1279478093278609491,
    1318361087833538631,
]
backpack_roles_shark_squad_animated = [False, False, False, False, False, False, False, True, False]
sherpa_roles_shark_squad_emojis = [
    "🦸",
    "🧙‍♀️",
    "🧟",
    "🥷",
    "🏰",
    "🤺",
    "🔫",
    "animateduwu",
    "Zerotwosurprisedbyliliiet112",
]
sherpa_roles_shark_squad_names = [
    "Marvel Rivals Sherpa",
    "TFD Sherpa",
    "Monster Hunter Sherpa",
    "Warframe Sherpa",
    "Elden Ring Sherpa",
    "Nightreign Sherpa",
    "Destiny Sherpa",
    "DNA Sherpa",
    "ZZZ Sherpa",
]
sherpa_roles_shark_squad_ids = [
    1432333018365689926,  # rivals
    1432333345567805450,  # tfd
    1432333501717413949,  # MH
    1432333639361888256,  # warframes
    1432425574181113856,  # ER
    1432425787927298329,  # Nightreign
    1445834184303054928,  # Destiny
    1459222669949141012,  # DNA
    1459229932508025046,  # ZZZ
]
sherpa_roles_shark_squad_emoji_ids = [
    None,
    None,
    None,
    None,
    None,
    None,
    None,
    1279478093278609491,
    1318361087833538631,
]
sherpa_roles_shark_squad_animated = [False, False, False, False, False, False, False, True, False]
roles_shark_squad_messages = ["birthdays", "general", "friend", "backpack", "sherpa"]

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


i = 0
for emoji in roles_test_server:
    cur.execute(
        "INSERT OR IGNORE INTO emojis (animated, name, discord_id) VALUES (?, ?, ?)",
        (False, emoji, roles_test_server_emoji_ids[i]),
    )
    conn.commit()

    emoji_id = cur.execute("SELECT id FROM emojis WHERE name = ?", (emoji,)).fetchone()[0]

    cur.execute("INSERT OR IGNORE INTO guilds (name, guild_id) VALUES (?, ?)", ("test server", 1066090135839580231))
    conn.commit()
    guild_id = cur.execute("SELECT id FROM guilds WHERE name = ?", ("test server",)).fetchone()[0]

    cur.execute("INSERT OR IGNORE INTO roleSets (name) VALUES (?)", (roles_test_server_messages[i],))
    conn.commit()
    roleSetID = cur.execute("SELECT id FROM roleSets WHERE name = ?", (roles_test_server_messages[i],)).fetchone()[0]

    cur.execute(
        "INSERT OR IGNORE INTO roles (name, role_id, emoji_id, guild_id, roleSet_ID) VALUES (?, ?, ?, ?, ?)",
        (roles_name_test_server[i], roles_test_server_ids[i], emoji_id, guild_id, roleSetID),
    )
    i += 1


for message in roles_shark_squad_messages:
    guild_table_id = put_guild_in_table("shark squad", 1273776575266951268)
    role_set_table_id = put_role_set_in_table(message)
    match message:
        case "birthdays":
            i = 0
            for emoji in birthday_roles_shark_squad_emojis:
                animated = birthday_roles_shark_squad_animated[i]
                emoji_id = birthday_roles_shark_squad_emoji_ids[i]
                emoji_table_id = put_emoji_in_table(animated=animated, emoji_name=emoji, discord_id=emoji_id)
                role_name = birthday_roles_shark_squad_names[i]
                role_id = birthday_roles_shark_squad_ids[i]
                put_role_in_table(role_name, role_id, emoji_table_id, guild_table_id, role_set_table_id)
                i += 1
        case "general":
            i = 0
            for emoji in general_roles_shark_squad_emojis:
                animated = general_roles_shark_squad_animated[i]
                emoji_id = general_roles_shark_squad_emoji_ids[i]
                emoji_table_id = put_emoji_in_table(animated=animated, emoji_name=emoji, discord_id=emoji_id)
                role_name = general_roles_shark_squad_names[i]
                role_id = general_roles_shark_squad_ids[i]
                put_role_in_table(role_name, role_id, emoji_table_id, guild_table_id, role_set_table_id)
                i += 1
        case "backpack":
            i = 0
            for emoji in backpack_roles_shark_squad_emojis:
                animated = backpack_roles_shark_squad_animated[i]
                emoji_id = backpack_roles_shark_squad_emoji_ids[i]
                emoji_table_id = put_emoji_in_table(animated=animated, emoji_name=emoji, discord_id=emoji_id)
                role_name = backpack_roles_shark_squad_names[i]
                role_id = backpack_roles_shark_squad_ids[i]
                put_role_in_table(role_name, role_id, emoji_table_id, guild_table_id, role_set_table_id)
                i += 1
        case "sherpa":
            i = 0
            for emoji in sherpa_roles_shark_squad_emojis:
                animated = sherpa_roles_shark_squad_animated[i]
                emoji_id = sherpa_roles_shark_squad_emoji_ids[i]
                emoji_table_id = put_emoji_in_table(animated=animated, emoji_name=emoji, discord_id=emoji_id)
                role_name = sherpa_roles_shark_squad_names[i]
                role_id = sherpa_roles_shark_squad_ids[i]
                put_role_in_table(role_name, role_id, emoji_table_id, guild_table_id, role_set_table_id)
                i += 1
        case "friend":
            i = 0
            for emoji in friend_roles_shark_squad_emojis:
                animated = friend_roles_shark_squad_animated[i]
                emoji_id = friend_roles_shark_squad_emoji_ids[i]
                emoji_table_id = put_emoji_in_table(animated=animated, emoji_name=emoji, discord_id=emoji_id)
                role_name = friend_roles_shark_squad_names[i]
                role_id = friend_roles_shark_squad_ids[i]
                put_role_in_table(role_name, role_id, emoji_table_id, guild_table_id, role_set_table_id)
                i += 1


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


def get_roles():
    """
    Returns the roleSetName, roleName and RoleID
    """
    role_names: list[str] = []
    role_ids: list[int] = []
    role_set_names: list[str] = []
    for emoji_result in emojiResults:
        role_names.append(emoji_result.roleName)
        role_ids.append(emoji_result.roleId)
        role_set_names.append(emoji_result.roleSetName)
    return role_names, role_ids, role_set_names


def add_role(
    role_name: str,
    role_id: int,
    role_emoji_name: str,
    is_emoji_animated: bool,
    role_emoji_id: int,
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
