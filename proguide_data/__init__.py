import os
from typing import Dict, List, Iterable
import json

data_dir = os.path.dirname(__file__)
root_dir = os.path.dirname(data_dir)

route_names_path = os.path.join(data_dir, "route_names.json")
route_data_path = os.path.join(data_dir, "route_data.json")

imgs_path = os.path.join(root_dir, "imgs")
routes_output_path = os.path.join(root_dir, "routes")

user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/" \
             "537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36"
request_headers = {'User-Agent': user_agent}


def get_route_names() -> Dict[str, List[str]]:
    with open(route_names_path, "r") as file:
        return json.load(file)


def get_route_data() -> Dict[str, Dict[str, Dict]]:
    try:
        with open(route_data_path, "r") as file:
            return json.load(file)
    except IOError:
        return {}


def get_imgs_pokemon_path(pokemon: str, ext: str) -> str:
    pokemon_imgs_dir = os.path.join(imgs_path, "pokemon")
    if not os.path.exists(pokemon_imgs_dir):
        os.mkdir(pokemon_imgs_dir)

    return os.path.join(pokemon_imgs_dir, pokemon + ext)


def get_route_output_path(region: str, route_id: str) -> str:
    if not os.path.exists(routes_output_path):
        os.mkdir(routes_output_path)

    region_path = os.path.join(routes_output_path, region)
    if not os.path.exists(region_path):
        os.mkdir(region_path)

    route_output_path = os.path.join(region_path, route_id)
    if not os.path.exists(route_output_path):
        os.mkdir(route_output_path)

    return route_output_path
