"""
Connect 4
=====
author: Snow Rabbit
"""

from datetime import datetime
from pydoc import doc
from typing import Optional, Tuple, Union

import discord
from discord.channel import DMChannel, TextChannel
from discord.member import Member
from discord.message import Message
from discord.reaction import Reaction
from discord.user import ClientUser

from . import embed_color
from .util import firebase_operator
from .util.web_stream import JsonStream


class Connect4Board:

    def __init__(self, column_num: int=7, row_num: int=6) -> None:
        self.column_num = column_num
        self.row_num = row_num
        self.board = [[0 for x in range(self.column_num)] for y in range(self.row_num)]

    
    def push(self, piece: int, column: int) -> bool:
        is_push = False
        if self.board[0][column] == 0:
            for i in range(self.row_num-1, -1, -1):
                if self.board[i][column] == 0:
                    self.board[i][column] = piece
                    is_push = True
                    break
        return is_push


    def is_filled(self) -> bool:
        for i in range(0, self.row_num):
            for j in range(0, self.column_num):
                if self.board[i][j] == 0:
                    return False
        return True

    
    def check_winner(self) -> int:
        for i in range(0, self.row_num):
            for j in range(0, self.column_num):
                # FIXME: There is a bug for checking 2-dim list index.
                # Check vertical
                try:
                    x1 = self.board[i][j]
                    x2 = self.board[i+1][j]
                    x3 = self.board[i+2][j]
                    x4 = self.board[i+3][j]
                    sum_value = x1 + x2 + x3 + x4
                    if abs(sum_value) == 4:
                        return int(sum_value / 4)
                except(IndexError):
                    pass
                # Check horizon
                try:
                    x1 = self.board[i][j]
                    x2 = self.board[i][j+1]
                    x3 = self.board[i][j+2]
                    x4 = self.board[i][j+3]
                    sum_value = x1 + x2 + x3 + x4
                    if abs(sum_value) == 4:
                        return int(sum_value / 4)
                except(IndexError):
                    pass
                # Check diagonally left (\)
                try:
                    x1 = self.board[i][j]
                    x2 = self.board[i+1][j+1]
                    x3 = self.board[i+2][j+2]
                    x4 = self.board[i+3][j+3]
                    sum_value = x1 + x2 + x3 + x4
                    if abs(sum_value) == 4:
                        return int(sum_value / 4)
                except(IndexError):
                    pass
                # Check diagonally right (/)
                try:
                    x1 = self.board[i][j]
                    x2 = self.board[i-1][j+1] if i-1 >= 0 else 0
                    x3 = self.board[i-2][j+2] if i-2 >= 0 else 0
                    x4 = self.board[i-3][j+3] if i-3 >= 0 else 0
                    sum_value = x1 + x2 + x3 + x4
                    if abs(sum_value) == 4:
                        return int(sum_value / 4)
                except(IndexError):
                    pass
        
        # Check draw
        if self.is_filled():
            return 99

        return 0

    
    def get_discord_string(self) -> str:
        string = "\n:one: :two: :three: :four: :five: :six: :seven:\n"
        for xs in self.board:
            for i in range(0, self.column_num):
                if xs[i] == 0:
                    string += ":white_square_button: "
                elif xs[i] == 1:
                    string += ":yellow_square: "
                elif xs[i] == -1:
                    string += ":red_square: "
            string += "\n"
            
        return string


