import os
from pylatex import Section, Subsubsection, LongTable, Command, TextColor, StandAloneGraphic, NoEscape
from typing import List
from . import get_route_data, get_route_output_path

rarity_colors = {
    "Common": "black",
    "Uncommon": "OliveGreen",
    "Rare": "RedOrange",
}


def generate_wild_pokemon_snippet(route_name: str, area: str, table: List, output_file: str):
    route_title = f"{route_name} ({area})"
    doc = Subsubsection(route_title)

    if area == "Land":
        bgcolor = "GroundColor"
    elif area == "Water":
        bgcolor = "WaterColor"
    elif area == "Headbuttable Trees":
        bgcolor = "GroundColor"
    else:
        bgcolor = "gray"

    try:
        headers = [key for key in table[0]]
    except IndexError:
        print(f"Empty table provided for {route_name} ({area})")
        return

    img_index = headers.index("Image")
    del headers[img_index]
    headers = [""] + headers
    rarity_index = headers.index("Rarity Tier")

    spec = "||" + " ".join("l" * len(headers)) + "||"
    with doc.create(LongTable(spec)) as data_table:
        data_table.add_hline()
        data_table.add_row(headers, color=bgcolor)
        data_table.add_hline()
        data_table.end_table_header()
        data_table.add_hline()

        color_index = 0
        for row in table:
            img_path = row.pop("Image")
            values = [
                StandAloneGraphic(f"{img_path}",
                                  image_options=NoEscape(r'width=0.02\textwidth'))
            ]
            values += list(row.values())
            values[rarity_index] = TextColor(rarity_colors.get(values[rarity_index], "black"), values[rarity_index])

            data_table.add_row(values, color=bgcolor)
            color_index = 1 if color_index == 0 else 0
            data_table.add_hline()

    doc.append(Command("caption", f"Wild Pokémon in {route_title}"))

    with open(output_file, "w") as file:
        doc.dump(file)

    return doc


def generate_route_snippets():
    route_data = get_route_data()
    for region in route_data:
        for route_id in route_data[region]:
            route_info = route_data[region][route_id]
            route_dir = get_route_output_path(region, route_id)
            if "wild_pokemon" in route_info:
                for area in route_info["wild_pokemon"]:
                    print(f"Generating {route_id} Wild Pokemon ({area})")
                    table = route_info["wild_pokemon"][area]
                    output_file = os.path.join(route_dir, "Wild_Pokémon_({}).tex".format(area.replace(" ", "_")))
                    generate_wild_pokemon_snippet(route_info["name"], area, table, output_file)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    args = parser.parse_args()

    generate_route_snippets()
