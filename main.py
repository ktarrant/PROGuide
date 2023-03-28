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


def add_wild_pokemon(doc: Section, table: BeautifulSoup):
    # The headers on the PRO Wiki tables are misaligned
    # So let us manually specify the correct headers
    land_headers = ["", "Pokémon", "Level Range",
                    "Morn", "Day", "Night",
                    "Held Item", "Rarity Tier"]
    water_headers = ["", "Pokémon", "Level Range",
                     "Morn", "Day", "Night",
                     "",  # "Rod",
                     "Held Item", "Rarity Tier"]

    rows = table.find_all("tr")
    headers = [th.text.strip() for th in rows[0].find_all("th")]
    start_index = 0
    if len(headers) == 0:
        headers = [th.text.strip() for th in rows[1].find_all("th")]
        start_index = 1
    if len(headers) == len(land_headers) - 3:
        headers = land_headers
        spec = "||" + " ".join("l" * len(land_headers)) + "||"
        style = "Land"
    elif len(headers) == len(water_headers) - 3:
        headers = water_headers
        spec = "||" + " ".join("l" * len(water_headers)) + "||"
        style = "Water"
    else:
        return

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
            img_link = entries[0].find("img").attrs["src"]
            cache_image(pokemon, img_link)

            values = [value.replace("Morning", "Morn") for value in values]
            values[0] = StandAloneGraphic(f"pokemon/{pokemon}",
                                          image_options=NoEscape(r'width=0.02\textwidth'))
            values[-1] = TextColor(rarity_colors.get(values[-1], "black"),
                                   values[-1])

            data_table.add_row(values)
            data_table.add_hline()

    return style


def cache_route_data(region: str, article_title: str):
    routes_dir = os.path.join(root_dir, "routes")
    if not os.path.exists(routes_dir):
        os.mkdir(routes_dir)

    region_dir = os.path.join(routes_dir, region)
    if not os.path.exists(region_dir):
        os.mkdir(region_dir)

    soup = load_route_page_soup(article_title)
    cursor = soup.find("h2")
    while cursor is not None:
        if cursor.text.strip() == "Wild Pokémon":
            break
        cursor = cursor.find_next_sibling("h2")

    cursor = cursor.find_next_sibling("h3")
    while cursor is not None:
        subtype = cursor.text.strip()
        article_title_full = f"{article_title}_({subtype})"

        table = cursor.find_next_sibling()

        doc = Subsubsection(f"Wild Pokemon ({subtype})")
        style = add_wild_pokemon(doc, table)
        doc.append(Command("caption",
                           article_title.replace("_", " ") + f" Wild Pokemon ({style})"))

        latex_dest = os.path.join(region_dir, article_title_full + ".tex")
        with open(latex_dest, "w") as file:
            doc.dump(file)

        cursor = cursor.find_next_sibling("h3")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    args = parser.parse_args()

    for region in pro_wiki_route_ids:
        for route in pro_wiki_route_ids[region]:
            cache_route_data(region, route)
