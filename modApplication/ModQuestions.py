import discord
import asyncio

class ModQuestions:
    def __init__(self, bot: discord.Client, channel: discord.TextChannel):
        self.bot = bot
        self.channel = channel

        self.questions = [
            "What is your twitch username?",
            "What days are you available on? (Send all applicable letters. I.E 'A B' for Monday and tuesday, or 'A C F' for Monday Wednesday and Saturday)",
            "Are you open to community projects? This can include leading specific games, creating events, movie nights, etc. (Y/N or Yes/No)",
            "Are you looking to mod primarily discord, live stream, or both?",
            "How often would you say you engage with the community on twitch or in discord?",
            "We do allow sensitive topics like religion, politics, sexuality, gender, etc. in the appropriate channels. Mods are expected to be available even for uncomfortable topics, and to intervene when needed. Are you willing to moderate potentially uncomfortable topics and remained unbiased? (Y/N or Yes/No)",
            "Have you worked as a twitch/discord moderator before? If yes, how did you support the streamer/community? (Y/N or Yes/No)",
            "Do you consider yourself a person who can handle things quickly, and be confident in their decisions when provided adequate resources and a team? (Y/N)",
            "Many people are fine handling positive interactions but freeze or disappear when they have to handle a negative interaction. Will you be able to handle yourself in a mature way and keep an open line of dialogue, even if the subject is uncomfortable? (Y/N or Yes/No)",
            "Abuse of power/making decisions without others/overriding other mods can lead to immediate termination of your role, and if bad enough, a ban. Is that understood? (Y/N or Yes/No)",
            "Certain behaviors are expected of mods such as handling disagreements privately, being available for individuals to ask questions, not allowing yourself to be dragged into an argument/shit storm in chat, etc. Can you hold yourself to that standard? (Y/N or Yes/No)",
            "Finally, why do you want to mod for Shark?"
        ]
        self.multiple_choice: dict[int, dict[str, str]] = { # question dict[question index, dict[letter, answer]]
            2: {"A. ": "Monday", "B.": "Tuesday", "C.": "Wednesday", "D.": "Thursday", "E.": "Friday", "F.": "Saturday", "G.": "Sunday"},
            4: {"A.": "Discord", "B.": "Twitch", "C.": "Both"},
            5: {"A.": "Multiple times a day", "B.": "Atleast once a day", "C.": "Several times a week", "D.": "a couple times a week", "E.": "Not frequently at all"}
        }
    
    async def send_questions(self) -> bool:
        bot = self.bot.user
        assert bot

        for question, i in zip(self.questions, range(len(self.questions))):
            # check if it's multiple choice:
            choices = self.multiple_choice.get(i)
            if choices: # if choices are available
                # question is multiple choice
                if i != 2:
                    message = question + "\nChoose one of the following:"
                else:
                    message = question

                for letter, choice in zip(choices.keys(), choices.values()):
                    message += f"\n{letter}: {choice}"
                
                await self.channel.send(message)

                def check(m: discord.Message) -> bool:
                    letters = ["A", "B", "C", "D", "E", "F", "G"]
                    if i == 2:
                        selections = m.content.upper().split() # Split By White space
                        return(
                            m.author.id != bot.id 
                            and len(selections) >= 1
                            and all(s in letters for s in selections)
                        )
                    selection = m.content.upper()
                    return(
                        m.author.id != bot.id
                        and len(selection) == 1
                        and all(s in letters for s in selection)
                    )
                    
                try:
                    follow = await self.bot.wait_for("message", check=check, timeout=60)
                except asyncio.TimeoutError:
                    await self.channel.send("Timed out, try again with `?Apply`")
                    return False
                
        return True