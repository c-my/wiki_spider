import os

file_root = 'C:\\Users\\CaiMY\\Downloads\\维基百科数据\\data\\'

if __name__ == '__main__':
    file_list = os.listdir(file_root)
    with open('data/zh_wiki_urls.txt', 'w', encoding='utf-8') as f:
        for file in file_list:
            f.write(file_root + file + '\n')
