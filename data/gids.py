import discord

def roles_per_gid(gids: dict[str, int], roles: dict[str, dict[str, int]]):
    ROLES_PER_GUILD: dict[int, dict[str, dict[discord.PartialEmoji, int]]] = {
        gids["test server"]: {
            "colour": {
                discord.PartialEmoji(name='🩵'): roles["colour"]["cyan"]
            },
            "general": {
                discord.PartialEmoji(name='❤️'): roles["general"]["red"]
            },
            "test": {
                discord.PartialEmoji(name='💚'): roles["test"]["green"]
            },
        },
        gids["shark squad"]: {
            "birthdays": {
                discord.PartialEmoji(name='🎆'): roles["birthdays"]["January babies"],
                discord.PartialEmoji(name='💌'): roles["birthdays"]["February babies"],
                discord.PartialEmoji(name='🍀'): roles["birthdays"]["March babies"],
                discord.PartialEmoji(name='🪺'): roles["birthdays"]["April babies"],
                discord.PartialEmoji(name='🌥️'): roles["birthdays"]["May babies"],
                discord.PartialEmoji(name='🌞'): roles["birthdays"]["June babies"],
                discord.PartialEmoji(name='🗽'): roles["birthdays"]["July babies"],
                discord.PartialEmoji(name='🌤️'): roles["birthdays"]["August babies"],
                discord.PartialEmoji(name='🍂'): roles["birthdays"]["September babies"],
                discord.PartialEmoji(name='👻'): roles["birthdays"]["October babies"],
                discord.PartialEmoji(name='🦃'): roles["birthdays"]["November babies"],
                discord.PartialEmoji(name='🎅'): roles["birthdays"]["December babies"],
            },
            "general": {
                discord.PartialEmoji(name='🎮'): roles["general"]["shark games"],
                discord.PartialEmoji(name='❗'): roles["general"]["shark update"],
                discord.PartialEmoji(name='💻'): roles["general"]["discord bot update"],
                discord.PartialEmoji(name='Zerotwodrinkbyliliiet112', id=1318361002072604692): roles["backpacks and sherpas"]["ZZZ backpack"],
                discord.PartialEmoji(name='🎫'): roles["general"]["shark movie ticket"],
            },
            "backpack": {
                discord.PartialEmoji(name='🦸'): roles["backpacks and sherpas"]["marvel rivals backpack"],
                discord.PartialEmoji(name='🧙‍♀️'): roles["backpacks and sherpas"]["TFD backpack"],
                discord.PartialEmoji(name='🧟'): roles["backpacks and sherpas"]["monster hunter backpack"],
                discord.PartialEmoji(name='🥷'): roles["backpacks and sherpas"]["warframe backpack"],
                discord.PartialEmoji(name='🏰'): roles["backpacks and sherpas"]["elden ring backpack"],
                discord.PartialEmoji(name='🤺'): roles["backpacks and sherpas"]["nightreign backpack"],
                discord.PartialEmoji(name='🔫'): roles["backpacks and sherpas"]["Destiney Backpack"],
                discord.PartialEmoji(name='animateduwu', animated=True, id=1279478093278609491): roles["backpacks and sherpas"]["DNA backpack"],
                discord.PartialEmoji(name='Zerotwosurprisedbyliliiet112', id=1318361087833538631): roles["backpacks and sherpas"]["ZZZ backpack"],
            },
            "sherpa": {
                discord.PartialEmoji(name='🦸'): roles["backpacks and sherpas"]["marvel rivals sherpa"],
                discord.PartialEmoji(name='🧙‍♀️'): roles["backpacks and sherpas"]["TFD sherpa"],
                discord.PartialEmoji(name='🧟'): roles["backpacks and sherpas"]["monster hunter sherpa"],
                discord.PartialEmoji(name='🥷'): roles["backpacks and sherpas"]["warframe sherpa"],
                discord.PartialEmoji(name='🏰'): roles["backpacks and sherpas"]["elden ring sherpa"],
                discord.PartialEmoji(name='🤺'): roles["backpacks and sherpas"]["nightreign sherpa"],
                discord.PartialEmoji(name='🔫'): roles["backpacks and sherpas"]["Destiney Sherpa"],
                discord.PartialEmoji(name='animateduwu', animated=True, id=1279478093278609491): roles["backpacks and sherpas"]["DNA sherpa"],
                discord.PartialEmoji(name='Zerotwosurprisedbyliliiet112', id=1318361087833538631): roles["backpacks and sherpas"]["ZZZ sherpa"],
            },
            "friend": {
                discord.PartialEmoji(name='🦸'): roles["friend"]["Marvel Rivals"],
                discord.PartialEmoji(name='🧙‍♀️'): roles["friend"]["TFD"],
                discord.PartialEmoji(name='🧟'): roles["friend"]["Monster Hunter"],
                discord.PartialEmoji(name='🥷'): roles["friend"]["Warframe"],
                discord.PartialEmoji(name='🏰'): roles["friend"]["Elden Ring"],
                discord.PartialEmoji(name='🤺'): roles["friend"]["Nightreign"],
                discord.PartialEmoji(name='🔫'): roles["friend"]["Destiney"],
                discord.PartialEmoji(name='animateduwu', animated=True, id=1279478093278609491): roles["friend"]["DNA"],
                discord.PartialEmoji(name='Zerotwosurprisedbyliliiet112', id=1318361087833538631): roles["friend"]["ZZZ"],
                discord.PartialEmoji(name='hello', id=1446858982403739689): roles["friend"]["Gaming Friend"]
            }
        }    
    }

    return ROLES_PER_GUILD