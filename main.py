import asyncio
import os

import uvicorn
from fastapi import BackgroundTasks, FastAPI

from MyBot import bot

app = FastAPI()


@app.post("/api/v1/update_react_roles/{guild_id}")
async def _update_react_roles(guild_id: int, background_tasks: BackgroundTasks):
    print("Ping gotten! Updating react roles")
    print("React roles updated!")
    guild = bot.get_guild(guild_id)
    if guild is not None:
        background_tasks.add_task(bot.ensure_react_roles_message, guild)
    return {"status", "ok"}


@app.post("/api/v1/twitch_ban/update")
async def _twitch_ban_list_updated(background_tasks: BackgroundTasks):
    print("Twitch ban happened")


async def main():
    token = os.getenv("token")
    assert token, "No token found in envvars. Impossible to continue."

    config = uvicorn.Config(app, "0.0.0.0", 9000)
    server = uvicorn.Server(config)

    await asyncio.gather(bot.start(token=token), server.serve(), return_exceptions=True)


if __name__ == "__main__":
    asyncio.run(main())
