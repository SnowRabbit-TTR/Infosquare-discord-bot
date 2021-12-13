"""
Word wolf
=====
author: Snow Rabbit
"""

import json
import random
import re
import string
from datetime import datetime
from typing import Dict, Optional, Tuple

import discord
from discord.channel import TextChannel
from discord.member import Member
from discord.message import Message
from discord.reaction import Reaction

from . import embed_color


class WordWolfGame:

    def __init__(self, players: list, wolf_num: int, available_genre: list) -> None:
        self.players = players
        self.wolf_num = wolf_num
        self.available_genre = available_genre
        self.all_questions, self.all_question_num = self.load_all_question()

        self.available_question_list = []
        self.selected_question_ids = []
        self.set_available_question()


    def load_all_question(self) -> Tuple[Dict, int]:
        json_file = "infosquare_package/data/wordwolf/question.json"

        with open(json_file, "r") as f:
            all_question = json.load(f)
        
        all_question_num = 0
        for genre in all_question:
            all_question_num += len(all_question[genre])
        
        return all_question, all_question_num

    
    def set_available_question(self) -> None:
        if not self.available_question_list:
            self.selected_question_ids = []

        self.available_question_list = []

        for genre in self.all_questions:
            if genre in self.available_genre:
                for question in self.all_questions[genre]:
                    if question["id"] not in self.selected_question_ids:
                        self.available_question_list.append(question)

    
    def generate_game(self) -> dict:
        # Select question.
        self.set_available_question()
        random.shuffle(self.available_question_list)
        question = self.available_question_list.pop(0)
        self.selected_question_ids.append(question["id"])
        words = question["words"]

        # Set citizen and wolf.
        shuffle_list = random.sample(self.players, len(self.players))
        wolfs = shuffle_list[:self.wolf_num]
        citizens = shuffle_list[self.wolf_num:]

        random.shuffle(words)
        wolf_word = words[0]
        citizen_word = words[1]

        setting = {}
        for w in wolfs:
            setting[w] = {"post": "wolf", "word": wolf_word}
        for c in citizens:
            setting[c] = {"post": "citizen", "word": citizen_word}

        return setting

    
    def set_players(self, players: list) -> None:
        self.players = players

    
    def set_wolf_num(self, wolf_num: int) -> None:
        self.wolf_num = wolf_num


    def set_available_genre(self, available_genre: list) -> None:
        self.available_genre = available_genre


    def get_available_genre(self) -> list:
        return self.available_genre
    
        
