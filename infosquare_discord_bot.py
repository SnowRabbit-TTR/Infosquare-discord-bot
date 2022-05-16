import os
from datetime import datetime, timedelta, timezone

import discord
from discord.channel import DMChannel, TextChannel
from discord.ext import tasks

from infosquare_package.autodelete import AutoDeleteListner
from infosquare_package.connect4 import Connect4Listner
from infosquare_package.info_tracker import (DistrictTracker,
                                             FieldOfficeTracker,
                                             HQGroupTracker, InvasionTracker,
                                             ServerTracker)
from infosquare_package.minesweeper import MinesweeperListner
from infosquare_package.seaturtle_soup import SeaTurtleSoupListner
from infosquare_package.wordwolf import WordWolfListner


TOKEN = os.environ["INFOSQUARE_BOT_TOKEN"]
DISTRICT_CHANNEL_ID = int(os.environ["DISTRICT_CHANNEL_ID"])
INVASION_CHANNEL_ID = int(os.environ["INVASION_CHANNEL_ID"])
SERVER_CHANNEL_ID = int(os.environ["SERVER_CHANNEL_ID"])
FIELDOFFICE_CHANNEL_ID = int(os.environ["FIELDOFFICE_CHANNEL_ID"])
HQGROUP_CHANNEL_ID = int(os.environ["HQGROUP_CHANNEL_ID"])
DEBUG_ID = int(os.environ["DEBUG_ID"])
RENEW_INFO_INTERVAL = 10

intents = discord.Intents.all()
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    global autodelete_listner, connect4_listner, minesweeper_listner, seaturtle_listner, wordwolf_listner

    autodelete_listner = AutoDeleteListner()
    connect4_listner = Connect4Listner(bot_user=client.user)
    minesweeper_listner = MinesweeperListner()
    seaturtle_listner = SeaTurtleSoupListner(bot_user=client.user)
    wordwolf_listner = WordWolfListner()

    global district_tracker, fieldoffice_tracker, hqgroup_tracker, invasion_tracker, server_tracker

    district_tracker = DistrictTracker(info_channel=client.get_channel(DISTRICT_CHANNEL_ID),
                                       bot_user=client.user)
    fieldoffice_tracker = FieldOfficeTracker(info_channel=client.get_channel(FIELDOFFICE_CHANNEL_ID),
                                             bot_user=client.user)
    hqgroup_tracker = HQGroupTracker(info_channel=client.get_channel(HQGROUP_CHANNEL_ID),
                                     bot_user=client.user)
    invasion_tracker = InvasionTracker(info_channel=client.get_channel(INVASION_CHANNEL_ID),
                                       bot_user=client.user)
    server_tracker = ServerTracker(info_channel=client.get_channel(SERVER_CHANNEL_ID), 
                                   bot_user=client.user)
                                             
    renew_infomation.start()
    countdown.start()

    print("Login suceeded.")


@tasks.loop(seconds=RENEW_INFO_INTERVAL)
async def renew_infomation():
    await district_tracker.notice()
    await server_tracker.notice()
    await fieldoffice_tracker.notice()
    await hqgroup_tracker.notice()
    invasion_tracker.load_information()


@tasks.loop(seconds=1)
async def countdown():
    await invasion_tracker.countdown(interval=1)


@client.event
async def on_message(message):

    # Confirm the message isn't sended from a bot.
    if message.author.bot:
        return
    
    # Auto message delete app
    await autodelete_listner.listen_command(message)

    # Find four (Connect 4)
    await connect4_listner.listen_command(message)

    # Minesweeper
    await minesweeper_listner.listen_command(message)

    # Sea turtle soup supporter
    await seaturtle_listner.listen_command(message)

    # Word wolf
    await wordwolf_listner.listen_command(message)

    # Debug
    if isinstance(message.channel, DMChannel):
        sended_time = datetime.now(timezone(timedelta(hours=+9), "JST")).strftime("%Y/%m/%d %H:%M:%S")
        debugger = await client.fetch_user(user_id=DEBUG_ID)
        await debugger.send(f"{sended_time}\n**{message.author}**\n{message.content}")


@client.event
async def on_reaction_add(reaction, user):

    # Confirm the reaction isn't sended from a bot.
    if user.bot:
        return

    channel = reaction.message.channel
    flags = []

    # Find four (Connect 4)
    flags.append(await connect4_listner.listen_reaction(channel, reaction, user))

    # Sea turtle soup
    flags.append(await seaturtle_listner.listen_reaction(reaction, user))

    # Word wolf
    flags.append(await wordwolf_listner.listen_reaction(reaction, user))

    try:
        # Bot cannot remove reactions sended by user on DMChannel :(
        if isinstance(channel, TextChannel) and any(flags):
            await reaction.remove(user)
    except:
        # TODO: Write exception handling.
        pass


# Start this bot and connect the surver.
client.run(TOKEN)
