import nbformat
import os

notebook_files = [
    os.path.join(os.getcwd(), "notebooks/landing_zone/data-collection.ipynb"),
    os.path.join(os.getcwd(), "notebooks/landing_zone/temporal_zone.ipynb"),
    os.path.join(os.getcwd(), "notebooks/landing_zone/persistent_zone.ipynb"),
    os.path.join(os.getcwd(), "notebooks/formatted_zone/formated_zone_audio.ipynb"),
    os.path.join(os.getcwd(), "notebooks/formatted_zone/formated_zone_images.ipynb"),
    os.path.join(os.getcwd(), "notebooks/formatted_zone/formated_zone_text.ipynb"),
    os.path.join(os.getcwd(), "notebooks/trusted_zone/trusted_zone_audio.ipynb"),
    os.path.join(os.getcwd(), "notebooks/trusted_zone/trusted_zone_images.ipynb")
    #os.path.join(os.getcwd(), "notebooks/trusted_zone/trusted_zone_text.ipynb"), dona error
]

output_filename = "pipeline.py"

with open(output_filename, "w") as output_file:
    for notebook_file in notebook_files:
        with open(notebook_file, "r") as nb_file:
            nb = nbformat.read(nb_file, as_version=4)
            for cell in nb.cells:
                if cell.cell_type == "code":
                    output_file.write("# From notebook: {}\n".format(notebook_file))
                    output_file.write(cell.source + "\n\n")