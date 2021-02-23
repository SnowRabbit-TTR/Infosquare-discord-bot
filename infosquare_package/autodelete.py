"""
Autodelete
=====
author: Snow Rabbit
"""

import re


class AutoDeleteObserver:

    def __init__(self):
        self.user_ids = {}

    
    async def start_autodelete(self, message):
        author_id = message.author.id
        author_name = message.author.nick if message.author.nick is not None else message.author.name

        if self.is_user_registered(author_id) == True:
            info_string = "{}さんはメッセージ自動削除botを既に起動しています。\n終了する場合は`/stop autodelete`を入力してください。".format(author_name)
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)
            return
        
        try:
            input_time = message.content.split(" ")[2]

            if re.match(r"^\d+s(ec)?$", input_time):  # seccond
                seccond = int(re.search(r'^\d+', input_time).group())
                if seccond <= 0 or seccond > 60:
                    info_string = "秒数[s]は1〜60の間で指定してください。"
                    info_message = await message.channel.send(info_string)
                    await info_message.delete(delay=30)
                    return
                time_string = "{}秒".format(seccond)
                show_seccond = seccond

            elif re.match(r"^\d+m(in)?$", input_time):  # minute
                minute = int(re.search(r'^\d+', input_time).group())
                if minute <= 0 or minute > 60:
                    info_string = "分数[m]は1〜60の間で指定してください。"
                    info_message = await message.channel.send(info_string)
                    await info_message.delete(delay=30)
                    return
                time_string = "{}分".format(minute)
                show_seccond = minute * 60

            elif re.match(r"^\d+h(our)?$", input_time):  # hour
                hour = int(re.search(r'^\d+', input_time).group())
                if hour <= 0 or hour > 24:
                    info_string = "時間数[h]は1〜24の間で指定してください。"
                    info_message = await message.channel.send(info_string)
                    await info_message.delete(delay=30)
                    return
                time_string = "{}時間".format(hour)
                show_seccond = hour * 3600

            elif re.match(r"^\d+$", input_time):  # default (= min)
                minute = int(re.search(r'^\d+', input_time).group())
                if minute <= 0 or minute > 60:
                    info_string = "削除までの時間は1分〜60分の間で指定してください。\n数字の後ろに's'/'h'を付けると1秒/1時間単位での指定ができます。"
                    info_message = await message.channel.send(info_string)
                    await info_message.delete(delay=30)
                    return
                time_string = "{}分".format(minute)
                show_seccond = minute * 60

            else:
                raise ValueError()

            self.register(author_id, show_seccond)
            info_string = "{0}さんがメッセージ自動削除botを起動しました。\n{1}さんが送信したメッセージは{2}後に自動的に削除されます。".format(author_name, author_name, time_string)
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)

        except:
            info_string = "メッセージ削除までの時間を正しく入力してください。\n`/start autodelete 削除までの時間`"
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)
            return

    
    async def stop_autodelete(self, message):
        author_id = message.author.id
        author_name = message.author.nick if message.author.nick is not None else message.author.name

        if self.is_user_registered(author_id) == False:
            info_string = "{}さんはメッセージ自動削除botを起動していません。\n開始する場合は`/start autodelete 削除までの時間`を入力してください。".format(author_name)
            info_message = await message.channel.send(info_string)
            await info_message.delete(delay=30)
            return

        self.unregister(author_id)
        info_string = "{}さんが送信したメッセージの自動削除を終了しました。".format(author_name)
        info_message = await message.channel.send(info_string)
        await info_message.delete(delay=30)
    

    async def observe(self, message):
        author_id = message.author.id

        if self.is_user_registered(author_id) == False:
            return
        
        show_seccond = self.get_show_second(author_id)
        await message.delete(delay=show_seccond)


    def register(self, user_id: int, show_seccond: int):
        self.user_ids[user_id] = show_seccond


    def unregister(self, user_id: int):
        del self.user_ids[user_id]

    
    def get_show_second(self, user_id: int):
        show_seccond = self.user_ids[user_id]
        return show_seccond


    def is_user_registered(self, user_id: int):
        if user_id in self.user_ids:
            return True
        else:
            return False
