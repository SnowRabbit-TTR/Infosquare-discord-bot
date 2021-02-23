"""
Information tracker
=====
author: Snow Rabbit
"""

from datetime import datetime, timedelta, timezone

import discord

from . import embed_color
from .util.web_stream import HTMLStream, JsonStream


class DistrictTracker:

    def __init__(self, district_info_channel, bot_user):
        self.district_info_channel = district_info_channel
        self.bot_user = bot_user
        self.district_info_message = None

        self.url = "https://toontownrewritten.com/api/population"
        self.invasions_tracker = InvasionTracker(invasion_info_channel=None, bot_user=None)
        self.embed_color = embed_color.DISTRICT_INFO_COLOR

        self.last_updated_population = None
        self.total_population = None
        self.population_by_district = None
        self.invasions = None


    async def notice(self):
        self.load_information()
        info_string, renew_time_string = self.get_info_string()
        district_info_embed = discord.Embed(title="**TTR Realtime Information Board**", color=self.embed_color)
        district_info_embed = district_info_embed.add_field(name=":park: ロビー情報", value=info_string)
        district_info_embed = district_info_embed.set_footer(text=renew_time_string)

        if self.district_info_message is None:
            history = await self.district_info_channel.history().flatten()
            if len(history) == 1 and history[0].author.id == self.bot_user.id:
                self.district_info_message = history[0]
            else:
                await self.district_info_channel.purge(limit=None)
                self.district_info_message = await self.district_info_channel.send(embed=district_info_embed)
                return

        await self.district_info_message.edit(embed=district_info_embed)
    
    
    def load_information(self):
        json_object = JsonStream().get_json_object(self.url)

        self.last_updated_population = json_object["lastUpdated"]
        self.total_population = json_object["totalPopulation"]
        self.population_by_district = sorted(json_object["populationByDistrict"].items())
        self.invasions = self.invasions_tracker.get_invasions()

    
    def get_info_string(self):
        info_string = ""
        all_population_emoji = self.convert_number_to_emoji(self.total_population)
        info_string += "現在の総プレイ人口：{}人\n\n".format(all_population_emoji)
        info_string += "　　人口　　　　ロビー\n"
        info_string += self.get_district_strings()
        info_string += "\n:speech_balloon:：スピードチャットのみ使用可能\n" + \
                       ":shield:：特定のイベントが開催されない\n" + \
                       ":sparkles:：召喚によるコグの侵略が発生しない\n" + \
                       ":gear:：コグの侵略が進行中\n\n"
        renew_time_string = "最終更新　{}".format(datetime.now(timezone(timedelta(hours=+9), "JST")).strftime("%H:%M"))
        
        return info_string, renew_time_string


    def convert_number_to_emoji(self, number: int):
        emoji_string = ""
        for x in str(number):
            if x == "0":
                emoji_string += ":zero:"
            elif x == "1":
                emoji_string += ":one:"
            elif x == "2":
                emoji_string += ":two:"
            elif x == "3":
                emoji_string += ":three:"
            elif x == "4":
                emoji_string += ":four:"
            elif x == "5":
                emoji_string += ":five:"
            elif x == "6":
                emoji_string += ":six:"
            elif x == "7":
                emoji_string += ":seven:"
            elif x == "8":
                emoji_string += ":eight:"
            elif x == "9":
                emoji_string += ":nine:"

        return emoji_string


    def get_district_strings(self):
        status_emoji = ""
        for pd in self.population_by_district:
            if pd[1] <= 300:
                status_emoji += ":blue_circle: "
            elif pd[1] > 500:
                status_emoji += ":red_circle: "
            else:
                status_emoji += ":green_circle: "

            for x in str(pd[1]).rjust(3):
                if x == " ":
                    status_emoji += "　"
                elif x == "0":
                    status_emoji += "０"
                elif x == "1":
                    status_emoji += "１"
                elif x == "2":
                    status_emoji += "２"
                elif x == "3":
                    status_emoji += "３"
                elif x == "4":
                    status_emoji += "４"
                elif x == "5":
                    status_emoji += "５"
                elif x == "6":
                    status_emoji += "６"
                elif x == "7":
                    status_emoji += "７"
                elif x == "8":
                    status_emoji += "８"
                elif x == "9":
                    status_emoji += "９"
            
            status_emoji += "　　**{}** ".format(pd[0])

            if pd[0] == "Blam Canyon":
                status_emoji += ":shield:"
            elif pd[0] == "Boingbury":
                status_emoji += ":speech_balloon:"
            elif pd[0] == "Fizzlefield":
                status_emoji += ":shield:"
            elif pd[0] == "Gulp Gulch":
                status_emoji += ":speech_balloon:" + ":shield:" + ":sparkles:"
            elif pd[0] == "Splat Summit":
                status_emoji += ":shield:" + ":sparkles:"
            elif pd[0] == "Whoosh Rapids":
                status_emoji += ":speech_balloon:"

            # HACK: Checking invasions method is too dirty.
            if pd[0] in str(self.invasions):
                status_emoji += ":gear:"
            
            status_emoji += "\n"
        
        return status_emoji  



