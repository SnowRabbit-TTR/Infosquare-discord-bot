"""
Connect 4
=====
author: Snow Rabbit
"""

from typing import Optional

import discord
from discord.channel import TextChannel
from discord.member import Member
from discord.message import Message
from discord.reaction import Reaction

from . import embed_color


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
                    x1 = self.board[i+1][j]
                    x2 = self.board[i+2][j]
                    x3 = self.board[i+3][j]
                    x4 = self.board[i+4][j]
                    sum_value = x1 + x2 + x3 + x4
                    if abs(sum_value) == 4:
                        return int(sum_value / 4)
                except(IndexError):
                    pass
                # Check horizon
                try:
                    x1 = self.board[i][j+1]
                    x2 = self.board[i][j+2]
                    x3 = self.board[i][j+3]
                    x4 = self.board[i][j+4]
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
        if self.is_filled() == True:
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


class Connect4GameMaster:
    
    def __init__(self) -> None:
        self.players = []
        self.embed_color = embed_color.CONNECT4_COLOR
        self.connect4_board = Connect4Board()

        self.is_playing = False
        self.can_push = False
        self.menu_message = None
        self.board_message = None
        self.first_player_name = None
        self.second_player_name = None
        self.now_turn_piece = 1  # 1 or -1


    async def establish(self, message: Message) -> None:
        if len(self.players) == 0:
            self.add_player(message.author)
            await self.show_menu(message.channel)
        else:
            info_string = "既にFind fourのグループが設立されています。\nグループに参加する場合は、メニュー画面の:person_raising_hand:を押してください。"
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)


    async def show_menu(self, channel: TextChannel) -> None:
        self.is_playing = False

        # About member
        info_string = "**------- 参加者 -------**\n"
        first_player = None if len(self.players) < 1 else self.players[0]["member"]
        second_player = None if len(self.players) < 2 else self.players[1]["member"]
        if first_player is not None:
            self.first_player_name = first_player.nick if first_player.nick is not None else first_player.name
        else:
            self.first_player_name = ""
        if second_player is not None:
            self.second_player_name = second_player.nick if second_player.nick is not None else second_player.name
        else:
            self.second_player_name = ""
        info_string += f"先攻 ： :yellow_square: {self.first_player_name}\n"
        info_string += f"後攻 ： :red_square: {self.second_player_name}\n"
        # About how to operate
        info_string += "\n:arrow_forward:：ゲームスタート\n"
        info_string += ":left_right_arrow:：先攻/後攻を交代する\n"
        info_string += ":person_raising_hand:：グループに参加する\n"
        info_string += ":wave:：グループから抜ける\n"
        #info_string += ":question:：ルール説明\n"  # TODO: Is the rules of Find 4 needed?

        menu_embed = discord.Embed(title="**Find four**", color=self.embed_color)
        menu_embed = menu_embed.add_field(name="メニュー画面", value=info_string)
        if self.menu_message is None:
            self.menu_message = await channel.send(embed=menu_embed)
            await self.menu_message.add_reaction("▶️")
            await self.menu_message.add_reaction("↔️")
            await self.menu_message.add_reaction("🙋")
            await self.menu_message.add_reaction("👋")
            #await self.menu_message.add_reaction("❓")  # TODO: Is the rules of Find 4 needed?
        else:
            await self.menu_message.edit(embed=menu_embed)
    

    async def show_board(self, channel: TextChannel, result: Optional[int]=None) -> None:
        turn_first, turn_second = (":arrow_forward:", ":black_large_square:") if self.now_turn_piece == 1 else (":black_large_square:", ":arrow_forward:")
        player_string = f"{turn_first} :yellow_square: **{self.first_player_name}**\n"
        player_string += f"{turn_second} :red_square: **{self.second_player_name}**\n"

        board_string = self.connect4_board.get_discord_string()
        if result is not None:
            if result == 1:
                board_string += f"\n**{self.first_player_name}さんの勝ちです！**"
            elif result == -1:
                board_string += f"\n**{self.second_player_name}さんの勝ちです！**"
            elif result == 99:
                board_string += "\n**引き分けです**"
            board_string += "\n\n:repeat:：同じメンバーで再戦する"
            board_string += "\n:wrench:：メニューに戻る"

        board_embed = discord.Embed(title="**Find four**", color=self.embed_color)
        board_embed = board_embed.add_field(name=player_string, value=board_string)

        if self.board_message is None:
            self.board_message = await channel.send(embed=board_embed)
        else:
            await self.board_message.edit(embed=board_embed)

    
    async def join(self, reaction: Reaction, user: Member) -> None:
        if self.menu_message is None or reaction.message.id != self.menu_message.id:
            return
        if self.is_playing == True:
            return
        if str(reaction) != "🙋":
            return
        if self.is_joined(user.id) == True:
            return
        if len(self.players) == 2:
            return
        
        self.add_player(user)
        await self.show_menu(reaction.message.channel)


    async def leave(self, reaction: Reaction, user: Member) -> None:
        if self.menu_message is None or reaction.message.id != self.menu_message.id:
            return
        if self.is_joined(user.id) == False:
            return
        if self.is_playing == True:
            return       
        if str(reaction) != "👋":
            return
        
        self.remove_player(user)
        await self.show_menu(reaction.message.channel)

        if len(self.players) == 0:
            await self.reset(reaction.message.channel)


    async def switch_player(self, reaction: Reaction, user: Member) -> None:
        if self.menu_message is None or reaction.message.id != self.menu_message.id:
            return
        if self.is_joined(user.id) == False:
            return
        if self.is_playing == True:
            return       
        if str(reaction) != "↔️":
            return

        self.players.reverse()

        await self.show_menu(reaction.message.channel)


    async def start_game(self, reaction: Reaction, user: Member, recursive: bool=False) -> None:
        if recursive == False:
            if self.menu_message is None or reaction.message.id != self.menu_message.id:
                return
            if self.is_joined(user.id) == False:
                return
            if self.is_playing == True:
                return
            if str(reaction) != "▶️":
                return

        self.is_playing = True
        self.can_push = True
        self.now_turn_piece = 1
        await self.show_board(reaction.message.channel)

        emoji_number_list = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣"]
        for emoji_number in emoji_number_list:
            await self.board_message.add_reaction(emoji_number)

    
    async def push_board(self, reaction: Reaction, user: Member) -> None:
        emoji_number_list = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣"]
        if self.board_message is None or reaction.message.id != self.board_message.id:
            return
        if self.is_joined(user.id) == False:
            return
        if self.is_playing == False:
            return
        if str(reaction) not in emoji_number_list:
            return
        if self.can_push == False:
            return
        
        if self.now_turn_piece == 1 and self.players[1]["id"] == user.id:
            return
        elif self.now_turn_piece == -1 and self.players[0]["id"] == user.id:
            return

        for i, num_emoji in enumerate(emoji_number_list):
            if str(reaction) == str(num_emoji):
                column = i
                break
        
        is_pushed = self.connect4_board.push(piece=self.now_turn_piece, column=column)
        if is_pushed == False:
            return
        result = self.connect4_board.check_winner()
        await reaction.remove(user)

        if result == 0:
            self.now_turn_piece *= -1
            await self.show_board(reaction.message.channel)
        else:
            self.can_push = False
            await self.show_board(reaction.message.channel, result=result)
            await self.board_message.add_reaction("🔁")
            await self.board_message.add_reaction("🔧")


    async def repeat_game_or_setting(self, reaction: Reaction, user: Member) -> None:
        if self.board_message is None or reaction.message.id != self.board_message.id:
            return
        if self.is_joined(user.id) == False:
            return
        if self.is_playing == False:
            return

        if str(reaction) == "🔁":
            await self.board_message.delete()
            self.board_message = None
            self.connect4_board.__init__()
            await self.start_game(reaction, user, recursive=True)

        elif str(reaction) == "🔧":
            await self.menu_message.delete()
            self.menu_message = None
            await self.show_menu(reaction.message.channel)
            await self.board_message.delete()
            self.board_message = None
            self.connect4_board.__init__()


    async def reset(self, channel: TextChannel) -> None:
        if self.menu_message is None:
            return
        else:
            await self.menu_message.delete()
            self.menu_message = None
        if self.board_message is not None:
            await self.board_message.delete()
            self.board_message = None

        self.__init__()
        info_string = "Find fourのグループが解散されました。\n新しくゲームを始めるには`/find four`を入力してください。"
        await channel.send(info_string)

    
    def add_player(self, member: Member) -> bool:
        player_id = member.id
        if self.is_joined(player_id) == False:
            self.players.append({"id": player_id, "member": member})
            return True
        else:
            return False

    
    def remove_player(self, member: Member) -> bool:
        player_id = member.id
        if self.is_joined(player_id) == True:
            for i, player in enumerate(self.players[:]):
                if player["id"] == player_id:
                    self.players.pop(i)
                    return True
            return False
        else:
            return False

    
    def is_joined(self, player_id: int) -> bool:
        for player in self.players:
            if player["id"] == player_id:
                return True
        return False
