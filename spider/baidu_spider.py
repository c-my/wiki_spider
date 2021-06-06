import re
from urllib.parse import unquote
from typing import List, Union

import requests
from bs4 import BeautifulSoup


class BaiduSpider:
    def __init__(self, config):
        self.baidu_item_base_url = "https://baike.baidu.com/item/"
        self.baidu_base_url = "https://baike.baidu.com/"
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"
        }
        return

    def get_web_content_by_keyword(self, key, is_from_file=False) -> dict:
        return self.get_web_content(self.baidu_item_base_url + key, is_from_file)

    def get_web_content(self, url, is_from_file=False) -> dict:
        body_text = self.get_web_body_text(url, is_from_file)
        if body_text is None:
            return {}
        return self.process_body(body_text)

    def get_extra_links(self, url: str, is_from_file=False) -> List[str]:
        extra_links = []

        body_text = self.get_web_body_text(url, is_from_file)
        soup = BeautifulSoup(body_text, features="lxml")
        left_form = soup.find("dl", {"class": "basicInfo-block basicInfo-left"})
        right_form = soup.find("dl", {"class": "basicInfo-block basicInfo-right"})
        if left_form is not None:
            left_keys = left_form.findChildren("dt")
            left_values = left_form.findChildren("dd")
            for i in range(len(left_keys)):
                hyper_link_tag = left_values[i].find("a")
                if hyper_link_tag is not None:
                    link = hyper_link_tag["href"]
                    extra_links.append(unquote(self.baidu_base_url[:-1] + link))

        if right_form is not None:
            right_keys = right_form.findChildren("dt")
            right_values = right_form.findChildren("dd")
            for i in range(len(right_keys)):
                hyper_link_tag = right_values[i].find("a")
                if hyper_link_tag is not None:
                    link = hyper_link_tag["href"]
                    extra_links.append(unquote(self.baidu_base_url[:-1] + link))
        return extra_links

    def get_web_body_text(self, url, is_from_file=False) -> Union[str, None]:
        if not is_from_file:
            r = requests.get(url, headers=self.headers, timeout=5)
            if not r.status_code == 200:
                return None
            return r.text
        else:
            text = ""
            with open(url, 'r', encoding='utf-8') as f:
                text = f.read()
            return text

    def process_body(self, body: str) -> dict:
        r = {}
        soup = BeautifulSoup(body, features="lxml")
        title = self.get_title(soup)
        if title is None:
            return None
        info = self.get_info(soup)
        if info == {}:
            return None
        img_urls = self.get_image(soup)
        summary = self.get_summary(soup)
        info["summary"] = summary
        info["imgs"] = img_urls

        r[title] = info
        return r

    def get_title(self, soup: BeautifulSoup):
        head = soup.find("dd", {"class": "lemmaWgt-lemmaTitle-title"}).findChild('h1')

        if head is None:
            return None
        return head.text

    def get_info(self, soup: BeautifulSoup) -> dict:
        """
        :param body: html content
        :return: dictionary contains property retrieved from wikipedia infobox
        """
        info_dict = {}
        left_form = soup.find("dl", {"class": "basicInfo-block basicInfo-left"})
        right_form = soup.find("dl", {"class": "basicInfo-block basicInfo-right"})
        if left_form is not None:
            left_keys = left_form.findChildren("dt")
            left_values = left_form.findChildren("dd")
            for i in range(len(left_keys)):
                info_dict[left_keys[i].text] = self.strip_info_value(left_values[i].text)
        if right_form is not None:
            right_keys = right_form.findChildren("dt")
            right_values = right_form.findChildren("dd")
            for i in range(len(right_keys)):
                info_dict[right_keys[i].text] = self.strip_info_value(right_values[i].text)

        return info_dict

    def get_summary(self, soup: BeautifulSoup):
        s = soup.find("div", {"class": "lemma-summary"}).text
        s = re.sub(r'\[(\d)*\]', "", s.replace("\n", ""))
        return s

    def get_image(self, soup: BeautifulSoup) -> List[str]:
        image_urls = []
        image_tags = soup.findAll("div", {"class": "lemma-picture"})
        for tag in image_tags:
            image_href = tag.find("a", {"class": "image-link"})["href"]
            r = requests.get(self.baidu_base_url + image_href[1:], headers=self.headers)
            s = BeautifulSoup(r.text, features="lxml")
            if s.find("img", {"id": "imgPicture"}) is None:
                continue
            image_urls.append(s.find("img", {"id": "imgPicture"})["src"])
        return image_urls

    def get_proxy(self) -> dict:
        return {
            'http': self.proxy_config["url"],
            'https': self.proxy_config["url"],
        }

    def strip_info_key(self, key: str):
        return key.strip("\n")

    def strip_info_value(self, value: str):
        return value.strip("\n")
