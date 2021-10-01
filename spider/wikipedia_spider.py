import concurrent
import json
import re
from typing import List, Set, Union

import requests
from bs4 import BeautifulSoup
from pandas.io.html import read_html
from tqdm import tqdm

_wiki_base_url_dict = {
    "en": "https://en.wikipedia.org",
    "ja": "https://ja.wikipedia.org",
    "ko": "https://ko.wikipedia.org",
    "ru": "https://ru.wikipedia.org",
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

    def process_body(self, body: str) -> Union[dict, None]:
        r = {}
        soup = BeautifulSoup(body, features="lxml")
        title = self.get_title(soup)
        if title is None:
            return None
        # info = self.get_info(body)
        info = self.get_info_plus(soup)
        if info == {}:
            return None
        info['paragraph_text'] = self.get_para_text(soup)
        # img_urls = self.get_image(soup)
        # info["imgs"] = img_urls
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

    def get_info_plus(self, soup: BeautifulSoup):

        infodict = {}
        infobox = soup.find("table", {"class": "infobox"})
        rows = infobox.findChildren("tr")
        for row in rows:
            if len(row.contents) != 2:
                continue
            # key = traverse_content('', row.contents[0])
            # value = traverse_content('', row.contents[1])
            key = row.contents[0].text
            value = row.contents[1].text
            infodict[key] = value
        return infodict

    def get_para_text(self, soup: BeautifulSoup):
        result_list = []
        body = soup.find("div", {"class": "mw-parser-output"})
        paragraphs = body.findChildren('p')
        for p in paragraphs:
            result_list.append(p.text)
        return result_list

    def get_image(self, soup: BeautifulSoup) -> List[str]:
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

    def get_lists(self, lists_of_lists_url: str) -> Set[str]:
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

    def get_links_from_list(self, list_url: str) -> Set[str]:
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

    def align_language_wrapper(self, url, lang_src, lang_tgt):
        r = requests.get(url, proxies=self.get_proxy())
        body = r.text
        soup = BeautifulSoup(body, features="lxml")
        lang_nav = soup.find("nav", {"id": "p-lang"})
        link_tag = lang_nav.find("a", string=lang_tgt)
        if link_tag is None:
            return None
        tgt_link = link_tag["href"]
        return {lang_src: url, lang_tgt: tgt_link}

    def align_language(self, urls_file, lang_src, lang_tgt: str):
        with open(urls_file, 'r', encoding='utf-8') as f:
            urls = [line[:-1] for line in f]
        try:
            result_urls = []
            with tqdm(total=len(urls)) as pbar:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = [executor.submit(self.align_language_wrapper, url, lang_src, lang_tgt) for url in urls]
                    for future in concurrent.futures.as_completed(futures):
                        r = future.result()
                        pbar.update(1)
                        if r is not None:
                            result_urls.append(r)
        except:
            file_name = f'data/{lang_src}-{lang_tgt}-align-urls.txt'
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(json.dumps(result_urls, ensure_ascii=False))
        else:
            file_name = f'data/{lang_src}-{lang_tgt}-align-urls.txt'
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(json.dumps(result_urls, ensure_ascii=False))

    def align_chinese_wrapper(self, url):
        lang_ko = '한국어'
        lang_ru = 'Русский'
        r = requests.get(url, proxies=self.get_proxy())
        body = r.text
        soup = BeautifulSoup(body, features="lxml")
        lang_nav = soup.find("nav", {"id": "p-lang"})
        link_tag_ko = lang_nav.find("a", string=lang_ko)
        link_tag_ru = lang_nav.find("a", string=lang_ru)
        if link_tag_ko is None and link_tag_ru is None:
            return None

        if link_tag_ko is not None:
            link_ko = link_tag_ko['href']
            res_ko = {'chinese': url, 'ko': link_ko}
        else:
            res_ko = None
        if link_tag_ru is not None:
            link_ru = link_tag_ru['href']
            res_ru = {'chinese': url, 'ru': link_ru}
        else:
            res_ru = None

        return res_ko, res_ru

    def align_chinese(self, urls_file: str):
        with open(urls_file, 'r', encoding='utf-8') as f:
            urls = ['https://zh.wikipedia.org/wiki/' + line[:-1] for line in f]

        # urls = urls[:50]

        try:
            result_urls = []
            with tqdm(total=len(urls)) as pbar:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    futures = [executor.submit(self.align_chinese_wrapper, url) for url in urls]
                    for future in concurrent.futures.as_completed(futures):
                        r = future.result()
                        pbar.update(1)
                        result_urls.append(r)
        except:
            ko_list = [u[0] for u in result_urls if u is not None and u[0] is not None]
            ru_list = [u[1] for u in result_urls if u is not None and u[1] is not None]
            file_name_ko = 'data/chinese-ko-align-urls.txt'
            file_name_ru = 'data/chinese-ru-align-urls.txt'
            with open(file_name_ko, 'w', encoding='utf-8') as f:
                f.write(json.dumps(ko_list, ensure_ascii=False))
            with open(file_name_ru, 'w', encoding='utf-8') as f:
                f.write(json.dumps(ru_list, ensure_ascii=False))
        else:
            ko_list = [u[0] for u in result_urls if u is not None and u[0] is not None]
            ru_list = [u[1] for u in result_urls if u is not None and u[1] is not None]
            file_name_ko = 'data/chinese-ko-align-urls.txt'
            file_name_ru = 'data/chinese-ru-align-urls.txt'
            with open(file_name_ko, 'w', encoding='utf-8') as f:
                f.write(json.dumps(ko_list, ensure_ascii=False))
            with open(file_name_ru, 'w', encoding='utf-8') as f:
                f.write(json.dumps(ru_list, ensure_ascii=False))

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
