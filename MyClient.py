import discord, os, logging, asyncio, random, time
from dotenv import load_dotenv
from pathlib import Path
import utils.read_Yaml as RY
from discord.ext import tasks
import datetime as dt
from SQL.levellingSQL import levellingSQL as level
from enum import Enum
from loops.birthdayloop.birthdayLoop import BirthdayLoop, SharkLoops, TIME_PER_LOOP, sg

# ======= Logging/Env =======
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="a")
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)
load_dotenv()
token = os.getenv("token")

# ======= CONFIG =======
CONFIG_PATH = Path(r"config.YAML")

config = RY.read_config(CONFIG=CONFIG_PATH)
prefix: str = "?"

# This is to check if the guild ID is in the config
def is_guild_in_config(guild_id: int):

    guild_ids: dict = config.get("guilds")

    if guild_id in guild_ids.values():
        return True
    else:
        return False
    
def is_rr_message_id_in_config(guild_name: str):

    guild_role_message_ids: dict = config.get("guild role messages")

    if guild_name in guild_role_message_ids.keys():
        return True
    else:
        return False

def get_channel_id(guild_name: str, channel: str):

    channels = config.get("channels").get(channel)

    if channels is None:
        return "Channel not in config"
    
    channels = channels.get(guild_name)

    if channels is None:
        return "Channel does not exist in the server"
    else:
        return int(channels)

GIDS: dict = config["guilds"]
ROLES: dict = config["roles"]
ROLES_PER_GUILD: dict[int, dict[str, dict[discord.PartialEmoji, int]]] = {
    GIDS["test server"]: {
        "colour": {
            discord.PartialEmoji(name='🩵'): ROLES["colour"]["cyan"]
        },
        "general": {
            discord.PartialEmoji(name='❤️'): ROLES["general"]["red"]
        },
        "test": {
            discord.PartialEmoji(name='💚'): ROLES["test"]["green"]
        },
    },
    GIDS["shark squad"]: {
        "birthdays": {
            discord.PartialEmoji(name='🎆'): ROLES["birthdays"]["January babies"],
            discord.PartialEmoji(name='💌'): ROLES["birthdays"]["February babies"],
            discord.PartialEmoji(name='🍀'): ROLES["birthdays"]["March babies"],
            discord.PartialEmoji(name='🪺'): ROLES["birthdays"]["April babies"],
            discord.PartialEmoji(name='🌥️'): ROLES["birthdays"]["May babies"],
            discord.PartialEmoji(name='🌞'): ROLES["birthdays"]["June babies"],
            discord.PartialEmoji(name='🗽'): ROLES["birthdays"]["July babies"],
            discord.PartialEmoji(name='🌤️'): ROLES["birthdays"]["August babies"],
            discord.PartialEmoji(name='🍂'): ROLES["birthdays"]["September babies"],
            discord.PartialEmoji(name='👻'): ROLES["birthdays"]["October babies"],
            discord.PartialEmoji(name='🦃'): ROLES["birthdays"]["November babies"],
            discord.PartialEmoji(name='🎅'): ROLES["birthdays"]["December babies"],
        },
        "general": {
            discord.PartialEmoji(name='🎮'): ROLES["general"]["shark games"],
            discord.PartialEmoji(name='❗'): ROLES["general"]["shark update"],
            discord.PartialEmoji(name='💻'): ROLES["general"]["discord bot update"]
        },
        "backpack": {
            discord.PartialEmoji(name='🦸'): ROLES["backpacks and sherpas"]["marvel rivals backpack"],
            discord.PartialEmoji(name='🧙‍♀️'): ROLES["backpacks and sherpas"]["TFD backpack"],
            discord.PartialEmoji(name='🧟'): ROLES["backpacks and sherpas"]["monster hunter backpack"],
            discord.PartialEmoji(name='🥷'): ROLES["backpacks and sherpas"]["warframe backpack"],
            discord.PartialEmoji(name='🏰'): ROLES["backpacks and sherpas"]["elden ring backpack"],
            discord.PartialEmoji(name='🤺'): ROLES["backpacks and sherpas"]["nightreign backpack"],
        },
        "sherpa": {
            discord.PartialEmoji(name='🦸'): ROLES["backpacks and sherpas"]["marvel rivals sherpa"],
            discord.PartialEmoji(name='🧙‍♀️'): ROLES["backpacks and sherpas"]["TFD sherpa"],
            discord.PartialEmoji(name='🧟'): ROLES["backpacks and sherpas"]["monster hunter sherpa"],
            discord.PartialEmoji(name='🥷'): ROLES["backpacks and sherpas"]["warframe sherpa"],
            discord.PartialEmoji(name='🏰'): ROLES["backpacks and sherpas"]["elden ring sherpa"],
            discord.PartialEmoji(name='🤺'): ROLES["backpacks and sherpas"]["nightreign sherpa"],
        }
    }    
}

