from asyncio import run
from pathlib import Path

from aiosqlite import connect

from utils.core import CustomCommand

db_path = Path("databases/commands.db")


async def init_db():
    async with connect(db_path) as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS commands
            (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                reply TEXT,
                mod_only BOOLEAN DEFAULT 0
            )
            """
        )
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS command_aliases
            (
                id INTEGER PRIMARY KEY,
                alias TEXT UNIQUE,
                command_id INTEGER NOT NULL REFERENCES commands(id) ON DELETE CASCADE
            )
            """
        )
        await conn.commit()


run(init_db())


async def get_custom_commands() -> list[CustomCommand]:
    async with connect(db_path) as conn:
        async with conn.execute(
            """
            SELECT c.name, c.reply, c.mod_only, GROUP_CONCAT(ca.alias, '|')
            FROM commands as c
            JOIN command_aliases as ca ON c.id = ca.command_id
            GROUP BY c.id
            """
        ) as cur:
            results = await cur.fetchall()
            commands: list[CustomCommand] = []
            for result in results:
                commands.append(
                    CustomCommand(
                        name=result[0],
                        reply=result[1],
                        mod_only=bool(result[2]),
                        aliases=result[3].split("|"),
                    )
                )
        async with conn.execute(
            "SELECT name, reply, mod_only FROM commands WHERE id NOT IN (select command_id FROM command_aliases)"
        ) as cur:
            results = await cur.fetchall()
            for result in results:
                commands.append(
                    CustomCommand(
                        name=result[0],
                        reply=result[1],
                        mod_only=bool(result[2]),
                        aliases=None,
                    )
                )

    return list(commands)
