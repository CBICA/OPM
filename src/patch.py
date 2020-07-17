import openslide
from pathlib import Path


class Patch:
    def __init__(self, slide_path, coordinates, level, size):
        self.slide_path = slide_path
        self.coordinates = coordinates
        self.level = level
        self.size = size

    def read_patch(self):
        return openslide.open_slide(self.slide_path).read_region(
            self.coordinates, self.level, self.size
        )

    def save(self, out_dir, output_format="_patch@{}_{}.png"):
        """
        Save patch.
        :param out_dir:
        :param output_format:
        :return:
        """
        path = Path(self.slide_path)
        return self.read_patch().save(
            fp=out_dir
            + path.name.split(path.suffix)[0]
            + output_format.format(self.coordinates, self.size),
            format="PNG",
        )
