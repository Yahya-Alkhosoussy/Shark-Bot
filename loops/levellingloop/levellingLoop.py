import logging, requests, discord
import utils.read_Yaml as RY
import SQL.levellingSQL.levellingSQL as ls
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from pathlib import Path

# ================== LOGGING AND CONFIG ===================
handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="a")
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(handler)

CONFIG_PATH = Path(r"loops\levellingloop\levelingConfig.yaml")
config = RY.read_config(CONFIG_PATH)

# ============== CREATING THE IMAGE ============
async def create_rank_card(user: discord.Member, rank: int, level: int, xp: int, xp_needed: int) -> discord.File:
    """
    Docstring for create_rank_card
    
    :param user: This is the person's discord user which will include information like their username and profile picture
    :type user: discord.Member
    :param rank: This is their rank on a leaderboard
    :type rank: int
    :param level: This is their level
    :type level: int
    :param xp: This is how much XP they gained
    :type xp: int
    :param xp_left_needed: This is how much XP is needed for the next level
    :type xp_left_needed: int
    """

    # Create a blank image
    black: tuple = (0, 0, 0)
    img = Image.open(r"loops\levellingloop\images\leveling up background.png")
    img = img.convert("RGBA")
    draw = ImageDraw.Draw(img) # Creates the drawing tool that will be working on the image

    profile_picture_url = user.display_avatar.url
    response = requests.get(profile_picture_url) # gets the image from the web
    profile_picture = Image.open(BytesIO(response.content)) # This opens the image as a PIL image object and doesn't download the image, as BytesIO stores it in memory
    profile_picture = profile_picture.resize(size=(192, 179))

    # Make the profile picture circular
    mask = Image.new(mode='L', size=(192, 179), color=0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse(xy=(0, 0, 192, 179), fill=255) # xy is in the format of x1, y1, x2, y2

    # Past the profile picture into the card
    img.paste(im=profile_picture, box=(79, 49), mask=mask)

    # Create overlay
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # colours in RGB
    skin_white: tuple = (255, 240, 236, 128) #RGB then opacity
    purple: tuple = (182, 59, 150, 255)
    grey: tuple = (60, 60, 60, 229)

    # draw opaque background behind rank and level
    level_x, level_y = 565, 75
    level_width, level_height = 220, 44
    overlay_draw.rectangle(xy=[level_x, level_y, level_x + level_width, level_y + level_height], fill=skin_white, outline=purple)

    rank_x, rank_y = 620, 15
    rank_width, rank_height = 165, 46
    overlay_draw.rectangle(xy=[rank_x, rank_y, rank_x + rank_width, rank_y + rank_height], fill=skin_white, outline=purple)

    # Draw the background of the progress bar
    bar_x, bar_y = 333, 138
    bar_width, bar_height = 451, 51
    overlay_draw.rectangle(xy=[bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], fill=grey )

    # compose it into the main image
    img = Image.alpha_composite(img, overlay)

    # Load fonts
    try: 
        font_large = ImageFont.truetype(font=r"loops\levellingloop\Fonts\arial.ttf", size=40)
        font_medium = ImageFont.truetype(font=r"loops\levellingloop\Fonts\arial.ttf", size=30)
        font_small = ImageFont.truetype(font=r"loops\levellingloop\Fonts\arial.ttf", size=20)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()
        logging.warning(f"[LEVELING SYSTEM] Unable to load font 'arial.ttf' using default.")

    # to be able to place the text on the background
    draw = ImageDraw.Draw(img)

    # Draw rank and level
    draw.text(xy=(650, 30), text=f"RANK #{rank}", fill=purple, font=font_small)
    draw.text(xy=(600, 80), text=f"LEVEL {level}", fill=purple, font=font_medium)

    # # Draw XP 
    # draw.text(xy=(750, 120), text=f"{xp:,}", fill=purple, font=font_medium) # the ':,' makes it a 1000 comma separator
    
    

    # draw progress bar filled
    progress = xp / xp_needed
    fill_width = int(bar_width * progress)
    draw.rectangle(xy=[bar_x, bar_y, bar_x + fill_width, bar_y + bar_height], fill=purple)

    # Save to BytesIO to send as discord file
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return discord.File(buffer, filename='rank_card.png')

# ============= LEVEL ROLES ===================
ROLES: dict = config.get("level roles")
ROLES_SHARK_SQUAD: dict = ROLES.get("shark squad")
# ============== LOOP LOGIC ===================
class levelingLoop:
    
    def __init__(self, bot):
        self.bot = bot

    async def add_users(self, user: discord.Member):
        return ls.add_user(username=user.name)

    async def add_role(self, user: discord.Member):
        level, _, _, _ = ls.get_info(username=user.name)
        
        
        level_role_id = ROLES_SHARK_SQUAD.get(f"level {level}")
        role = user.guild.get_role(level_role_id)
        if role is None:
            if level <= 5:
                logging.warning(f"[LEVELLING SYSTEM] ROLE 'level {level}' is not registered for guild {user.guild.name}")
            return
        
        try:
            await user.add_roles(role)
            logging.info(f"Added role {role} to {user.name}")
        except discord.HTTPException:
            logging.error("No can do, HTTPException")
            return

    
    async def message_handle(self, message: discord.Message):
        config = RY.read_config(CONFIG_PATH) # This is here too just so it can check for live changes
        boost_event  = config.get("boost")
        print(boost_event)
        boost_amount = config.get("boost amount")
        print(boost_amount)

        username = message.author.name

        # Make sure the user is added to the database
        ls.add_user(username=username)
        
        # Add to the user's level
        ls.add_to_level(username=username, boost=boost_event, boost_amount=boost_amount)

        leveled_up = ls.check_level(username=username) # leveled_up is a boolean and level is an integer

        if leveled_up:
            level, exp, exp_needed, rank = ls.get_info(username=username)
            card = await create_rank_card(user=message.author, rank=rank, level=level, xp=exp, xp_needed=exp_needed)
            channel = message.channel
            message_to_send: str | None
            if level == 1:
                message_to_send = f"""_Weaving through sunlit coral gardens where each wave catches the light, you enter the Shimmering Shallow Reefs._
Keep swimming and chatting — the sparkling waters of the Kelp Forest are just ahead. You now have more areas to explore! {message.author.mention}"""
            elif level == 2:
                message_to_send = f"""_Mid-depth currents sway the kelp, and tiny flecks of light dance across the water._
Swim a little further and you'll find your way into the wide, open ocean - so many new friends! {message.author.mention}"""
            elif level == 3:
                message_to_send = f"""These waters are vast, the currents gentle but sparkling all around you._
Every movement leaves a trail of glittering ripples.
Keep exploring — the Twilight Zone waits. {message.author.mention}"""
            elif level == 4:
                message_to_send = f"""_Sunlight fades, but you see tiny bioluminescent glimmers dance along the darkened waves before you._
Chat, swim, and level up to reach the Abyssal Deep, the ocean's most secret and glittering depths. {message.author.mention}"""
            elif level == 5:
                message_to_send = f"""_You've reached the deepest glittering waters, where rare and magical creatures dwell. A siren's song beckons from down in the deep._
The currents here shimmer with bioluminescent magic — irl-pics, selfies, venting, and more are now unlocked.
Swim thoughtfully, respect the depths, and enjoy your sparkling new habitat. {message.author.mention}"""
            else:
                message_to_send = None

            await self.add_role(message.author)

            if message_to_send is not None:
                await channel.send(message_to_send, file=card)
    
    async def check_level(self, message: discord.Message):
        username = message.author.name
        level, exp, exp_needed, rank = ls.get_info(username=username)

        card = await create_rank_card(user=message.author, rank=rank, level=level, xp=exp, xp_needed=exp_needed)

        await message.reply(f"You currently are level {level} with {exp} xp and here's your card!", file=card)

            
