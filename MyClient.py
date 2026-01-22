import discord, os, logging, asyncio, random
from pydantic import ValidationError
from dotenv import load_dotenv
from pathlib import Path
import utils.read_Yaml as RY
import datetime as dt
from enum import Enum
from loops.birthdayloop.birthdayLoop import BirthdayLoop, SharkLoops, sg
from loops.levellingloop.levellingLoop import levelingLoop
from ticketingSystem.Ticket_System import TicketSystem

from data.gids import roles_per_gid
from handlers.reactions import reaction_handler, AppConfig

# ======= Logging/Env =======
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="a")
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)
load_dotenv()
token = os.getenv("token")

# ======= CONFIG =======
CONFIG_PATH = Path(r"config.YAML")
TICKET_CONFIG_PATH = Path(r"ticketingSystem\ticketing.yaml")

raw_config = RY.read_config(CONFIG=CONFIG_PATH)
ticket_config = RY.read_config(CONFIG=TICKET_CONFIG_PATH)
prefix: str = "?"

try:
    config = AppConfig.model_construct(
        guilds = raw_config["guilds"],
        roles = raw_config["roles"],
        channels = raw_config["channels"],
        guild_role_messages = raw_config["guild role messages"],
        birthday_message = raw_config["birthday message"],
        boost = raw_config["boost"],
        boost_amount = raw_config["boost amount"],
        time_per_loop = raw_config["time per loop"],
        set_up_done = raw_config["set up done"]
    )
except ValidationError as e:
    print(e)