# ======= ENUM CLASS =======
class sharks_index(Enum):
    SHARK_NAME   = 0
    TIME_CAUGHT  = 1
    SHARK_FACT   = 2
    SHARK_WEIGHT = 3
    NET_TYPE     = 4
    COINS        = 5
    RARITY       = 6

# ======= BOT =======
class MyClient(discord.Client):
    # Suppress error on the User attribute being None since it fills up later
    user: discord.ClientUser

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shark_loops = SharkLoops(self)
        self.birthday_loops = BirthdayLoop(self)

    # levelling system
    @tasks.loop(seconds=5, reconnect=True)
    async def levels_loop(self, guild_id: int):
        # loop logic
        ""
        
    @levels_loop.before_loop
    async def before_levels_loop(self):
        # ensures cache/guilds/channels are ready before first run
        await self.wait_until_ready()
        logging.info("Levelling loop is about to start.")
    
    @levels_loop.after_loop
    async def after_levels_loop(self):
        if self.levels_loop.is_being_cancelled():
            logging.info("Levels loop is being cancelled (shutdown).")
        else:
            logging.info("levels loop ended normally.")

    @levels_loop.error
    async def levels_loop_error(self, error):
        # catch unhandelled exceptions inside the Loop
        logging.exception("levels loop error: %s", error)
    # ======= ON RUN =======
    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("----------------------------------------------")
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")
        
        id_to_name: dict = {int(v): k for k, v in config["guilds"].items()}

        for guild in self.guilds:
            await self.ensure_react_roles_message(guild)
            guild_name: str = id_to_name.get(guild.id)
            if guild_name == "shark squad":
                self.birthday_loops.start_for(guild.id)
        

    # ======= ANNOUNCE ARRIVAL =======
    async def on_member_join(self, member):
        guild = member.guild
        welcome_channels = config["channels"]["welcome"]
        # The reverse seems illogical, but that is because server names on discord may not match the ones in the YAML file, so for consistency we use the one on the YAML
        id_to_name: dict = {int(v): k for k, v in config["guilds"].items()}
        guild_name: str = id_to_name.get(guild.id) 
        channel_id = welcome_channels.get(guild_name)
        if not channel_id:
            logging.warning(f"[WELCOME] No channel configured for {guild_name} ({guild.id})")
            return
        
        channel = guild.get_channel(channel_id)
        if channel is not None:
            to_send = f'Welcome {member.mention} to {guild_name}! Hope you enjoy your stay!'
            await channel.send(to_send)
        else:
            logging.warning(f"[WELCOME] Channel not found for {guild_name} ({guild.id})")

    # ======= ANNOUNCE DEPARTURE =======
    async def on_member_remove(self, member):
        guild = member.guild
        welcome_channels = config["channels"]["welcome"]
        # The reverse seems illogical, but that is because server names on discord may not match the ones in the YAML file, so for consistency we use the one on the YAML
        id_to_name: dict = {int(v): k for k, v in config["guilds"].items()}
        guild_name: str = id_to_name.get(guild.id) 
        channel_id = welcome_channels.get(guild_name)
        if not channel_id:
            logging.warning(f"[GOODBYE] No channel configured for {guild_name} ({guild.id})")
            return
        
        channel = guild.get_channel(channel_id)
        if channel is not None:
            if guild_name == "shark squad":
                to_send = f'{member} has left the Aquarium.'
                await channel.send(to_send)
            else:
                to_send = f'{member} has left the server'
                await channel.send(to_send)

    # ======= Ensures React Roles message exists =======
    async def ensure_react_roles_message(self, guild: discord.Guild):
        # check for guild config, if none found then skip
        if not is_guild_in_config(guild.id):
            logging.error(f"Guild {guild.name} is not in the config. Skipping")
            return

        id_to_name: dict = {int(v): k for k, v in config["guilds"].items()}
        guild_name: str = id_to_name.get(guild.id)
        # print(guild_name)
        
        react_role_messages: dict = config.get("guild role messages").setdefault(guild_name, {})
        # print(react_role_messages)

        if not is_rr_message_id_in_config(guild_name=guild_name):
            logging.error(f"Guild {guild.name} is does not have a react roles message ID Key")
            return        

        for rr_message in react_role_messages:
            # print(react_role_messages[rr_message])

            channel_id = int(get_channel_id(guild_name, "roles"))
            channel = guild.get_channel(channel_id) if channel_id else None

            if react_role_messages[rr_message] != 0:
                logging.info(f"There is already a react roles message of {rr_message} for {guild_name}")
                if channel is None:
                    logging.error(f"[RR] No valid channel configured for {guild_name}")
                    continue # Keep original flow
                    
                try:
                    message_id = int(react_role_messages[rr_message])
                    message = await channel.fetch_message(message_id)
                except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
                    logging.error(f"[RR] could not fetch existing react-roles message {rr_message} in {guild_name}")
                    continue

                mapping = ROLES_PER_GUILD.get(guild.id).get(rr_message)
                if not mapping:
                    continue # nothing to add
                
                existing = {str(r.emoji) for r in message.reactions}
                for emoji in mapping.keys():
                    if str(emoji) not in existing:
                        try:
                            await message.add_reaction(emoji)
                        except discord.HTTPException:
                            logging.error(f"[RR] could not add reaction {emoji} in {guild_name}")

                current_content = message.content or ""
                current_lines = current_content.splitlines()
                header = current_lines[0] if current_lines else "React to get your roles: "
                existing_entries = set(current_lines[1 :]) if len(current_lines) > 1 else set()

                desired_entries = [f"{emoji} -> <@&{role_id}>" for emoji, role_id in mapping.items()]
                to_append = [line for line in desired_entries if line not in existing_entries]

                if to_append: #make sure it isn't empty
                    new_content = (header + "\n" + "\n".join(sorted(existing_entries)) + ("\n" if existing_entries else "") + "\n".join(to_append)).strip()
                    try:
                        await message.edit(content=new_content)
                    except discord.HTTPException:
                        logging.error(f"[RR could not edit react-roles message {rr_message} in {guild_name}]")
                # ---------------------------------------------------------------------------------------------
                continue
            

            if channel is None:
                logging.error(f"[RR] No valid channel configured for {guild_name}")
                return

            mapping = ROLES_PER_GUILD.get(guild.id).get(rr_message)
            # print("current mapping: ",mapping)
            # print(f"emoji: ",mapping)
            message = await channel.send(
                "React to get your roles: \n" +
                "\n".join(f"{emoji} -> <@&{role_id}>" for emoji, role_id in mapping.items())
            )

            # Add the reactions we'll listen for
            for emoji in mapping.keys():
                try:
                    await message.add_reaction(emoji)
                except discord.HTTPException:
                    logging.error(f"[RR] could not add reaction {emoji} in {guild_name}")
            
            config["guild role messages"][guild_name][rr_message] = message.id
            RY.save_config(CONFIG=CONFIG_PATH, cfg=config)
        
    # ======= REACTION ROLES ADD ROLE =======
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):

        guilds = config["guilds"]
        gid = payload.guild_id

        if gid is None: 
            logging.info("[RR] Reaction was not from a guild")
            return
        
        id_to_name = {int(v): k for k, v in guilds.items()}
        if gid is None:
            logging.error(f"Guild ID could not be found")
            return
        
        guild_name = id_to_name.get(int(gid))

        rr_message_ids: dict = config.get("guild role messages").get(guild_name)
        found = False
        message_id: int
        for id in rr_message_ids.values():
            if payload.message_id == id:
                found = True
                message_id = id
                logging.info(f"found message! Reaction to message id: {id}")
        if not found:
            logging.info("Message isn't in my list")
            return
        
        react_role_messages: dict = config.get("guild role messages").setdefault(guild_name, {})
        id_to_name_rr = {int(v): k for k, v in react_role_messages.items()}
        rr_message = id_to_name_rr.get(message_id)
        mapping = ROLES_PER_GUILD.get(gid).get(rr_message)
        key = payload.emoji
        try: 
            role_id = mapping.get(key)
            print(f"found role ID: {role_id}")
        except KeyError:
            logging.info("not the emoji i care about")
            return
        
        guild = self.get_guild(gid)
        role = guild.get_role(role_id)
        if role is None:
            logging.warning(f"Couldn't find role with ID of {role_id} and emoji of {key}")
            return
        
        try:
            await payload.member.add_roles(role)
            logging.info(f"Added role {role} to {payload.member.name}")
        except discord.HTTPException:
            logging.error("HTTPException, I couldn't do it")
            return
        
    # ======= REACTION ROLES ADD ROLE =======
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):

        guilds = config["guilds"]
        gid = payload.guild_id

        if gid is None: 
            logging.info("[RR] Reaction was not from a guild")
            return
        
        id_to_name = {int(v): k for k, v in guilds.items()}
        if gid is None:
            logging.error(f"Guild ID could not be found")
            return
        
        guild_name = id_to_name.get(int(gid))

        rr_message_ids: dict = config.get("guild role messages").get(guild_name)
        found = False
        message_id: int
        for id in rr_message_ids.values():
            if payload.message_id == id:
                found = True
                message_id = id
                logging.info(f"found message! Reaction to message id: {id}")
        if not found:
            logging.info("Message isn't in my list")
            return
        
        react_role_messages: dict = config.get("guild role messages").setdefault(guild_name, {})
        id_to_name_rr = {int(v): k for k, v in react_role_messages.items()}
        rr_message = id_to_name_rr.get(message_id)
        mapping = ROLES_PER_GUILD.get(gid).get(rr_message)
        key = payload.emoji
        try: 
            role_id = mapping.get(key)
            print(f"found role ID: {role_id}")
        except KeyError:
            logging.info("not the emoji i care about")
            return
        
        guild = self.get_guild(gid)
        role = guild.get_role(role_id)
        if role is None:
            logging.warning(f"Couldn't find role with ID of {role_id} and emoji of {key}")
            return
        
        member = guild.get_member(payload.user_id)

        try:
            await member.remove_roles(role)
            logging.info(f"removed role {role} from {member.name}")
        except discord.HTTPException:
            logging.error("HTTPException, I couldn't do it")
            return

    async def on_message(self, message):
        # ignore if it's the bot's message
        if message.author.id == self.user.id:
            return
        
        if message.guild == None:
            await message.reply("I do not respond to dms, please message me in a server where my commands work. Thank you!")

        if message.content.startswith(prefix + "hello"):
            await message.reply("Hello!")
        
        if message.content.startswith(prefix + "describe game"):
            send = f"The shark catch game is a game where once every {TIME_PER_LOOP / 60} minutes a shark will appear for two minutes and everyone will have the opportunity to try and catch it! Collect as many sharks as you can and gain coins that can be used to buy better nets! Good luck!"
            await message.reply(send)
        if message.content.startswith(prefix + "help"):
            send = """Thank you for asking for help! Here are my commands:
General:
1. `?help` - Shows all commands.
Shark Catch Game:
1. `?game on` - Start's shark catch game.
2. `?get dex` - Shows all the sharks you caught and how many you've caught.
3. `?get dex detailed` - Sends you your detailed dex into your DMs.
4. `?my nets` - Shows you all the nets you own.
5. `?catch` - Use this when trying to catch a shark! This will use the default net with a low chance of success
6. `?catch [net name]` - Use this when trying to use a specific net. If you enter a net you do not own it will ignore that net and use the basic one.
7. `?coins` - Tells you the amount of coins you currently have.
8. `?buy net` - Use this when trying to buy a new net!
9. `?describe game` - Gives a short description of the game.
            """
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
            user = message.author

            owned_nets, about_to_break, broken, net_uses = sg.get_net_availability(message.author)

            await message.reply("Which net do you want to use?🎣 Type `?net name` to use it or send `cancel` to cancel! If you do not own any nets send `?none` to use a basic net. (You have 30 seconds to send one of the two)")

            def check(m: discord.Message):
                return (
                    m.author.id == message.author.id and
                    m.channel.id == message.channel.id and
                    (m.content.strip().lower() == "cancel" or m.content.strip().startswith(prefix))
                )
            
            try:
                follow = await client.wait_for("message", check=check, timeout=30)
            except asyncio.TimeoutError:
                await message.reply("Timed out, try again with `?fish`")

            logging.info(follow.content.strip().lower()[1:])

            if follow.content.strip().lower() == "cancel":
                await follow.reply("Cancelled.")
                return
            # print(nets)
            if follow.content.strip().lower()[1:] in owned_nets:
                # print("found it")
                if follow.content.strip().lower()[1:] in about_to_break and net_uses == 21:
                    await message.reply("WARNING: Net is about to break, 1 more use left. Do not worry through because you have 4 more of the same net left")
                elif follow.content.strip().lower()[1:] in about_to_break and net_uses == 16:
                    await message.reply("WARNING: Net is about to break, 1 more use left. Do not worry through because you have 3 more of the same net left")
                elif follow.content.strip().lower()[1:] in about_to_break and net_uses == 11:
                    await message.reply("WARNING: Net is about to break, 1 more use left. Do not worry through because you have 2 more of the same net left")
                elif follow.content.strip().lower()[1:] in about_to_break and net_uses == 6:
                    await message.reply("WARNING: Net is about to break, 1 more use left. Do not worry through because you have 1 more of the same net left")
                elif follow.content.strip().lower()[1:] in about_to_break and net_uses == 1:
                    await message.reply("WARNING: Net is about to break, 1 more use left. This is your last net")
                
                
                if follow.content.strip().lower()[1:] in broken and net_uses == 20:
                    await message.reply("WARNING: Net broken, don't worry through because you have 4 more of the same net left")
                elif follow.content.strip().lower()[1:] in broken and net_uses == 15:
                    await message.reply("WARNING: Net broken, don't worry through because you have 3 more of the same net left")
                elif follow.content.strip().lower()[1:] in broken and net_uses == 10:
                    await message.reply("WARNING: Net broken, don't worry through because you have 2 more of the same net left")
                elif follow.content.strip().lower()[1:] in broken and net_uses == 5:
                    await message.reply("WARNING: Net broken, don't worry through because you have 1 more of the same net left")
                elif follow.content.strip().lower()[1:] in broken and net_uses == 0:
                    await message.reply("WARNING: Net broken. You have no more uses of the same net left")
                
                await message.reply("Net found, fishing now! 🎣")
                net = follow.content.strip().lower()[1:]
            elif follow.content.strip().lower()[1:] == "none":
                await message.reply("Using basic net. Fishing now! 🎣")
                net = "rope net"
            else:
                await message.reply("Net not found, defaulting to basic net. Fishing now!🎣")
                net = "rope net"
            
            fish_odds = sg.fishing_odds_fish(username=user, net_used=net)

            rand_int = random.randint(1, 100)
            if rand_int <= fish_odds: #did it catch anything
                catch_type = random.randint(1, 100)
                if catch_type <= 5:
                    names = sg.get_shark_names("very common") 
                    rand_idx = random.randint(0, len(names) - 1) 
                    current_time = dt.datetime.now()
                    time_caught: str = f"{current_time.date()} {current_time.hour}"
                    sg.create_dex(user, names[rand_idx], time_caught, net, "normal")
                    coin = sg.reward_coins(user, shark=True, rare="normal", shark_name=names[rand_idx])
                    await message.reply(f"Oh lord, you have caught a shark that has randomly stumbled it's way here! 🦈 Congratulations on the {names[rand_idx]}. You have been given {coin} coins.")
                elif catch_type <= 25: # large fish 20% chance
                    rarity = random.randint(1, 100)
                    if rarity <= 10:
                        coin = sg.reward_coins(user, False, "legendary", size="large")
                        sg.fish_caught(user, "legendary")
                        await message.reply(f"Congratulations! You have caught a large legendary fish! 🐟 You have been rewarded {coin} coins.")
                    elif rarity <= 40:
                        coin = sg.reward_coins(user, False, "shiny", size="large")
                        sg.fish_caught(user, "shiny")
                        await message.reply(f"Congratulations! You have caught a large shiny fish! 🐟 You have been rewarded {coin} coins")
                    else:
                        coin = sg.reward_coins(user, False, "normal", size="large")
                        sg.fish_caught(user, "common")
                        await message.reply(f"Congratulations! You have caught a large normal fish! 🐟 You have been rewarded {coin} coins")
                elif catch_type <= 50: # medium fish 25% chance
                    rarity = random.randint(1, 100)
                    if rarity <= 10:
                        coin = sg.reward_coins(user, False, "legendary", size="medium")
                        sg.fish_caught(user, "legendary")
                        await message.reply(f"Congratulations! You have caught a medium legendary fish! 🐟 You have been rewarded {coin} coins")
                    elif rarity <= 40:
                        coin = sg.reward_coins(user, False, "shiny", size="medium")
                        sg.fish_caught(user, "shiny")
                        await message.reply(f"Congratulations! You have caught a medium shiny fish! 🐟 You have been rewarded {coin} coins")
                    else:
                        coin = sg.reward_coins(user, False, "normal", size="medium")
                        sg.fish_caught(user, "common")
                        await message.reply(f"Congratulations! You have caught a medium normal fish! 🐟 You have been rewarded {coin} coins")
                elif catch_type <= 80: # small fish 30%
                    rarity = random.randint(1, 100)
                    if rarity <= 10:
                        coin = sg.reward_coins(user, False, "legendary", size="small")
                        sg.fish_caught(user, "legendary")
                        await message.reply(f"Congratulations! You have caught a small legendary fish! 🐟 You have been rewarded {coin} coins")
                    elif rarity <= 40:
                        coin = sg.reward_coins(user, False, "shiny", size="small")
                        sg.fish_caught(user, "shiny")
                        await message.reply(f"Congratulations! You have caught a small shiny fish! 🐟 You have been rewarded {coin} coins")
                    else:
                        coin = sg.reward_coins(user, False, "normal", size="small")
                        sg.fish_caught(user, "common")
                        await message.reply(f"Congratulations! You have caught a small normal fish! 🐟 You have been rewarded {coin} coins")
                else:
                    coin = sg.reward_coins(user, False, "trash")
                    await message.reply(f"Oh no! You have caught trash 🗑️. You have been rewarded {coin} coins")
            else:
                await message.reply(f"Unfortunate, you have not caught anything. 😞")
            
            sg.remove_net_use(user, net, net_uses - 1)
                
                

        if message.content.startswith(prefix + "get dex"):
            user = message.author

            dex, coins = sg.get_basic_dex(user)
            if dex is None:
                await message.reply("You have not caught any sharks yet! You also have 0 coins")
            else:
                send = "You have caught these sharks: \n"

                for shark in dex:
                    s = "s" if dex.get(shark) > 1 else ""
                    send += f"{dex.get(shark)} {shark}{s} 🦈 \n"
                
                send += f"You also have {coins} coins"
                await message.reply(send)

        if message.content.startswith(prefix + "get dex detailed"):
            user = message.author
            
            dex = sg.get_dex(user)

            if dex is None:
                await user.send("You have not caught a shark so you have no dex, go catch sharks!")

            send = "Here's your sharkdex: \n"

            index = 1

            for item in dex:

                send += f"""shark {index}: 
name: {item[sharks_index.SHARK_NAME.value]} 🦈
rarity: {item[sharks_index.RARITY.value]} 
time caught: {item[sharks_index.TIME_CAUGHT.value]} 🕰️
facts: {item[sharks_index.SHARK_FACT.value]} 📰
weight: {item[sharks_index.SHARK_WEIGHT.value]} ⚖️
net used: {item[sharks_index.NET_TYPE.value]} 🎣
coins balance: {item[sharks_index.COINS.value]} 🪙

"""
                index += 1

            await user.send(send)
        
        if message.content.startswith(prefix + "my nets"):
            user = message.author
            nets = sg.get_net_availability(user)
            send = "Here's your nets: \n"
            i = 1
            for net in nets:
                send += f"{i}. {net} \n"
            
            await message.reply(send)
        
        if message.content.startswith(prefix + "coins"):
            coins = 0 if sg.check_currency(message.author) is None else sg.check_currency(message.author)

            await message.reply(f"You have {coins} coins!")

        if message.content.startswith(prefix + "add coins"):

            sg.add_coins("spiderbyte2007", 250)

            await message.reply("done")

        if message.content.startswith(prefix + "buy net"):
            
            send = "Choose a net to buy: (choose within the next 30 seconds) \n To choose type `?net name` or type cancel to cancel \n"

            nets, prices = sg.get_nets()
            
            
            follow_found = False
            
            i = 1
            for net in nets:
                send += f"{i}. the {net} costs {prices[i - 1]} \n"
                i += 1

            await message.reply(send)

            def check(m: discord.Message):
                return (
                    m.author.id == message.author.id and
                    m.channel.id == message.channel.id and
                    (m.content.strip().lower() == "cancel" or m.content.strip().startswith(prefix))
                )
            
            try:
                follow = await client.wait_for("message", check=check, timeout=30)
                follow_found = True
            except asyncio.TimeoutError:
                await message.reply("Timed out, try again with `?buy net`")
                follow_found = False
                
            if follow_found:
                logging.info(follow.content.strip().lower()[1:])

                if follow.content.strip().lower() == "cancel":
                    await follow.reply("Cancelled.")
                    return
                # print(nets)
                if follow.content.strip().lower()[1:] in nets:
                    print("found it")
                    if sg.buy_net(message.author, follow.content.strip().lower()[1:]):
                        await message.reply(f"Successfully bought {follow.content.strip().lower()[1:]}")



        if message.content.startswith(prefix + "shark facts"):
            await message.reply(r"To get facts about specific sharks send: ?{sharkname} {fact} or type cancel to abort. Example: Reef Shark weight")
            
            def check(m: discord.Message):
                return (
                    m.author.id == message.author.id and
                    m.channel.id == message.channel.id and
                    (m.content.strip().lower() == "cancel" or m.content.strip().startswith(prefix))
                )
            
            try:
                follow = await client.wait_for("message", check=check, timeout=30)
            except asyncio.TimeoutError:
                await message.reply("Timed out, try again with `?shark facts`")

            if follow.content.strip().lower() == "cancel":
                await follow.reply("Cancelled.")
                return
            
            # 3) Parse "?{shark} {field}" by splitting from the right
            body = follow.content.strip()[len(prefix):].strip()
            if " " not in body:
                await follow.reply("Usage: `?{shark name} {field}` e.g., `?Reef Shark emoji`")
                return

            name_part, field_part = body.rsplit(" ", 1)
            name = name_part.strip()
            field = field_part.lower().strip()

            result = sg.get_something(name=name, thing=field)
            await follow.reply(result)
# ===== RUN =====
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = MyClient(intents=intents, allowed_mentions=discord.AllowedMentions(everyone=True))
client.run(token=token, log_handler=handler)

