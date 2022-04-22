"""
Information tracker
=====
author: Snow Rabbit
"""

import operator
from abc import abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Union

import discord
from bs4.element import ResultSet
from discord.channel import TextChannel
from discord.embeds import Embed
from discord.message import Message
from discord.user import ClientUser

from . import embed_color
from .util.web_stream import HTMLStream, JsonStream


class Tracker:
    """Tracker
    ----------

    Super class of the tracker that collect and display information.
    The subclasses need to implement `load_information` and `make_info_strings`.

    Attributes:
        info_channel (:class:`TextChannel`):
            Channel to display information.
        bot_user (:class:`ClientUser`):
            The bot user to be used for tracking.
        info_message (:class:`Optional[Message]`):
            Message displaying information.
            It is set to None at initialization.
        embed_color: (:class:`int`): 
            Hex value of color for `discord.Embed`.
        embed_field_tytle: (:class:`str`): 
            Title string of the information.
            (It is not the `title` argument of `discord.Embed`.)
            Defined in the subclasses and used inside `make_info_strings`.
    """

    def __init__(self, info_channel: TextChannel, bot_user: ClientUser) -> None:
        self.info_channel: TextChannel = info_channel
        self.bot_user: ClientUser = bot_user
        self.info_message: Optional[Message] = None
        self.embed_color: int
        self.embed_field_tytle: str

    
    def make_embed(self, info_string_list: List[Dict[str, str]]) -> Embed:
        info_embed = discord.Embed(title="**TTR Realtime Information Board**", color=self.embed_color)
        for info_string in info_string_list:
            info_embed.add_field(name=info_string["name"], value=info_string["value"], inline=False)
        renew_time_string = f"最終更新　{datetime.now(timezone(timedelta(hours=+9), 'JST')).strftime('%H:%M')}"
        info_embed = info_embed.set_footer(text=renew_time_string)
        
        return info_embed

    
    async def notice(self) -> None:
        # HACK: Shouldn't handle 'load_information' in 'notice'.
        if type(self) is not InvasionTracker:
            self.load_information()
        info_string_list = self.make_info_strings()
        info_embed = self.make_embed(info_string_list)

        if self.info_message is None:
            history = await self.info_channel.history().flatten()
            if len(history) == 1 and history[0].author.id == self.bot_user.id:
                self.info_message = history[0]
            else:
                await self.info_channel.purge(limit=None)
                self.info_message = await self.info_channel.send(embed=info_embed)
                return

        await self.info_message.edit(embed=info_embed)


    @abstractmethod
    def load_information(self) -> None:
        raise NotImplementedError()


    @abstractmethod
    def make_info_strings(self) -> List[Dict[str, str]]:
        raise NotImplementedError()


    def load_data_api(self, url: str) -> dict:
        return JsonStream().get_json_object(url=url)


    def load_data_scraping(self, url: str) -> ResultSet:
        return HTMLStream().get_soup_object(url=url, soup_class="list-group-item sub-component")

    
    def convert_number_to_emoji(self, number: Union[int, str]) -> str:
        num2emoji = {
            "1": ":one:", "2": ":two:", "3": ":three:",
            "4": ":four:", "5": ":five:", "6": ":six:",
            "7": ":seven:", "8": ":eight:", "9": ":nine:",
            "0": ":zero:"
        }
        emoji_string = ""
        for num in str(number):
            emoji_string += num2emoji[num]

        return emoji_string

    
    def convert_number_to_fullwidth(self, number: Union[int, str]) -> str:
        return str(number).translate(
                    str.maketrans({chr(0x0021 + i): chr(0xFF01 + i) for i in range(94)})
               ).replace(" ", "\u3000")