GIDS: dict = config.guilds
ROLES: dict = config.roles

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
        self.leveling_loop = levelingLoop(self)
        self.ticket_system = TicketSystem(self)
        self._ticket_setup_done: dict = config.set_up_done
        self.reaction_handler = reaction_handler(config_path=CONFIG_PATH, roles_per_guild=roles_per_gid(GIDS, ROLES), bot=self)
        
    # ======= ON RUN =======
    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("----------------------------------------------")
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")
        
        id_to_name: dict = {int(v): k for k, v in config.guilds.items()}

        for guild in self.guilds:

            await self.ensure_react_roles_message(guild)
            guild_name: str = id_to_name.get(guild.id)
            
            if guild_name == "shark squad":
                self.birthday_loops.start_for(guild.id)
                for member in guild.members:
                    added = await self.leveling_loop.add_users(user=member)
                    if added: await self.leveling_loop.add_role(user=member)

            
            if not self._ticket_setup_done.get(guild_name):
                print("set up not done")
                await self.ticket_system.setup_hook()
                logging.info("[TICKETING SYSTEM] Ticket system set up, checking for messages now")

                embed_message_ids = ticket_config.get("embed message ids")                
                if embed_message_ids.get(guild_name) == 0:
                    channel_id = ticket_config.get("ticket channels").get(guild_name)
                    if channel_id is not None or channel_id != 0:
                        channel = guild.get_channel(channel_id)
                    else:
                        logging.warning(f"[TICKET SYSTEM] Channel ID for {guild_name} is either None or Zero!")
                    await self.ticket_system.send_ticket_panel(channel=channel)
                    logging.info(f"[TICKETING SYSTEM] Ticket embed sent to {guild_name}")
                
                self._ticket_setup_done[guild_name] = True
        
    # ======= ANNOUNCE ARRIVAL =======
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        welcome_channels = config["channels"]["welcome"]
        # The reverse seems illogical, but that is because server names on discord may not match the ones in the YAML file, so for consistency we use the one on the YAML
        id_to_name: dict = {int(v): k for k, v in config.guilds.items()}
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

        if guild_name == "shark squad":
            chatting_channels = config["channels"]["chatting"]
            chatting_channel = guild.get_channel(chatting_channels.get(guild_name))

            message = f"""_Tiny fry drifting in sparkling nursery currents. The water shimmers around you, catching the first hints of ocean magic._
Chat, explore, and let your fins grow — your journey through the glittering ocean has just begun. You'll find more to explore at level 1. {member.mention} """
            await chatting_channel.send(message)
            await self.leveling_loop.add_users(user=member)
            await self.leveling_loop.add_role(user=member)

    # ======= ANNOUNCE DEPARTURE =======
    async def on_member_remove(self, member):
        guild = member.guild
        welcome_channels = config["channels"]["welcome"]
        # The reverse seems illogical, but that is because server names on discord may not match the ones in the YAML file, so for consistency we use the one on the YAML
        id_to_name: dict = {int(v): k for k, v in config.guilds.items()}
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

    async def ensure_react_roles_message(self, guild: discord.Guild):
        await self.reaction_handler.ensure_react_roles_message_internal(guild=guild, config=config)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await self.reaction_handler.on_raw_reaction_add_internal(payload=payload, config=config)
    
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await self.reaction_handler.on_raw_reaction_remove_internal(payload=payload, config=config)

    async def on_message(self, message: discord.Message):
        # ignore if it's the bot's message
        if message.author.id == self.user.id:
            return

        if message.guild == None:
            await message.reply("I do not respond to dms, please message me in a server where my commands work. Thank you!")
        
        # leveling system messages
        id_to_name: dict = {int(v): k for k, v in config.guilds.items()}
        if len(message.content) >= 10 and id_to_name.get(message.guild.id) == "shark squad":
            await self.leveling_loop.message_handle(message)
        
        if message.content.startswith(prefix + "check level") and id_to_name.get(message.guild.id) == "shark squad":
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
            """
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

            """

            await message.reply(rules_part1)
            await message.reply(rules_part2)

        if message.content.startswith(prefix + "describe game"):
            TIME_PER_LOOP = config.get("time per loop")
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

            config_2 = RY.read_config(CONFIG_PATH)

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
            channel = message.channel
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
                await channel.send("Using basic net. Fishing now! 🎣")
                net = "rope net"
            else:
                await channel.send("Net not found, defaulting to basic net. Fishing now!🎣")
                net = "rope net"
            
            fish_odds = sg.fishing_odds_fish(username=user, net_used=net)

            boost = config_2.get("boost")
            boost_amount = config_2.get("boost amount")

            rand_int = random.randint(0, 99)
            if rand_int <= fish_odds: #did it catch anything
                catch_type = random.randint(1, 100)
                if catch_type <= 5:
                    names = sg.get_shark_names("very common") 
                    rand_idx = random.randint(0, len(names) - 1) 
                    current_time = dt.datetime.now()
                    time_caught: str = f"{current_time.date()} {current_time.hour}"
                    sg.create_dex(user, names[rand_idx], time_caught, net, "normal", net_uses)
                    coin = sg.reward_coins(user, shark=True, rare="normal", shark_name=names[rand_idx])
                    await channel.send(f"Oh lord, you have caught a shark that has randomly stumbled it's way here! 🦈 Congratulations on the {names[rand_idx]}. You have been given {coin} coins.")
                elif catch_type <= 25: # large fish 20% chance
                    rarity = random.randint(1, 100)
                    if rarity <= 10:
                        coin = sg.reward_coins(user, False, "legendary", size="large", boost=boost, boost_amount=boost_amount)
                        sg.fish_caught(user, "legendary")
                        await channel.send(f"Congratulations! You have caught a large legendary fish! 🐟 You have been rewarded {coin} coins.")
                    elif rarity <= 40:
                        coin = sg.reward_coins(user, False, "shiny", size="large", boost=boost, boost_amount=boost_amount)
                        sg.fish_caught(user, "shiny")
                        await channel.send(f"Congratulations! You have caught a large shiny fish! 🐟 You have been rewarded {coin} coins")
                    else:
                        coin = sg.reward_coins(user, False, "normal", size="large", boost=boost, boost_amount=boost_amount)
                        sg.fish_caught(user, "common")
                        await channel.send(f"Congratulations! You have caught a large normal fish! 🐟 You have been rewarded {coin} coins")
                elif catch_type <= 50: # medium fish 25% chance
                    rarity = random.randint(1, 100)
                    if rarity <= 10:
                        coin = sg.reward_coins(user, False, "legendary", size="medium", boost=boost, boost_amount=boost_amount)
                        sg.fish_caught(user, "legendary")
                        await channel.send(f"Congratulations! You have caught a medium legendary fish! 🐟 You have been rewarded {coin} coins")
                    elif rarity <= 40:
                        coin = sg.reward_coins(user, False, "shiny", size="medium", boost=boost, boost_amount=boost_amount)
                        sg.fish_caught(user, "shiny")
                        await channel.send(f"Congratulations! You have caught a medium shiny fish! 🐟 You have been rewarded {coin} coins")
                    else:
                        coin = sg.reward_coins(user, False, "normal", size="medium", boost=boost, boost_amount=boost_amount)
                        sg.fish_caught(user, "common")
                        await channel.send(f"Congratulations! You have caught a medium normal fish! 🐟 You have been rewarded {coin} coins")
                elif catch_type <= 80: # small fish 30%
                    rarity = random.randint(1, 100)
                    if rarity <= 10:
                        coin = sg.reward_coins(user, False, "legendary", size="small", boost=boost, boost_amount=boost_amount)
                        sg.fish_caught(user, "legendary")
                        await channel.send(f"Congratulations! You have caught a small legendary fish! 🐟 You have been rewarded {coin} coins")
                    elif rarity <= 40:
                        coin = sg.reward_coins(user, False, "shiny", size="small", boost=boost, boost_amount=boost_amount)
                        sg.fish_caught(user, "shiny")
                        await channel.send(f"Congratulations! You have caught a small shiny fish! 🐟 You have been rewarded {coin} coins")
                    else:
                        coin = sg.reward_coins(user, False, "normal", size="small", boost=boost, boost_amount=boost_amount)
                        sg.fish_caught(user, "common")
                        await channel.send(f"Congratulations! You have caught a small normal fish! 🐟 You have been rewarded {coin} coins")
                else:
                    coin = sg.reward_coins(user, False, "trash", boost=boost, boost_amount=boost_amount)
                    await channel.send(f"Oh no! You have caught trash 🗑️. You have been rewarded {coin} coins")
            else:
                await channel.send(f"Unfortunate, you have not caught anything. 😞")
            if net != "rope net" and net is not None:
                sg.remove_net_use(user, net, net_uses - 1)

        if message.content.startswith(prefix + "get dex"):
            user = message.author

            dex, coins = sg.get_basic_dex(user)
            if dex is None:
                await message.reply("You have not caught any sharks yet! You also have 0 coins")
            else:
                message_1 = "You have caught these sharks: \n"
                # back ups in case of the 2000 character limit
                message_2: str = ""
                message_3: str = ""

                for shark in dex:
                    s = "s" if dex.get(shark) > 1 else ""
                    string = f"{dex.get(shark)} {shark}{s} 🦈 \n"
                    if len(message_1 + string) < 2000:
                        message_1 += string 
                    elif len(message_2 + string) < 2000:
                        message_2 += string
                    else:
                        message_3 += string
                    
                if len(message_2) == 0:
                    message_1 += f"You also have {coins} coins"
                elif len(message_3) == 0:
                    message_2 += f"You also have {coins} coins"
                else:
                    message_3 += f"You also have {coins} coins"

                
                await message.reply(message_1)
                channel = message.channel
                if len(message_2) != 0:
                    await channel.send(message_2)
                if len(message_3) != 0:
                    await channel.send(message_3)

        if message.content.startswith(prefix + "get dex detailed"):
            user = message.author
            
            dex = sg.get_dex(user)

            if dex is None:
                await user.send("You have not caught a shark so you have no dex, go catch sharks!")

            message_1: str = "Here's your sharkdex: \n"
            # back ups in case the 2000 character limit discord has is reached
            message_2: str
            message_3: str

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
                if len(message_1 + string) < 2000:
                    message_1 += string
                elif len(message_2 + string) < 2000:
                    message_2 += string
                else:
                    message_3 += string

                index += 1

            await user.send(message_1)
            if len(message_2) != 0:
                await user.send(message_2)
            if len(message_3) != 0:
                await user.send(message_3)

        if message.content.startswith(prefix + "my nets"):
            user = message.author
            nets, about_to_break, _, _ = sg.get_net_availability(user)
            send = "Here's your available nets: \n"
            i = 1
            for net in nets:
                send += f"{i}. {net} \n"
                i +=1
            i = 1
            if about_to_break:
                send += "Here are your nets that are about to break: \n"
                for atb in about_to_break:
                    send += f"{i}. {atb} \n"
            
            await message.reply(send)
        
        if message.content.startswith(prefix + "coins"):
            coins = 0 if sg.check_currency(message.author) is None else sg.check_currency(message.author)

            await message.reply(f"You have {coins} coins!")

        if message.content.startswith(prefix + "add coins"):

            sg.add_coins(message.author, 500)

            await message.reply("done")

        if message.content.startswith(prefix + "buy net"):
            
            send = "Choose a net to buy: (choose within the next 30 seconds) \n To choose type the number of the net or type cancel to cancel \n"

            nets, prices = sg.get_nets()
            
            
            follow_found = False
            
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
                except:
                    isInt = False
                return (
                    m.author.id == message.author.id and
                    m.channel.id == message.channel.id and
                    (m.content.strip().lower() == "cancel" or isInt)
                )
            
            try:
                follow = await client.wait_for("message", check=check, timeout=30)
                follow_found = True
            except asyncio.TimeoutError:
                await message.reply("Timed out, try again with `?buy net`")
                follow_found = False
                
            if follow_found:
                logging.info(follow.content.strip().lower())

                if follow.content.strip().lower() == "cancel":
                    await follow.reply("Cancelled.")
                    return
                # print(nets)
                success, net_name, reason = sg.buy_net(message.author, int(follow.content.strip().lower()))
                if success:
                    logging.info(f"Found net: {net_name} for {message.author}")
                    await follow.reply(f"Successfully bought {net_name}")
                else:
                    logging.info(f"Could not buy {net_name} for {message.author}")
                    await follow.reply(f"Could not buy net because {reason}")

        if message.content.startswith(prefix + "shark facts"):
            await message.reply(r"To get facts about specific sharks send: ?{sharkname} or type cancel to abort. Example: Reef Shark")
            
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
            
            class fact_nums(Enum):
                NAME    = 0
                FACT    = 1
                EMOJI   = 2
                WEIGHT  = 3
                RARITY  = 4

            # 3) Parse "?{shark}" by removing the prefix
            name = follow.content.strip()[len(prefix):]

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

