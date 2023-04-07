import json
import os
from bs4 import BeautifulSoup
import requests
from typing import List, Dict
from . import (
    request_headers,
    get_route_names,
    get_route_data,
    route_data_path,
    imgs_path,
    get_imgs_pokemon_path
)

pro_wiki_url_base = "https://prowiki.info/?title="


def cache_image(pokemon: str, url: str):
    _, ext = os.path.splitext(url)
    cached_path = get_imgs_pokemon_path(pokemon, ext)
    if os.path.exists(cached_path):
        return os.path.relpath(cached_path, imgs_path)

    print(f"Downloading image: {url}")
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(cached_path, 'wb') as f:
            for chunk in r:
                f.write(chunk)
    return os.path.relpath(cached_path, imgs_path)


def load_route_page_soup(article_title: str) -> BeautifulSoup:
    url = f"{pro_wiki_url_base}{article_title}"
    print(f"Loading url: {url}")
    response = requests.get(url, headers=request_headers)
    html = response.text
    return BeautifulSoup(html, 'html.parser')


def add_wild_pokemon(data: Dict[str, object], table: BeautifulSoup, style: str):
    # The headers on the PRO Wiki tables are misaligned
    # So let us manually specify the correct headers
    land_headers = ["", "Pokémon", "Level Range",
                    "Morning", "Day", "Night",
                    "Held Item", "Rarity Tier"]
    water_headers = ["", "Pokémon", "Level Range",
                     "Morning", "Day", "Night",
                     "",  # "Rod",
                     "Held Item", "Rarity Tier"]
    headbutt_headers = ["",  "Pokémon", "Level Range", "Rarity Tier"]

    rows = table.find_all("tr")
    if len(rows) == 0:
        return False

    headers = [th.text.strip() for th in rows[0].find_all("th")]
    if len(headers) == 0:
        headers = [th.text.strip() for th in rows[1].find_all("th")]

    if style is None:
        if len(headers) == len(land_headers) - 3:
            style = "Land"
        elif len(headers) == len(water_headers) - 3:
            style = "Water"
        elif len(headers) == len(headbutt_headers) - 1:
            style = "Headbuttable Trees"
        else:
            return False

    if style == "Land":
        headers = land_headers
        start_index = 0
    elif style == "Water":
        headers = water_headers
        start_index = 1
    elif style == "Headbuttable Trees":
        headers = headbutt_headers
        start_index = 1
    else:
        headers = land_headers
        start_index = 0

    data_table = []
    for row in rows[start_index:]:
        entries = row.find_all("td")
        values = [td.text.strip() for td in entries]
        if len(values) != len(headers):
            continue

        pokemon = values[1]
        try:
            img_link = entries[0].find("img").attrs["src"]
        except AttributeError:
            continue

        cached_image = cache_image(pokemon, img_link)

        row_data = dict(Image=cached_image)
        row_data.update(
            {key: value for key, value in zip(headers, values) if key}
        )
        if "Morning" in headers:
            spawn_times = [time_of_day for time_of_day in ["Morning", "Day", "Night"]
                           if row_data.pop(time_of_day).strip()]
            row_data["Spawn Times"] = spawn_times
        data_table += [row_data]

    wp_table = data.get("wild_pokemon", {})
    wp_table[style] = data_table
    data["wild_pokemon"] = wp_table
    return True


def add_items(data: Dict[str, object], table: BeautifulSoup):
    headers = ["Image"] + [th.text.strip() for th in table.find_all("th")]

    rows = table.find_all("tr")
    if len(rows) == 0:
        return False

    data_table = []
    for row in rows[1:]:
        entries = row.find_all("td")
        values = [td.text.strip() for td in entries]
        if len(values) != len(headers):
            continue

        try:
            img_link = entries[0].find("img").attrs["src"]
        except AttributeError:
            continue

        # cached_image = cache_image(pokemon, img_link)

        row_data = dict(Image="")  # cached_image
        row_data.update(
            {key: value for key, value in zip(headers, values) if key}
        )
        data_table += [row_data]

    data["items"] = data_table
    return True


def get_page_data(article_title: str) -> Dict[str, object]:
    """
    Returns a dict with the route information extracted from a prowiki page.
    :param article_title: The name of the route (Used to query prowiki)
    :return:
    """
    soup = load_route_page_soup(article_title)
    cursor = soup.find("h2")
    section_header = None
    subsection_header = None
    data = dict(name=article_title.replace("_", " "))
    while cursor is not None:
        if cursor.name == "h2":
            section_header = cursor.text.strip()
            subsection_header = None

        elif cursor.name == "h3":
            subsection_header = cursor.text.strip()

        elif cursor.name == "table":
            if section_header == "Wild Pokémon":
                add_wild_pokemon(data, cursor, subsection_header)
            elif section_header == "Items":
                add_items(data, cursor)
            else:
                print(f"Did not process content {section_header}, {subsection_header}")

        cursor = cursor.next_sibling

    return data


def update_route_data(route_names: List[str] = None):
    """ Updates the routes.json data file with route data from prowiki.
    :param route_names: List of routes to update, or None to update all known routes.
    """
    all_route_names = get_route_names()
    route_data = get_route_data()
    for region in all_route_names:
        region_data = route_data.get(region, {})
        for route in all_route_names[region]:
            if route_names is not None and route not in route_names:
                continue
            page_data = get_page_data(route)
            route_info = region_data.get(route, {})
            route_info.update(page_data)
            region_data[route] = route_info
        route_data[region] = region_data

    with open(route_data_path, "w") as file:
        json.dump(route_data, file, indent=4)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Updates database based on prowiki pages")
    parser.add_argument("--routes", help="comma-separated list of route IDs to query",
                        default=None)
    args = parser.parse_args()

    if args.routes is None:
        routes = None
    else:
        routes = args.routes.split(",")
    update_route_data(routes)
