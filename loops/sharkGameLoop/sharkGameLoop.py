import asyncio
import datetime as dt
import logging
import random
import time
from pathlib import Path

import discord
from discord.ext import tasks

# import your helpers/config
import SQL.sharkGames.sharkGameSQL as sg
from utils.core import AppConfig
from utils.fishing import FishingConfig, remove_net_use

fishing_config = FishingConfig(Path(r"fishing\fishing.yaml"))


class SharkLoops:
    def __init__(self, client: discord.Client, config: AppConfig):
        self.config = config
        self.client = client
        self._loops: dict[int, tasks.Loop] = {}  # guild id -> Loop.
        self.check_interval = self.load_interval()

    def is_running(self, guild_id: int) -> bool:
        loop = self._loops.get(guild_id)  # returns none if it doesn't exist
        return bool(loop and loop.is_running())

    def load_interval(self) -> int:
        self.config.reload()
        return self.config.time_per_loop

    def start_for(self, guild_id: int):
        if self.is_running(guild_id=guild_id):
            return
        c = self.client

        async def _tick():
            # Check if interval changed
            new_interval = self.load_interval()
            if new_interval != self.check_interval:
                self.check_interval = new_interval
                # change the interval o fthe loop
                if guild_id in self._loops:
                    self._loops[guild_id].change_interval(seconds=new_interval)

            # The loop body
            names: list[str] = sg.get_names_of_sharks()
            if not names:
                return  # nothing to drop

            rand_int = random.randint(1, 100)

            if rand_int <= 9:
                list_of_names = sg.get_shark_names(sg.SharkRarity.ULTRA_RARE)
            elif rand_int <= 20:
                list_of_names = sg.get_shark_names(sg.SharkRarity.RARE)
            elif rand_int <= 35:
                list_of_names = sg.get_shark_names(sg.SharkRarity.UNCOMMON)
            elif rand_int <= 65:
                list_of_names = sg.get_shark_names(sg.SharkRarity.COMMON)
            else:
                list_of_names = sg.get_shark_names(sg.SharkRarity.VERY_COMMON)

            name_index = random.randint(0, len(list_of_names) - 1)
            name_to_drop: str = names[name_index]  # use name index and not rand_int next time idiot.
            # print(name_to_drop)
            random_number_2 = random.randint(0, 100)

            if random_number_2 <= 2:
                rarity = "legendary"
            elif random_number_2 > 2 and random_number_2 <= 5:
                rarity = "shiny"
            else:
                rarity = "normal"

            guild_name: str = self.config.guilds[guild_id]
            try:
                channel_id = self.config.get_channel_id(guild_name=guild_name, channel="game")
                channel = c.get_channel(channel_id)
                if channel and isinstance(channel, discord.TextChannel):
                    await channel.send("A shark just appeared 🦈! Quick, type `?catch` within 2 minutes to catch it 🎣")
                else:
                    print(f"channel could be None, here's channel: {channel} and here's ID {channel_id}")
                    raise TypeError(f"Request for Channel ID {channel_id} returned a non-text channel or None")
            except KeyError as e:
                print("Hey! I got a key error for ya: ", e)
                raise e

            def check(m: discord.Message):
                return m.channel.id == channel_id and not m.author.bot and m.content.lower().startswith("?catch")

            deadline = time.monotonic() + self.config.window_time
            caught_users: dict[str, discord.Message] = {}  # username -> first catch message
            lists_of_after: dict[str, str] = {}

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
                after = content[len("?catch") :].strip() if content.lower().startswith("?catch") else ""

                # only first successful catch per user counts
                user_name = msg.author.name
                if user_name not in caught_users:
                    caught_users[user_name] = msg
                    lists_of_after[user_name] = after
                    # Send a message to the user if the net is not available after they send the `?catch` command.
                    if not sg.is_net_available(user_name, after) and after:
                        await channel.send(
                            f"{msg.author.mention} you do not own {lists_of_after.get(user_name)}! Defaulting to rope net."
                        )
                        lists_of_after[user_name] = "rope net"

            success: list = []
            coins: int = 0

            odds = sg.fishing_odds_shark
            for user in caught_users:  # looks through all the keys
                num = random.randint(0, 100)
                net = lists_of_after[user] if lists_of_after[user] else "rope net"
                net_uses = 0
                if net != "rope net":
                    warning, net_uses = remove_net_use(net=net, user=user)
                    net_uses -= 1
                    if warning:
                        await channel.send(warning)

                if num <= odds(str(user), net):
                    current_time = dt.datetime.now()
                    time_caught: str = f"{current_time.date()} {current_time.hour}"
                    success.append(user)
                    sg.create_dex(
                        username=user,
                        shark_name=name_to_drop,
                        when_caught=time_caught,
                        net_used=net,
                        rarity=rarity,
                        net_uses=net_uses,
                    )
                    if fishing_config.boost is not None:
                        coins = sg.reward_coins(
                            username=user,
                            rare=rarity,
                            shark=True,
                            shark_name=name_to_drop,
                            boost=fishing_config.boost,
                            boost_amount=fishing_config.boost_amount,
                        )
                    else:
                        coins = sg.reward_coins(username=user, rare=rarity, shark=True, shark_name=name_to_drop)

                if net != "rope net" and net is not None:
                    sg.remove_net_use(user, net, net_uses)
                    if net_uses == 0:
                        sg.remove_net(user, net)
            if not success:
                await channel.send(f"A {rarity} {name_to_drop} has escaped, no one caught it. 😞")
            elif len(success) == 1:
                await channel.send(
                    f"Congratulations to {success[0]} who caught a {rarity} {name_to_drop} 👏. You have been granted {coins}"
                )
            else:
                people = ""
                i = 0
                for person in success:
                    if i < len(success):
                        people += f"{person}, "
                    elif i - 1 == len(success):
                        people += f"{person} and "
                    else:
                        people += f"{person}"
                await channel.send(
                    f"Congratulations to {people} for catching a {rarity} {name_to_drop} 👏. You have been granted {coins}"
                )

        loop = tasks.loop(seconds=self.check_interval, reconnect=True)(_tick)
        guild_name: str = self.config.guilds[guild_id]

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
        async def _error(self, error: BaseException):
            logging.exception("Shark game loop error %s", error)

        self._loops[guild_id] = loop
        loop.start()

    def stop_for(self, guild_id: int) -> bool:
        loop = self._loops[guild_id]
        if loop and loop.is_running():
            loop.stop()
            return True
        return False
