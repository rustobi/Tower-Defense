import json, os, pygame, random
from pygame.locals import *
from PIL import Image as pil_image
from PIL import ImageDraw, ImageOps
from tempfile import TemporaryFile
from pathlib import Path
import cv2
import numpy as np

class Draw_map():
    def __init__(self, blocksize_x, blocksize_y, column_size, row_size, map_config, screen):
        self.column_size = column_size
        self.row_size = row_size
        self.blocksize_x = blocksize_x
        self.blocksize_y = blocksize_y
        self.map_config = map_config
        self.screen = screen
        self.screen_size = self.screen.get_size()
        self.map_design = {}
        self.random_default_map = []
        self.random_stones_default_map = []
        self.images_fconcat = []
        self.positions_fconcat = []
        self.tile_map = json.loads(self.map_config.get("MAP", "tile_map"))
        self.cached_map = {}
        self.create_random_default()
        self.create_random_stones()
        self.map_image = self.create_field()

    def update(self, y, blocksize):
        if self.screen_size != self.screen.get_size():
            self.set_screen(blocksize)
        self.screen.blit(self.map_image, (0, -y))

    def create_random_default(self):
        for x in range(self.column_size):
            self.random_default_map.append([])
            for y in range(self.row_size):
                default_image = json.loads(self.map_config.get("TILES", "default"))
                default_image += "_" + str(random.randint(1, json.loads(self.map_config.get("TILES", "default_random")))) + ".png"
                default_image = os.path.join(Path(__file__).parent, "tiles", default_image)
                if os.path.isfile(default_image):
                    self.random_default_map[x].append(default_image)

    def create_random_stones(self):
        for r_index, row in enumerate(self.random_default_map):
            self.random_stones_default_map.append([])
            for c_index, default_image in enumerate(row):
                if random.randint(0, 20) == 0:
                    stone_image = default_image.split("_")[0]
                    number = default_image.split("_")[1].split(".")[0]
                    stone_image += "_s_t_" + str(number) + ".png"
                    if os.path.isfile(stone_image):
                        self.random_stones_default_map[r_index].append(stone_image)
                    else:
                        self.random_stones_default_map[r_index].append("")
                else:
                    self.random_stones_default_map[r_index].append("")
        

    def create_field(self, set_screen=False):
        # SET DEFAULT GRASS
        for r_index, row in enumerate(self.random_default_map):
            for c_index, default_image in enumerate(row):
                if not set_screen:
                    self.images_fconcat.append(default_image)
                self.positions_fconcat.append((c_index * self.blocksize_x, r_index * self.blocksize_y))

        # SET DEFAULT STONES
        for r_index, row in enumerate(self.random_stones_default_map):
            for c_index, stone_image in enumerate(row):
                if not stone_image:
                    continue
                if not set_screen:
                    self.images_fconcat.append(stone_image)
                self.positions_fconcat.append((c_index * self.blocksize_x, r_index * self.blocksize_y))

        # SET MAP SPECIFIC IMAGES
        for r_index, row in enumerate(self.tile_map):
            for c_index, col in enumerate(row):
                if not col:
                    continue
                if col.startswith("empire"):
                    continue
                file = os.path.join(Path(__file__).parent, "tiles", json.loads(self.map_config.get("TILES", col)))
                if os.path.isfile(file):
                    if not set_screen:
                        self.images_fconcat.append(file)
                    self.positions_fconcat.append((c_index * self.blocksize_x , r_index * self.blocksize_y))
        self.map_image = self.concat_field()
        self.map_image = pygame.image.load(self.map_image).convert()
        return self.map_image


    def concat_field(self):
        # CONCAT TO PICTURE
        fp = TemporaryFile()
        dst = pil_image.new('RGB', (self.screen.get_width(), self.blocksize_y * self.column_size))
        for image, pos in zip(self.images_fconcat, self.positions_fconcat):
            im = pil_image.open(image)
            im = im.convert("RGBA")
            im = im.resize((self.blocksize_x, self.blocksize_y), pil_image.Resampling.LANCZOS)
            dst.paste(im, pos, im)
    
        dst.save(fp, "PNG")
        fp.seek(0)
        return fp

    def get_max_y_offset(self):
        return self.blocksize_y * self.column_size - self.screen.get_height()

    def get_start_end_points(self):
        start_point = json.loads(self.map_config.get("MAP", "start_point"))
        end_point = json.loads(self.map_config.get("MAP", "end_point"))
        return start_point, end_point
    
    def set_screen(self, blocksize):
        self.screen_size = self.screen.get_size()
        self.blocksize_x, self.blocksize_y = blocksize
        self.positions_fconcat.clear()

        if self.screen.get_size() not in self.cached_map:
            self.cached_map[self.screen.get_size()] = self.create_field(set_screen=True)
        self.map_image = self.cached_map[self.screen.get_size()]