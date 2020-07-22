from pathlib import Path
import openslide
from .utils import *


class Patch:
    def __init__(self, slide_path, coordinates, level, size):
        self.slide_path = slide_path
        self.coordinates = coordinates
        self.level = level
        self.size = size

    def read_patch(self):
        return openslide.open_slide(self.slide_path).read_region(
            (self.coordinates[1], self.coordinates[0]), self.level, self.size
        )

    def save(self, out_dir, output_format="_patch@({},{})_{}x{}.png"):
        """
        Save patch.
        :param out_dir:
        :param output_format:
        :return:
        """
        patch = self.read_patch()
        is_viable = gaussian_blur(patch, patch.size, UPPPER_LIMIT, LOWER_LIMIT)
        if is_viable:
            path = Path(self.slide_path)
            self.read_patch().save(
                fp=out_dir
                   + path.name.split(path.suffix)[0]
                   + output_format.format(self.coordinates[0], self.coordinates[1], self.size[0], self.size[1]),
                format="PNG",
            )
            return True
        else:
            return False
