"""
Minesweeper
=====
author: Snow Rabbit
"""

import random
from datetime import datetime

import discord

from . import embed_color


class MinesweeperBoard:

    def __init__(self, bomb_num: int, row_num: int):
        self.bomb_num = bomb_num
        self.row_num = row_num
        self.stage = [[0 for x in range(row_num)] for y in range(row_num)]

        index = []
        for x in range(1, row_num):
            for y in range(1, row_num+1):
                index.append(10 * x + y)
        bomb_index = random.sample(index, bomb_num)

        for bi in bomb_index:
            # FIXME: If row_num is more than 10, this phase need to be fixed.
            bx = int(str(bi)[0]) - 1
            by = int(str(bi)[-1]) - 1
            self.stage[bx][by] = 100
        
        self.generate_minesweeper_map()
    

    def generate_minesweeper_map(self):
        for x in range(self.row_num):
            for y in range(self.row_num):
                if self.stage[x][y] >= 100:
                    if x-1 >= 0 and y-1 >= 0:
                        try:
                            self.stage[x-1][y-1] += 1
                        except(IndexError):
                            pass
                    if y-1 >= 0:
                        try:
                            self.stage[x][y-1] +=1
                        except(IndexError):
                            pass
                        try:
                            self.stage[x+1][y-1] += 1
                        except(IndexError):
                            pass
                    if x-1 >= 0:
                        try:
                            self.stage[x-1][y] += 1
                        except(IndexError):
                            pass
                        try:
                            self.stage[x-1][y+1] += 1
                        except(IndexError):
                            pass
                    try:
                        self.stage[x+1][y] += 1
                    except(IndexError):
                        pass
                    try:
                        self.stage[x][y+1] += 1
                    except(IndexError):
                        pass
                    try:
                        self.stage[x+1][y+1] += 1
                    except(IndexError):
                        pass

        
    def convert_map2string(self):
        board_string = ""

        for x in range(self.row_num):
            for y in range(self.row_num):
                if self.stage[x][y] >= 100:
                    board_string += "||:skull_crossbones:||"
                elif self.stage[x][y] == 0:
                    board_string += "||:zero:||"
                elif self.stage[x][y] == 1:
                    board_string += "||:one:||"
                elif self.stage[x][y] == 2:
                    board_string += "||:two:||"
                elif self.stage[x][y] == 3:
                    board_string += "||:three:||"
                elif self.stage[x][y] == 4:
                    board_string += "||:four:||"
                elif self.stage[x][y] == 5:
                    board_string += "||:five:||"
                elif self.stage[x][y] == 6:
                    board_string += "||:six:||"
                elif self.stage[x][y] == 7:
                    board_string += "||:seven:||"
                elif self.stage[x][y] == 8:
                    board_string += "||:eight:||"
            board_string += "\n"

        return board_string



class MinesweeperGameMaster:  

    def __init__(self, bomb_num=7, row_num=7):
        self.board = None
        self.is_play = False
        self.timelimit = 2
        self.bomb_num = bomb_num
        self.row_num = row_num
        self.startup_channel = {}
        self.embed_color = embed_color.MINESWEEPER_COLOR
    

    async def start_new_game(self, message, in_dm_channel=False):
        if in_dm_channel == False:
            if self.check_multiple_startup(message.channel) == False:
                info_string = "多重起動はできません。:no_good:"
                info_message = await message.channel.send(info_string)
                await info_message.delete(delay=30)
                return

        minesweeper_string = self.generate_minesweeper_string(in_dm_channel=in_dm_channel)
        minsweeper_embed = discord.Embed(title="**Minesweeper**", color=self.embed_color)
        minsweeper_embed = minsweeper_embed.add_field(name="マインスイーパー！", value=minesweeper_string)
        minesweeper_message = await message.channel.send(embed=minsweeper_embed)
        await minesweeper_message.delete(delay=self.timelimit * 60)


    def generate_minesweeper_string(self, in_dm_channel=False):
        self.board = MinesweeperBoard(bomb_num=self.bomb_num, row_num=self.row_num)
        minesweeper_string = "ガイコツの数は{}個です。\n".format(self.bomb_num)
        minesweeper_string += "一番下の行にはガイコツはいません。\n"
        if in_dm_channel == False:
            minesweeper_string += "開始から{}分が経過すると、この盤面は自動的に消去されます。\n\n".format(self.timelimit)
        else:
            minesweeper_string += "\n"
        minesweeper_string += self.board.convert_map2string()

        return minesweeper_string


    def check_multiple_startup(self, channel):
        now_epochtime = int(datetime.now().strftime("%s"))

        if channel.id not in self.startup_channel:
            self.startup_channel[channel.id] = now_epochtime
            return True
        
        last_startup_time = self.startup_channel[channel.id]
        if now_epochtime - last_startup_time > self.timelimit * 60:
            self.startup_channel[channel.id] = now_epochtime
            return True
        else:
            return False