class WordWolfGameMaster:

    def __init__(self, players=[], wolf_num=1, available_genre=["food", "love", "life", "play"]) -> None:
        self.players = players
        self.wolf_num = wolf_num
        self.available_genre = available_genre
        self.embed_color = embed_color.WORDWOLF_COLOR

        self.is_playing = False
        self.is_ready = False
        self.registered_player = {}
        self.phase = "setting"
        self.menu_message = None
        self.start_thinking_message = None
        self.result_message = None
        self.how2play_message = None
        self.show_how2play_epochtime = None

        self.game_set = None
        self.wordwolf_game = WordWolfGame(players=players, wolf_num=wolf_num, available_genre=available_genre)


    async def establish(self, message: Message) -> None:
        if len(self.players) == 0:
            self.add_player(message.author)
            await self.show_menu(message.channel)
        else:
            info_string = "既にワードウルフのグループが設立されています。\nグループに参加する場合は、メニュー画面の:person_raising_hand:を押してください。"
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)


    async def show_menu(self, channel: TextChannel) -> None:
        self.is_playing = False
        self.phase = "setting"

        # About member
        info_string = "**------- 参加者 -------**\n"
        for member in self.registered_player.values():
            info_string += f"{member.nick if member.nick is not None else member.name}\n"
        if len(self.players) < 3:
            info_string += ":warning: __ゲームの開始には最低3人が必要です。__\n"
        info_string += f"\n人狼の数：{self.wolf_num}\n"
        if len(self.players) > 3 and self.check_wolf_num() == False:
            info_string += ":warning: __人狼の数が不正です。__\n"
        # About genre
        genres = {"food": "食べ物", "love": "恋愛", "life": "生活", "play": "遊び"}
        available_genre = self.wordwolf_game.get_available_genre()
        info_string += "\n**------- お題のジャンル -------**\n"
        for i, (k, v) in enumerate(genres.items()):
            info_string += f"{i+1}: {v}  {':white_check_mark:' if k in available_genre else ':x:'}\n"
        info_string += "\n"
        # About how to operate
        info_string += ":arrow_forward:：ゲームスタート\n"
        info_string += ":person_raising_hand:：グループに参加する\n"
        info_string += ":wave:：グループから抜ける\n"
        info_string += ":question:：ルール説明\n"
        info_string += "`/wolf 人狼の数`：人狼の人数を変更\n"
        info_string += "`/genre ジャンル番号`：お題のジャンルを変更\n\n"
        info_string += "----- ジャンル変更の入力例 -----\n"
        info_string += "'食べ物'のみ: `/genre 1`\n"
        info_string += "'恋愛'と'遊び': `/genre 24`"

        menu_embed = discord.Embed(title="**Word wolf** (beta)", color=self.embed_color)
        menu_embed = menu_embed.add_field(name="メニュー画面", value=info_string)
        if self.menu_message is None:
            self.menu_message = await channel.send(embed=menu_embed)
            await self.menu_message.add_reaction("▶️")
            await self.menu_message.add_reaction("🙋")
            await self.menu_message.add_reaction("👋")
            await self.menu_message.add_reaction("❓")
        else:
            await self.menu_message.edit(embed=menu_embed)


    async def join(self, reaction: Reaction, user: Member) -> None:
        if self.menu_message is None:
            return
        if reaction.message.id != self.menu_message.id:
            return
        if self.is_joined(user.id) == True:
            return
        if self.is_playing == True:
            return
        if self.phase != "setting":
            return
        if str(reaction) != "🙋":
            return
        
        self.add_player(user)
        await self.show_menu(reaction.message.channel)


    async def leave(self, reaction: Reaction, user: Member) -> None:
        if self.menu_message is None:
            return
        if reaction.message.id != self.menu_message.id:
            return
        if self.is_joined(user.id) == False:
            return
        if self.phase != "setting":
            return
        if self.is_playing == True:
            return       
        if str(reaction) != "👋":
            return
        
        self.remove_player(user)
        await self.show_menu(reaction.message.channel)

        if len(self.players) == 0:
            await self.reset(reaction.message.channel)
    

    async def start_game(self, reaction: Reaction, user: Member, recursive_channel: bool=None) -> None:
        if recursive_channel is None:
            if self.menu_message is None:
                return
            if reaction.message.id != self.menu_message.id:
                return
            if self.is_joined(user.id) == False:
                return
            if self.is_playing == True:
                return
            if str(reaction) != "▶️":
                return
            send_channel = self.menu_message.channel
        else:
            send_channel = recursive_channel

        if self.is_ready_for_game() == False:
            return

        self.phase = "discussion"
        self.is_playing = True
        hash_value = "".join(random.choices(string.ascii_letters + string.digits, k=7))
        hash_string = f"【Hash: {hash_value}】"
        self.game_set = self.wordwolf_game.generate_game()

        # Send the word to players by DM.
        for player_id, player_info in self.game_set.items():
            player = self.registered_player[player_id]
            player_name = player.nick if player.nick is not None else player.name
            word = player_info["word"]
            info_string = f"{player_name}さんのお題は\n**{word}**\nです。"
            word_notice_embed = discord.Embed(title="**Word wolf** (beta)", color=self.embed_color)
            word_notice_embed = word_notice_embed.add_field(name="お題確認", value=info_string)
            word_notice_embed = word_notice_embed.set_footer(text=hash_string)
            player_dm_channel = await player.create_dm()
            await player_dm_channel.send(embed=word_notice_embed)
        
        # Send the message about starting thinking.
        info_string = "参加者にダイレクトメッセージでお題を送信しました。\n"
        info_string += "お題を確認したら話し合いを行ない、人狼を決めてください。\n\n"
        info_string += "人狼を決定したら、:bulb:マークを押して結果を確認してください。"
        start_thinking_embed = discord.Embed(title="**Word wolf** (beta)", color=self.embed_color)
        start_thinking_embed = start_thinking_embed.add_field(name="議論スタート！", value=info_string)
        start_thinking_embed = start_thinking_embed.set_footer(text=hash_string)

        self.start_thinking_message = await send_channel.send(embed=start_thinking_embed)
        await self.start_thinking_message.add_reaction("💡")
    

    async def show_result(self, reaction: Reaction, user: Member) -> None:
        if self.start_thinking_message is None:
            return
        if reaction.message.id != self.start_thinking_message.id:
            return
        if self.is_joined(user.id) == False:
            return
        if str(reaction) != "💡":
            return
        if self.phase != "discussion":
            return
        
        self.phase = "result"
        send_channel = self.start_thinking_message.channel

        info_string = ""
        wolfs = []
        for player_id in self.players:
            player = self.registered_player[player_id]
            player_name = player.nick if player.nick is not None else player.name
            word = self.game_set[player_id]["word"]
            if self.game_set[player_id]["post"] == "wolf":
                post = ":wolf:"
                wolfs.append(f"**{player_name}**さん")
            else:
                post = ":bust_in_silhouette:"
            info_string += f"{post} {player_name}  :  {word}\n"
        info_string += f"\n人狼は{'、'.join(wolfs)}でした。\n\n"
        info_string += "同じメンバーで再戦する場合は:repeat:マーク、メニューに戻る場合は:wrench:マークを押してください。"
        
        result_embed = discord.Embed(title="**Word wolf** (beta)", color=self.embed_color)
        result_embed = result_embed.add_field(name="結果発表", value=info_string)

        self.result_message = await send_channel.send(embed=result_embed)
        await self.result_message.add_reaction("🔁")
        await self.result_message.add_reaction("🔧")


    async def continue_game(self, reaction: Reaction, user: Member) -> None:
        if self.result_message is None:
            return
        if reaction.message.id != self.result_message.id:
            return
        if self.is_joined(user.id) == False:
            return
        if str(reaction) not in ["🔁", "🔧"]:
            return
        if self.phase != "result":
            return
        
        wordwolf_channel = self.result_message.channel

        if str(reaction) == "🔁":
            await self.start_thinking_message.delete()
            await self.result_message.delete()
            await self.start_game(reaction=None, user=None, recursive_channel=wordwolf_channel)

        elif str(reaction) == "🔧":
            self.is_playing == False
            await self.menu_message.delete()
            self.menu_message = None
            await self.show_menu(wordwolf_channel)
            await self.start_thinking_message.delete()
            self.start_thinking_message = None
            await self.result_message.delete()
            self.result_message = None

    
    async def how_to_play_wordwolf(self, reaction: Reaction, user: Member) -> None:
        if self.menu_message is None:
            return
        if reaction.message.id != self.menu_message.id:
            return
        if self.is_joined(user.id) == False:
            return
        if str(reaction) != "❓":
            return
        if self.phase != "setting":
            return

        show_time = 120
        now_epochtime = int(datetime.now().strftime("%s"))
        if self.show_how2play_epochtime is None:
            self.show_how2play_epochtime = now_epochtime
        else:
            if now_epochtime - self.show_how2play_epochtime > show_time:
                self.show_how2play_epochtime = now_epochtime
            else:
                return

        image_url = "https://raw.githubusercontent.com/SnowRabbit-TTR/Infosquare-discord-bot/master/infosquare_package/data/wordwolf/how_to_play_wordwolf.png"
        
        how2play_embed = discord.Embed(title="**Word wolf** (beta)", color=self.embed_color)
        how2play_embed.set_image(url=image_url)
        self.how2play_message = await self.menu_message.channel.send(embed=how2play_embed)
        await self.how2play_message.delete(delay=show_time)


    async def reset(self, channel: TextChannel, breaker: Optional[Member]=None):
        if breaker is not None:
            if self.is_joined(breaker.id) == False:
                return
        
        if self.menu_message is not None:
            await self.menu_message.delete()
        if self.start_thinking_message is not None:
            await self.start_thinking_message.delete()
        if self.result_message is not None:
            await self.result_message.delete()
        if self.how2play_message is not None:
            await self.how2play_message.delete()

        self.__init__(players=[], wolf_num=1, available_genre=["food", "love", "life", "play"])
        info_string = "ワードウルフのグループが解散されました。\n新しくゲームを始めるには`/wordwolf`を入力してください。"
        await channel.send(info_string)


    async def set_wolf_num(self, message: Message) -> None:
        author_name = message.author.nick if message.author.nick is not None else message.author.name
        author_id = message.author.id

        if len(self.players) == 0:
            return
        if self.is_joined(author_id) == False:
            info_string = f"{author_name}さんはワードウルフのグループに参加していません。\nグループに参加する場合は、メニュー画面の:person_raising_hand:を押してください。"
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)
            return
        
        if not re.match(r"^(\/wolf)\s\d+$", message.content):
            info_string = "人狼の数を正しく設定してください。\n`/wolf 人狼の数`"
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)
            return
        
        wolf_num = int(re.search(r"\d+$", message.content).group())

        if self.check_wolf_num(set_wolf_num=wolf_num) == False:
            info_string = "人狼の数が不正です。"
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)
            return
        
        self.wolf_num = wolf_num
        self.wordwolf_game.set_wolf_num(wolf_num)
        info_string = f"人狼の数を{self.wolf_num}人に設定しました。"
        info_message = await message.channel.send(info_string)
        await info_message.delete(delay=30)

        menu_channel = self.menu_message.channel
        await self.menu_message.delete()
        self.menu_message = None
        await self.show_menu(menu_channel)


    async def set_available_genre(self, message: Message) -> None:
        author_name = message.author.nick if message.author.nick is not None else message.author.name
        author_id = message.author.id

        if len(self.players) == 0:
            return
        if self.is_joined(author_id) == False:
            info_string = f"{author_name}さんはワードウルフのグループに参加していません。\nグループに参加する場合は、メニュー画面の:person_raising_hand:を押してください。"
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)
            return

        if not re.match(r"^(\/genre)\s(\s*[1-4]?)*$", message.content):
            info_string = "お題のジャンルを正しく入力してください。\n`/genre ジャンル番号`"
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)
            return

        genre_string = "".join(message.content.split()[1:])
        available_genre = []

        if "1" in genre_string:
            available_genre.append("food")
        if "2" in genre_string:
            available_genre.append("love")
        if "3" in genre_string:
            available_genre.append("life")
        if "4" in genre_string:
            available_genre.append("play")
        
        self.wordwolf_game.set_available_genre(available_genre)
        self.available_genre = available_genre
        info_string = "お題のジャンルを変更しました。"
        info_message = await message.channel.send(info_string)
        await info_message.delete(delay=30)

        menu_channel = self.menu_message.channel
        await self.menu_message.delete()
        self.menu_message = None
        await self.show_menu(menu_channel)


    def add_player(self, member: Member) -> None:
        player_id = member.id
        if player_id not in self.players:
            self.registered_player[player_id] = member
            self.players.append(player_id)
            self.wordwolf_game.set_players(self.players)
            return True
        else:
            return False


    def remove_player(self, member: Member) -> None:
        player_id = member.id
        if player_id in self.players:
            del self.registered_player[player_id]
            self.players.remove(player_id)
            self.wordwolf_game.set_players(self.players)
            return True
        else:
            return False


    def check_wolf_num(self, set_wolf_num: Optional[int]=None) -> bool:
        wolf_num = self.wolf_num if set_wolf_num is None else set_wolf_num
        if len(self.players) > 2 * wolf_num:
            return True
        else:
            return False

    
    def is_ready_for_game(self) -> bool:
        if self.check_wolf_num == False:
            return False
        if len(self.players) < 3:
            return False
        
        return True


    def is_joined(self, player_id: int) -> bool:
        if player_id in self.players:
            return True
        else:
            return False


# TODO: Make updater of questions.
class WordWolfUpdater:
    pass
