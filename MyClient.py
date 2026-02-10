import asyncio
import logging
import os
from enum import Enum
from pathlib import Path

import discord
from dotenv import load_dotenv
from pydantic import ValidationError

from data.gids import roles_per_gid
from fishing.fishing import Fishing
from handlers.reactions import reaction_handler
from loops.birthdayloop.birthdayLoop import BirthdayLoop
from loops.levellingloop.levellingLoop import levelingLoop
from loops.sharkGameLoop.sharkGameLoop import SharkLoops, sg
from ticketingSystem.Ticket_System import TicketSystem
from utils.core import AppConfig
from utils.ticketing import TicketingConfig

# ======= Logging/Env =======
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="a")
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)
load_dotenv()
token = os.getenv("token")
assert token, "No token found in envvars. Impossible to continue."
# ======= CONFIG =======
CONFIG_PATH = Path(r"config.YAML")
TICKET_CONFIG_PATH = Path(r"ticketingSystem\ticketing.yaml")

prefix: str = "?"

try:
    config = AppConfig(CONFIG_PATH)
    ticket_config = TicketingConfig(TICKET_CONFIG_PATH)
except ValidationError as e:
    logging.critical("Unable to load config. Inner Exception:\n{e}")
    raise e

GIDS: dict[str, int] = {k: v.id for k, v in config.guilds}
ROLES: dict = config.roles


# ======= ENUM CLASS =======
class sharks_index(Enum):
    SHARK_NAME = 0
    TIME_CAUGHT = 1
    SHARK_FACT = 2
    SHARK_WEIGHT = 3
    NET_TYPE = 4
    COINS = 5
    RARITY = 6


