import concurrent.futures
import configparser
import json
import datetime
import logging

from spider.baidu_spider import BaiduSpider
from spider.wikipedia_spider import WikiSpider

military_list_of_lists_url_list_en = [
    "https://en.wikipedia.org/wiki/Lists_of_accidents_and_incidents_involving_military_aircraft",
    "https://en.wikipedia.org/wiki/Lists_of_armoured_fighting_vehicles",
    "https://en.wikipedia.org/wiki/List_of_artillery", "https://en.wikipedia.org/wiki/Lists_of_gun_cartridges",
    "https://en.wikipedia.org/wiki/Lists_of_military_aircraft_by_nation",
    "https://en.wikipedia.org/wiki/Lists_of_Bulgarian_military_aircraft",
    "https://en.wikipedia.org/wiki/Lists_of_military_equipment",
    "https://en.wikipedia.org/wiki/Lists_of_currently_active_military_equipment_by_country",
    "https://en.wikipedia.org/wiki/Lists_of_military_installations",
    "https://en.wikipedia.org/wiki/Lists_of_naval_flags", "https://en.wikipedia.org/wiki/Lists_of_swords",
    "https://en.wikipedia.org/wiki/Lists_of_weapons",
    "https://en.wikipedia.org/wiki/Lists_of_World_War_II_military_equipment",
]

military_list_of_lists_url_list_jp = [
    "https://ja.wikipedia.org/wiki/%E8%BB%8D%E4%BA%8B%E5%AD%A6%E8%80%85",
    "https://ja.wikipedia.org/wiki/%E8%BB%8D%E4%BA%8B%E7%95%A5%E8%AA%9E%E4%B8%80%E8%A6%A7",
    "https://ja.wikipedia.org/wiki/%E8%BB%8D%E9%9A%8A%E3%81%AE%E9%9A%8E%E7%B4%9A",
    "https://ja.wikipedia.org/wiki/%E5%90%84%E5%9B%BD%E3%81%AE%E8%BB%8D%E9%9A%8A%E3%81%AE%E4%B8%80%E8%A6%A7",
    "https://ja.wikipedia.org/wiki/%E9%99%B8%E8%BB%8D%E3%81%AE%E4%B8%80%E8%A6%A7",
    "https://ja.wikipedia.org/wiki/%E6%B5%B7%E8%BB%8D%E3%81%AE%E4%B8%80%E8%A6%A7",
    "https://ja.wikipedia.org/wiki/%E7%A9%BA%E8%BB%8D%E3%81%AE%E4%B8%80%E8%A6%A7",
    "https://ja.wikipedia.org/wiki/%E6%AD%B4%E5%8F%B2%E4%B8%8A%E3%81%AE%E8%BB%8D%E9%9A%8A%E3%81%AE%E4%B8%80%E8%A6%A7",
    "https://ja.wikipedia.org/wiki/%E7%A9%BA%E8%BB%8D%E5%9F%BA%E5%9C%B0%E3%81%AE%E4%B8%80%E8%A6%A7",
    "https://ja.wikipedia.org/wiki/%E3%82%A2%E3%83%A1%E3%83%AA%E3%82%AB%E7%A9%BA%E8%BB%8D%E5%9F%BA%E5%9C%B0%E3%81%AE%E4%B8%80%E8%A6%A7",
    "https://ja.wikipedia.org/wiki/%E7%89%B9%E6%AE%8A%E9%83%A8%E9%9A%8A%E3%81%AE%E4%B8%80%E8%A6%A7",
    "https://ja.wikipedia.org/wiki/%E9%99%B8%E4%B8%8A%E8%87%AA%E8%A1%9B%E9%9A%8A%E3%81%AE%E9%A7%90%E5%B1%AF%E5%9C%B0%E4%B8%80%E8%A6%A7",
    "https://ja.wikipedia.org/wiki/%E6%B5%B7%E4%B8%8A%E8%87%AA%E8%A1%9B%E9%9A%8A%E3%81%AE%E9%99%B8%E4%B8%8A%E6%96%BD%E8%A8%AD%E4%B8%80%E8%A6%A7",
    "https://ja.wikipedia.org/wiki/%E8%88%AA%E7%A9%BA%E8%87%AA%E8%A1%9B%E9%9A%8A%E3%81%AE%E5%9F%BA%E5%9C%B0%E4%B8%80%E8%A6%A7",
    "https://ja.wikipedia.org/wiki/%E8%BB%8D%E9%9A%8A%E3%82%92%E4%BF%9D%E6%9C%89%E3%81%97%E3%81%A6%E3%81%84%E3%81%AA%E3%81%84%E5%9B%BD%E5%AE%B6%E3%81%AE%E4%B8%80%E8%A6%A7",
    "https://ja.wikipedia.org/wiki/%E9%98%B2%E8%A1%9B%E4%B8%8D%E7%A5%A5%E4%BA%8B#%E4%B8%BB%E3%81%AA%E4%B8%8D%E7%A5%A5%E4%BA%8B",
    "https://ja.wikipedia.org/wiki/%E8%BB%8D%E5%AD%A6%E8%80%85",
    "https://ja.wikipedia.org/wiki/%E6%88%A6%E4%BA%89%E4%B8%80%E8%A6%A7",
    "https://ja.wikipedia.org/wiki/%E6%88%A6%E9%97%98%E4%B8%80%E8%A6%A7",
]


