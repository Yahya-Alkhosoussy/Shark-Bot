import asyncio
import datetime as dt
import logging
import random
from enum import Enum
from pathlib import Path

import discord

import exceptions.exceptions as ex
import SQL.sharkGamesSQL.sharkGameSQL as sg
from SQL.fishingSQL.baits import (
    add_fish_caught,
    add_to_shop,
    baits_in_shop,
    buy_baits,
    check_user_is_in_baits,
    get_baits,
    get_fish_caught,
    update_shop_prices,
    use_bait,
)
from utils.fishing import FishingConfig, remove_net_use


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
        if bait is not None:
            use_bait(message.author.name, bait=bait)
            baits, uses = get_baits(username=message.author.name)
            use = 0
            i = 0
            for name in baits:
                if name != bait:
                    i += 1
                    continue
                use = uses[i]
                break
            if use > 1:
                await channel.send(f"Bait {bait} used! you now have {use} uses left!")
            elif use == 1:
                await channel.send(f"Bait {bait} used! Becareful! you now have {use} use left!")
            else:
                await channel.send(f"Bait {bait} used! Becareful! you now have no more uses left!")

        if follow.content.strip().lower()[1:] in owned_nets:
            warning = remove_net_use(net=follow.content.strip().lower()[1:], user=user.name)
            if warning:
                await message.reply(warning)

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
            check_user_is_in_baits(username=message.author.name)
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
                        add_fish_caught(username=user.name, size="large", rarity="legendary")
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
                        add_fish_caught(username=user.name, size="large", rarity="shiny")
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
                        add_fish_caught(username=user.name, size="large", rarity="common")
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
                        add_fish_caught(username=user.name, size="medium", rarity="legendary")
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
                        add_fish_caught(username=user.name, size="medium", rarity="shiny")
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
                        add_fish_caught(username=user.name, size="medium", rarity="common")
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
                        add_fish_caught(username=user.name, size="small", rarity="legendary")
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
                        add_fish_caught(username=user.name, size="small", rarity="shiny")
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
                        add_fish_caught(username=user.name, size="small", rarity="common")
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
            if rand_int <= fish_odds + 10:  # did it catch anything
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
                        add_fish_caught(username=user.name, size="large", rarity="legendary")
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
                        add_fish_caught(username=user.name, size="large", rarity="shiny")
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
                        add_fish_caught(username=user.name, size="large", rarity="common")
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
                        add_fish_caught(username=user.name, size="medium", rarity="legendary")
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
                        add_fish_caught(username=user.name, size="medium", rarity="shiny")
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
                        add_fish_caught(username=user.name, size="medium", rarity="common")
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
                        add_fish_caught(username=user.name, size="small", rarity="legendary")
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
                        add_fish_caught(username=user.name, size="small", rarity="shiny")
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
                        add_fish_caught(username=user.name, size="small", rarity="common")
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
            send += f"{i}. {name} - {price} coins.\n"

        for bait in baits:
            name = bait[0] + " x 5"
            price = bait[1] * 5
            i += 1
            send += f"{i}. {name} - {price} coins.\n"

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
            check_user_is_in_baits(username=message.author.name)
            success, bait_bought, reason = buy_baits(username=message.author.name, bait=int(follow.content))
        except ex.ItemNotFound as e:
            raise e
        except ValueError:
            raise ex.ItemNotFound("Bait not found!!", error_code=1002)

        if not success:
            await follow.reply(f"Coult not buy net because {reason}")
        else:
            await follow.reply(f"Successfully bought {bait_bought}!")

    async def get_fish(self, message: discord.Message):
        class fish_indicies(Enum):
            USERNAME = 0
            LARGE_COMMON_FISH = 1
            LARGE_SHINY_FISH = 2
            LARGE_LEGENDARY_FISH = 3
            MEDIUM_COMMON_FISH = 4
            MEDIUM_SHINY_FISH = 5
            MEDIUM_LEGENDARY_FISH = 6
            SMALL_COMMON_FISH = 7
            SMALL_SHINY_FISH = 8
            SMALL_LEGENDARY_FISH = 9

        fish = get_fish_caught(message.author.name)
        send = f"""This is a list of the fish you caught:
Large common fish: {fish[fish_indicies.LARGE_COMMON_FISH.value]}
Large shiny fish: {fish[fish_indicies.LARGE_SHINY_FISH.value]}
Large legendary fish: {fish[fish_indicies.LARGE_LEGENDARY_FISH.value]}
Medium common fish: {fish[fish_indicies.MEDIUM_COMMON_FISH.value]}
Medium shiny fish: {fish[fish_indicies.MEDIUM_SHINY_FISH.value]}
Medium legendary fish: {fish[fish_indicies.MEDIUM_LEGENDARY_FISH.value]}
Small common fish: {fish[fish_indicies.SMALL_COMMON_FISH.value]}
Small shiny fish: {fish[fish_indicies.SMALL_SHINY_FISH.value]}
Small legendary fish: {fish[fish_indicies.SMALL_LEGENDARY_FISH.value]}
"""
        await message.reply(send)