class DistrictTracker(Tracker):

    def __init__(self, info_channel: TextChannel, bot_user: ClientUser) -> None:
        super().__init__(info_channel, bot_user)
        self.embed_color: int = embed_color.DISTRICT_INFO_COLOR
        self.embed_field_tytle: str = ":park: ロビー情報"
        self.url: str = "https://toontownrewritten.com/api/population"

        self.total_population: int
        self.population_by_district: list
        self.invasions: list

        # HACK: There is no need to create an InvasionTracker instance just to find out invasion information.
        self.invasions_tracker = InvasionTracker(info_channel=None, bot_user=None)
    

    def load_information(self) -> None:
        json_object = self.load_data_api(url=self.url)
        self.total_population = json_object["totalPopulation"]
        self.population_by_district = sorted(json_object["populationByDistrict"].items())
        self.invasions = self.invasions_tracker.get_invasions()

    
    def make_info_strings(self) -> List[Dict[str, str]]:
        all_population_emoji = self.convert_number_to_emoji(self.total_population)
        info_string = f"現在の総プレイ人口：{all_population_emoji}人\n\n" + \
                       "　　人口　　　　ロビー\n" + \
                      f"{self.make_district_string()}" + \
                       "\n:speech_balloon:：スピードチャットのみ使用可能\n" + \
                       ":shield:：特定のイベントが開催されない\n" + \
                       ":sparkles:：召喚によるコグの侵略が発生しない\n" + \
                       ":gear:：コグの侵略が進行中\n\n"
        
        return [{"name": self.embed_field_tytle, "value": info_string}]

    
    def make_district_string(self) -> str:
        status_string = ""
        for pd in self.population_by_district:
            if pd[1] <= 300:
                status_string += ":blue_circle: "
            elif pd[1] > 500:
                status_string += ":red_circle: "
            else:
                status_string += ":green_circle: "

            status_string += self.convert_number_to_fullwidth(str(pd[1]).rjust(3))
            status_string += f"　　**{pd[0]}** "

            if pd[0] in ["Boingbury", "Gulp Gulch", "Whoosh Rapids"]:
                status_string += ":speech_balloon:"
            if pd[0] in ["Blam Canyon", "Fizzlefield", "Gulp Gulch", "Splat Summit", "Zapwood"]:
                status_string += ":shield:"
            if pd[0] in ["Gulp Gulch", "Splat Summit"]:
                status_string += ":sparkles:"
            
            # HACK: Need refactoring.
            if pd[0] in str(self.invasions):
                status_string += ":gear:"
                
            status_string += "\n"

        return status_string


class ServerTracker(Tracker):

    def __init__(self, info_channel: TextChannel, bot_user: ClientUser) -> None:
        super().__init__(info_channel, bot_user)
        self.embed_field_tytle: str = ":chart_with_downwards_trend: サーバー稼働状況"
        self.url: str = "https://status.toontownrewritten.com/"

        self.pr_soup: ResultSet = None
        self.is_stable: int = 1

    
    def load_information(self) -> None:
        self.pr_soup = self.load_data_scraping(url=self.url)

    
    def make_info_strings(self) -> List[Dict[str, str]]:
        info_string = "\n**Game Servers**\n" + \
                      self.get_status_emoji(self.pr_soup[1].small.string) + " ゲームサーバー\n" + \
                      self.get_status_emoji(self.pr_soup[2].small.string) + " スピードチャット＋\n" + \
                      self.get_status_emoji(self.pr_soup[3].small.string) + " ゲームサービス全般\n" + \
                      "\n**Website**\n" + \
                      self.get_status_emoji(self.pr_soup[4].small.string) + " ダウンロードサーバー\n" + \
                      self.get_status_emoji(self.pr_soup[5].small.string) + " 公式ホームページ/ログインサーバー\n" + \
                      "\n**Support System**\n" + \
                      self.get_status_emoji(self.pr_soup[0].small.string) + " メールサポート\n"
        
        self.set_embed_color()

        return [{"name": self.embed_field_tytle, "value": info_string}]

    
    def get_status_emoji(self, string: str) -> str:
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

        
    def set_embed_color(self) -> None:
        if self.is_stable == 1:
            self.embed_color = embed_color.SERVER_INFO_STABLE_COLOR
        elif self.is_stable == 2:
            self.embed_color = embed_color.SERVER_INFO_ISSUE_COLOR
        elif self.is_stable == 3:
            self.embed_color = embed_color.SERVER_INFO_OUTAGE_COLOR
        else:
            self.embed_color = embed_color.SERVER_INFO_DOWN_COLOR


