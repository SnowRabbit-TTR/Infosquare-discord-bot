"""
Sea turtle soup supporter
=====
author: Snow Rabbit
"""

import discord
from discord.member import Member
from discord.message import Message
from discord.reaction import Reaction
from discord.user import ClientUser

from . import embed_color


class SeaTurtleSoupSupporter:
    
    def __init__(self, bot_user: ClientUser) -> None:
        self.bot_user = bot_user
        self.embed_color = embed_color.SEATURTLESOUP_COLOR
        self.master = {"id": None, "name": ""}
        self.is_playing = False
        self.menu_message = None
        self.questions = {}


    async def start_game(self, message: Message) -> None:
        if self.is_playing == True:
            info_string = f"現在の出題者は{self.master['name']}さんです。\n出題者を変更する場合は、`/stop umigame`を入力して一度ゲームを終了してください。"
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)
            return

        self.is_playing = True
        master_id = message.author.id
        master_name = message.author.nick if message.author.nick is not None else message.author.name
        self.master = {"id": master_id, "name": master_name}

        info_string = f"問題の出題者を** {self.master['name']} **さんに設定しました。\n"
        info_string += "質問者は語尾に「？」をつけて質問してください。\n"
        info_string += "その質問に対してリアクションが付きます。\n"
        info_string += f"\n{self.master['name']}さんは質問に対して、\n"
        info_string += "　:o: ： **はい**\n"
        info_string += "　:x: ： **いいえ**\n"
        info_string += "　:face_with_raised_eyebrow: ： **どちらともいえない・関係ない**\n"
        info_string += "のいずれかを押して回答してください。\n"
        info_string += "\nゲームを終了するには`/stop umigame`を入力してください。"

        menu_embed = discord.Embed(title="**ウミガメのスープ**", color=self.embed_color)
        menu_embed = menu_embed.add_field(name="ゲーム開始", value=info_string)

        self.menu_message = await message.channel.send(embed=menu_embed)
        #await self.menu_message.add_reaction("👋")  # TODO: Break the game from reaction buttons.


    async def stop_game(self, message: Message) -> None:
        if self.is_playing == False:
            return
        
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

    
    async def respond(self, reaction: Reaction, user: Member) -> None:
        reaction_list = ["⭕", "❌", "🤨"]
        if self.is_playing == False:
            return
        if reaction.message.id not in self.questions:
            return
        if user.id != self.master["id"] or str(reaction) not in reaction_list:
            await reaction.remove(user)
            return

        for r in reaction_list:
            if str(r) != str(reaction):
                await reaction.message.remove_reaction(r, self.bot_user)

        del self.questions[reaction.message.id]
