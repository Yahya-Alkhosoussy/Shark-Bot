import asyncio
import datetime as dt
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from sqlite3 import OperationalError

import discord
from discord.ext import commands
from dotenv import load_dotenv, set_key
from pydantic import ValidationError

from exceptions import exceptions as ex
from fishing.fishing import Fishing
from handlers.reactions import reaction_handler
from logModActions.modActions import ModLoop
from loops.birthdayloop.birthdayLoop import BirthdayLoop, add_birthday_to_sql, add_custom_gif_internal
from loops.clipping.clips import ClipLoop
from loops.levellingloop.levellingLoop import levelingLoop
from loops.sharkGameLoop.sharkGameLoop import SharkLoops, sg
from loops.twitchliveloop.TwitchLiveLoop import TwitchLiveLoop
from modApplication.ApplicationSystem import ApplicationSystem
from modApplication.ModQuestions import ModQuestions
from socialMedia.tiktok import TikTokLoop
from socialMedia.youtube import YoutubeLoop
from SQL.birthdaySQL.birthdays import add_birthday_message, add_gif_to_table
from SQL.clipManagement.clips import add_user, get_nick, get_username
from SQL.fishingSQL.baits import get_baits
from SQL.rolesSQL.roles import fill_emoji_map
from SQL.socialMedia.twitchLive import add_user as add_twitch_live_user
from ticketingSystem.Ticket_System import TicketSystem
from utils.core import AppConfig, get_full_path
from utils.pullingFromTwitch import get_clips, user_exists
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
    logging.critical(f"Unable to load config. Inner Exception:\n {str(e)}")
    raise e

