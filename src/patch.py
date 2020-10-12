from pathlib import Path
import openslide
from .utils import *


class Patch:
    def __init__(self, manager, coordinates, level, size):
        self.manager = manager
        self.slide_path = manager.path
        self.coordinates = coordinates
        self.level = level
        self.size = size

    def read_patch(self):
        return openslide.open_slide(self.slide_path).read_region(
            (self.coordinates[1], self.coordinates[0]), self.level, self.size
        )

    def save(self, out_dir, output_format="_patch@({},{})_{}x{}.png", save=True):
        """
        Save patch.
        :param out_dir:
        :param output_format:
        :return:
        """
        patch = self.read_patch()

        for check_function in self.manager.valid_patch_checks:
            if not check_function(patch):
                return [False, self]
        
        try:
            if save:
                path = Path(self.slide_path)
                self.read_patch().save(
                    fp=out_dir
                       + path.name.split(path.suffix)[0]
                       + output_format.format(self.coordinates[0], self.coordinates[1], self.size[0], self.size[1]),
                    format="PNG",
                )

            return [True, self]

        except:
            return [False, self]
