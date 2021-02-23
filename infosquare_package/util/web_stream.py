import json
import urllib.request

import requests
from bs4 import BeautifulSoup


class JsonStream:

    def get_json_object(self, url):
        headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0"}
        request = urllib.request.Request(url=url, headers=headers)
        response = urllib.request.urlopen(request)
        json_object = json.loads(response.read().decode("utf8"))

        return json_object



class HTMLStream:
    
    def get_html_object(self, url):
        headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:47.0) Gecko/20100101 Firefox/47.0"}
        html_object = requests.get(url, headers=headers)

        return html_object

    
    def get_soup_object(self, url, soup_class):
        html_object = self.get_html_object(url)
        soup = BeautifulSoup(html_object.content, "html.parser")
        pr_soup = soup.find_all(class_=soup_class)

        return pr_soup
