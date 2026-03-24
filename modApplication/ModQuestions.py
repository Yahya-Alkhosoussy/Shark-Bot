import asyncio

import discord

from modApplication.CloseButton import CloseButton


class ModQuestions:
    def __init__(self, bot: discord.Client, channel: discord.TextChannel | None):
        self.bot = bot
        self.channel = channel

        self.questions = [
            "What is your twitch username?",
            "What days are you available on? (Send all applicable letters. I.E 'A B' for Monday and tuesday, or 'A C F' for Monday Wednesday and Saturday)",  # noqa: E501
            "Are you open to community projects? This can include leading specific games, creating events, movie nights, etc. (Y/N or Yes/No)",  # noqa: E501
            "Are you looking to mod primarily discord, live stream, or both?",
            "How often would you say you engage with the community on twitch or in discord?",
            "We do allow sensitive topics like religion, politics, sexuality, gender, etc. in the appropriate channels. Mods are expected to be available even for uncomfortable topics, and to intervene when needed. Are you willing to moderate potentially uncomfortable topics and remained unbiased? (Y/N or Yes/No)",  # noqa: E501
            "Have you worked as a twitch/discord moderator before? (Y/N or Yes/No)",
            "Do you consider yourself a person who can handle things quickly, and be confident in their decisions when provided adequate resources and a team? (Y/N or Yes/No)",  # noqa: E501
            "Many people are fine handling positive interactions but freeze or disappear when they have to handle a negative interaction. Will you be able to handle yourself in a mature way and keep an open line of dialogue, even if the subject is uncomfortable? (Y/N or Yes/No)",  # noqa: E501
            "Abuse of power/making decisions without others/overriding other mods can lead to immediate termination of your role, and if bad enough, a ban. Is that understood? (Y/N or Yes/No)",  # noqa: E501
            "Certain behaviors are expected of mods such as handling disagreements privately, being available for individuals to ask questions, not allowing yourself to be dragged into an argument/shit storm in chat, etc. Can you hold yourself to that standard? (Y/N or Yes/No)",  # noqa: E501
            "Finally, why do you want to mod for Shark?",
        ]
        self.multiple_choice: dict[int, dict[str, str]] = {  # question dict[question index, dict[letter, answer]]
            2: {
                "A": "Monday",
                "B": "Tuesday",
                "C": "Wednesday",
                "D": "Thursday",
                "E": "Friday",
                "F": "Saturday",
                "G": "Sunday",
            },
            4: {"A": "Discord", "B": "Twitch", "C": "Both"},
            5: {
                "A": "Multiple times a day",
                "B": "Atleast once a day",
                "C": "Several times a week",
                "D": "a couple times a week",
                "E": "Not frequently at all",
            },
        }

    async def send_questions(self, channel: discord.TextChannel | None):
        if self.channel is None and channel is not None:
            self.channel = channel

        assert self.channel

        bot = self.bot.user
        assert bot
        await self.channel.send("""Before you start your application, make sure to read every question carefully.
For open ended questions you will have 60 seconds to write your answers, and please send it all in one message or it will confuse the bot.""")  # noqa: E501
        await self.channel.send(
            "Starting your mod application now. Spider has access to this channel so feel free to @ him if needed"
        )

        for question, i in zip(self.questions, range(1, len(self.questions) + 1)):
            # check if it's multiple choice:
            choices = self.multiple_choice.get(i)
            if choices:  # if choices are available
                while True:
                    # question is multiple choice
                    if i != 2:
                        message = question + "\nChoose one of the following:"
                    else:
                        message = question

                    for letter, choice in zip(choices.keys(), choices.values()):
                        message += f"\n{letter}: {choice}"

                    await self.channel.send("You have 2 minutes to choose: \n" + message)

                    def check(m: discord.Message) -> bool:
                        letters = ["A", "B", "C", "D", "E", "F", "G"]
                        if i == 2:
                            selections = m.content.upper().split()  # Split By White space
                            return m.author.id != bot.id and len(selections) >= 1 and all(s in letters for s in selections)
                        selection = m.content.upper()
                        return m.author.id != bot.id and len(selection) == 1 and selection in letters

                    try:
                        follow = await self.bot.wait_for("message", check=check, timeout=120)
                    except asyncio.TimeoutError:
                        await self.channel.send("Timed out, try again with `?Apply`")
                        return

                    if i == 2:
                        new_selection = []
                        for key in follow.content.upper().split():
                            new_selection.append(choices.get(key))
                        message = "To confirm, You are available on the following days: " + ", ".join(new_selection)

                        message += "\nSend Y for yes and N for no"
                        await self.channel.send(message)
                    else:
                        selection = choices.get(follow.content)
                        await self.channel.send(
                            f"To confirm, you chose '{selection}' as your answer(s). Send Y for yes and N for no"
                        )

                    def confirm_Y_N(m: discord.Message) -> bool:
                        return m.author.id != bot.id and (m.content.upper() == "Y" or m.content.upper() == "N")

                    try:
                        confirmation = await self.bot.wait_for("message", check=confirm_Y_N, timeout=120)
                    except asyncio.TimeoutError:
                        await self.channel.send("Timed out, try again with `?Apply`")
                        return

                    if confirmation.content.upper() == "N":
                        await self.channel.send("I will ask the question again.")
                    else:
                        break
            elif "Y/N" in question:  # yes or no
                while True:
                    await self.channel.send(question)

                    def check_Y_N(m: discord.Message) -> bool:
                        return m.author.id != bot.id and (
                            (m.content.upper() == "Y" or m.content.upper() == "N")
                            or (m.content.upper() == "YES" or m.content.upper() == "NO")
                        )

                    try:
                        follow = await self.bot.wait_for("message", check=check_Y_N, timeout=120)
                    except asyncio.TimeoutError:
                        await self.channel.send("Timed out, try again with `?Apply`")
                        return

                    if follow.content.lower() == "yes" or follow.content.lower() == "no":
                        answer = follow.content
                    elif follow.content.lower() == "y":
                        answer = "Yes"
                    else:
                        answer = "No"

                    await self.channel.send(f"To confirm you answered '{answer}' right? If yes then send Y, if not send N")

                    def confirm_Y_N(m: discord.Message) -> bool:
                        return m.author.id != bot.id and (m.content.upper() == "Y" or m.content.upper() == "N")

                    try:
                        confirmation = await self.bot.wait_for("message", check=confirm_Y_N, timeout=120)
                    except asyncio.TimeoutError:
                        await self.channel.send("Timed out, try again with `?Apply`")
                        return

                    if confirmation.content.upper() == "N":
                        await self.channel.send("I will ask the question again.")
                    elif i == 7:
                        while True:
                            await self.channel.send("how did you support the streamer/community?")

                            def check(m: discord.Message) -> bool:
                                return m.author.id != bot.id

                            try:
                                follow = await self.bot.wait_for("message", check=check, timeout=120)
                            except asyncio.TimeoutError:
                                await self.channel.send("Timed out, try again with `?Apply`")
                                return

                            await self.channel.send(
                                f"To confirm you answered '{follow.content}' right? If yes then send Y, if not send N"
                            )

                            def confirm_Y_N(m: discord.Message) -> bool:
                                return m.author.id != bot.id and (m.content.upper() == "Y" or m.content.upper() == "N")

                            try:
                                confirmation = await self.bot.wait_for("message", check=confirm_Y_N, timeout=120)
                            except asyncio.TimeoutError:
                                await self.channel.send("Timed out, try again with `?Apply`")
                                return

                            if confirmation.content.upper() == "N":
                                await self.channel.send("I will ask the question again.")
                            else:
                                break
                        break
                    else:
                        break

            else:  # open ended
                while True:
                    await self.channel.send(question)

                    def check(m: discord.Message) -> bool:
                        return m.author.id != bot.id

                    try:
                        follow = await self.bot.wait_for("message", check=check, timeout=120)
                    except asyncio.TimeoutError:
                        await self.channel.send("Timed out, try again with `?Apply`")
                        return

                    await self.channel.send(
                        f"To confirm you answered '{follow.content}' right? If yes then send Y, if not send N"
                    )

                    def confirm_Y_N(m: discord.Message) -> bool:
                        return m.author.id != bot.id and (m.content.upper() == "Y" or m.content.upper() == "N")

                    try:
                        confirmation = await self.bot.wait_for("message", check=confirm_Y_N, timeout=120)
                    except asyncio.TimeoutError:
                        await self.channel.send("Timed out, try again with `?Apply`")
                        return

                    if confirmation.content.upper() == "N":
                        await self.channel.send("I will ask the question again.")
                    else:
                        break

        await self.channel.send(
            "Thank you for filling in the application. You can choose to submit it now or use `?Apply` to reapply and change your answers"  # noqa
        )

        embed = discord.Embed(
            description="Do you want to submit or delete?",  # ticket welcome message  # noqa: E501
            color=discord.colour.Color.blue(),
        )
        await self.channel.send(embed=embed, view=CloseButton(bot=self.bot))
