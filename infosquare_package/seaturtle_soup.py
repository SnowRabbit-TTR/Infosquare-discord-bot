"""
Sea turtle soup supporter
=====
author: Snow Rabbit
"""

import discord
from discord.channel import TextChannel
from discord.member import Member
from discord.message import Message
from discord.reaction import Reaction
from discord.user import ClientUser

from . import embed_color


class SeaTurtleSoupListner:

    def __init__(self, bot_user: ClientUser) -> None:
        self.supporter = SeaTurtleSoupSupporter(bot_user=bot_user)

    
    async def listen_command(self, message: Message) -> None:
        if not isinstance(message.channel, TextChannel):
            return
        
        # Start the game of sea turtle soup.
        if message.content.lower() in ["/umigame", "/startumigame"]:
            if self.supporter.is_playing:
                info_string = f"現在の出題者は{self.supporter.master['name']}さんです。\n出題者を変更する場合は、`/stop umigame`を入力して一度ゲームを終了してください。"
                info_message = await message.channel.send(info_string)
                await info_message.delete(delay=30)
            else:
                await self.supporter.start_game(message)

        # Stop the game.
        elif message.content.replace(" ", "").lower() == "/stopumigame":
            if self.supporter.is_playing:
                await self.supporter.stop_game(message)
        
        # Make reaction to question messages.
        elif message.content.endswith(("？", "?")):
            conditions = [self.supporter.is_playing,
                          message.channel.id == self.supporter.menu_message.channel.id]
            if all(conditions):
                await self.supporter.make_reaction(message)


    async def listen_reaction(self, reaction: Reaction, user: Member) -> bool:
        # Respond
        respond_list = ["⭕", "❌", "🤨"]
        if str(reaction) in respond_list:
            conditions = [self.supporter.is_playing,
                          reaction.message.id in self.supporter.questions]
            if all(conditions):
                if user.id == self.supporter.master["id"]:
                    await self.supporter.respond(reaction)
                return True
        return False


class SeaTurtleSoupSupporter:
    
    def __init__(self, bot_user: ClientUser) -> None:
        self.bot_user = bot_user
        self.embed_color = embed_color.SEATURTLESOUP_COLOR
        self.master = {"id": None, "name": ""}
        self.is_playing = False
        self.menu_message = None
        self.questions = {}


    async def start_game(self, message: Message) -> None:
        if self.is_playing:
            info_string = f"現在の出題者は{self.master['name']}さんです。\n出題者を変更する場合は、`/stop umigame`を入力して一度ゲームを終了してください。"
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)
            return

        self.is_playing = True
        master_id = message.author.id
        master_name = message.author.nick if message.author.nick is not None else message.author.name
        self.master = {"id": master_id, "name": master_name}

        info_string = f"問題の出題者を** {self.master['name']} **さんに設定しました。\n" + \
                      "質問者は語尾に「？」をつけて質問してください。\n" + \
                      "その質問に対してリアクションが付きます。\n" + \
                      f"\n{self.master['name']}さんは質問に対して、\n" + \
                      "　:o: ： **はい**\n" + \
                      "　:x: ： **いいえ**\n" + \
                      "　:face_with_raised_eyebrow: ： **どちらともいえない・関係ない**\n" + \
                      "のいずれかを押して回答してください。\n" + \
                      "\nゲームを終了するには`/stop umigame`を入力してください。"

        menu_embed = discord.Embed(title="**ウミガメのスープ**", color=self.embed_color)
        menu_embed = menu_embed.add_field(name="ゲーム開始", value=info_string)

        self.menu_message = await message.channel.send(embed=menu_embed)
        #await self.menu_message.add_reaction("👋")  # TODO: Break the game from reaction buttons.


    async def stop_game(self, message: Message) -> None:
        await self.menu_message.delete()
        self.menu_message = None
        self.is_playing = False

        info_string = "ウミガメのスープのゲームを終了しました。\n新しくゲームを始めるには、出題者が`/umigame`を入力してください。"
        await message.channel.send(info_string)

    
    async def make_reaction(self, message: Message) -> None:
        if self.is_playing == False:
            return
        if message.channel.id != self.menu_message.channel.id:
            return
        
        self.questions[message.id] = message
        await message.add_reaction("⭕")
        await message.add_reaction("❌")
        await message.add_reaction("🤨")

    
    async def respond(self, reaction: Reaction) -> None:
        reaction_list = ["⭕", "❌", "🤨"]
        for r in reaction_list:
            if str(r) != str(reaction):
                await reaction.message.remove_reaction(r, self.bot_user)

        del self.questions[reaction.message.id]
