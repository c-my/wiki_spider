import os

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


if __name__ == '__main__':
    build_baidubaike_url_list()