class Connect4Listner:

    EMOJI_NUMBERS_LIST = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣"]


    def __init__(self, bot_user: ClientUser) -> None:
        self.gamemaster = Connect4GameMaster(bot_user=bot_user)
    

    async def listen_command(self, message: Message) -> None:
        # Make find four game group.
        if message.content.replace(" ", "").lower() in ["/findfour", "/find4", "/connectfour", "/connect4"]:
            await self.gamemaster.establish(message)

        # Hidden command to break find four game group.
        if message.content.replace(" ", "").lower() in ["/breakfindfour", "/breakfind4"]:
            await self.gamemaster.reset(message.channel)

        # Show statistics
        if message.content.replace(" ", "").lower() in ["/findfourstatistics", "/find4statistics"]:
            await self.gamemaster.show_statistics(message.channel)

    
    async def listen_reaction(self, channel: Union[DMChannel, TextChannel], reaction: Reaction,
                              user: Member) -> bool:
        try:
            # Join
            if str(reaction) == "🙋":
                conditions = [reaction.message.id == self.gamemaster.games[channel.id]["menu_message"].id,
                              user not in self.gamemaster.games[channel.id]["players"]]
                if all(conditions):
                    await self.gamemaster.join(channel, user)
                    return True

            # Leave
            elif str(reaction) == "👋":
                conditions = [user in self.gamemaster.games[channel.id]["players"],
                              self.gamemaster.games[channel.id]["is_playing"] == False]
                if all(conditions):
                    await self.gamemaster.leave(channel, user)
                    return True

            # Switch players
            elif str(reaction) == "↔️":
                conditions = [user in self.gamemaster.games[channel.id]["players"],
                              len(self.gamemaster.games[channel.id]["players"]) == 2,
                              self.gamemaster.games[channel.id]["is_playing"] == False]
                if all(conditions):
                    await self.gamemaster.switch_player(channel)
                    return True

            # Start game
            elif str(reaction) == "▶️":
                conditions = [user in self.gamemaster.games[channel.id]["players"],
                              len(self.gamemaster.games[channel.id]["players"]) == 2,
                              self.gamemaster.games[channel.id]["is_playing"] == False]
                if all(conditions):
                    await self.gamemaster.start_game(channel)
                    return True
            
            # Choose column
            elif str(reaction) in self.EMOJI_NUMBERS_LIST:
                conditions = [user in self.gamemaster.games[channel.id]["players"],
                              self.gamemaster.games[channel.id]["can_push"],
                              self.gamemaster.games[channel.id]["players"][int((1 - self.gamemaster.games[channel.id]["now_turn"]) / 2)].id == user.id]
                if all(conditions):
                    for i, num_emoji in enumerate(self.EMOJI_NUMBERS_LIST):
                        if str(reaction) == str(num_emoji):
                            column = i
                            break
                    await self.gamemaster.push_board(channel, column)
                    return True

            # Repeat game
            elif str(reaction) == "🔁":
                conditions = [reaction.message.id == self.gamemaster.games[channel.id]["board_message"].id,
                              self.gamemaster.games[channel.id]["is_playing"] == False]
                if all(conditions):
                    await self.gamemaster.repeat_game(channel)
                    return True

            # Back to menu
            elif str(reaction) == "🔧":
                conditions = [reaction.message.id == self.gamemaster.games[channel.id]["board_message"].id,
                              self.gamemaster.games[channel.id]["is_playing"] == False]
                if all(conditions):
                    await self.gamemaster.back_to_menu(channel)
                    return True
        
        except:
            pass

        return False


