import configparser
import json

from spider import WikiSpider

keywords = ["AK-47突击步枪", "CAESAR自行火炮", "东北大学_(中国)", "北京理工大学"]

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read("config.ini")
    s = WikiSpider(config)

    with open("result.json", 'w', encoding="utf-8") as f:
        result_list = [s.search_by_chinese(k) for k in keywords]
        f.write(json.dumps(result_list, ensure_ascii=False))
