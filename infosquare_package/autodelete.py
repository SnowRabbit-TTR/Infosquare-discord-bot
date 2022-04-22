"""
Autodelete
=====
author: Snow Rabbit
"""

import re

from discord.message import Message


class AutoDeleteListner:

    def __init__(self) -> None:
        self.observer = AutoDeleteObserver()


    async def listen_command(self, message: Message) -> None:
        # Stop auto delete app.
        if message.content.replace(" ", "").lower() == "/stopautodelete":
            await self.observer.stop_autodelete(message)

        # Find the message of auto delete app user.
        await self.observer.observe(message)

        # Start auto delete app.
        if message.content.replace(" ", "").lower().startswith("/startautodelete"):
            await self.observer.start_autodelete(message)


class AutoDeleteObserver:

    def __init__(self) -> None:
        self.user_ids = {}

    
    async def start_autodelete(self, message: Message) -> None:
        author_id = message.author.id
        author_name = message.author.nick if message.author.nick is not None else message.author.name

        if self.is_user_registered(author_id):
            info_string = f"{author_name}さんはメッセージ自動削除botを既に起動しています。\n終了する場合は`/stop autodelete`を入力してください。"
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)
            return
        
        try:
            input_time = message.content.split(" ")[2]

            if re.match(r"^\d+s(ec)?$", input_time):  # second
                second = int(re.search(r'^\d+', input_time).group())
                if second <= 0 or second > 60:
                    info_string = "秒数[s]は1〜60の間で指定してください。"
                    info_message = await message.channel.send(info_string)
                    await info_message.delete(delay=30)
                    return
                time_string = f"{second}秒"
                show_second = second

            elif re.match(r"^\d+m(in)?$", input_time):  # minute
                minute = int(re.search(r'^\d+', input_time).group())
                if minute <= 0 or minute > 60:
                    info_string = "分数[m]は1〜60の間で指定してください。"
                    info_message = await message.channel.send(info_string)
                    await info_message.delete(delay=30)
                    return
                time_string = f"{minute}分"
                show_second = minute * 60

            elif re.match(r"^\d+h(our)?$", input_time):  # hour
                hour = int(re.search(r'^\d+', input_time).group())
                if hour <= 0 or hour > 24:
                    info_string = "時間数[h]は1〜24の間で指定してください。"
                    info_message = await message.channel.send(info_string)
                    await info_message.delete(delay=30)
                    return
                time_string = f"{hour}時間"
                show_second = hour * 3600

            elif re.match(r"^\d+$", input_time):  # default (= min)
                minute = int(re.search(r'^\d+', input_time).group())
                if minute <= 0 or minute > 60:
                    info_string = "削除までの時間は1分〜60分の間で指定してください。\n数字の後ろに's'/'h'を付けると1秒/1時間単位での指定ができます。"
                    info_message = await message.channel.send(info_string)
                    await info_message.delete(delay=30)
                    return
                time_string = f"{minute}分"
                show_second = minute * 60

            else:
                raise ValueError()

            self.register(author_id, show_second)
            info_string = f"{author_name}さんがメッセージ自動削除botを起動しました。\n{author_name}さんが送信したメッセージは{time_string}後に自動的に削除されます。"
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)

        except:
            info_string = "メッセージ削除までの時間を正しく入力してください。\n`/start autodelete 削除までの時間`"
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)
            return

    
    async def stop_autodelete(self, message: Message) -> None:
        author_id = message.author.id
        author_name = message.author.nick if message.author.nick is not None else message.author.name

        if self.is_user_registered(author_id) == False:
            info_string = f"{author_name}さんはメッセージ自動削除botを起動していません。\n開始する場合は`/start autodelete 削除までの時間`を入力してください。"
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)
            return

        self.unregister(author_id)
        info_string = f"{author_name}さんが送信したメッセージの自動削除を終了しました。"
        info_message = await message.channel.send(info_string)
        await info_message.delete(delay=30)
    

    async def observe(self, message: Message) -> None:
        author_id = message.author.id

        if self.is_user_registered(author_id) == False:
            return
        
        show_second = self.get_show_second(author_id)
        await message.delete(delay=show_second)


    def register(self, user_id: int, show_second: int) -> None:
        self.user_ids[user_id] = show_second


    def unregister(self, user_id: int) -> None:
        del self.user_ids[user_id]

    
    def get_show_second(self, user_id: int) -> int:
        show_second = self.user_ids[user_id]
        return show_second


    def is_user_registered(self, user_id: int) -> bool:
        if user_id in self.user_ids:
            return True
        else:
            return False
