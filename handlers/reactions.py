import logging

import discord

from utils.core import AppConfig, RoleMessageSet


class reaction_handler:
    ROLES_PER_GUILD: dict

    def __init__(
        self, config: AppConfig, roles_per_guild: dict[int, dict[str, dict[discord.PartialEmoji, int]]], bot: discord.Client
    ):
        self.config = config
        self.ROLES_PER_GUILD = roles_per_guild
        self.BOT = bot

    # ======= Ensures React Roles message exists =======
    async def ensure_react_roles_message_internal(self, guild: discord.Guild):
        # check for guild config, if none found then skip
        if not self.config.is_guild_in_config(guild_id=guild.id):
            raise ValueError(f"Guild {guild.name} is not in the config. Skipping")

        guild_name: str = self.config.guilds[guild.id]
        # print(guild_name)

        react_role_messages: RoleMessageSet = self.config.guild_role_messages.setdefault(
            self.config.guilds.get(guild_name), RoleMessageSet([])
        )
        # print(react_role_messages)

        if not self.config.is_rr_message_id_in_config(guild_name=guild_name):
            raise KeyError(f"Guild {guild.name} does not have a react roles message ID Key")

        for rr_name, rr_message in react_role_messages:
            # print(react_role_messages[rr_message])

            channel_id = int(self.config.get_channel_id(guild_name=guild_name, channel="roles"))
            channel = guild.get_channel(channel_id) if channel_id else None

            guild_roles = self.ROLES_PER_GUILD[guild.id]
            role_mapping = guild_roles[rr_message.name] if guild_roles else None
            # print("current mapping: ",role_mapping)
            # print(f"emoji: ",role_mapping)

            message = None
            try:
                message_id = react_role_messages[rr_message.name]
                if isinstance(channel, discord.TextChannel):
                    message = await channel.fetch_message(message_id)
                else:
                    raise TypeError("[RR] cannot fetch messages from a non-text channel")
            except (discord.NotFound, discord.Forbidden, discord.HTTPException, TypeError) as e:
                logging.error(
                    f"[RR] could not fetch existing react-roles message {rr_message.name} in {guild_name}\nInner Exception: {e}"
                )
                continue

            if react_role_messages[rr_message.name] != 0:
                logging.info(f"There is already a react roles message of {rr_message} for {guild_name}")
                if channel is None:
                    logging.error(f"[RR] No valid channel configured for {guild_name}")
                    continue  # Keep original flow

                if not role_mapping:
                    continue  # nothing to add

                existing = {str(r.emoji) for r in message.reactions} if message else {}
                for emoji in role_mapping.keys():
                    if existing and message and emoji not in existing:
                        try:
                            await message.add_reaction(emoji)
                        except discord.HTTPException:
                            logging.error(f"[RR] could not add reaction {emoji} in {guild_name}")

                current_content = ""
                current_lines = current_content.splitlines()
                header = current_lines[0] if current_lines else "React to get your roles: "
                existing_entries = set(current_lines[1:]) if len(current_lines) > 1 else set()

                desired_entries = [f"{emoji} -> <@&{role_id}>" for emoji, role_id in role_mapping.items()]
                to_append = [line for line in desired_entries if line not in existing_entries]

                if to_append and message:  # make sure it isn't empty
                    new_content = (
                        header
                        + "\n"
                        + "\n".join(sorted(existing_entries))
                        + ("\n" if existing_entries else "")
                        + "\n".join(to_append)
                    ).strip()
                    try:
                        await message.edit(content=new_content)
                    except discord.HTTPException:
                        logging.error(f"[RR could not edit react-roles message {rr_message} in {guild_name}]")
                # ---------------------------------------------------------------------------------------------
                continue

            if channel is None or not isinstance(channel, discord.TextChannel):
                raise LookupError(f"[RR] No valid channel configured for {guild_name}")

            if isinstance(channel, discord.TextChannel):
                message = await channel.send(
                    "React to get your roles: \n"
                    + "\n".join(
                        (f"{emoji} -> <@&{role_id}>" for emoji, role_id in role_mapping.items()) if role_mapping else ""
                    )
                )

                if message:
                    # Add the reactions we'll listen for
                    if role_mapping:
                        for emoji in role_mapping.keys():
                            try:
                                await message.add_reaction(emoji)
                            except discord.HTTPException:
                                logging.error(f"[RR] could not add reaction {emoji} in {guild_name}")

                    self.config.guild_role_messages[self.config.guilds.get(guild_name)][rr_message.name] = message.id
                    self.config.saveConfig()
                else:
                    logging.error(f"[RR] could not add reactions in {guild_name}. Channel returned message as None")
                    return
            else:
                logging.critical("[RR] Bad channel type, not a TextChannel")
                return

    # ======= REACTION ROLES ADD ROLE =======
    async def on_raw_reaction_add_internal(self, payload: discord.RawReactionActionEvent):
        gid = payload.guild_id

        if gid is None:
            logging.error("Guild ID could not be found")
            return

        guild_name = self.config.guilds[int(gid)]
        rr_message_ids: RoleMessageSet = self.config.guild_role_messages.setdefault(
            self.config.guilds.get(guild_name), RoleMessageSet([])
        )
        message_id: int | None = None

        for id in rr_message_ids.todict().values():
            if payload.message_id == id:
                message_id = id
                logging.info(f"found message! Reaction to message id: {id}")
        if not message_id:
            logging.info("Message isn't in my list")
            return

        id_to_name_rr = {v.id: k for k, v in rr_message_ids.items()}
        rr_message = id_to_name_rr[message_id]
        mapping = self.ROLES_PER_GUILD[gid][rr_message]
        key = payload.emoji
        try:
            role_id = mapping.get(str(key))
            if role_id is None:
                role_id = mapping[key]
            print(f"found role ID: {role_id}")
        except KeyError:
            logging.info("not the emoji i care about")
            return

        guild = self.BOT.get_guild(gid)
        if guild is None:
            logging.warning(f"Couldn't find guild with ID of {gid}")
            return

        role = guild.get_role(role_id)
        if role is None:
            logging.warning(f"Couldn't find role with ID of {role_id} and emoji of {key}")
            return

        if payload.member:
            try:
                await payload.member.add_roles(role)
                logging.info(f"Added role {role} to {payload.member.name}")
            except discord.HTTPException:
                logging.error("HTTPException, I couldn't do it")
                return
        else:
            logging.error("Cannot attach a role to a non-existent member (payload.member is None)")
            return

    # ======= REACTION ROLES ADD ROLE =======
    async def on_raw_reaction_remove_internal(self, payload: discord.RawReactionActionEvent):
        gid = payload.guild_id

        if gid is None:
            logging.info("[RR] Reaction was not from a guild")
            return

        if gid is None:
            logging.error("Guild ID could not be found")
            return

        guild_name = self.config.guilds[int(gid)]

        rr_message_ids: RoleMessageSet = self.config.guild_role_messages[self.config.guilds.get(guild_name)]
        message_id: int | None = None
        for id in rr_message_ids.todict().values():
            if payload.message_id == id:
                message_id = id
                logging.info(f"found message! Reaction to message id: {id}")
        if not message_id:
            logging.info("Message isn't in my list")
            return

        react_role_messages: RoleMessageSet = self.config.guild_role_messages.setdefault(
            self.config.guilds.get(guild_name), RoleMessageSet([])
        )
        id_to_name_rr = {v.id: k for k, v in react_role_messages.items()}
        rr_message = id_to_name_rr[message_id]
        mapping = self.ROLES_PER_GUILD[gid][rr_message]
        key = payload.emoji
        try:
            role_id = mapping.get(str(key))
            if role_id is None:
                role_id = mapping[key]
            print(f"found role ID: {role_id}")
        except KeyError:
            logging.info("not the emoji i care about")
            return

        guild = self.BOT.get_guild(gid)
        if guild is None:
            logging.warning(f"Couldn't find guild with ID of {gid}")
            return

        role = guild.get_role(role_id) if guild else None
        if role is None:
            logging.warning(f"Couldn't find role with ID of {role_id} and emoji of {key}")
            return

        member = guild.get_member(payload.user_id)

        if member:
            try:
                await member.remove_roles(role)
                logging.info(f"Removed role {role} from {member.name}")
            except discord.HTTPException:
                logging.error("HTTPException, I couldn't do it")
                return
        else:
            logging.error(f"Failed to remove reaction. get_member failed for guild ID {gid} and user ID {payload.user_id}")