# ======= BOT =======
class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shark_loops = SharkLoops(self, config)
        self.birthday_loops = BirthdayLoop(self, config)
        self.leveling_loop = levelingLoop(self)
        self.ticket_system = TicketSystem(self)
        self._ticket_setup_done: dict = config.set_up_done
        self.reaction_handler = reaction_handler(config=config, roles_per_guild=roles_per_gid(GIDS, ROLES), bot=self)
        self.fishing = Fishing(self)

    # ======= ON RUN =======
    async def on_ready(self):
        assert self.user is not None
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("----------------------------------------------")
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")

        for guild in self.guilds:
            await self.reaction_handler.ensure_react_roles_message_internal(guild=guild)
            guild_name: str = config.guilds[guild.id]

            if guild_name == "shark squad":
                self.birthday_loops.start_for(guild.id)
                for member in guild.members:
                    try:
                        user_added = await self.leveling_loop.add_users(user=member)
                    except Exception as e:
                        raise e

                    if user_added:
                        try:
                            role_added = await self.leveling_loop.add_role(user=member)
                            if role_added is None:
                                logging.warning(f"Failed to add role to member {member}, returned None")
                        except Exception as e:
                            raise e
                    else:
                        logging.warning(f"Failed to add user with member {member}, returned None")

            for key, value in self._ticket_setup_done.items():
                if key == config.guilds.get(guild_name):
                    if not value:
                        print("set up not done")
                        await self.ticket_system.setup_hook()
                        logging.info("[TICKETING SYSTEM] Ticket system set up, checking for messages now")

                        embed_message_ids = ticket_config.embed_messages
                        if embed_message_ids and embed_message_ids[guild_name] == 0:
                            channel_id = ticket_config.ticket_channels[guild_name]
                            if channel_id is not None or channel_id != 0:
                                channel = guild.get_channel(channel_id)
                                if channel and isinstance(channel, discord.TextChannel):
                                    await self.ticket_system.send_ticket_panel(channel=channel)
                                else:
                                    logging.warning(
                                        f"[TICKET SYSTEM] Channel {channel_id} does not exist or is not a TextChannel"
                                    )
                                    return
                            else:
                                logging.warning(f"[TICKET SYSTEM] Channel ID for {guild_name} is either None or Zero!")
                                return

                            logging.info(f"[TICKETING SYSTEM] Ticket embed sent to {guild_name}")

                            self._ticket_setup_done[key] = True
                            print(config.set_up_done)
                            print(self._ticket_setup_done)
                            config.saveConfig()
                            print("After saving:")
                            print(config.set_up_done)

    # ======= ANNOUNCE ARRIVAL =======
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        welcome_channels = config.channels["welcome"]
        # The reverse seems illogical, but that is because server names on discord may not match the ones in the YAML file,
        # so for consistency we use the one on the YAML
        guild_name: str = config.guilds[guild.id]
        channel_id = welcome_channels[guild_name]
        if not channel_id:
            logging.warning(f"[WELCOME] No channel configured for {guild_name} ({guild.id})")
            return

        channel = guild.get_channel(channel_id)
        if channel and isinstance(channel, discord.TextChannel):
            to_send = f"Welcome {member.mention} to {guild_name}! Hope you enjoy your stay!"
            await channel.send(to_send)
        else:
            logging.warning(f"[WELCOME] Channel not found for {guild_name} ({guild.id})")

        if guild_name == "shark squad":
            chatting_channel = guild.get_channel(config.channels["chatting"][guild_name])

            message = f"""_Tiny fry drifting in sparkling nursery currents. The water shimmers around you, catching the first hints of ocean magic._
Chat, explore, and let your fins grow — your journey through the glittering ocean has just begun. You'll find more to explore at level 1. {member.mention} """  # noqa: E501
            if chatting_channel and isinstance(chatting_channel, discord.TextChannel):
                await chatting_channel.send(message)
            await self.leveling_loop.add_users(user=member)
            await self.leveling_loop.add_role(user=member)

    # ======= ANNOUNCE DEPARTURE =======
    async def on_member_remove(self, member):
        guild = member.guild
        welcome_channels = config.channels["welcome"]
        # The reverse seems illogical, but that is because server names on discord may not match the ones in the YAML file,
        # so for consistency we use the one on the YAML
        guild_name: str = config.guilds[guild.id]
        channel_id = welcome_channels.get(guild_name)
        if channel_id is None:
            logging.warning(f"[GOODBYE] No channel configured for {guild_name} ({guild.id})")
            return

        channel = guild.get_channel(channel_id)
        if channel is not None:
            if guild_name == "shark squad":
                to_send = f"{member} has left the Aquarium."
                await channel.send(to_send)
            else:
                to_send = f"{member} has left the server"
                await channel.send(to_send)

    async def ensure_react_roles_message(self, guild: discord.Guild):
        try:
            await self.reaction_handler.ensure_react_roles_message_internal(guild=guild)
        except (KeyError, ValueError, LookupError) as e:
            logging.error(f"Failed to ensure react roles message(s) exist. Inner error:\n{e}")
        except Exception as e:
            raise e

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.reaction_handler.on_raw_reaction_add_internal(payload=payload)

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.reaction_handler.on_raw_reaction_remove_internal(payload=payload)

    async def on_message(self, message: discord.Message):
        user = message.author

        # ignore if it's the bot's message
        if self.user and user.id == self.user.id:
            return

        if message.guild is None:
            await message.reply("I do not respond to dms, please message me in a server where my commands work. Thank you!")
            return
        elif message.content.startswith(prefix + "emoji"):
            await message.reply(":ZeroTwoBonkbyliliiet112:")
            return

        # leveling system messages
        if len(message.content) >= 10 and config.guilds[message.guild.id] == "shark squad":
            await self.leveling_loop.message_handle(message)

        if message.content.startswith(prefix + "check level") and config.guilds[message.guild.id] == "shark squad":
            await self.leveling_loop.check_level(message)

        if message.content.startswith(prefix + "hello"):
            await message.reply("Hello!")

        if message.content.startswith(prefix + "rules"):
            rules_part1 = """
            The golden rule: don't be a dick. You never know what someone else is going through — patience and empathy go a long way.
            General rules:
                1. Use the correct channels. Keep things organized; ask if you're unsure or if there is a want for additional channels.
2. Respect stream spaces. Streaming Voice Channels are for streaming — do not interrupt or demand to join. If you see others already in a space, do not come in and take it over. Do not talk over others or take up all the oxygen. The room is to be shared.
3. The rule above also applies to general Voice Channels, the public ones are free for anyone to use, just be respectful and ask, but do not demand.
4. Absolutely NO AI ART ~ AI is a wonderful tool for those who may have unexpected gaps as they are still learning or due to other issues, but that is never a justified reason to use someone else's art without permision. Any art posted needs to be your own. Theft of art is an instant ban from the both twitch and discord.
5. Protect your privacy. Do not share Personally Identifiable Information (i.e phone number, snapchat, etc.).
6. Outside issues stay outside. Shark & the mods cannot moderate what happens beyond the server — report or block as needed.
7. Be an adult (18+). Act with maturity and respect.
            """  # noqa: E501
            rules_part2 = """
                8. No racism, bigorty or "jokes" about them. Dark humor is fine but read the room - do not use dark humor to hide racism or hatefulness.
9. Respect others' space. You'll get the same in return.
10. No trauma Dumping. Venting is fine in the <#1313754697152073789> channel — let other chats stay light and welcoming.
11. No spam or unsolicited DMs. Always ask first.
12. No backseating or spoilers. Let others explore and play at their own pace unless help is requested.
13. Politics are allowed in tge server for a few reasons — the first being that many of our lives were made political without our consent. Creating a safe environment means that topics will occasionally come up that impact our every day lives, including politics. If you are not comfortable having a mature conversation where you can recognize when to walk away when it comes to politics, do not engage with these discussions. Politics that promote hate will not be tolerated. While shark is certainly one to point out hateful politics and correct the behavior, remember that your education is your responsibility. You are not required to all have the same political beliefs, but be open to growth and actually listen to those affected if you are going to be a part of these topics.
14. For any issues, questions, concerns, etc. you can reach out to any mod. Shark's DMs are also open. Shark has an open door policy - just know it may take me a bit to respond, but shark will for sure get back to you.
            ---------
A few notes:
    - Tag requests: If you want updates, select the Shark Update options <#1336429573608574986> — that's how I make sure no one's left out.
- If shark ever misremembers something about you, it is never intentional. She cares deeply about this community — thank you for your understanding as we keep improving it together.

            """  # noqa: E501

            await message.reply(rules_part1)
            await message.reply(rules_part2)

        if message.content.startswith(prefix + "describe game"):
            send = f"The shark catch game is a game where once every {config.time_per_loop / 60} minutes a shark will appear for two minutes and everyone will have the opportunity to try and catch it! Collect as many sharks as you can and gain coins that can be used to buy better nets! Good luck!"  # noqa: E501
            await message.reply(send)

        if message.content.startswith(prefix + "help"):
            send = """Thank you for asking for help! Here are my commands:
General:
1. `?help` - Shows all commands.
2. `?rules` - Show cases all the rules
3. `?hello` - The bot greets you :>
Shark Catch Game:
1. `?get dex` - Shows all the sharks you caught and how many you've caught.
2. `?detailed dex ` - Sends you your detailed dex into your DMs.
3. `?my nets` - Shows you all the nets you own.
4. `?catch` - Use this when trying to catch a shark! This will use the default net with a low chance of success
5. `?catch [net name]` - Use this when trying to use a specific net. If you enter a net you do not own it will ignore that net and use the basic one.
6. `?coins` - Tells you the amount of coins you currently have.
7. `?buy net` - Use this when trying to buy a new net!
8. `?describe game` - Gives a short description of the game.
9. `?fish` - Starts fishing and asks you for a net to use.
10. `?my baits` - Shows you all the baits you own.
11. `?[bait name]` - Starts fishing with the bait of your choice.
12. `?buy bait` - Use this when trying to buy bait!
            """  # noqa: E501
            await message.reply(send)

        if message.content.startswith(prefix + "game on"):
            active_guild_id = message.guild.id
            if self.shark_loops.is_running(active_guild_id):
                await message.reply("Game is already running")
                return

            self.shark_loops.start_for(active_guild_id)
            await message.reply("Started!")

        if message.content.startswith(prefix + "stop"):
            active_guild_id = message.guild.id
            if self.shark_loops.is_running(active_guild_id):
                self.shark_loops.stop_for(active_guild_id)
                await message.reply("Stopped.")
            else:
                await message.reply("Huh? I'm not running.")

        if message.content.startswith(prefix + "fish"):
            await self.fishing.fish(message=message, config=config)

        if message.content.startswith(prefix + "get dex"):
            basic_dex = sg.get_basic_dex(str(user.name))
            (dex, coins) = basic_dex if basic_dex else (None, None)

            if dex is None:
                await message.reply("You have not caught any sharks yet!")
            else:
                all_messages: list[str] = []
                messages = "You have caught these sharks: \n"

                i = 0
                amount_of_sharks = 0
                for shark in dex:
                    i += 1
                    s = "s" if dex[shark] > 1 else ""
                    amount_of_sharks += dex[shark]
                    string = f"{dex[shark]} {shark}{s} 🦈 \n"
                    if len(messages + string) < 2000:
                        messages += string
                    else:
                        all_messages.append(messages)
                        messages = ""
                last_message_to_append: str = (
                    f"That's a total of {amount_of_sharks} shark{'s' if i > 1 else ''}!\nYou also have {coins or 0} coins"  # noqa: E501
                )
                if len(messages + last_message_to_append) < 2000:
                    messages += last_message_to_append
                    all_messages.append(messages)
                else:
                    all_messages.append(messages)
                    all_messages.append(last_message_to_append)
                await message.reply(all_messages[0])
                channel = message.channel
                if len(all_messages) > 1:
                    for msg in all_messages:
                        channel.send(msg)

        if message.content.startswith(prefix + "detailed dex"):
            dex = sg.get_dex(str(user))

            if dex:
                all_messages: list[str] = []
                messages: str = "Here's your sharkdex: \n"

                index = 1

                for item in dex:
                    string = f"""shark {index}:
    name: {item[sharks_index.SHARK_NAME.value]} 🦈
    rarity: {item[sharks_index.RARITY.value]}
    time caught: {item[sharks_index.TIME_CAUGHT.value]} 🕰️
    facts: {item[sharks_index.SHARK_FACT.value]} 📰
    weight: {item[sharks_index.SHARK_WEIGHT.value]} ⚖️
    net used: {item[sharks_index.NET_TYPE.value]} 🎣
    coins balance: {item[sharks_index.COINS.value]} 🪙

    """
                    if len(messages + string) < 2000:
                        messages += string
                    else:
                        all_messages.append(messages)
                        messages = ""

                    index += 1
                if len(messages) != 0:
                    all_messages.append(messages)
                for msg in all_messages:
                    await user.send(msg)

            else:
                await user.send("You have not caught a shark so you have no dex, go catch sharks!")

        if message.content.startswith(prefix + "my nets"):
            nets, about_to_break, _, _ = sg.get_net_availability(str(user))
            send = "Here's your available nets: \n"
            i = 1
            for net in nets:
                send += f"{i}. {net} \n"
                i += 1
            i = 1
            if about_to_break:
                send += "Here are your nets that are about to break: \n"
                for atb in about_to_break:
                    send += f"{i}. {atb} \n"

            await message.reply(send)

        if message.content.startswith(prefix + "coins"):
            coins = 0 if sg.check_currency(str(user)) is None else sg.check_currency(str(user))

            await message.reply(f"You have {coins} coins!")

        if message.content.startswith(prefix + "add coins"):
            sg.add_coins(str(user), 500)

            await message.reply("done")

        if message.content.startswith(prefix + "buy net"):
            send = "Choose a net to buy: (choose within the next 30 seconds) \n To choose type the number of the net or type cancel to cancel \n"  # noqa: E501

            nets, prices = sg.get_nets()

            i = 1
            for net in nets:
                send += f"{i}. the {net} costs {prices[i - 1]} \n"
                i += 1

            await message.reply(send)
            channel = message.channel

            def check(m: discord.Message):
                isInt: bool = False

                try:
                    int(m.content.strip())
                    isInt = True
                except Exception:
                    isInt = False
                return (
                    m.author.id == user.id
                    and m.channel.id == message.channel.id
                    and (m.content.strip().lower() == "cancel" or isInt)
                )

            follow = None

            try:
                follow = await client.wait_for("message", check=check, timeout=30)
            except asyncio.TimeoutError:
                await message.reply("Timed out, try again with `?buy net`")

            if follow:
                logging.info(follow.content.strip().lower())

                if follow.content.strip().lower() == "cancel":
                    await follow.reply("Cancelled.")
                    return
                # print(nets)
                success, net_name, reason = sg.buy_net(str(user), int(follow.content.strip().lower())) or (None, None, None)
                if success:
                    logging.info(f"Found net: {net_name} for {user}")
                    await follow.reply(f"Successfully bought {net_name}")
                else:
                    logging.info(f"Could not buy {net_name} for {user}")
                    await follow.reply(f"Could not buy net because {reason}")

        if message.content.startswith(prefix + "shark facts"):
            await message.reply(
                r"To get facts about specific sharks send: ?{sharkname} or type cancel to abort. Example: Reef Shark"
            )

            def check(m: discord.Message):
                return (
                    m.author.id == user.id
                    and m.channel.id == message.channel.id
                    and (m.content.strip().lower() == "cancel" or m.content.strip().startswith(prefix))
                )

            follow = None

            try:
                follow = await client.wait_for("message", check=check, timeout=30)
            except asyncio.TimeoutError:
                await message.reply("Timed out, try again with `?shark facts`")
                return
            except Exception:
                await message.reply("Unexpected error. Try again or report this bug to the bot's author")
                return

            if follow and follow.content.strip().lower() == "cancel":
                await follow.reply("Cancelled.")
                return

            class fact_nums(Enum):
                NAME = 0
                FACT = 1
                EMOJI = 2
                WEIGHT = 3
                RARITY = 4

            # 3) Parse "?{shark}" by removing the prefix
            name = follow.content.strip()[len(prefix) :]

            facts = sg.get_all_facts(name)

            result = f"""Facts about the {facts[fact_nums.NAME.value]}:
Fact: {facts[fact_nums.FACT.value]}
Emoji: {facts[fact_nums.EMOJI.value]}
Weight: {facts[fact_nums.WEIGHT.value]}
Rarity: {facts[fact_nums.RARITY.value]}
            """
            await follow.reply(result)


# ===== RUN =====
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = MyClient(intents=intents, allowed_mentions=discord.AllowedMentions(everyone=True))
client.run(token=token, log_handler=handler)
