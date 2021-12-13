import os
from datetime import datetime, timedelta, timezone

import discord
from discord.channel import DMChannel, TextChannel
from discord.ext import tasks

from infosquare_package.autodelete import AutoDeleteObserver
from infosquare_package.connect4 import Connect4GameMaster
from infosquare_package.info_tracker import (DistrictTracker,
                                             FieldOfficeTracker,
                                             InvasionTracker, ServerTracker)
from infosquare_package.minesweeper import MinesweeperGameMaster
from infosquare_package.seaturtle_soup import SeaTurtleSoupSupporter
from infosquare_package.wordwolf import WordWolfGameMaster


TOKEN = os.environ["INFOSQUARE_BOT_TOKEN"]
DISTRICT_CHANNEL_ID = int(os.environ["DISTRICT_CHANNEL_ID"])
INVASION_CHANNEL_ID = int(os.environ["INVASION_CHANNEL_ID"])
SERVER_CHANNEL_ID = int(os.environ["SERVER_CHANNEL_ID"])
FIELDOFFICE_CHANNEL_ID = int(os.environ["FIELDOFFICE_CHANNEL_ID"])
DEBUG_ID = int(os.environ["DEBUG_ID"])
RENEW_INFO_INTERVAL = 10

client = discord.Client()

autodelete_observer = AutoDeleteObserver()
connect4_gamemaster = Connect4GameMaster()
minesweeper_gamemaster = MinesweeperGameMaster()
wordwolf_gamemaster = WordWolfGameMaster()


@client.event
async def on_ready():
    global district_tracker, invasion_tracker, server_tracker, fieldoffice_tracker, seaturtle_supporter

    district_tracker = DistrictTracker(info_channel=client.get_channel(DISTRICT_CHANNEL_ID),
                                       bot_user=client.user)
    invasion_tracker = InvasionTracker(info_channel=client.get_channel(INVASION_CHANNEL_ID),
                                       bot_user=client.user)
    server_tracker = ServerTracker(info_channel=client.get_channel(SERVER_CHANNEL_ID), 
                                   bot_user=client.user)
    fieldoffice_tracker = FieldOfficeTracker(info_channel=client.get_channel(FIELDOFFICE_CHANNEL_ID),
                                             bot_user=client.user)
    seaturtle_supporter = SeaTurtleSoupSupporter(bot_user=client.user)

    renew_infomation.start()
    countdown.start()

    print("Login suceeded.")


@tasks.loop(seconds=RENEW_INFO_INTERVAL)
async def renew_infomation():
    await district_tracker.notice()
    await server_tracker.notice()
    await fieldoffice_tracker.notice()
    invasion_tracker.load_information()


@tasks.loop(seconds=1)
async def countdown():
    await invasion_tracker.countdown(interval=1)


@client.event
async def on_message(message):

    # Confirm the message isn't sended from a bot.
    if message.author.bot:
        return
    
    # Watch only message sended on TextChannel.
    # Target: Autodelete app, Minesweeper, Find 4, and Word wolf.
    if isinstance(message.channel, TextChannel):

        """
        Auto message delete app
        =====
        author: Snow Rabbit
        """
        # Stop auto delete app.
        if message.content.replace(" ", "").lower() == "/stopautodelete":
            await autodelete_observer.stop_autodelete(message)

        # Find the message of auto delete app user.
        await autodelete_observer.observe(message)

        # Start auto delete app.
        if message.content.startswith("/start autodelete"):
            await autodelete_observer.start_autodelete(message)


        """
        Minesweeper on TextChannel
        =====
        author: Snow Rabbit
        """
        if message.content in ["/minesweeper", "/Minesweeper", "/マインスイーパー", "/マインスイーパ", "/まいんすいーぱー", "/まいんすいーぱ"]:
            await minesweeper_gamemaster.start_new_game(message)

        
        """
        Find four (Connect 4)
        ===
        author: Snow Rabbit
        """
        # Make find four game group.
        if message.content.replace(" ", "").lower() in ["/findfour", "/find4", "/connectfour", "/connect4"]:
            await connect4_gamemaster.establish(message)

        # Hidden command to break find four game group.
        if message.content.replace(" ", "").lower() in ["/breakfindfour", "/breakfind4"]:
            await connect4_gamemaster.reset(message.channel)


        """
        Sea turtle soup supporter
        =====
        author: Snow Rabbit
        """
        # Start the game of sea turtle soup.
        if message.content.lower() in ["/umigame", "/startumigame"]:
            await seaturtle_supporter.start_game(message)

        # Stop the game.
        if message.content.replace(" ", "").lower() == "/stopumigame":
            await seaturtle_supporter.stop_game(message)
        
        # Make reaction to question messages.
        if message.content.endswith(("？", "?")):
            await seaturtle_supporter.make_reaction(message)


        """
        Word wolf
        =====
        author: Snow Rabbit
        """
        # Make word wolf game group.
        if message.content in ["/wordwolf", "/word wolf", "/Wordwolf", "/Word wolf", "/ワードウルフ", "/わーどうるふ"]:
            await wordwolf_gamemaster.establish(message)

        # Change the number of wolfs.
        # TODO: This command will be invoked from the reaction for menu message in the future.
        if message.content.startswith("/wolf"):
            await wordwolf_gamemaster.set_wolf_num(message)
    
        # Change available genres.
        # TODO: This command will be invoked from the reaction for menu message in the future.
        if message.content.startswith("/genre"):
            await wordwolf_gamemaster.set_available_genre(message)
        
        # Hidden command to break word wolf game group.
        if message.content.replace(" ", "").lower() == "/breakwordwolf":
            await wordwolf_gamemaster.reset(message.channel, breaker=message.author)


    # Watch only message sended on DMChannel.
    # Target: Minesweeper and Group Notificator (Temporally unusable).
    if isinstance(message.channel, DMChannel):

        """
        Minesweeper on DMChannel
        =====
        author: Snow Rabbit
        """
        if message.content in ["/minesweeper", "/Minesweeper", "/マインスイーパー", "/マインスイーパ", "/まいんすいーぱー", "/まいんすいーぱ"]:
            await minesweeper_gamemaster.start_new_game(message, in_dm_channel=True)

        sended_time = datetime.now(timezone(timedelta(hours=+9), "JST")).strftime("%Y/%m/%d %H:%M:%S")
        debugger = await client.fetch_user(user_id=DEBUG_ID)
        await debugger.send(f"{sended_time}\n**{message.author}**\n{message.content}")


@client.event
async def on_reaction_add(reaction, user):

    # Confirm the reaction isn't sended from a bot.
    if user.bot:
        return

    # Concern find four
    # HACK: Checking reaction method should be integrated.
    await connect4_gamemaster.join(reaction, user)
    await connect4_gamemaster.leave(reaction, user)
    await connect4_gamemaster.switch_player(reaction, user)
    await connect4_gamemaster.start_game(reaction, user)
    await connect4_gamemaster.push_board(reaction, user)
    await connect4_gamemaster.repeat_game_or_setting(reaction, user)

    # Concern sea turtle soup
    await seaturtle_supporter.respond(reaction, user)

    # Concern word wolf
    # HACK: Checking reaction method should be integrated.
    await wordwolf_gamemaster.join(reaction, user)
    await wordwolf_gamemaster.leave(reaction, user)
    await wordwolf_gamemaster.how_to_play_wordwolf(reaction, user)
    await wordwolf_gamemaster.start_game(reaction, user)
    await wordwolf_gamemaster.show_result(reaction, user)
    await wordwolf_gamemaster.continue_game(reaction, user)


# Start this bot and connect the surver.
client.run(TOKEN)
