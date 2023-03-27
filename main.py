import os
from bs4 import BeautifulSoup
import requests
from pylatex import Section, Subsection, LongTable

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
        "Mt._Coronet", "Route_216", "Route_217", "Acuity_Lakefront",
    ]
}


def load_route_page_soup(article_title: str) -> BeautifulSoup:
    url = f"{pro_wiki_url_base}{article_title}"
    print(f"Loading url: {url}")
    response = requests.get(url, headers=request_headers)
    html = response.text
    return BeautifulSoup(html, 'html.parser')


def add_wild_pokemon(doc: Section, table: BeautifulSoup, style: str = "Land"):
    # The headers on the PRO Wiki tables are misaligned
    # So let us manually specify the correct headers
    land_headers = ["Img", "Pokémon", "Level Range",
                    "Morning", "Day", "Night",
                    "Held Item", "Rarity Tier"]
    water_headers = ["Img", "Pokémon", "Level Range",
                     "Morning", "Day", "Night",
                     "Rod", "Held Item", "Rarity Tier"]

    rows = table.find_all("tr")
    headers = [th.text.strip() for th in rows[0].find_all("th")]
    start_index = 0
    if len(headers) == 0:
        headers = [th.text.strip() for th in rows[1].find_all("th")]
        start_index = 1
    if len(headers) == len(land_headers) - 3:
        headers = land_headers
        spec = "||" + " ".join("l" * len(land_headers)) + "||"
    elif len(headers) == len(water_headers) - 3:
        headers = water_headers
        spec = "||" + " ".join("l" * len(water_headers)) + "||"
    else:
        return

    with doc.create(LongTable(spec)) as data_table:
        data_table.add_hline()
        data_table.add_row(headers)
        data_table.add_hline()
        data_table.end_table_header()
        data_table.add_hline()

        for row in rows[start_index:]:
            values = [td.text.strip() for td in row.find_all("td")]
            if len(values) != len(headers):
                continue

            data_table.add_row(values)
            data_table.add_hline()


def cache_route_data(region: str, article_title: str):
    routes_dir = os.path.join(root_dir, "routes")
    if not os.path.exists(routes_dir):
        os.mkdir(routes_dir)

    region_dir = os.path.join(routes_dir, region)
    if not os.path.exists(region_dir):
        os.mkdir(region_dir)

    imgs_dir = os.path.join(root_dir, "imgs")
    if not os.path.exists(imgs_dir):
        os.mkdir(imgs_dir)

    pokemon_imgs_dir = os.path.join(imgs_dir, "pokemon")
    if not os.path.exists(pokemon_imgs_dir):
        os.mkdir(pokemon_imgs_dir)

    soup = load_route_page_soup(article_title)
    pokemon_tables = [table for table in soup.find_all("table")
                      if "Level range" in table.text]

    doc = Subsection("Wild Pokemon")
    for table in pokemon_tables:
        add_wild_pokemon(doc, table, style="Land")

    latex_dest = os.path.join(region_dir, article_title + ".tex")
    with open(latex_dest, "w") as file:
        doc.dump(file)

    return doc


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    args = parser.parse_args()

    for region in pro_wiki_route_ids:
        for route in pro_wiki_route_ids[region]:
            cache_route_data(region, route)
