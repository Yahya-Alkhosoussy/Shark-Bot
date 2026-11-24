from asyncio import run
from pathlib import Path

from aiosqlite import connect
from discord import Member, User

from utils.ban_list import BannedMember, Channels, Servers, Statuses, TwitchUser

db_path = Path("databases/shared ban list.db")


async def init_db():
    async with connect(db_path) as conn:
        await conn.execute(
            """CREATE TABLE IF NOT EXISTS ban_list
            (
                id INTEGER PRIMARY KEY,
                discord_id INTEGER UNIQUE,
                discord_username TEXT,
                reason TEXT,
                status TEXT,
                initial_server_ban TEXT
            )"""
        )
        await conn.execute(
            """CREATE TABLE IF NOT EXISTS twitch_ban_list
            (
                id INTEGER PRIMARY KEY,
                twitch_id TEXT UNIQUE,
                twitch_username TEXT,
                reason TEXT,
                status TEXT,
                initial_channel_ban TEXT
            )"""
        )
        await conn.commit()


async def add_to_ban_list(member: Member | User, ban_reason: str = ""):
    async with connect(db_path) as conn:
        await conn.execute(
            "INSERT OR IGNORE INTO ban_list (discord_id, discord_username, reason, status, initial_server_ban)"
            " VALUES (?, ?, ?, ?, ?)",
            (member.id, member.name, ban_reason, Statuses.BANNED.value, Servers.SHARKOCALYPSE.value),
        )
        await conn.commit()


async def check_if_user_in_ban_list(member: Member | User):
    async with connect(db_path) as conn:
        async with conn.execute("SELECT status FROM ban_list WHERE discord_id=?", (member.id,)) as cur:
            result = await cur.fetchone()
            if result is None:
                return False
            status = Statuses(result[0])
            if status == Statuses.BANNED:
                return True
            return False


async def get_banned_member(member: Member | User) -> BannedMember:
    async with connect(db_path) as conn:
        async with conn.execute(
            "SELECT reason, status, initial_server_ban FROM ban_list WHERE discord_id=?", (member.id,)
        ) as cur:
            result = await cur.fetchone()
            if result is None:
                raise ValueError(f"Could not find user with id {member.id}")
            return BannedMember(member.name, member.id, result[0], result[1], result[2])


async def set_as_unbanned(member: Member | User):
    _member = await get_banned_member(member)
    if _member.initial_server_ban != Servers.SHARKOCALYPSE:
        return
    async with connect(db_path) as conn:
        await conn.execute("UPDATE ban_list SET status='unbanned' WHERE discord_id=?", (member.id,))
        await conn.commit()


async def get_banned_members() -> list[BannedMember]:
    async with connect(db_path) as conn:
        async with conn.execute("SELECT discord_username, discord_id, reason, status, initial_server_ban FROM ban_list") as cur:
            results = await cur.fetchall()
            to_return: list[BannedMember] = []
            for result in results:
                to_return.append(
                    BannedMember(
                        name=result[0],
                        id=result[1],
                        reason_for_ban=result[2],
                        status=Statuses(result[3]),
                        initial_server_ban=Servers(result[4]),
                    )
                )
    return to_return


async def add_to_twitch_ban_list(user: TwitchUser):
    async with connect(db_path) as conn:
        await conn.execute(
            "INSERT OR IGNORE INTO twitch_ban_list (twitch_id, twitch_username, reason, status, initial_channel_ban)"
            " VALUES (?, ?, ?, ?, ?)",
            (user.id, user.display, user.reason_for_ban, user.status.value, Channels.SHARKOCALYPSE.value),
        )
        await conn.commit()


async def get_twitch_ban_list() -> list[TwitchUser]:
    async with connect(db_path) as conn:
        cursor = await conn.execute(
            "SELECT twitch_id, twitch_username, reason, status, initial_channel_ban FROM twitch_ban_list"
        )
        results = await cursor.fetchall()
        _list: list[TwitchUser] = []
        for result in results:
            _list.append(TwitchUser(result[1], result[0], result[2], Statuses(result[3]), Channels(result[4])))

    return _list


run(init_db())
