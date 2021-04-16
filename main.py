import configparser
import json

from spider import WikiSpider

Military_list_of_lists_url_list = [
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

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read("config.ini")
    s = WikiSpider(config)
    link_set = set()
    try:
        for list_url in Military_list_of_lists_url_list:
            list_list = s.get_lists(list_url)
            for list_page in list_list:
                new_url = s.get_links_from_list(list_page)

                link_set |= new_url
    except Exception as e:
        with open("urls.txt", "w", encoding="utf-8") as f:
            for u in link_set:
                f.write(u + "\n")
        print(e)
    else:
        with open("urls.txt", "w", encoding="utf-8") as f:
            for u in link_set:
                f.write(u + "\n")
    print(len(link_set))
