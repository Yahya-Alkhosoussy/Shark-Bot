import logging, discord, datetime as dt
from discord.ext import tasks
from ..sharkGameLoop.sharkGameLoop import get_channel_id, config, RY, CONFIG_PATH, SharkLoops, TIME_PER_LOOP, sg
from zoneinfo import ZoneInfo

def mark_reminder_as_done(month: str):
    cfg: dict = RY.read_config(CONFIG=CONFIG_PATH)
    node: dict = cfg.get("birthday message")
    # print("found it")
    # print(event_name)
    if month in node:
        node[month] = True
        RY.save_config(cfg=cfg, CONFIG=CONFIG_PATH)
        logging.info(f"Saved YAML config successfully and marked {month} that is under reminders as done.")
    else:
        logging.warning(f"{month} was not found in YAML config")

class BirthdayLoop:
    def __init__(self, client: discord.client):
        self.client = client
        self._loops: dict[int, tasks.Loop] = {} # Guild_id --> Loop

    def is_running(self, guild_id: int) -> bool:
        loop = self._loops.get(guild_id)
        return bool(loop and loop.is_running())

    def start_for(self, guild_id: int):
        if self.is_running(guild_id):
            return

        central = ZoneInfo("America/Chicago")

        current_year = dt.datetime.now(central).year
        print(current_year)

        firsts = [f"{current_year}-{str(i).zfill(2)}-01" for i in range(1, 13, 1)]
        # print(firsts)
        c = self.client

        async def _tick():
            # The Loop Body
            current_date = dt.datetime.now(central).date()
            birthday_messages = config["birthday message"]
            month = current_date.strftime("%B")
            if str(current_date) in firsts and not birthday_messages.get(month):
                id_to_name: dict = {int(v): k for k, v in config["guilds"].items()}
                guild_name: str  = id_to_name.get(guild_id)
                channel_id: int  = get_channel_id(guild_name=guild_name, channel="chatting")
                channel = c.get_channel(channel_id)

                current_month = current_date.month
                print(current_month)
                match current_month:
                    case 1:
                        await channel.send("Happy Birthday to <@&1335413563627409429>")
                        logging.info("Said happy birthday to Jan babies!")
                        mark_reminder_as_done("January")
                    case 2:
                        await channel.send("Happy Birthday to <@&1335415340049371188>")
                        logging.info("Said happy birthday to Feb babies!")
                        mark_reminder_as_done("February")
                    case 3:
                        await channel.send("Happy Birthday to <@&1335416311089463378>")
                        logging.info("Said happy birthday to March babies!")
                        mark_reminder_as_done("March")
                    case 4:
                        await channel.send("Happy Birthday to <@&1335416850615504957>")
                        logging.info("Said happy birthday to April babies!")
                        mark_reminder_as_done("April")
                    case 5:
                        await channel.send("Happy Birthday to <@&1335417252270571560>")
                        logging.info("Said happy birthday to May babies!")
                        mark_reminder_as_done("May")
                    case 6:
                        await channel.send("Happy Birthday to <@&1335417579832873072>")#
                        logging.info("Said happy birthday to June babies!")
                        mark_reminder_as_done("June")
                    case 7:
                        await channel.send("Happy Birthday to <@&1335417607825784864>")
                        logging.info("Said happy birthday to July babies!")
                        mark_reminder_as_done("July")
                    case 8:
                        await channel.send("Happy Birthday to <@&1335417655309369375>")
                        logging.info("Said happy birthday to August babies!")
                        mark_reminder_as_done("August")
                    case 9:
                        await channel.send("Happy Birthday to <@&1335417694228316172>")
                        logging.info("Said happy birthday to September babies!")
                        mark_reminder_as_done("September")
                    case 10:
                        await channel.send("Happy Birthday to <@&1335417733281480774>")
                        logging.info("Said happy birthday to October babies!")
                        mark_reminder_as_done("October")
                    case 11:
                        await channel.send("Happy Birthday to <@&1335417768404848640>")
                        logging.info("Said happy birthday to November babies!")
                        mark_reminder_as_done("November")
                    case 12:
                        await channel.send("Happy Birthday to <@&1335417794799341670>")
                        logging.info("Said happy birthday to December babies!")
                        mark_reminder_as_done("December")
        
        loop = tasks.loop(hours=12, reconnect=True)(_tick)
        
        @loop.before_loop
        async def _before():
            await self.client.wait_until_ready()
            logging.info(f"Birthday loop started")
        
        @loop.after_loop
        async def _after():
            if loop.is_being_cancelled():
                logging.info(f"Birthday loop cancelled (shutdown)")
            else:
                logging.info("Birthday loop ended normally.")
        
        @loop.error
        async def _error(error: Exception):
            logging.exception("birthday loop error %s", error)
        
        self._loops[guild_id] = loop
        loop.start()
    
    def stop_for(self, guild_id: int) -> bool:
        loop = self._loops.get(guild_id)
        if loop and loop.is_running():
            loop.stop()
            return True
        return False

            
            