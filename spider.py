import re

import requests
from bs4 import BeautifulSoup
from pandas.io.html import read_html


class WikiSpider:
    def __init__(self, config):
        self.proxy_config = config["PROXY"]
        self.wiki_base_url = "https://zh.wikipedia.org"
        self.wiki_url = self.wiki_base_url + "/wiki/"

    def search_by_chinese(self, keyword):
        url = self.get_wiki_url(keyword)
        return self.get_web_content(url)

    def get_web_content(self, url) -> dict:
        r = requests.get(url, proxies=self.get_proxy())

        return self.process_body(r.text)

    def process_body(self, body) -> dict:
        info = self.get_info(body)
        img_urls = self.get_image(body)
        info["imgs"] = img_urls
        return info

    def get_info(self, body) -> dict:
        """
        :param body: html content
        :return: dictionary contains property retrieved from wikipedia infobox
        """
        info_dict = {}

        info_boxes = read_html(str(body), index_col=0, attrs={"class": "infobox vcard"})
        tmp_dict = info_boxes[0].to_dict()
        for k, v in tmp_dict.items():
            info_dict = v
            break  # tmp_dict only has one key
        # todo：translate to simplified Chinese
        # remove cite chars and \xa0
        info_dict = {k: re.sub(r'\[(\d)*\]', "", str(v).replace("\xa0", "")) for k, v in info_dict.items() if
                     k != v and str(k).lower() != "nan" and str(v).lower() != "nan"}
        return info_dict

    def get_image(self, body) -> list[str]:
        img_urls = []
        soup = BeautifulSoup(body, features="lxml")
        thumbs = soup.findAll("img", {"class": "thumbimage"})
        for thumb in thumbs:
            img_page_url = self.wiki_base_url + thumb.parent["href"]
            img_page = requests.get(img_page_url, proxies=self.get_proxy())
            img_page_body = img_page.text
            s = BeautifulSoup(img_page_body, features="lxml")
            full_media_div = s.findAll("div", {"class": "fullMedia"})[0]
            img_url = "https:" + full_media_div.findAll("a", {"class": "internal"})[0]["href"]
            img_urls.append(img_url)
        return img_urls

    def get_wiki_url(self, keyword) -> str:
        return self.wiki_url + keyword

    def get_proxy(self) -> dict:
        return {
            'http': self.proxy_config["url"],
            'https': self.proxy_config["url"],
        }
