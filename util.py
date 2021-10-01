import os
from pathlib import Path

url_file = "data/en_wiki_urls.txt"


def build_baidubaike_url_list():
    file_list = []
    files = os.listdir("data/baidubaike")
    for file in files:
        file_list.append(file)
    with open("data/baidu_baike_urls.txt", "w", encoding="utf-8") as f:
        for file in file_list:
            with open("data/baidubaike/" + file, "r", encoding="utf-8") as g:
                urls = g.readlines()
            for url in urls:
                f.write("https://baike.baidu.com/item/" + url)


def build_wiki_url_list():
    line_list = []
    with open(url_file, "r", encoding="utf-8") as f:
        line_list = f.readlines()
    for i, line in enumerate(line_list):
        idx = line.find("#")
        if idx != -1:
            line_list[i] = line[:idx] + "\n"
    result = list(set(line_list))
    with open("t.txt", "w", encoding="utf-8") as f:
        for r in result:
            f.write(r)


def generate_wiki_file_list():
    dir = os.listdir('./data/wikiPages')
    abs_path_list = []
    for f in dir:
        if os.path.isdir(f):
            continue
        # print(f)
        abs_path_list.append('data/wikiPages/'+f)
    with open('data/wiki_page_url_tmp.txt', 'w', encoding='utf-8') as f:
        for p in abs_path_list:
            f.write(p + '\n')
    return abs_path_list


if __name__ == '__main__':
    # build_baidubaike_url_list()
    abs_path_list = generate_wiki_file_list()