class Connect4GameMaster:
    
    def __init__(self, bot_user: ClientUser) -> None:
        self.games = {}
        self.bot_user = bot_user
        self.ai = UnbeatableAI()


    def get_player_name(self, user: ClientUser) -> str:
        if user == self.bot_user:
            return "AI :robot:"
        return user.display_name


    def add_player(self, channel_id: int, user: ClientUser) -> bool:
        player_num = len(self.games[channel_id]["players"])
        if player_num < 2:
            self.games[channel_id]["players"].append(user)
            if player_num == 0:
                self.games[channel_id]["first_player_name"] = self.get_player_name(user)
            elif player_num == 1:
                self.games[channel_id]["second_player_name"] = self.get_player_name(user)
            return True
        else:
            return False

    
    def remove_player(self, channel_id: int, user: ClientUser) -> bool:
        for i, player in enumerate(self.games[channel_id]["players"][:]):
            if player == user:
                self.games[channel_id]["players"].pop(i)
                if i == 0:
                    self.games[channel_id]["first_player_name"] = ""
                    if len(self.games[channel_id]["players"]) != 0:
                        self.games[channel_id]["first_player_name"] = self.games[channel_id]["second_player_name"]
                        self.games[channel_id]["second_player_name"] = ""
                elif i == 1:
                    self.games[channel_id]["second_player_name"] = ""
                return True
        return False

    
    def initialize_game(self, channel: Union[DMChannel, TextChannel]) -> None:
        self.games[channel.id] = {
            "players": [],
            "board": Connect4Board(),
            "channel": channel,
            "menu_message": None,
            "board_message": None,
            "first_player_name": "",
            "second_player_name": "",
            "vs_ai": False,
            "is_playing": False,
            "can_push": False,
            "now_turn": 1,
            "history": "",
        }


    def set_result(self, channel_id: int, winner: int) -> None:
        doc_dict = {
            "channel_id": channel_id,
            "timestamp": datetime.now(),
            "players": [
                self.games[channel_id]["players"][0].id,
                self.games[channel_id]["players"][1].id
            ],
            "history": self.games[channel_id]["history"],
            "vs_ai": self.games[channel_id]["vs_ai"],
            "winner": int((1 - winner) / 2)
        }

        firebase_operator.set_doc(
            collection_name="findfour_results",
            doc_dict=doc_dict
        )

    
    def get_results(self) -> Tuple[int, int, int]:
        doc_list = firebase_operator.get_doc_list("findfour_results")
        all_match_num = len(doc_list)
        vs_ai_num = len([doc for doc in doc_list if doc["vs_ai"]])
        ai_win_num = len([doc for doc in doc_list if doc["vs_ai"] and 
                          doc["players"][doc["winner"]] == self.bot_user.id])
        return all_match_num, vs_ai_num, ai_win_num


    async def reset(self, channel: TextChannel) -> None:
        if self.games[channel.id]["menu_message"] is not None:
            await self.games[channel.id]["menu_message"].delete()
        if self.games[channel.id]["board_message"] is not None:
            await self.games[channel.id]["board_message"].delete()
        del self.games[channel.id]
        
        info_string = "Find fourのグループが解散されました。\n新しくゲームを始めるには`/findfour`を入力してください。"
        await channel.send(info_string)


    async def establish(self, message: Message) -> None:
        channel_id = message.channel.id
        if channel_id in self.games:
            info_string = "既にFind fourのグループが設立されています。\n" + \
                          "グループに参加する場合は、メニュー画面の:person_raising_hand:を押してください。"
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)
            return
        
        self.initialize_game(channel=message.channel)

        self.add_player(channel_id, message.author)
        
        if isinstance(message.channel, DMChannel):
            self.add_player(message.channel.id, self.bot_user)
            self.games[channel_id]["vs_ai"] = True

        await self.show_menu(message.channel)


    async def show_menu(self, channel: Union[DMChannel, TextChannel]) -> None:
        info_string = "**------- 参加者 -------**\n" + \
                      f"先攻 ： :yellow_square: {self.games[channel.id]['first_player_name']}\n" + \
                      f"後攻 ： :red_square: {self.games[channel.id]['second_player_name']}\n\n" + \
                      ":arrow_forward:：ゲームスタート\n" + \
                      ":left_right_arrow:：先攻/後攻を交代する\n"
        if isinstance(self.games[channel.id]["channel"], TextChannel):
            info_string += ":person_raising_hand:：グループに参加する\n" + \
                           ":wave:：グループから抜ける\n"
        elif isinstance(self.games[channel.id]["channel"], DMChannel):
            info_string += ":wave:：ゲームを終了する\n"

        menu_embed = discord.Embed(title="**Find four**", color=embed_color.CONNECT4_COLOR)
        menu_embed = menu_embed.add_field(name="メニュー画面", value=info_string)

        if self.games[channel.id]["menu_message"] is None:
            menu_message = await channel.send(embed=menu_embed)
            await menu_message.add_reaction("▶️")
            await menu_message.add_reaction("↔️")
            if isinstance(self.games[channel.id]["channel"], TextChannel):
                await menu_message.add_reaction("🙋")
                await menu_message.add_reaction("👋")
            else:
                await menu_message.add_reaction("👋")
            self.games[channel.id]["menu_message"] = menu_message
        else:
            await self.games[channel.id]["menu_message"].edit(embed=menu_embed)
    

    async def show_board(self, channel: Union[DMChannel, TextChannel], result: Optional[int]=None) -> None:
        if self.games[channel.id]["now_turn"] == 1:
            turn_first, turn_second = (":arrow_forward:", ":black_large_square:")
        else:
            turn_first, turn_second = (":black_large_square:", ":arrow_forward:")
        player_string = f"{turn_first} :yellow_square: **{self.games[channel.id]['first_player_name']}**\n" + \
                        f"{turn_second} :red_square: **{self.games[channel.id]['second_player_name']}**\n"
        
        board_string = self.games[channel.id]["board"].get_discord_string()
        
        if result is not None:
            if result == 1:
                board_string += f"\n**{self.games[channel.id]['first_player_name']}さんの勝ちです！**\n\n"
            elif result == -1:
                board_string += f"\n**{self.games[channel.id]['second_player_name']}さんの勝ちです！**\n\n"
            elif result == 99:
                board_string += "\n**引き分けです**\n\n"
            
            if isinstance(self.games[channel.id]["channel"], TextChannel):
                board_string += ":repeat:：同じメンバーで再戦する\n"
            elif isinstance(self.games[channel.id]["channel"], DMChannel):
                board_string += ":repeat:：もう一度プレイする\n"
            
            board_string += ":wrench:：メニューに戻る"

        board_embed = discord.Embed(title="**Find four**", color=embed_color.CONNECT4_COLOR)
        board_embed = board_embed.add_field(name=player_string, value=board_string)

        if self.games[channel.id]["board_message"] is None:
            self.games[channel.id]["board_message"] = await channel.send(embed=board_embed)
        else:
            await self.games[channel.id]["board_message"].edit(embed=board_embed)


    async def push_board(self, channel: Union[DMChannel, TextChannel], column_num: int) -> None:
        is_pushed = self.games[channel.id]["board"].push(
            piece=self.games[channel.id]["now_turn"], column=column_num
        )
        if is_pushed == False:
            return
        self.games[channel.id]["history"] += str(column_num + 1)

        result = self.games[channel.id]["board"].check_winner()
        if result == 0:
            self.games[channel.id]["now_turn"] *= -1
            await self.show_board(channel)
            next_index = int((self.games[channel.id]["now_turn"] - 1) / (-2))
            if self.games[channel.id]["players"][next_index].bot:
                hand = self.ai.get_hand(pos=self.games[channel.id]["history"])
                await self.push_board(channel, hand)
        else:
            self.games[channel.id]["is_playing"] = False
            self.games[channel.id]["can_push"] = False
            await self.show_board(channel, result=result)
            self.set_result(channel.id, result)
            await self.games[channel.id]["board_message"].add_reaction("🔁")
            await self.games[channel.id]["board_message"].add_reaction("🔧")
    

    async def join(self, channel: Union[DMChannel, TextChannel], user: Member) -> None:        
        self.add_player(channel.id, user)
        await self.show_menu(channel)


    async def leave(self, channel: Union[DMChannel, TextChannel], user: Member) -> None:
        self.remove_player(channel.id, user)
        await self.show_menu(channel)

        if isinstance(self.games[channel.id]["channel"], DMChannel) or len(self.games[channel.id]["players"]) == 0:
            await self.reset(channel)
    

    async def switch_player(self, channel: Union[DMChannel, TextChannel]) -> None:
        self.games[channel.id]["players"].reverse()
        self.games[channel.id]["first_player_name"], self.games[channel.id]["second_player_name"] = \
            self.games[channel.id]["second_player_name"], self.games[channel.id]["first_player_name"]

        await self.show_menu(channel)


    async def start_game(self, channel: Union[DMChannel, TextChannel]) -> None:
        self.games[channel.id]["is_playing"] = True
        self.games[channel.id]["can_push"] = True
        self.games[channel.id]["now_turn"] = 1
        self.games[channel.id]["history"] = ""
        await self.show_board(channel)

        emoji_number_list = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣"]
        for emoji_number in emoji_number_list:
            await self.games[channel.id]["board_message"].add_reaction(emoji_number)

        if self.games[channel.id]["players"][0].bot:
            hand = self.ai.get_hand(pos="")
            await self.push_board(channel, hand)
    

    async def repeat_game(self, channel: Union[DMChannel, TextChannel]) -> None:
        await self.games[channel.id]["board_message"].delete()
        self.games[channel.id]["board_message"] = None
        self.games[channel.id]["board"].__init__()
        await self.start_game(channel)


    async def back_to_menu(self, channel: Union[DMChannel, TextChannel]) -> None:
        self.games[channel.id]["board"].__init__()
        await self.games[channel.id]["board_message"].delete()
        self.games[channel.id]["board_message"] = None
        await self.games[channel.id]["menu_message"].delete()
        self.games[channel.id]["menu_message"] = None
        await self.show_menu(channel)

    
    async def show_statistics(self, channel: Union[DMChannel, TextChannel]) -> None:
        all_match_num, vs_ai_num, ai_win_num = self.get_results()
        ai_win_rate = f"{100 * ai_win_num / vs_ai_num:.2f} %" if vs_ai_num else "---"
        info_string = f"合計対戦回数：{all_match_num}\n" + \
                      f"   対人戦：{all_match_num - vs_ai_num}\n" + \
                      f"   AI戦：{vs_ai_num}\n" + \
                      f"   AIの勝利回数：{ai_win_num}（勝率：{ai_win_rate}）"
        await channel.send(info_string)
        

class UnbeatableAI:

    def __init__(self) -> None:
        pass

    
    def get_score(self, pos: str) -> list:
        url = f"https://connect4.gamesolver.org/solve?pos={pos}"
        json_object = JsonStream().get_json_object(url=url)
        return json_object["score"]


    def get_hand(self, pos: str) -> int:
        score_list = [-100 if score == 100 else score for score in self.get_score(pos)]
        max_score = max(score_list)
        return score_list.index(max_score)
