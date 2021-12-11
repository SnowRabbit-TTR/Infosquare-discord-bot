"""
Information tracker
=====
author: Snow Rabbit
"""

import operator
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
        self.is_stable = 1
        info_string, renew_time_string = self.get_info_string()

        if self.is_stable == 1:
            color = embed_color.SERVER_INFO_STABLE_COLOR
        elif self.is_stable == 2:
            color = embed_color.SERVER_INFO_ISSUE_COLOR
        elif self.is_stable == 3:
            color = embed_color.SERVER_INFO_OUTAGE_COLOR
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
        elif string == "Partial Outage":
            self.is_stable = 3 if self.is_stable < 3 else self.is_stable
            return ":exclamation:"
        else:
            self.is_stable = 4 if self.is_stable < 4 else self.is_stable
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
        self.invasions = []


    async def notice(self, load_json=True):
        if load_json == True:
            self.load_invasion_info()

        invasion_info_embed = discord.Embed(title="**TTR Realtime Information Board**", color=self.embed_color)
        info_string = "表示されている残り時間は実際とは異なる場合があります。\n"
        invasion_info_embed = invasion_info_embed.add_field(name=":gear: 現在進行中のコグ侵略情報", value=info_string)
        for invasion in self.invasions:
            info_string = self.get_invasion_string(invasion)
            cog_name = "**{0} {1}**".format(invasion["status"], invasion["cog"])
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
    

    async def countdown(self, is_renew=False, interval=1):
        if is_renew == True:
            await self.notice(load_json=True)
        else:
            for i, invasion in enumerate(self.invasions[:]):
                if invasion["estimated"] >= 0:
                    self.invasions[i]["estimated"] -= interval
            await self.notice(load_json=False)


    def load_invasion_info(self):
        json_object = JsonStream().get_json_object(self.url)
        self.invasions = []

        for invasion in json_object["invasions"]:

            progress = invasion["defeated"] / invasion["total"]
            if progress < 0.75:
                status = ":green_circle:"
            elif 0.75 <= progress < 0.9:
                status = ":yellow_circle:"
            else:
                status = ":red_circle:"
            invasion["status"] = status

            # HACK: Is this correct to check mega invasions?
            if invasion["total"] == 1000000:
                invasion["is_mega"] = True
                invasion["estimated"] = -1000000
            else:
                invasion["is_mega"] = False
                invasion["estimated"] = (invasion["total"] - invasion["defeated"]) / invasion["defeat_rate"]

            self.invasions.append(invasion)

    
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

    
    def get_invasion_string(self, invasion: dict):
        if invasion["is_mega"] == True:
            time_string = "MEGA INVASION!"
            defeat_string = "---"
        else:
            time_string = self.convert_sec_to_timestr(invasion["estimated"])
            defeat_string = "{0} / {1}".format(invasion["defeated"], invasion["total"])

        info_string = "ロビー ： **{}**\n".format(invasion["district"])
        info_string += "残り時間 ： **{}**\n".format(time_string)
        info_string += "倒されたコグの数 ： **{}**\n\n".format(defeat_string)

        return info_string

    
    # HACK: This method is just used for DistrictTracker.
    def get_invasions(self):
        self.load_invasion_info()
        return self.invasions



# TODO: Make super class for Tracker.
class FieldOfficeTracker:

    def __init__(self, fieldoffice_info_channel, bot_user):
        self.fieldoffice_info_channel = fieldoffice_info_channel
        self.bot_user = bot_user
        self.fieldoffice_info_message = None

        self.url = "https://www.toontownrewritten.com/api/fieldoffices"
        self.embed_color = embed_color.FIELDOFFICE_INFO_COLOR
        self.progress = {}

        self.zoneid_lookup = {
            "3100": "Walrus Way", "3200": "Sleet Street", "3300": "Polar Place",
            "4100": "Alto Avenue", "4200": "Baritone Boulevard", "4300": "Tenor Terrace",
            "5100": "Elm Street", "5200": "Maple Street", "5300": "Oak Street",
            "9100": "Lullaby Lane", "9200": "Pajama Place"
        }


    async def notice(self):
        self.load_information()
        info_string, renew_time_string = self.get_info_string()
        fieldoffice_info_embed = discord.Embed(title="**TTR Realtime Information Board**", color=self.embed_color)
        fieldoffice_info_embed = fieldoffice_info_embed.add_field(name=":office: Field office", value=info_string)
        fieldoffice_info_embed = fieldoffice_info_embed.set_footer(text=renew_time_string)

        if self.fieldoffice_info_message is None:
            history = await self.fieldoffice_info_channel.history().flatten()
            if len(history) == 1 and history[0].author.id == self.bot_user.id:
                self.fieldoffice_info_message = history[0]
            else:
                await self.fieldoffice_info_channel.purge(limit=None)
                self.fieldoffice_info_message = await self.fieldoffice_info_channel.send(embed=fieldoffice_info_embed)
                return

        await self.fieldoffice_info_message.edit(embed=fieldoffice_info_embed)

    
    def load_information(self):
        self.progress = JsonStream().get_json_object(self.url)

    
    def convert_number_to_emoji(self, number: int):
        number_str = str(number)
        emoji_string = ":black_large_square:" * (3 - len(number_str))
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

    
    def get_fieldoffice_strings(self):
        fieldoffice_list = []
        for street_id, office in self.progress["fieldOffices"].items():
            fieldoffice_list.append({
                "difficulty": office["difficulty"] + 1,
                "annexes": office["annexes"],
                "street": self.zoneid_lookup[street_id],
                "open": office["open"]
            })

        fieldoffice_list = sorted(fieldoffice_list, key=operator.itemgetter("difficulty", "annexes"))

        fieldoffice_string = ""
        for office in fieldoffice_list:
            is_open = ":green_circle:" if office["open"] else ":x:"
            stars = ":black_large_square:" * (3 - office["difficulty"]) + ":star:" * office["difficulty"]
            annexes = self.convert_number_to_emoji(office["annexes"])
            street = office["street"]
            fieldoffice_string += f"{is_open}　{stars}　{annexes}　{street}\n"
        
        return fieldoffice_string

    
    def get_info_string(self):
        info_string = ""
        info_string += ":black_large_square:　**難易度** 　　**Annexes**　**Street**\n"
        info_string += self.get_fieldoffice_strings()
        info_string += "\n:green_circle:：Open\n" + \
                       ":x:：Closed\n\n"
        renew_time_string = "最終更新　{}".format(datetime.now(timezone(timedelta(hours=+9), "JST")).strftime("%H:%M"))
        
        return info_string, renew_time_string
