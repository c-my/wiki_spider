import re

import requests
from bs4 import BeautifulSoup
from pandas.io.html import read_html

_wiki_base_url_dict = {
    "en": "https://en.wikipedia.org",
    "ja": "https://ja.wikipedia.org",
    "ko": "https://ko.wikipedia.org",
    "zh": "https://zh.wikipedia.org"
}

_wiki_list_regex_dict = {
    "en": r"^List of[\s\S]*$",
    "ja": r"^[\s\S]+一覧$",
}


def _is_en_content_page(url: str) -> bool:
    return not (":" in url or
                url.startswith("/wiki/List_of") or
                url.startswith("/wiki/Lists_of")
                )


def _is_ja_content_page(url: str) -> bool:
    return not (":" in url or
                url.endswith("一覧")
                )


def _is_ko_content_page(url: str) -> bool:
    raise NotImplementedError


_is_content_page_func = {
    "en": _is_en_content_page,
    "ja": _is_ja_content_page,
    'ko': _is_ko_content_page,
}


class WikiSpider:
    def __init__(self, config, language):
        self.proxy_config = config["PROXY"]
        if language not in _wiki_base_url_dict:
            raise ValueError("language code [{}] is not supported".format(language))

        self.language = language
        self.wiki_base_url = _wiki_base_url_dict[self.language]
        self.wiki_url = self.wiki_base_url + "/wiki/"

    def search_by_chinese(self, keyword):
        url = self.get_wiki_url(keyword)
        return self.get_web_content(url)

    def get_web_content(self, url, is_from_file=False) -> dict:
        if not is_from_file:
            r = requests.get(url, proxies=self.get_proxy())

            return self.process_body(r.text)
        else:
            text = ""
            with open(url, 'r', encoding='utf-8') as f:
                text = f.read()
            return self.process_body(text)

    def process_body(self, body: str) -> dict:
        r = {}
        soup = BeautifulSoup(body, features="lxml")
        title = self.get_title(soup)
        if title is None:
            return None
        info = self.get_info(body)
        if info == {}:
            return None
        img_urls = self.get_image(soup)
        info["imgs"] = img_urls
        r[title] = info
        return r

    def get_title(self, soup: BeautifulSoup):
        head = soup.find("h1", {"id": "firstHeading"})
        if head is None:
            return None
        return head.text

    def get_info(self, body) -> dict:
        """
        :param body: html content
        :return: dictionary contains property retrieved from wikipedia infobox
        """
        info_dict = {}
        try:
            info_boxes = read_html(str(body), index_col=0, attrs={"class": "infobox"})
        except ValueError as e:
            return info_dict
        tmp_dict = info_boxes[0].to_dict()
        for k, v in tmp_dict.items():
            info_dict = v
            break  # tmp_dict only has one key
        # todo：translate to simplified Chinese
        # remove cite chars and \xa0
        info_dict = {
            self.strip_info_key(str(k)): self.strip_info_value(str(v)) for
            k, v in
            info_dict.items() if
            k != v and str(k).lower() != "nan" and str(v).lower() != "nan"}
        return info_dict

    def get_image(self, soup: BeautifulSoup) -> list[str]:
        img_urls = []
        # soup = BeautifulSoup(body, features="lxml")
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

    def get_lists(self, lists_of_lists_url: str) -> set[str]:
        """
        get lists from a wikipedia lists_of_lists page
        :param lists_of_lists_url: page url
        :return: set of lists
        """
        r = requests.get(lists_of_lists_url, proxies=self.get_proxy())
        body = r.text
        soup = BeautifulSoup(body, features="lxml")
        links = soup.findAll("a", {"title": re.compile(_wiki_list_regex_dict[self.language])})
        list_link_set = {self.wiki_base_url + link["href"] for link in links}
        return list_link_set

    def get_links_from_list(self, list_url: str) -> set[str]:
        """
        get all related links in wikipedia list page
        :param list_url: page url
        :return: set of related links
        """
        r = requests.get(list_url, proxies=self.get_proxy())
        body = r.text
        soup = BeautifulSoup(body, features="lxml")
        possible_area = soup.findAll("div", {"class": "mw-parser-output"})
        if len(possible_area) == 0:
            return set()
        area = possible_area[0]

        links = area.findAll("a", {"href": re.compile(r"^(/wiki/)[\s\S]*$")})
        link_set = {self.wiki_base_url + link["href"] for link in links if self.is_content_page(link["href"])}
        return link_set

    def get_wiki_url(self, keyword: str) -> str:
        return self.wiki_url + keyword

    def is_content_page(self, url: str) -> bool:
        return _is_content_page_func[self.language](url)

    def strip_info_key(self, info: str) -> str:
        # r = re.sub(r'\[(\d)*\]', "", info.replace("\xa0", "")
        #            .replace("\ufeff", "")
        #            )
        return info

    def strip_info_value(self, info: str) -> str:
        r = re.sub(r'\[(\d)*\]', "", info
                   .replace(".mw-parser-output", "")
                   .replace(".geo-default", "")
                   .replace(".geo-dms", "")
                   .replace(".geo-nondefault", "")
                   .replace(".longitude", "")
                   .replace(".latitude", "")
                   .replace(".geo-dec", "")
                   .replace(".geo-multi-punct", "")
                   .replace("{display:inline}", "")
                   .replace("{display:none}", "")
                   .replace("{white-space:nowrap}", "")
                   )

        return r.replace(" ,", "").strip().lstrip(",")

    def get_proxy(self) -> dict:
        return {
            'http': self.proxy_config["url"],
            'https': self.proxy_config["url"],
        }