class ServerTracker:

    def __init__(self, server_info_channel, bot_user: int):
        self.server_info_channel = server_info_channel
        self.bot_user = bot_user
        self.server_info_message = None

        self.url = "https://status.toontownrewritten.com/"
        self.pr_soup = None
        self.is_stable = 1


    async def notice(self):
        self.load_server_status()
        info_string, renew_time_string = self.get_info_string()

        if self.is_stable == 1:
            color = embed_color.SERVER_INFO_STABLE_COLOR
        elif self.is_stable == 2:
            color = embed_color.SERVER_INFO_ISSUE_COLOR
        else:
            color = embed_color.SERVER_INFO_DOWN_COLOR
        
        server_info_embed = discord.Embed(title="**TTR Realtime Information Board**", color=color)
        server_info_embed = server_info_embed.add_field(name=":chart_with_downwards_trend: サーバー稼働状況", value=info_string)
        server_info_embed = server_info_embed.set_footer(text=renew_time_string)

        # First sending after initialize.
        if self.server_info_message is None:
            history = await self.server_info_channel.history().flatten()
            if len(history) == 1 and history[0].author.id == self.bot_user.id:
                self.server_info_message = history[0]
            else:
                await self.server_info_channel.purge(limit=None)
                self.server_info_message = await self.server_info_channel.send(embed=server_info_embed)
                return

        await self.server_info_message.edit(embed=server_info_embed)


    def load_server_status(self):
        self.pr_soup = HTMLStream().get_soup_object(url=self.url, soup_class="list-group-item sub-component")


    def get_info_string(self):
        info_string = "\n**Game Servers**\n"
        info_string += self.get_status_emoji(self.pr_soup[1].small.string) + " ゲームサーバー\n"
        info_string += self.get_status_emoji(self.pr_soup[2].small.string) + " スピードチャット＋\n"
        info_string += self.get_status_emoji(self.pr_soup[3].small.string) + " ゲームサービス全般\n"
        info_string += "\n**Website**\n"
        info_string += self.get_status_emoji(self.pr_soup[4].small.string) + " ダウンロードサーバー\n"
        info_string += self.get_status_emoji(self.pr_soup[5].small.string) + " 公式ホームページ/ログインサーバー\n"
        info_string += "\n**Support System**\n"
        info_string += self.get_status_emoji(self.pr_soup[0].small.string) + " メールサポート\n"
        renew_time_string = "最終更新　{}".format(datetime.now(timezone(timedelta(hours=+9), "JST")).strftime("%H:%M"))
        
        return info_string, renew_time_string
    
    
    def get_status_emoji(self, string):
        if string == "Operational":
            return ":white_check_mark:"
        elif string == "Performance Issues":
            self.is_stable = 2 if self.is_stable < 2 else self.is_stable
            return ":warning:"
        else:
            self.is_stable = 3 if self.is_stable < 3 else self.is_stable
            return ":x:"



# TODO: Remake GroupTracker
class GroupTracker:
    pass



