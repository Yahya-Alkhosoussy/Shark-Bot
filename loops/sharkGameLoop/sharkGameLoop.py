import asyncio, logging, random, time, discord, datetime as dt
from discord.ext import tasks
from pathlib import Path
import utils.read_Yaml as RY

# import your helpers/config
import SQL.sharkGamesSQL.sharkGameSQL as sg

TIME_PER_LOOP = 1800 #in seconds

CONFIG_PATH = Path(r"config.YAML")

config = RY.read_config(CONFIG=CONFIG_PATH)

def get_channel_id(guild_name: str, channel: str):

    channels = config.get("channels").get(channel)

    if channels is None:
        return "Channel not in config"
    
    channels = channels.get(guild_name)

    if channels is None:
        return "Channel does not exist in the server"
    else:
        return int(channels)

class SharkLoops:
    def __init__(self, client: discord.client):
        self.client = client
        self._loops: dict[int, tasks.Loop] = {} #guild id -> Loop.

    def is_running(self, guild_id: int) -> bool:
        loop = self._loops.get(guild_id)
        return bool(loop and loop.is_running())
    
    def start_for(self, guild_id: int):
        if self.is_running(guild_id=guild_id):
            return
        c = self.client
        async def _tick():
            # The loop body
            names: list[str] = sg.get_names_of_sharks()
            if not names:
                return # nothing to drop
            
            rand_int = random.randint(1, 100)
            
            if rand_int <= 4:
                list_of_names = sg.get_shark_names("ultra-rare")
            elif rand_int <= 10:
                list_of_names = sg.get_shark_names("rare")
            elif rand_int <= 20:
                list_of_names = sg.get_shark_names("uncommon")
            elif rand_int <= 50:
                list_of_names = sg.get_shark_names("common")
            else:
                list_of_names = sg.get_shark_names("very common")

            name_index = random.randint(0, len(list_of_names) - 1)
            name_to_drop: str = names[name_index] # use name index and not rand_int next time idiot.
            # print(name_to_drop)
            random_number_2 = random.randint(0, 100)
            
            if random_number_2 <= 2:
                rarity = "legendary"
            elif random_number_2 > 2 and random_number_2 <= 5:
                rarity = "shiny"
            else:
                rarity = "normal"

            id_to_name: dict = {int(v): k for k, v in config["guilds"].items()}
            guild_name: str = id_to_name.get(guild_id)
            channel_id = get_channel_id(guild_name=guild_name, channel="game")
            # print(channel_id)
            channel = c.get_channel(channel_id)
            # print(channel)
            await channel.send("A shark just appeared 🦈! Quick, type `?catch` within 2 minutes to catch it 🎣")

            def check(m: discord.Message):
                return (
                    m.channel.id == channel_id
                    and not m.author.bot
                    and m.content.lower().startswith("?catch")
                )
            
            window_seconds = 120
            
            deadline = time.monotonic() + window_seconds
            caught_users: dict[str, discord.Message] = {}  # username -> first catch message
            lists_of_after: dict[str, str]= {}

            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                try:
                    msg: discord.Message = await c.wait_for("message", check=check, timeout=remaining)
                except asyncio.TimeoutError:
                    break
                    
                content = msg.content.strip()

                # Remove the command prefix only once, then strip leading spaces
                after = content[len("?catch"):].strip() if content.lower().startswith("?catch") else ""

                # only first successful catch per user counts
                if msg.author.name not in caught_users:
                    # print(msg.author.name)
                    caught_users[msg.author.name] = msg
                    lists_of_after[msg.author.name] = after

            success: list = []

            odds = sg.fishing_odds_shark

            for user in caught_users: # looks through all the keys
                num = random.randint(0, 100)
                net = lists_of_after.get(user) if sg.is_net_available(user, lists_of_after.get(user)) else "rope net"
                if net != "rope net":
                    available_nets, about_to_break, broken_nets, net_uses = sg.get_net_availability(user)
                    if net in available_nets:
                        # print("found it")
                        if net in about_to_break and net_uses == 21:
                            await channel.send(f"WARNING @{user}: Net is about to break, 1 more use left. Do not worry through because you have 4 more of the same net left")
                        elif net in about_to_break and net_uses == 16:
                            await channel.send(f"WARNING @{user}: Net is about to break, 1 more use left. Do not worry through because you have 3 more of the same net left")
                        elif net in about_to_break and net_uses == 11:
                            await channel.send(f"WARNING @{user}: Net is about to break, 1 more use left. Do not worry through because you have 2 more of the same net left")
                        elif net in about_to_break and net_uses == 6:
                            await channel.send(f"WARNING @{user}: Net is about to break, 1 more use left. Do not worry through because you have 1 more of the same net left")
                        elif net in about_to_break and net_uses == 1:
                            await channel.send(f"WARNING @{user}: Net is about to break, 1 more use left. This is your last net")
                        
                        
                        if net in broken_nets and net_uses == 20:
                            await channel.send(f"WARNING @{user}: Net broken, don't worry through because you have 4 more of the same net left")
                        elif net in broken_nets and net_uses == 15:
                            await channel.reply(f"WARNING @{user}: Net broken, don't worry through because you have 3 more of the same net left")
                        elif net in broken_nets and net_uses == 10:
                            await channel.reply(f"WARNING @{user}: Net broken, don't worry through because you have 2 more of the same net left")
                        elif net in broken_nets and net_uses == 5:
                            await channel.reply(f"WARNING @{user}: Net broken, don't worry through because you have 1 more of the same net left")
                        elif net in broken_nets and net_uses == 0:
                            await channel.reply(f"WARNING @{user}: Net broken. You have no more uses of the same net left")
                            
                if num <= odds(str(user), net):

                    current_time = dt.datetime.now()
                    time_caught: str = f"{current_time.date()} {current_time.hour}"
                    success.append(user)
                    sg.create_dex(username=user, shark_name=name_to_drop, when_caught=time_caught, net_used=net, rarity=rarity)
                    coins = sg.reward_coins(username=user, rare=rarity, shark=True, shark_name=name_to_drop)
                sg.remove_net_use(user, net, net_uses - 1)
            if not success:
                await channel.send(f"A {rarity} {name_to_drop} has escaped, no one caught it. 😞")
            elif len(success) == 1:
                await channel.send(f"Congratulations to {success[0]} who caught a {rarity} {name_to_drop} 👏. You have been granted {coins}")
            else:
                people = ""
                i = 0
                for person in success:
                    if i < len(success):
                        people += f"{person}, "
                    else:
                        people += f"{person}"
                await channel.send(f"Congratulations to {people} for catching a {rarity} {name_to_drop} 👏. You have been granted {coins}")

        loop = tasks.loop(seconds=TIME_PER_LOOP, reconnect=True)(_tick)
        id_to_name: dict = {int(v): k for k, v in config["guilds"].items()}
        guild_name: str | None = id_to_name.get(guild_id)

        @loop.before_loop
        async def _before():
            await self.client.wait_until_ready()
            logging.info(f"[{guild_name}] Shark game loop started (startup)")
        
        async def _after():
            if loop.is_being_cancelled():
                logging.info(f"[{guild_name}] Shark game loop cancelled (shutdown)")
            else:
                logging.info(f"[{guild_name}] Shark game loop ended normally.")
        
        @loop.error
        async def _error(error: Exception):
            logging.exception(f"[{guild_name}] Shark game loop error %s", error)
        
        self._loops[guild_id] = loop
        loop.start()
        
    def stop_for(self, guild_id: int) -> bool:
        loop = self._loops.get(guild_id)
        if loop and loop.is_running():
            loop.stop()
            return True
        return False
