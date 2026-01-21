import logging, discord
import utils.read_Yaml as RY
from utils.core import *

class reaction_handler:
    ROLES_PER_GUILD: dict
    CONFIG_PATH: str

    def __init__(self, config_path, roles_per_guild, bot: discord.Client):
        self.CONFIG_PATH = config_path
        self.ROLES_PER_GUILD = roles_per_guild
        self.bot = bot

    # ======= Ensures React Roles message exists =======
    async def ensure_react_roles_message_internal(self, config: AppConfig, guild: discord.Guild):
        # check for guild config, if none found then skip
        if not is_guild_in_config(guild_id=guild.id, config=config):
            logging.error(f"Guild {guild.name} is not in the config. Skipping")
            return

        id_to_name: dict = {int(v): k for k, v in config.guilds.items()}
        guild_name: str = id_to_name.get(guild.id)
        # print(guild_name)
        
        react_role_messages: dict = config.guild_role_messages.setdefault(guild_name, {})
        # print(react_role_messages)

        if not is_rr_message_id_in_config(guild_name=guild_name, config=config):
            logging.error(f"Guild {guild.name} is does not have a react roles message ID Key")
            return        

        for rr_message in react_role_messages:
            # print(react_role_messages[rr_message])

            channel_id = int(get_channel_id(config=config, guild_name=guild_name, channel="roles"))
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

                mapping = self.ROLES_PER_GUILD.get(guild.id).get(rr_message)
                if not mapping:
                    continue # nothing to add
                
                existing = {str(r.emoji) for r in message.reactions}
                for emoji in mapping.keys():
                    if emoji not in existing:
                        try:
                            await message.add_reaction(emoji)
                        except discord.HTTPException:
                            logging.error(f"[RR] could not add reaction {emoji} in {guild_name}")

                current_content = ""
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

            mapping = self.ROLES_PER_GUILD.get(guild.id).get(rr_message)
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
            
            config.guild_role_messages[guild_name][rr_message] = message.id
            RY.save_config(CONFIG=self.CONFIG_PATH, cfg=config)
        
    # ======= REACTION ROLES ADD ROLE =======
    async def on_raw_reaction_add_internal(self, config: AppConfig, payload: discord.RawReactionActionEvent):

        guilds = config.guilds
        gid = payload.guild_id

        if gid is None: 
            logging.info("[RR] Reaction was not from a guild")
            return
        
        id_to_name = {int(v): k for k, v in guilds.items()}
        if gid is None:
            logging.error(f"Guild ID could not be found")
            return
        
        guild_name = id_to_name.get(int(gid))

        rr_message_ids: dict = config.guild_role_messages.get(guild_name)
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
        
        react_role_messages: dict = config.guild_role_messages.setdefault(guild_name, {})
        id_to_name_rr = {int(v): k for k, v in react_role_messages.items()}
        rr_message = id_to_name_rr.get(message_id)
        mapping = self.ROLES_PER_GUILD.get(gid).get(rr_message)
        key = payload.emoji
        try: 
            role_id = mapping.get(str(key))
            if role_id == None:
                role_id = mapping.get(key)
            print(f"found role ID: {role_id}")
        except KeyError:
            logging.info("not the emoji i care about")
            return
        
        guild = self.bot.get_guild(gid)
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
    async def on_raw_reaction_remove_internal(self, config: AppConfig, payload: discord.RawReactionActionEvent):

        guilds = config.guilds
        gid = payload.guild_id

        if gid is None: 
            logging.info("[RR] Reaction was not from a guild")
            return
        
        id_to_name = {int(v): k for k, v in guilds.items()}
        if gid is None:
            logging.error(f"Guild ID could not be found")
            return
        
        guild_name = id_to_name.get(int(gid))

        rr_message_ids: dict = config.guild_role_messages.get(guild_name)
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
        
        react_role_messages: dict = config.guild_role_messages.setdefault(guild_name, {})
        id_to_name_rr = {int(v): k for k, v in react_role_messages.items()}
        rr_message = id_to_name_rr.get(message_id)
        mapping = self.ROLES_PER_GUILD.get(gid).get(rr_message)
        key = payload.emoji
        try: 
            role_id = mapping.get(str(key))
            if role_id == None:
                role_id = mapping.get(key)
            print(f"found role ID: {role_id}")
        except KeyError:
            logging.info("not the emoji i care about")
            return
        
        guild = self.bot.get_guild(gid)
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