class InvasionTracker(Tracker):

    def __init__(self, info_channel: TextChannel, bot_user: ClientUser) -> None:
        super().__init__(info_channel, bot_user)
        self.embed_color: int = embed_color.INVASION_INFO_COLOR
        self.embed_field_tytle: str = ":gear: 現在進行中のコグ侵略情報"
        self.url: str = "https://toonhq.org/api/v1/invasion/"

        self.invasions: list = []

    
    def load_information(self) -> None:
        json_object = self.load_data_api(self.url)
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

    
    def make_info_strings(self) -> List[Dict[str, str]]:
        info_string_list = [{
            "name": self.embed_field_tytle,
            "value": "表示されている残り時間は実際と異なる場合があります。\n"
        }]
        for invasion in self.invasions:
            cog_name = f"**{invasion['status']} {invasion['cog']}**"
            info_string = self.get_invasion_string(invasion)
            info_string_list.append({
                "name": cog_name,
                "value": info_string
            })
        
        return info_string_list

    
    async def countdown(self, interval: int=1) -> None:
        for i, invasion in enumerate(self.invasions[:]):
            if invasion["estimated"] >= 0:
                self.invasions[i]["estimated"] -= interval
        await self.notice()


    def get_invasion_string(self, invasion: dict) -> str:
        if invasion["is_mega"]:
            time_string = "MEGA INVASION!"
            defeat_string = "---"
        else:
            time_string = self.convert_sec_to_timestr(invasion["estimated"])
            defeat_string = f"{invasion['defeated']} / {invasion['total']}"

        info_string = f"ロビー ： **{invasion['district']}**\n" + \
                      f"残り時間 ： **{time_string}**\n" + \
                      f"倒されたコグの数 ： **{defeat_string}**\n\n"

        return info_string

    
    def convert_sec_to_timestr(self, left_sec: str) -> str:
        if left_sec < 30:
            return "まもなく終了"
        
        time_string = ""
        if left_sec > 3600:
            hour = int(left_sec / 3600)
            time_string += f"{hour} : "
            left_sec = left_sec - 3600 * hour
        minute = int(left_sec / 60)
        time_string += f"{minute:02} : "
        second = int(left_sec - minute * 60)
        time_string += f"{second:02}"

        return time_string

    
    # HACK: This method is just used for DistrictTracker.
    def get_invasions(self) -> dict:
        self.load_information()
        return self.invasions


class FieldOfficeTracker(Tracker):

    def __init__(self, info_channel: TextChannel, bot_user: ClientUser) -> None:
        super().__init__(info_channel, bot_user)
        self.embed_color: int = embed_color.FIELDOFFICE_INFO_COLOR
        self.embed_field_tytle: str = ":office: Field Office情報"
        self.url: str = "https://www.toontownrewritten.com/api/fieldoffices"

        self.fieldoffice_list: list
        self.zoneid_dict: dict = {
            "3100": "Walrus Way", "3200": "Sleet Street", "3300": "Polar Place",
            "4100": "Alto Avenue", "4200": "Baritone Boulevard", "4300": "Tenor Terrace",
            "5100": "Elm Street", "5200": "Maple Street", "5300": "Oak Street",
            "9100": "Lullaby Lane", "9200": "Pajama Place"
        }

    
    def load_information(self) -> None:
        json_object = self.load_data_api(url=self.url)
        self.fieldoffice_list = []
        for street_id, office in json_object["fieldOffices"].items():
            self.fieldoffice_list.append({
                "difficulty": office["difficulty"] + 1,
                "annexes": office["annexes"],
                "street": self.zoneid_dict[street_id],
                "open": office["open"]
            })

        self.fieldoffice_list = sorted(self.fieldoffice_list, key=operator.itemgetter("difficulty", "annexes"))

    
    def make_info_strings(self) -> List[Dict[str, str]]:
        info_string = "**Stars** 　　 **Annexes**　  　     **Street**\n"
        
        for office in self.fieldoffice_list:
            is_open = ":green_circle:" if office["open"] else ":x:"
            stars = ":black_large_square:" * (3 - office["difficulty"]) + \
                    ":star:" * office["difficulty"]
            annexes = self.convert_number_to_fullwidth(str(office["annexes"]).rjust(3))
            street = office["street"]
            info_string += f"{stars}　 {annexes}　 {is_open}  {street}\n"
        
        info_string += "\n:green_circle:：Open\n" + \
                       ":x:：Closed\n\n"
        
        return [{"name": self.embed_field_tytle, "value": info_string}]


# TODO: Remake GroupTracker
class GroupTracker(Tracker):
    
    def __init__(self, info_channel: TextChannel, bot_user: ClientUser) -> None:
        super().__init__(info_channel, bot_user)

    
    def load_information(self) -> None:
        return super().load_information()

    
    def make_info_strings(self) -> List[Dict[str, str]]:
        return super().make_info_strings()
