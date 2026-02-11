import asyncio
import datetime as dt
import logging
import random
from pathlib import Path

import discord

import SQL.sharkGamesSQL.sharkGameSQL as sg
from utils.fishing import FishingConfig


class Fishing:
    def __init__(self, client: discord.Client):
        self.client = client
        super().__init__()

    async def fish(self, message: discord.Message, bait: str | None = None):
        config = FishingConfig(Path(r"fishing\fishing.yaml"))
        user = message.author

        owned_nets, about_to_break, broken, net_uses = sg.get_net_availability(str(user))

        await message.reply(
            "Which net do you want to use?🎣 Type `?net name` to use it or send `cancel` to cancel! If you do not own any nets send `?none` to use a basic net. (You have 30 seconds to send one of the two)"  # noqa: E501
        )

        def check(m: discord.Message):
            return (
                m.author.id == user.id
                and m.channel.id == message.channel.id
                and (m.content.strip().lower() == "cancel" or m.content.strip().startswith("?"))
            )

        try:
            follow = await self.client.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await message.reply("Timed out, try again with `?fish`")
            return

        logging.info(follow.content.strip().lower()[1:])

        if follow.content.strip().lower() == "cancel":
            await follow.reply("Cancelled.")
            return
        # print(nets)
        channel = message.channel
        if follow.content.strip().lower()[1:] not in owned_nets:
            await channel.send("Net not found, defaulting to basic net. Fishing now!🎣")
            net = "rope net"
        if follow.content.strip().lower()[1:] in owned_nets:
            # print("found it")
            if follow.content.strip().lower()[1:] in about_to_break and net_uses == 21:
                await message.reply(
                    "WARNING: Net is about to break, 1 more use left. Do not worry through because you have 4 more of the same net left"  # noqa: E501
                )
            elif follow.content.strip().lower()[1:] in about_to_break and net_uses == 16:
                await message.reply(
                    "WARNING: Net is about to break, 1 more use left. Do not worry through because you have 3 more of the same net left"  # noqa: E501
                )
            elif follow.content.strip().lower()[1:] in about_to_break and net_uses == 11:
                await message.reply(
                    "WARNING: Net is about to break, 1 more use left. Do not worry through because you have 2 more of the same net left"  # noqa: E501
                )
            elif follow.content.strip().lower()[1:] in about_to_break and net_uses == 6:
                await message.reply(
                    "WARNING: Net is about to break, 1 more use left. Do not worry through because you have 1 more of the same net left"  # noqa: E501
                )
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

        fish_odds = sg.fishing_odds_fish(username=str(user), net_used=net)

        boost = config["boost"]
        boost_amount = config["boost amount"]

        rand_int = random.randint(0, 99)
        if rand_int <= fish_odds:  # did it catch anything
            catch_type = random.randint(1, 100)
            if catch_type <= 5:
                names = sg.get_shark_names(sg.SharkRarity.VERY_COMMON)
                rand_idx = random.randint(0, len(names) - 1)
                current_time = dt.datetime.now()
                time_caught: str = f"{current_time.date()} {current_time.hour}"
                sg.create_dex(str(user), names[rand_idx], time_caught, net, "normal", net_uses)
                coin = sg.reward_coins(str(user), shark=True, rare="normal", shark_name=names[rand_idx])
                await channel.send(
                    f"Oh lord, you have caught a shark that has randomly stumbled it's way here! 🦈 Congratulations on the {names[rand_idx]}. You have been given {coin} coins."  # noqa: E501
                )
            elif catch_type <= 25:  # large fish 20% chance
                rarity = random.randint(1, 100)
                if rarity <= 10:
                    coin = sg.reward_coins(
                        str(user),
                        False,
                        "legendary",
                        size="large",
                        boost=boost,
                        boost_amount=boost_amount,
                    )
                    sg.fish_caught(str(user), "legendary")
                    await channel.send(
                        f"Congratulations! You have caught a large legendary fish! 🐟 You have been rewarded {coin} coins."
                    )
                elif rarity <= 40:
                    coin = sg.reward_coins(
                        str(user),
                        False,
                        "shiny",
                        size="large",
                        boost=boost,
                        boost_amount=boost_amount,
                    )
                    sg.fish_caught(str(user), "shiny")
                    await channel.send(
                        f"Congratulations! You have caught a large shiny fish! 🐟 You have been rewarded {coin} coins"
                    )
                else:
                    coin = sg.reward_coins(
                        str(user),
                        False,
                        "normal",
                        size="large",
                        boost=boost,
                        boost_amount=boost_amount,
                    )
                    sg.fish_caught(str(user), "common")
                    await channel.send(
                        f"Congratulations! You have caught a large normal fish! 🐟 You have been rewarded {coin} coins"
                    )
            elif catch_type <= 50:  # medium fish 25% chance
                rarity = random.randint(1, 100)
                if rarity <= 10:
                    coin = sg.reward_coins(
                        str(user),
                        False,
                        "legendary",
                        size="medium",
                        boost=boost,
                        boost_amount=boost_amount,
                    )
                    sg.fish_caught(str(user), "legendary")
                    await channel.send(
                        f"Congratulations! You have caught a medium legendary fish! 🐟 You have been rewarded {coin} coins"
                    )
                elif rarity <= 40:
                    coin = sg.reward_coins(
                        str(user),
                        False,
                        "shiny",
                        size="medium",
                        boost=boost,
                        boost_amount=boost_amount,
                    )
                    sg.fish_caught(str(user), "shiny")
                    await channel.send(
                        f"Congratulations! You have caught a medium shiny fish! 🐟 You have been rewarded {coin} coins"
                    )
                else:
                    coin = sg.reward_coins(
                        str(user),
                        False,
                        "normal",
                        size="medium",
                        boost=boost,
                        boost_amount=boost_amount,
                    )
                    sg.fish_caught(str(user), "common")
                    await channel.send(
                        f"Congratulations! You have caught a medium normal fish! 🐟 You have been rewarded {coin} coins"
                    )
            elif catch_type <= 80:  # small fish 30%
                rarity = random.randint(1, 100)
                if rarity <= 10:
                    coin = sg.reward_coins(
                        str(user),
                        False,
                        "legendary",
                        size="small",
                        boost=boost,
                        boost_amount=boost_amount,
                    )
                    sg.fish_caught(str(user), "legendary")
                    await channel.send(
                        f"Congratulations! You have caught a small legendary fish! 🐟 You have been rewarded {coin} coins"
                    )
                elif rarity <= 40:
                    coin = sg.reward_coins(
                        str(user),
                        False,
                        "shiny",
                        size="small",
                        boost=boost,
                        boost_amount=boost_amount,
                    )
                    sg.fish_caught(str(user), "shiny")
                    await channel.send(
                        f"Congratulations! You have caught a small shiny fish! 🐟 You have been rewarded {coin} coins"
                    )
                else:
                    coin = sg.reward_coins(
                        str(user),
                        False,
                        "normal",
                        size="small",
                        boost=boost,
                        boost_amount=boost_amount,
                    )
                    sg.fish_caught(str(user), "common")
                    await channel.send(
                        f"Congratulations! You have caught a small normal fish! 🐟 You have been rewarded {coin} coins"
                    )
            else:
                coin = sg.reward_coins(
                    str(user),
                    False,
                    "trash",
                    boost=boost,
                    boost_amount=boost_amount,
                )
                await channel.send(f"Oh no! You have caught trash 🗑️. You have been rewarded {coin} coins")
        else:
            await channel.send("Unfortunate, you have not caught anything. 😞")
        if net != "rope net" and net is not None:
            sg.remove_net_use(str(user), net, net_uses - 1)