GIDS: dict[str, int] = {k: v.id for k, v in config.guilds}


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
class MyBot(commands.Bot):
    def __init__(self, intents: discord.Intents, **kwargs):
        super().__init__(command_prefix=prefix, intents=intents, **kwargs)
        self.shark_loops = SharkLoops(self, config)
        self.birthday_loops = BirthdayLoop(self, config)
        self.leveling_loop = levelingLoop(self)
        self.ticket_system = TicketSystem(self)
        self._ticket_setup_done: dict = config.set_up_done
        self.reaction_handler = reaction_handler(config=config, roles_per_guild=fill_emoji_map(), bot=self)
        self.fishing = Fishing(self)
        self.mod_loop = ModLoop(self, config)
        self.tiktok_loop = TikTokLoop(self, config)
        self.clipping_loop = ClipLoop(self, config)
        self.twitch_loop = TwitchLiveLoop(self, config)
        self.mod_application = ApplicationSystem(bot=self)
        self.mod_questions = ModQuestions(bot=self, channel=None)
        self.youtube_loop = YoutubeLoop(bot=self, config=config)

    # ======= ON RUN =======
    async def on_ready(self):
        assert self.user is not None
        print("")
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("----------------------------------------------")
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")

        # Set up app commands
        async def setup_guild(guild):
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            await self.reaction_handler.ensure_react_roles_message_internal(guild=guild)
            print(f"Tree set up for {guild.name}")

        # runs parallel with the other loop
        await asyncio.gather(*[setup_guild(guild) for guild in self.guilds], self.tree.sync())

        for guild in self.guilds:
            guild_name: str = config.guilds[guild.id]
            if guild_name == "shark squad":
                for member in guild.members:
                    try:
                        await self.leveling_loop.check_role(user=member)
                        user_added = await self.leveling_loop.add_users(user=member)
                    except Exception as e:
                        logging.error(str(e))
                        user_added = False
                    if user_added:
                        try:
                            role_added = await self.leveling_loop.add_role(user=member)
                            if role_added is None:
                                logging.warning(f"Failed to add role to member {member}, returned None")
                        except Exception as e:
                            logging.error(str(e))
                self.birthday_loops.start_for(guild.id)
                self.mod_loop.start_for(guild.id)
                self.tiktok_loop.start_for(guild.id)
                self.clipping_loop.start_for(guild.id)
                self.twitch_loop.start_for(guild.id)
                self.youtube_loop.start_for(guild.id)

                shark_message_id = config.shark_message_id
                shark_channel_id = config.get_channel_id(guild_name, channel="game")
                shark_channel = self.get_channel(shark_channel_id)
                if not isinstance(shark_channel, discord.TextChannel):
                    print("channel is in an incorrect format")
                    return
                shark_message = await shark_channel.fetch_message(shark_message_id)
                if not isinstance(shark_message, discord.Message):
                    print("message is not the right type: ", type(shark_message))
                    return
                dt = timedelta(minutes=30)
                now = datetime.now(timezone.utc)
                delta = now - shark_message.created_at
                if delta >= dt:
                    self.shark_loops.start_for(guild.id)
                else:
                    remaining = dt - delta
                    asyncio.create_task(self.start_shark_game_after_delay(guild_id=guild.id, remaining=remaining))

            await self.ticket_system.setup_hook()
            channel_id = config.get_channel_id(guild_name=guild_name, channel="mod app")
            channel = self.get_channel(channel_id)
            if not isinstance(channel, discord.TextChannel):
                print("channel is in an incorrect format")
                return
            await self.mod_application.setup_hook(guild_name=guild_name, channel=channel)

            for key, value in self._ticket_setup_done.items():
                if key == config.guilds.get(guild_name):
                    if not value:
                        print("set up not done")

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
            logging.error(f"Failed to ensure react roles message(s) exist. Inner error:\n{str(e)}")
        except Exception as e:
            raise e

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.reaction_handler.on_raw_reaction_add_internal(payload=payload)

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.reaction_handler.on_raw_reaction_remove_internal(payload=payload)

    async def on_message(self, message: discord.Message) -> None:
        user = message.author
        handled = False

        # ignore if it's the bot's message
        if self.user and user.id == self.user.id:
            return

        if message.guild is None:
            await message.reply("I do not respond to dms, please message me in a server where my commands work. Thank you!")
            return

        # leveling system messages
        if len(message.content) >= 10 and config.guilds[message.guild.id] == "shark squad":
            await self.leveling_loop.message_handle(message)

        if message.content.startswith(prefix + "check level") and config.guilds[message.guild.id] == "shark squad":
            await self.leveling_loop.check_level(message)
            handled = True

        if message.content.startswith(prefix + "mod help"):
            if isinstance(message.author, discord.Member):
                is_mod: bool = config.check_for_mod_role(message.author.roles)

                if not is_mod:
                    await message.reply("You aren't a mod, go away")
                    return

                to_send = """Thank you for asking for help!
The following are mod exclusive actions:
1. `?timeout [@user] [duration in seconds]` - This command is to timeout any user for a set duration, if no duration is given it will default to a 10 minute timeout
2. `?kick [@user]` - This command is to kick any user from the server.
3. `?ban [@user]` - This command is to ban any user from the server.
4. `?add role` - This command prompts a series of requests that the bot will send for more information to add a role to react roles.
5. `?update shop items` - This command prompts a series of requests that the bot will send for more information to update shop items for the bait shop.
6. `?update shop prices` - same as above but for prices."""  # noqa: E501
                await message.reply(to_send)
                handled = True

        if message.content.startswith(prefix + "hello"):
            await message.reply("Hello!")
            handled = True

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
            handled = True

        if message.content.startswith(prefix + "describe game"):
            send = f"The shark catch game is a game where once every {config.time_per_loop / 60} minutes a shark will appear for two minutes and everyone will have the opportunity to try and catch it! Collect as many sharks as you can and gain coins that can be used to buy better nets! Good luck!"  # noqa: E501
            await message.reply(send)
            handled = True

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
11. `?fish [bait name]` - Starts fishing with the bait of your choice.
12. `?buy bait` - Use this when trying to buy bait!
            """  # noqa: E501
            await message.reply(send)
            handled = True

        if message.content.startswith(prefix + "stop"):
            active_guild_id = message.guild.id
            if self.shark_loops.is_running(active_guild_id):
                self.shark_loops.stop_for(active_guild_id)
                await message.reply("Stopped.")
            else:
                await message.reply("Huh? I'm not running.")
            handled = True

        if message.content.startswith(prefix + "fish"):
            after: str | None = None if len(message.content[6:]) == 0 else message.content[6:]
            if after is not None:
                baits, _ = get_baits(message.author.name)
                if after not in baits:
                    await message.reply(f"You do not own the bait ({after}) or it is an invalid bait, try the command again")
                    return
            try:
                await self.fishing.fish(message=message, bait=after)
            except ex.ItemNotFound as e:
                await message.channel.send(f"{message.author.mention} {str(e)}")
            handled = True

        if message.content.startswith(prefix + "buy bait"):
            try:
                await self.fishing.buy_bait(message)
            except ex.ItemNotFound as e:
                await message.reply(f"Had issues buying bait. Error: {str(e)}")
            handled = True

        if message.content.startswith(prefix + "my baits"):
            bait_names, uses = get_baits(username=message.author.name)
            if not bait_names:
                await message.reply("You do not own any baits")
                return
            send = "Here are the baits you own:\n"
            i = 0
            for bait in bait_names:
                i += 1
                send += f"{i}. {bait} - {uses[i - 1]} use{'s' if uses[i - 1] > 1 else ''} \n"
            await message.reply(send)
            handled = True

        if message.content.startswith(prefix + "my fish"):
            await self.fishing.get_fish(message=message)
            handled = True

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
                        await channel.send(msg)
            handled = True

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
            handled = True

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
            handled = True

        if message.content.startswith(prefix + "coins"):
            coins = 0 if sg.check_currency(str(user)) is None else sg.check_currency(str(user))

            await message.reply(f"You have {coins} coins!")
            handled = True

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
                follow = await self.wait_for("message", check=check, timeout=30)
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
            handled = True

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
                follow = await self.wait_for("message", check=check, timeout=30)
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
            handled = True

        if message.content.startswith(prefix + "Apply"):
            assert isinstance(message.channel, discord.TextChannel)
            assert isinstance(message.author, discord.Member)
            await self.mod_questions.send_questions(message.channel, author=message.author)
            handled = True

        if not handled:
            await self.process_commands(message)

    async def start_shark_game_after_delay(self, guild_id: int, remaining: timedelta):
        await asyncio.sleep(remaining.total_seconds())
        self.shark_loops.start_for(guild_id)


# ===== RUN =====
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.message_content = True
bot = MyBot(intents=intents, allowed_mentions=discord.AllowedMentions(everyone=True))
bot.owner_id = 604366329302220820  # replace with own ID if replicating


def is_mod():
    async def check(ctx: commands.Context):
        assert isinstance(ctx.author, discord.Member)
        if not config.check_for_mod_role(ctx.author.roles):
            raise ex.InvalidRole("Invalid role, this is only for mods")
        return True

    return commands.check(check)


@bot.tree.command(name="add-birthday", description="Adds your birthday to wish you a happy birthday on that day")
@discord.app_commands.describe(
    birth_month="This is your birth month (i.e 2 for february, 6 for june etc.)", birthday="Your birth day"
)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@discord.app_commands.allowed_installs(guilds=True, users=False)
async def add_birthday(interaction: discord.Interaction, birth_month: int, birthday: int):
    await interaction.response.send_message("Adding your birthday.")
    try:
        await add_birthday_to_sql(interaction=interaction, birthmonth=birth_month, birthday=birthday)
    except (OperationalError, ex.BirthdateFormatError) as e:
        if isinstance(interaction.channel, discord.TextChannel):
            await interaction.channel.send(str(e))
        else:
            logging.error(str(e))


@bot.tree.command(name="add-custom-birthday-gif", description="Add your own custom birthday gif!!")
@discord.app_commands.describe(
    index="This is your birthday and birthmonth in one number (i.e for february 19th it's 1902, for 6th of June it's 0606)",
    gif_link="This is the link to the gif you want to add",
)
@discord.app_commands.allowed_contexts(guilds=True, dms=False, private_channels=True)
@discord.app_commands.allowed_installs(guilds=True, users=False)
async def add_custom_gif(interaction: discord.Interaction, index: int, gif_link: str):
    await interaction.response.send_message("Adding your custom gif...")
    try:
        await add_custom_gif_internal(interaction, gif_link=gif_link, gif_index=index)
    except ex.FormatError as e:
        channel = interaction.channel
        if isinstance(channel, discord.TextChannel):
            await channel.send(f"Encountered an error, {str(e)}")
        else:
            logging.error(str(e))


@bot.tree.command(name="add_channel_for_clips", description="Add your channel to get ur clips sent somewhere after ur stream")
@discord.app_commands.describe(
    twitch_username="This is your twitch username.",
    to_dms="This should be a Yes or a No, whether you want the clips to be sent to your dms or not.",
    channel_id="If you don't want it to be DMed to you, choose a channel. If you do want it to be sent to your dms just put a 0",
)
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@discord.app_commands.allowed_installs(guilds=True, users=True)
async def add_channel_to_clips(interaction: discord.Interaction, twitch_username: str, to_dms: str, channel_id: int):
    await interaction.response.send_message("Adding your twitch username to our database...")
    username = twitch_username
    user = interaction.user
    if to_dms.lower() == "yes":
        add_user(discord_id=user.id, user=user.name, username=username, dms=True)
    else:
        add_user(discord_id=user.id, user=user.name, username=username, dms=False, channel_id=channel_id)


@bot.tree.command(name="clips", description="Get twitch clips manually")
@discord.app_commands.describe()
@discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
@discord.app_commands.allowed_installs(guilds=True, users=True)
async def clips(interaction: discord.Interaction, days_ago: int, hours_ago: int, minutes_ago: int):
    await interaction.response.send_message("Getting your clips")
    username = get_username(interaction.user.id)
    nick = get_nick(interaction.user.id)

    clips = get_clips(username, days_ago, hours_ago, minutes_ago, user=nick)

    print("Clips gotten")

    channel = interaction.channel

    messages = []
    to_send = "Here are the clips you requested: \n"

    for clip in clips:
        if len(to_send) + len(clip) + 1 > 2000:
            messages.append(to_send)
            to_send = clip + "\n"
        else:
            to_send += clip + "\n"
    if len(messages) == 0:
        messages.append(to_send)
    for message in messages:
        if isinstance(channel, discord.TextChannel):
            await channel.send(message)


@bot.tree.command(name="shark-frenzy-live", description="Sign up to automatically tell others you're live in #shark-frenzy")
@discord.app_commands.describe()
async def live_setup(interaction: discord.Interaction, twitch_username: str, custom_message: str):
    await interaction.response.send_message("Validating your information")
    user = interaction.user
    channel = interaction.channel
    assert isinstance(user, discord.Member)

    roles = user.roles
    role_found = False
    for role in roles:
        if role.name == "Shark's VIPs":
            role_found = True
            break

    if not role_found:
        if isinstance(channel, discord.TextChannel):
            await channel.send(f"{user.mention}, I was unable to verify your information. You do not have the necessary role.")
            return
    if not user_exists(username=twitch_username):
        if isinstance(channel, discord.TextChannel):
            await channel.send(
                f"{user.mention}, I was unable to find your twitch, are you sure your username ({twitch_username}) is correct?"
            )
            return

    discord_id = interaction.user.id
    add_twitch_live_user(twitch_username, discord_id, custom_message)

    if isinstance(channel, discord.TextChannel):
        await channel.send(f"{user.mention}, data validated. Thank you!")
        return


@bot.tree.command(name="only-for-spider")
@commands.is_owner()
async def live_setup_2(interaction: discord.Interaction, twitch_username: str, custom_message: str, discord_id: str):
    await interaction.response.send_message("Validating the information")
    channel = interaction.channel
    guild = interaction.guild
    assert isinstance(channel, discord.TextChannel)
    try:
        discord_id_int = int(discord_id)
    except BaseException as e:
        await channel.send(f"invalid user ID, error {e}")
        return

    if guild is None:
        await channel.send("Error, guild not found")
        return
    user = guild.get_member(discord_id_int)
    if user is None:
        await channel.send("Error, member not found")
        return
    roles = user.roles
    role_found = False
    for role in roles:
        if role.name == "Shark's VIPs" or "Admin":
            role_found = True
            break

    if not role_found:
        await channel.send(f"{user.name} does not have the necessary role.")
        return
    if not user_exists(username=twitch_username):
        await channel.send(
            f"{user.mention}, I was unable to find your twitch, are you sure your username ({twitch_username}) is correct?"
        )
        return

    add_twitch_live_user(twitch_username, discord_id_int, custom_message)

    await channel.send(f"{user} data validated. Thank you!")
    return


@bot.command(name="restart", hidden=True)
@commands.is_owner()
async def restart_bot(ctx: commands.Context):

    while True:
        if not bot.shark_loops.is_idle:
            await ctx.send("Waiting for shark loop to finish iterating...")
            await asyncio.sleep(10)
        else:
            break

    await ctx.send("Checking for updates...")

    # sync up python's PATH with window's PATH
    os.environ["PATH"] = get_full_path()

    git_path = shutil.which("git")

    try:
        assert git_path
        res = subprocess.run([git_path, "pull"], capture_output=True, check=True, text=True, shell=True)
        await ctx.send("Pulled successfully")
        await ctx.send(res.stdout)
        res_2 = subprocess.run([sys.executable, "setup.py"], check=True, capture_output=True, text=True)
        await ctx.send("Successfully installed all pip installs")
        await ctx.send(res_2.stdout[-len(" Setup complete!") :])
    except subprocess.CalledProcessError as e:
        await ctx.send(f"failed: error {e.stderr}")
    except Exception as e:
        await ctx.send(f"Failed: Error {str(e)}")

    await ctx.send("Restarting now...")

    subprocess.Popen([sys.executable] + sys.argv)

    await bot.close()  # closes the bot normally


@bot.command(name="timeout")
@is_mod()
async def timeout(ctx: commands.Context, member: discord.Member, duration: int):
    assert ctx.guild
    until = dt.timedelta(seconds=duration)
    await member.timeout(until)
    await config.send_discord_mod_log(
        log_message=f"{ctx.author.name} has timed out user ({member.name} {f'(nicknamed: {member.nick})) ' if member.nick else ''}for {duration} seconds",  # noqa: E501
        bot=bot,
        guild_id=ctx.guild.id,
    )


@bot.command(name="kick")
@is_mod()
async def kick(ctx: commands.Context, member: discord.Member):
    assert ctx.guild
    await member.kick()
    await config.send_discord_mod_log(
        log_message=f"{ctx.author.name} has kicked user {member.name} {f'(nicknamed: {member.nick})) ' if member.nick else ''}from the server.",  # noqa: E501
        bot=bot,
        guild_id=ctx.guild.id,
    )


@bot.command(name="ban")
@is_mod()
async def ban(ctx: commands.Context, member: discord.Member):
    assert ctx.guild
    await member.ban()
    await config.send_discord_mod_log(
        log_message=f"{ctx.author.name} has banned user {member.name} {f'(nicknamed: {member.nick})) ' if member.nick else ''}from the server.",  # noqa: E501
        bot=bot,
        guild_id=ctx.guild.id,
    )


@bot.group()
async def add(ctx: commands.Context):
    pass


@add.command(name="role")
@is_mod()
async def add_role(ctx: commands.Context):
    assert ctx.guild
    role_id = await bot.reaction_handler.add_to_react_roles(ctx.message)
    if role_id is not None:
        await config.send_discord_mod_log(
            log_message=f"{ctx.author.name} has added a role (<@&{role_id}>) to react roles.",
            bot=bot,
            guild_id=ctx.guild.id,
        )


@add.command(name="coins")
@commands.is_owner()
async def add_coins(ctx: commands.Context, member: discord.Member, coins: int):
    sg.add_coins(member.name, coins)
    await ctx.reply(f"{coins} added to {member.name}'s account")


@add.command(name="gif")
@is_mod()
async def add_gif(ctx: commands.Context, link: str):
    await ctx.reply("Attempting to add gif...")
    if link[:6] != "https://":
        raise ex.FormatError("Gif is not a link", 1006)
    add_gif_to_table(link)
    await ctx.reply("Gif added")


@add.command(name="message")
@is_mod()
async def add_message(ctx: commands.Context, message: str):
    await ctx.reply("Attempting to add message")
    add_birthday_message(message)
    await ctx.reply("Message added!")


@bot.group()
async def update(ctx: commands.Context):
    pass


@update.command(name="env")
@commands.is_owner()
async def env(ctx: commands.Context, var_name: str, var_value: str):
    # update in memory
    os.environ[var_name] = var_value

    # update .env file
    set_key(".env", var_name, var_value)

    await ctx.send("Updated environmental variable!")


@update.group()
async def shop(ctx: commands.Context):
    pass


@shop.command(name="items")
@is_mod()
async def update_shop_items(ctx: commands.Context):
    assert ctx.guild
    await bot.fishing.add_into_shop_internal(message=ctx.message)
    await config.send_discord_mod_log(
        log_message=f"{ctx.author.name} has added an item to the shop.",
        bot=bot,
        guild_id=ctx.guild.id,
    )


@shop.command(name="prices")
@is_mod()
async def update_shop_prices(ctx: commands.Context):
    assert ctx.guild
    await bot.fishing.update_shop_prices_internal(message=ctx.message)
    await config.send_discord_mod_log(
        log_message=f"{ctx.author.name} has updated prices in the shop.",
        bot=bot,
        guild_id=ctx.guild.id,
    )


# check for errors
@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.reply("I don't know that command")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.reply("You do not have permissions to use that command. Go away")
    elif isinstance(error, commands.CheckFailure):
        await ctx.reply("You cannot use this command. Go away")
    elif isinstance(error, ex.InvalidRole):
        await ctx.reply(f"You cannot use this role. Error message {error.message}")
    elif isinstance(error, commands.CommandInvokeError):
        origin = error.original
        if isinstance(origin, ValueError):
            await ctx.reply("I cannot fulfil your request. One of your values isn't in the correct format")
    elif isinstance(error, commands.MissingRequiredArgument):
        missing = error.param.name
        await ctx.reply(f"I cannot fulfil your request, I am missing a component: {missing}")
    elif isinstance(error, commands.TooManyArguments):
        await ctx.reply("I cannot fulfil your request, you have given me too much information to work with.")
    elif isinstance(error, ex.RoleNotAdded):
        await ctx.reply(f"I could not add the role. Error: {str(error)}")
    elif isinstance(error, ex.FormatError):
        await ctx.reply(f"The format is incorrect, format error: {error.message}")

    bot_channel = bot.get_channel(1430445244733722694)
    if isinstance(bot_channel, discord.TextChannel):
        author = ctx.author
        if not author or isinstance(author, discord.User):
            return
        user = author.nick if author.nick else author.name
        if isinstance(error, commands.CommandNotFound):
            await ctx.reply(f"{user} tried using command {ctx.message.content} and I do not recognize that")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.reply(f"{user} tried using command {ctx.command} but does not have the permissions needed")
        else:
            await ctx.reply(f"{user} tried using command {ctx.command} but is missing something")
        return


bot.run(token=token, log_handler=handler)
