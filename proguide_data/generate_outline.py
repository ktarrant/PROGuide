from proguide_data import get_route_data, get_route_names, routes_output_path, root_dir
from pylatex import Document, Subsubsection, NoEscape
import os


def generate_outline(region: str) -> Document:
    route_names = get_route_names()
    route_data = get_route_data()
    doc = Document()

    for route_name in route_names[region]:
        route_info = route_data[region][route_name]
        if "Name" in route_info:
            route_title = route_info["Name"]
        else:
            route_title = route_name.replace("_", " ")
        doc.append(Subsubsection(route_title))
        route_dir_path = os.path.join(routes_output_path, region, route_name)

        if not os.path.exists(route_dir_path):
            continue

        for root, dirs, files in os.walk(route_dir_path):
            for file in files:
                relative_path = os.path.relpath(os.path.join(root, file), root_dir)
                relative_file, etx = os.path.splitext(relative_path)
                doc.append(NoEscape(r"\input{" + relative_file + "}"))

    with open(region + ".tex", "w") as file:
        doc.dump(file)


if __name__ == "__main__":
    generate_outline("Johto")
