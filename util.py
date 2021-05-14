url_file = "data/en_wiki_urls.txt"

if __name__ == '__main__':
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
