import os
from bs4 import BeautifulSoup
import requests
from pylatex import Section, Subsubsection, LongTable, Command, TextColor, StandAloneGraphic, NoEscape

rarity_colors = {
    "Common": "black",
    "Uncommon": "teal",
    "Rare": "violet",
}

root_dir = os.path.dirname(__file__)

pro_wiki_url_base = "https://prowiki.info/?title="
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/" \
             "537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
request_headers = {'User-Agent': user_agent}

pro_wiki_route_ids = {
    "Sinnoh": [
        "Lake_Verity", "Route_201", "Route_202",
        "Route_218",
        "Route_203", "Route_204",
        "Ravaged_Path", "Oreburgh_Gate", "Route_207", "Oreburgh_Mine",
        "Route_205", "Valley_Windworks", "Eterna_Forest",
        "Route_211", "Mt._Coronet", "Old_Chateau",
        "Route_206", "Wayward_Cave", "Route_207", "Route_208",
        "Amity_Square", "Route_209", "Lost_Tower", "Solaceon_Ruins",
        "Route_210", "Route_215", "Route_214", "Valor_Lakefront",
        "Route_213", "Great_Marsh",
        "Route_212", "Route_210", "Route_211",
        "Fuego_Ironworks", "Floaroma_Meadow", "Sandgem_Beach",
        "Route_219", "Route_220", "Route_221",
        "Iron_Island", "Wayward_Cave", "Valor_Lakefront", "Lake_Valor",
        "Mt._Coronet_North", "Mt._Coronet_South",
        "Route_216", "Route_217", "Acuity_Lakefront",
    ]
}


def load_route_page_soup(article_title: str) -> BeautifulSoup:
    url = f"{pro_wiki_url_base}{article_title}"
    print(f"Loading url: {url}")
    response = requests.get(url, headers=request_headers)
    html = response.text
    return BeautifulSoup(html, 'html.parser')


def cache_image(pokemon: str, url: str):
    imgs_dir = os.path.join(root_dir, "imgs")
    if not os.path.exists(imgs_dir):
        os.mkdir(imgs_dir)

    pokemon_imgs_dir = os.path.join(imgs_dir, "pokemon")
    if not os.path.exists(pokemon_imgs_dir):
        os.mkdir(pokemon_imgs_dir)

    _, ext = os.path.splitext(url)
    cached_path = os.path.join(pokemon_imgs_dir, pokemon + ext)
    if os.path.exists(cached_path):
        return

    print(f"Downloading image: {url}")
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open(cached_path, 'wb') as f:
            for chunk in r:
                f.write(chunk)


def add_wild_pokemon(doc: Section, table: BeautifulSoup, style: str):
    # The headers on the PRO Wiki tables are misaligned
    # So let us manually specify the correct headers
    land_headers = ["", "Pokémon", "Level Range",
                    "Morn", "Day", "Night",
                    "Held Item", "Rarity Tier"]
    water_headers = ["", "Pokémon", "Level Range",
                     "Morn", "Day", "Night",
                     "",  # "Rod",
                     "Held Item", "Rarity Tier"]
    headbutt_headers = ["",  "Pokémon", "Level Range", "Rarity Tier"]

    rows = table.find_all("tr")
    if len(rows) == 0:
        return False

    headers = [th.text.strip() for th in rows[0].find_all("th")]
    start_index = 0
    if len(headers) == 0:
        headers = [th.text.strip() for th in rows[1].find_all("th")]
        start_index = 1

    if style is None or style not in ["Land", "Water", "Headbuttable Trees"]:
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

    spec = "||" + " ".join("l" * len(headers)) + "||"
    with doc.create(LongTable(spec)) as data_table:
        data_table.add_hline()
        data_table.add_row(headers)
        data_table.add_hline()
        data_table.end_table_header()
        data_table.add_hline()

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

            cache_image(pokemon, img_link)

            values = [value.replace("Morning", "Morn") for value in values]
            values[0] = StandAloneGraphic(f"pokemon/{pokemon}",
                                          image_options=NoEscape(r'width=0.02\textwidth'))
            values[-1] = TextColor(rarity_colors.get(values[-1], "black"),
                                   values[-1])

            data_table.add_row(values)
            data_table.add_hline()

    return True


def process_content(region: str, article_title: str, section_header: str, subsection_header: str,
                    contents: BeautifulSoup) -> Subsubsection:
    routes_dir = os.path.join(root_dir, "routes")
    if not os.path.exists(routes_dir):
        os.mkdir(routes_dir)

    region_dir = os.path.join(routes_dir, region)
    if not os.path.exists(region_dir):
        os.mkdir(region_dir)

    article_title = article_title.replace("_", " ")

    if section_header == "Wild Pokémon":
        section_title = "Wild Pokémon"
        if subsection_header is None:
            route_title = article_title
        else:
            if subsection_header.startswith(article_title):
                subsection_header = subsection_header.replace(article_title + " ", "")

            route_title = f"{article_title} ({subsection_header})"
            section_title += f" ({subsection_header})"

        doc = Subsubsection(section_title)
        add_wild_pokemon(doc, contents, subsection_header)
        doc.append(Command("caption", "Wild Pokemon in " + route_title))

        file_title = route_title.replace(" ", "_")
        latex_dest = os.path.join(region_dir, file_title + ".tex")
        with open(latex_dest, "w") as file:
            doc.dump(file)

        return doc


    else:
        print(f"Did not process content {section_header}, {subsection_header}")

        return None


def cache_route_data(region: str, article_title: str):
    soup = load_route_page_soup(article_title)
    cursor = soup.find("h2")
    section_header = None
    subsection_header = None
    while cursor is not None:
        if cursor.name == "h2":
            section_header = cursor.text.strip()
            subsection_header = None

        elif cursor.name == "h3":
            subsection_header = cursor.text.strip()

        elif cursor.name == "table":
            if section_header is not None:
                process_content(region, article_title, section_header, subsection_header, cursor)

        cursor = cursor.next_sibling


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    args = parser.parse_args()

    for region in pro_wiki_route_ids:
        for route in pro_wiki_route_ids[region]:
            cache_route_data(region, route)