class InvasionTracker:

    def __init__(self, invasion_info_channel, bot_user):
        self.invasion_info_channel = invasion_info_channel
        self.bot_user = bot_user
        self.invasion_info_message = None

        self.url = "https://toonhq.org/api/v1/invasion/"
        self.embed_color = embed_color.INVASION_INFO_COLOR

        self.invasions = None
        self.error = None
        self.last_updated_invasion = None
        self.ttr_working = None
        self.average_defeat_rates = {}


    async def notice(self):
        self.load_invasion_info()

        invasion_info_embed = discord.Embed(title="**TTR Realtime Information Board**", color=self.embed_color)
        info_string = "表示されている残り時間は実際とは異なる場合があります。\n"
        invasion_info_embed = invasion_info_embed.add_field(name=":gear: 現在進行中のコグ侵略情報", value=info_string)
        for invasion in self.invasions:
            cog_name, info_string = self.get_invasion_string(invasion)
            invasion_info_embed = invasion_info_embed.add_field(name=cog_name, value=info_string, inline=False)
        renew_time_string = "最終更新　{}".format(datetime.now(timezone(timedelta(hours=+9), "JST")).strftime("%H:%M"))
        invasion_info_embed = invasion_info_embed.set_footer(text=renew_time_string)

        # First sending after initialize.
        if self.invasion_info_message is None:
            history = await self.invasion_info_channel.history().flatten()
            if len(history) == 1 and history[0].author.id == self.bot_user.id:
                self.invasion_info_message = history[0]
            else:
                await self.invasion_info_channel.purge(limit=None)
                self.invasion_info_message = await self.invasion_info_channel.send(embed=invasion_info_embed)
                return

        await self.invasion_info_message.edit(embed=invasion_info_embed)
    

    def load_invasion_info(self):
        json_object = JsonStream().get_json_object(self.url)
        self.invasions = json_object["invasions"]
        self.error = json_object["meta"]["error"]
        self.last_updated_invasion = json_object["meta"]["last_updated"]
        self.ttr_working = json_object["meta"]["ttr_working"]

        for invasion in self.invasions:
            invasion_id = invasion["id"]
            defeat_rate = invasion["defeat_rate"]

            if invasion_id in self.average_defeat_rates:
                count = self.average_defeat_rates[invasion_id]["count"]
                average = self.average_defeat_rates[invasion_id]["average"]
                self.average_defeat_rates[invasion_id]["average"] = \
                    (count * average + defeat_rate) / (count + 1)
                self.average_defeat_rates[invasion_id]["count"] += 1
            else:
                self.average_defeat_rates[invasion_id] = {"average": defeat_rate, "count": 1}

    
    def convert_sec_to_timestr(self, left_sec):
        if left_sec < 30:
            return "まもなく終了"
        
        time_string = ""
        if left_sec > 3600:
            hour = int(left_sec / 3600)
            time_string += "{} : ".format(hour)
            left_sec = left_sec - 3600 * hour
        minute = int(left_sec / 60)
        time_string += "{:02} : ".format(minute)
        second = int(left_sec - minute * 60)
        time_string += "{:02}".format(second)

        return time_string

    
    def get_invasion_string(self, invasion_dict: dict):
        invasion_id = invasion_dict["id"]
        defeated = invasion_dict["defeated"]
        total = invasion_dict["total"]
        district = invasion_dict["district"]
        cog_name = invasion_dict["cog"]

        progress = defeated / total
        if progress < 0.75:
            cog_name = ":green_circle: **{}**".format(cog_name)
        elif 0.75 <= progress < 0.9:
            cog_name = ":yellow_circle: **{}**".format(cog_name)
        else:
            cog_name = ":red_circle: **{}**".format(cog_name)

        if total == 1000000:  # HACK: Is this correct to check mega invasions?
            time_string = "MEGA INVASION!"
            defeat_string = "---"
        else:
            estimated = (total - defeated) / self.average_defeat_rates[invasion_id]["average"]
            time_string = self.convert_sec_to_timestr(estimated)
            defeat_string = "{0} / {1}".format(defeated, total)

        info_string = "ロビー ： **{}**\n".format(district)
        info_string += "残り時間 ： **{}**\n".format(time_string)
        info_string += "倒されたコグの数 ： **{}**\n\n".format(defeat_string)

        return cog_name, info_string

    
    #HACK: This method is just used for DistrictTracker.
    def get_invasions(self):
        self.load_invasion_info()
        return self.invasions
