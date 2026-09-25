from asyncio import run
from pathlib import Path

from aiosqlite import connect
from discord import Member, User

from utils.ban_list import Servers

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
        await conn.commit()


async def add_to_ban_list(member: Member | User, ban_reason: str = ""):
    async with connect(db_path) as conn:
        await conn.execute(
            "INSERT OR IGNORE INTO ban_list (discord_id, discord_username, reason, status, initial_server_ban)"
            " VALUES (?, ?, ?, ?, ?)",
            (member.id, member.name, ban_reason, "banned", Servers.SHARKOCALYPSE.value),
        )
        await conn.commit()


async def check_if_user_in_ban_list(member: Member | User):
    async with connect(db_path) as conn:
        async with conn.execute("SELECT status FROM ban_list WHERE discord_id=?", (member.id,)) as cur:
            result = await cur.fetchone()
            if result is None:
                return False
            status = result[0]
            if status == "banned":
                return True
            return False


async def set_as_unbanned(member: Member | User):
    async with connect(db_path) as conn:
        await conn.execute("UPDATE ban_list SET status='unbanned' WHERE discord_id=?", (member.id,))
        await conn.commit()


run(init_db())
