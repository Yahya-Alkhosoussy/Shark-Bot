import asyncio
import datetime as dt
import logging
import random
from pathlib import Path

import discord

import exceptions.exceptions as ex
import SQL.sharkGamesSQL.sharkGameSQL as sg
from SQL.fishingSQL.baits import add_to_shop, baits_in_shop, buy_baits, update_shop_prices
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
        if bait is None:
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
        else:  # If bait is used
            rarity: sg.SharkRarity
            match bait:
                case "chum":
                    rarity = sg.SharkRarity.VERY_COMMON
                case "bait ball":
                    rarity = sg.SharkRarity.COMMON
                case "mackerel":
                    rarity = sg.SharkRarity.UNCOMMON
                case "stingray":
                    rarity = sg.SharkRarity.RARE
                case "barracuda":
                    rarity = sg.SharkRarity.ULTRA_RARE
                case _:
                    raise ex.ItemNotFound(f"Could not find bait ({bait}) in list", 1001)
            if rand_int <= fish_odds:  # did it catch anything
                catch_type = random.randint(1, 100)
                if catch_type <= 35:
                    names = sg.get_shark_names(rarity=rarity)
                    rand_idx = random.randint(0, len(names) - 1)
                    current_time = dt.datetime.now()
                    time_caught: str = f"{current_time.date()} {current_time.hour}"
                    sg.create_dex(str(user), names[rand_idx], time_caught, net, "normal", net_uses)
                    coin = sg.reward_coins(str(user), shark=True, rare="normal", shark_name=names[rand_idx])
                    await channel.send(
                        f"Oh lord, you have caught a shark that has randomly stumbled it's way here! 🦈 Congratulations on the {names[rand_idx]}. You have been given {coin} coins."  # noqa: E501
                    )
                elif catch_type <= 65:  # large fish 30% chance
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
                elif catch_type <= 80:  # medium fish 15% chance
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
                elif catch_type <= 90:  # small fish 10%
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
                else:  # Trash 10%
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

    async def add_into_shop_internal(self, message: discord.Message):
        await message.reply(
            "Please send the name of the bait you want to add, you have 30 seconds to send it! (WARNING: ONLY THE NAME SHOULD BE SENT)"  # noqa: E501
        )
        channel = message.channel
        await channel.send("Or cancel please send `?cancel`")

        def check(m: discord.Message):
            return m.author.id == message.author.id and m.channel.id == message.channel.id

        try:
            follow = await self.client.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await message.reply("Timed out, try again with `?update shop items`")
            return

        if follow.content.strip().lower == "?cancel":
            await follow.reply("Cancelled.")
            return

        await follow.reply(
            f"To confirm you want {follow.content} to be the name of the bait. Send `?confirm` to confirm and send anything else to cancel."  # noqa: E501
        )

        try:
            follow_up = await self.client.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await follow.reply("Timed out, try again with `?update shop items`")
            return

        if follow_up.content != "?confirm":
            await follow_up.reply("Cancelled your request.")
            return

        await follow_up.reply(
            f"Bait name will be {follow.content}. Send the price of the bait or send `?cancel` to cancel! You have 30 seconds!"
        )
        bait_name = follow.content
        channel.send("Please only send the number!")
        try:
            follow_up_2 = await self.client.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await follow_up.reply("Timed out, try again with `?update shop items`")
            return

        if follow_up_2.content == "?cancel":
            await follow_up_2.reply("Cancelled your request.")
            return

        try:
            await follow_up_2.reply(
                f"{follow_up.content} will cost {int(follow_up_2.content)} coins, to confirm send `?confirm` and anything else to cancel"  # noqa E501
            )
        except ValueError as e:
            raise f"Ran into an issue updating the shop items: {e}"

        try:
            follow_up_3 = await self.client.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await follow_up_2.reply("Timed out, try again with `?update shop items`")
            return

        if follow_up_3.content != "?confirm":
            await follow_up_3.reply("Cancelled your request.")

        await follow_up_3.reply("Adding bait to shop...")
        price = int(follow_up_2.content)
        try:
            add_to_shop(bait=bait_name, price=price)
            await follow_up_3.reply("Bait added to the shop!")
        except Exception as e:
            raise e  # custom message from add_to_shop

    async def update_shop_prices_internal(self, message: discord.Message):
        await message.reply(
            "Please send the name of the bait you want to edit the price of, you have 30 seconds to send it! (WARNING: ONLY THE NAME SHOULD BE SENT)"  # noqa: E501
        )
        channel = message.channel
        await channel.send("Or cancel please send `?cancel`")

        def check(m: discord.Message):
            return m.author.id == message.author.id and m.channel.id == message.channel.id

        try:
            follow = await self.client.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await message.reply("Timed out, try again with `?update shop items`")
            return

        if follow.content.strip().lower == "?cancel":
            await follow.reply("Cancelled.")
            return

        await follow.reply(
            f"To confirm you want to edit the following bait: {follow.content}. Send `?confirm` to confirm and send anything else to cancel."  # noqa: E501
        )

        try:
            follow_up = await self.client.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await follow.reply("Timed out, try again with `?update shop items`")
            return

        if follow_up.content != "?confirm":
            await follow_up.reply("Cancelled your request.")
            return

        await follow_up.reply(
            f"Bait that will be edited is: {follow.content}. Send the price of the bait or send `?cancel` to cancel! You have 30 seconds!"  # noqa: E501
        )
        bait_name = follow.content
        channel.send("Please only send the number!")
        try:
            follow_up_2 = await self.client.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await follow_up.reply("Timed out, try again with `?update shop items`")
            return

        if follow_up_2.content == "?cancel":
            await follow_up_2.reply("Cancelled your request.")
            return

        try:
            await follow_up_2.reply(
                f"{follow_up.content} will cost {int(follow_up_2.content)} coins, to confirm send `?confirm` and anything else to cancel"  # noqa E501
            )
        except ValueError as e:
            raise f"Ran into an issue updating the shop items: {e}"

        try:
            follow_up_3 = await self.client.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await follow_up_2.reply("Timed out, try again with `?update shop items`")
            return

        if follow_up_3.content != "?confirm":
            await follow_up_3.reply("Cancelled your request.")

        await follow_up_3.reply("Editing bait price in the shop...")
        price = int(follow_up_2.content)
        try:
            update_shop_prices(bait=bait_name, price=price)
            await follow_up_3.reply("Price updated in the shop!")
        except Exception as e:
            raise e  # custom message from update_shop_prices

    async def buy_bait(self, message: discord.Message):
        baits = baits_in_shop()
        send = "Choose a bait to buy (choose within the next 30 seconds) \n To choose type the number of the bait or type cancel to cancel \n"  # noqa: E501
        i = 0
        for bait in baits:
            name = bait[0]
            price = bait[1]
            i += 1
            send += f"{i}. {name} that costs {price} per piece.\n"

        for bait in baits:
            name = bait[0] + "x 5"
            price = bait[1] * 5
            i += 1
            send += f"{i}. {name} that costs {price} per 5 pieces.\n"

        await message.reply(send)

        def check(m: discord.Message):
            isInt: bool = False

            try:
                int(m.content.strip())
                isInt = True
            except Exception:
                isInt = False
            return (
                m.author.id == message.author.id
                and m.channel.id == message.channel.id
                and (m.content.strip().lower() == "cancel" or isInt)
            )

        follow = None

        try:
            follow = await self.client.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await message.reply("Timed out, try again with `?buy bait`")

        if follow:
            logging.info(follow.content.strip().lower())

            if follow.content.strip().lower() == "cancel":
                await follow.reply("Cancelled.")
                return
        try:
            success, bait_bought, reason = buy_baits(username=message.author.name, bait=follow)
        except ex.ItemNotFound as e:
            raise e

        if not success:
            await follow.reply(f"Coult not buy net because {reason}")
        else:
            await follow.reply(f"Successfully bought {bait_bought}!")
