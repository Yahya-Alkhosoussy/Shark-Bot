import datetime as dt
import logging
import random
from pathlib import Path
from zoneinfo import ZoneInfo

import discord
from discord.ext import tasks
from pydantic import ValidationError

import SQL.birthdaySQL.birthdays as b
from exceptions.exceptions import BirthdateFormatError, FormatError
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
        loop = self._loops.get(guild_id)
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
            current_date = dt.datetime.now().date()
            birthday_messages = self.config.birthday_message
            month = current_date.strftime("%B")
            guild_name: str = self.config.guilds[guild_id]
            channel_id: int = self.config.get_channel_id(guild_name=guild_name, channel="chatting")
            channel = self.client.get_channel(channel_id)
            if not (channel and isinstance(channel, discord.TextChannel)):
                logging.error(f"Channel not found for channelId: {channel_id}, or channel is not a TextChannel")
                return

            if str(current_date) in firsts and not birthday_messages[month]:
                current_month = current_date.month
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

            user_ids, birthdays = b.get_birthdays()
            current_date = str(current_date).replace(str(current_year) + "-", "")
            birthdays_today: list[discord.User] = []
            for user_id, birthday in zip(user_ids, birthdays):
                if birthday != current_date:
                    print("skipping")
                    continue

                user = await self.client.fetch_user(user_id)
                birthdays_today.append(user)

            if len(birthdays_today) == 1:
                user = birthdays_today[0]
                if user.name == "spiderbyte2007":
                    gif = b.get_gif(1902)
                    message = b.get_birthday_message(1902)
                    await channel.send(message + f"{user.mention}")
                    await channel.send(gif)
                else:
                    num_of_gifs = b.get_number_of_gifs()
                    rand_int = random.randint(1, num_of_gifs)
                    gif: str = b.get_gif(index=rand_int)
                    num_of_messages = b.get_number_of_messages()
                    message_index = random.randint(1, num_of_messages)
                    message = b.get_birthday_message(message_index)
                    await channel.send(message + f"{user.mention}")
                    await channel.send(gif)
            elif len(birthdays_today) > 1:
                num_of_gifs = b.get_number_of_gifs()
                rand_int = random.randint(1, num_of_gifs)
                gif = b.get_gif(index=rand_int)
                num_of_messages = b.get_number_of_messages()
                message_index = random.randint(1, num_of_messages)
                message = b.get_birthday_message(message_index)
                to_send = message + ", ".join(user.mention for user in birthdays_today)
                await channel.send(to_send)

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


async def add_birthday_to_sql(interaction: discord.Interaction, birthmonth: int, birthday: int):
    try:
        birthday_datetime = dt.datetime.strptime(str(birthmonth) + "-" + str(birthday), r"%m-%d")
    except ValueError:
        raise BirthdateFormatError("Birthday format is incorrect", error_code=1005)
    normalised_date = str(birthday_datetime.date()).replace("1900-", "")
    try:
        b.add_birthday(username=interaction.user.name, user_id=interaction.user.id, birthday=normalised_date)
    except Exception as e:
        raise e

    channel = interaction.channel
    if isinstance(channel, discord.TextChannel):
        await channel.send("Birthday Added!")


async def add_custom_gif_internal(interaction: discord.Interaction, gif_link: str, gif_index: int):
    try:
        b.add_custom_gif(ID=gif_index, link=gif_link)
    except FormatError as e:
        raise e

    channel = interaction.channel
    if isinstance(channel, discord.TextChannel):
        await channel.send("custom gif added!")
