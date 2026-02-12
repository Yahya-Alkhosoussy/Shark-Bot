import datetime as dt
import logging
from pathlib import Path
from zoneinfo import ZoneInfo

import discord
from discord.ext import tasks
from pydantic import ValidationError

from utils.core import AppConfig

try:
    config_a = AppConfig(Path(r"config.YAML"))
except ValidationError as e:
    print(e)


class BirthdayLoop:
    def __init__(self, client: discord.Client, config: AppConfig):
        self.client = client
        self.config = config
        self._loops: dict[int, tasks.Loop] = {}  # Guild_id --> Loop

    def is_running(self, guild_id: int) -> bool:
        loop = self._loops[guild_id]
        return bool(loop and loop.is_running())

    def start_for(self, guild_id: int):
        if self.is_running(guild_id):
            return

        central = ZoneInfo("America/Chicago")

        current_year = dt.datetime.now(central).year

        firsts = [f"{current_year}-{str(i).zfill(2)}-01" for i in range(1, 13, 1)]
        # print(firsts)

        async def _tick():
            # The Loop Body
            current_date = dt.datetime.now(central).date()
            birthday_messages = self.config.birthday_message
            month = current_date.strftime("%B")
            if str(current_date) in firsts and not birthday_messages[month]:
                guild_name: str = self.config.guilds[guild_id]
                channel_id: int = self.config.get_channel_id(guild_name=guild_name, channel="chatting")
                channel = self.client.get_channel(channel_id)

                if not (channel and isinstance(channel, discord.TextChannel)):
                    logging.error(f"Channel not found for channelId: {channel_id}, or channel is not a TextChannel")
                    return

                current_month = current_date.month
                print(current_month)
                match current_month:
                    case 1:
                        await channel.send("Happy Birthday to <@&1335413563627409429>")
                        logging.info("Said happy birthday to Jan babies!")
                        if self.config.mark_reminder_as_done("January"):
                            logging.info(f"Saved YAML config successfully and marked {month} that is under reminders as done.")
                        else:
                            logging.warning(f"{month} was not found in loaded config")
                    case 2:
                        await channel.send("Happy Birthday to <@&1335415340049371188>")
                        logging.info("Said happy birthday to Feb babies!")
                        if self.config.mark_reminder_as_done("February"):
                            logging.info(f"Saved YAML config successfully and marked {month} that is under reminders as done.")
                        else:
                            logging.warning(f"{month} was not found in loaded config")
                    case 3:
                        await channel.send("Happy Birthday to <@&1335416311089463378>")
                        logging.info("Said happy birthday to March babies!")
                        if self.config.mark_reminder_as_done("March"):
                            logging.info(f"Saved YAML config successfully and marked {month} that is under reminders as done.")
                        else:
                            logging.warning(f"{month} was not found in loaded config")
                    case 4:
                        await channel.send("Happy Birthday to <@&1335416850615504957>")
                        logging.info("Said happy birthday to April babies!")
                        if self.config.mark_reminder_as_done("April"):
                            logging.info(f"Saved YAML config successfully and marked {month} that is under reminders as done.")
                        else:
                            logging.warning(f"{month} was not found in loaded config")
                    case 5:
                        await channel.send("Happy Birthday to <@&1335417252270571560>")
                        logging.info("Said happy birthday to May babies!")
                        if self.config.mark_reminder_as_done("May"):
                            logging.info(f"Saved YAML config successfully and marked {month} that is under reminders as done.")
                        else:
                            logging.warning(f"{month} was not found in loaded config")
                    case 6:
                        await channel.send("Happy Birthday to <@&1335417579832873072>")  #
                        logging.info("Said happy birthday to June babies!")
                        if self.config.mark_reminder_as_done("June"):
                            logging.info(f"Saved YAML config successfully and marked {month} that is under reminders as done.")
                        else:
                            logging.warning(f"{month} was not found in loaded config")
                    case 7:
                        await channel.send("Happy Birthday to <@&1335417607825784864>")
                        logging.info("Said happy birthday to July babies!")
                        if self.config.mark_reminder_as_done("July"):
                            logging.info(f"Saved YAML config successfully and marked {month} that is under reminders as done.")
                        else:
                            logging.warning(f"{month} was not found in loaded config")
                    case 8:
                        await channel.send("Happy Birthday to <@&1335417655309369375>")
                        logging.info("Said happy birthday to August babies!")
                        if self.config.mark_reminder_as_done("August"):
                            logging.info(f"Saved YAML config successfully and marked {month} that is under reminders as done.")
                        else:
                            logging.warning(f"{month} was not found in loaded config")
                    case 9:
                        await channel.send("Happy Birthday to <@&1335417694228316172>")
                        logging.info("Said happy birthday to September babies!")
                        if self.config.mark_reminder_as_done("September"):
                            logging.info(f"Saved YAML config successfully and marked {month} that is under reminders as done.")
                        else:
                            logging.warning(f"{month} was not found in loaded config")
                    case 10:
                        await channel.send("Happy Birthday to <@&1335417733281480774>")
                        logging.info("Said happy birthday to October babies!")
                        if self.config.mark_reminder_as_done("October"):
                            logging.info(f"Saved YAML config successfully and marked {month} that is under reminders as done.")
                        else:
                            logging.warning(f"{month} was not found in loaded config")
                    case 11:
                        await channel.send("Happy Birthday to <@&1335417768404848640>")
                        logging.info("Said happy birthday to November babies!")
                        if self.config.mark_reminder_as_done("November"):
                            logging.info(f"Saved YAML config successfully and marked {month} that is under reminders as done.")
                        else:
                            logging.warning(f"{month} was not found in loaded config")
                    case 12:
                        await channel.send("Happy Birthday to <@&1335417794799341670>")
                        logging.info("Said happy birthday to December babies!")
                        if self.config.mark_reminder_as_done("December"):
                            logging.info(f"Saved YAML config successfully and marked {month} that is under reminders as done.")
                        else:
                            logging.warning(f"{month} was not found in loaded config")

        loop = tasks.loop(hours=13, reconnect=True)(_tick)

        @loop.before_loop
        async def _before():
            await self.client.wait_until_ready()
            logging.info("Birthday loop started")

        @loop.after_loop
        async def _after():
            if loop.is_being_cancelled():
                logging.info("Birthday loop cancelled (shutdown)")
            else:
                logging.info("Birthday loop ended normally.")

        @loop.error
        async def _error(self, error: BaseException):
            logging.exception(f"birthday loop error {error}")

        self._loops[guild_id] = loop
        loop.start()

    def stop_for(self, guild_id: int) -> bool:
        loop = self._loops[guild_id]
        if loop and loop.is_running():
            loop.stop()
            return True
        return False
