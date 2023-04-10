import os
from pylatex import LongTable, Command, TextColor, StandAloneGraphic, NoEscape, Label, Marker
from typing import List
from . import get_route_data, get_route_output_path

rarity_colors = {
    "Common": "black",
    "Uncommon": "OliveGreen",
    "Rare": "RedOrange",
}

spawn_times_colors = {
    "Morning": "yellow",
    "Day": "orange",
    "Night": "blue",
}
no_spawn_color = "gray"


def generate_spawn_times_text(spawn_times: List[str]) -> str:
    rv = []
    for spawn_time in spawn_times_colors:
        if spawn_time in spawn_times:
            color = spawn_times_colors[spawn_time]
            spawn_time = spawn_time.replace("Morning", "Morn")
            rv += [f"\\textcolor{{{color}}}{{{spawn_time}}}"]
        else:
            pass
            # spawn_time = spawn_time.replace("Morning", "Morn")
            # rv += [f"\\textcolor{{{no_spawn_color}}}{{\\sout{{{spawn_time}}}}}"]
    return NoEscape("  ".join(rv))


def generate_wild_pokemon_snippet(route_id: str, area: str, table: List, output_file: str):
    route_name = route_id.replace("_", " ")
    if area is None:
        route_title = route_name
    else:
        route_title = f"{route_name} ({area})"

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
    try:
        spawn_times_index = headers.index("Spawn Times")
    except ValueError:
        spawn_times_index = -1

    spec = "||" + " ".join("l" * len(headers)) + "||"
    doc = LongTable(spec)
    doc.add_hline()
    doc.add_row(headers, color=bgcolor)
    doc.add_hline()
    doc.end_table_header()
    doc.add_hline()

    color_index = 0
    for row in table:
        img_path = row.pop("Image")
        values = [
            StandAloneGraphic(f"{img_path}",
                              image_options=NoEscape(r'width=0.02\textwidth'))
        ]
        values += list(row.values())
        values[rarity_index] = TextColor(rarity_colors.get(values[rarity_index], "black"), values[rarity_index])
        if spawn_times_index >= 0:
            values[spawn_times_index] = generate_spawn_times_text(values[spawn_times_index])
        doc.add_row(values, color=bgcolor)
        color_index = 1 if color_index == 0 else 0
        doc.add_hline()

    doc.append(Command("caption", f"Wild Pokémon in {route_title}"))
    label_id = route_id + "_" + area
    label_id = label_id.replace("(", "").replace(")", "")
    doc.append(Label(Marker(label_id, prefix="tab")))

    with open(output_file, "w") as file:
        doc.dump(file)

    return doc


def generate_items_snippet(route_id: str, table: List, output_file: str):
    route_name = route_id.replace("_", " ")
    spec = "|| l l l l ||"
    doc = LongTable(spec)
    doc.add_hline()
    for entry in table:
        doc.add_row([entry["Image"], entry["Item"], entry["Quantity"], entry["Cooldown"]])
        # doc.add_row([entry["Location"]])
        doc.add_hline()
    doc.end_table_header()
    doc.add_hline()

    doc.append(Command("caption", f"Items in {route_name}"))
    label_id = route_id + "_Items"
    label_id = label_id
    doc.append(Label(Marker(label_id, prefix="tab")))

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
                    generate_wild_pokemon_snippet(route_id, area, table, output_file)

            if "items" in route_info:
                table = route_info["items"]
                output_file = os.path.join(route_dir, "Items.tex")
                generate_items_snippet(route_id, table, output_file)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()

    args = parser.parse_args()

    generate_route_snippets()