def get_web_content_wrapper(wiki_spider: WikiSpider, url: str, loggers: logging.Logger, is_from_file=False):
    try:
        return wiki_spider.get_web_content(url, is_from_file=is_from_file)
    except Exception as e:
        loggers.warning("failed to get content: {}".format(url))
        return None


def get_web_content_json(configure, language, url_list_file, output_file, is_from_file=False):
    logging.basicConfig(filename='spider.log', format="%(asctime)s  %(filename)s : %(levelname)s  %(message)s",
                        datefmt='%Y-%m-%d: %H:%M:%S',
                        level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    s = WikiSpider(configure, language)

    with open(url_list_file, "r", encoding='utf-8') as f:
        for line in f:
            url_list.append(line[:-1])

    result_list = []
    logger.info("spider start")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(get_web_content_wrapper, s, url, logger, is_from_file) for url in url_list]
        for future in concurrent.futures.as_completed(futures):
            r = future.result()
            if r is not None:
                result_list.append(r)
    logger.info("spider finished")
    logger.info("writing result to file: {}".format(output_file))
    with open(output_file, 'w', encoding='utf-8') as f:
        for result in result_list:
            j = json.dumps(result, ensure_ascii=False)
            f.write(j + '\n')
    logger.info("writing finished")
    logger.info("{} line writen".format(len(result_list)))


def get_web_list(configure, list_of_list_url_list, language, output_path):
    logging.basicConfig(filename='spider.log', format="%(asctime)s  %(filename)s : %(levelname)s  %(message)s",
                        datefmt='%Y-%m-%d: %H:%M:%S',
                        level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    s = WikiSpider(configure, language)

    # for idx, url in enumerate(url_list):
    #     s.get_web_content(url)
    #     if idx % 10 == 0:
    #         logger.debug("{} urls processed".format(idx))
    #         # print(idx)

    link_set = set()
    try:
        for list_url in list_of_list_url_list:
            list_list = s.get_lists(list_url)
            for list_page in list_list:
                new_url = s.get_links_from_list(list_page)

                link_set |= new_url
    except Exception as e:
        with open(output_path, "w", encoding="utf-8") as f:
            for u in link_set:
                f.write(u + "\n")
        print(e)
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            for u in link_set:
                f.write(u + "\n")
    print(len(link_set))


def test_baidu(config):
    s = BaiduSpider(config)
    r = s.get_web_content("https://baike.baidu.com/item/%E6%AD%BC-20")
    j = json.dumps(r, ensure_ascii=False)
    with open("test.txt", "w", encoding="utf-8") as f:
        f.write(j + "\n")
    # print(s.get_web_content("https://baike.baidu.com/item/%E6%AD%BC-20"))


if __name__ == '__main__':
    url_list = []

    config = configparser.ConfigParser()
    config.read("config.ini")
    # get_web_list(config, military_list_of_lists_url_list_jp, "ja", "data/ja_wiki_urls.txt")
    # get_web_content_json(config, 'zh', "data/zh_wiki_urls.txt", "data/zh_data.txt", is_from_file=True)
    test_baidu(config)
