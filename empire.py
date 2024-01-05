import math
from typing import Any
import pygame, os
from pygame.locals import *
from pathlib import Path

class Empire(pygame.sprite.Sprite):
    def __init__(self, screen, start_position, map_offset, blocksize):
        # INIT_SPRITE
        pygame.sprite.Sprite.__init__(self)

        # INIT PARAMETER
        self.screen = screen
        self.map_offset = map_offset
        self.max_health = 100
        self.health = self.max_health
        self.blocksize = blocksize
        self.map_offset = map_offset

        # EMPIRE CONF
        self.screen_size = self.screen.get_size()
        self.offset = self.map_offset[0]
        self.image_cache = {self.screen.get_size(): self.get_empire_image()}
        self.image = self.image_cache.get(self.screen.get_size())
        self.rect = pygame.rect.Rect(0, 0, self.image.get_width() // 2, self.image.get_height())
        self.rect.center = (start_position[0] - self.blocksize[0] // 2, start_position[1] - self.offset)

    def update(self, blocksize):
        if self.screen_size != self.screen.get_size():
            self.set_screen(blocksize)
        self.rect.center = (self.rect.centerx, self.rect.centery - self.map_offset[0] + self.offset)
        self.offset = self.map_offset[0]

    def get_empire_image(self):
        for root, folders, _ in os.walk(Path(__file__).parent):
            if "empire" in folders:
                empire_img_path = os.path.join(root, "empire", "empire.png")
        
        empire_image = pygame.image.load(empire_img_path)
        empire_image = pygame.transform.smoothscale(empire_image, (self.blocksize[0] * 2, self.blocksize[1] * 2))
        return empire_image

    def damage(self, damage):
        self.health -= damage

    def set_screen(self, blocksize):
        self.blocksize = blocksize
        self.image = self.image_cache.setdefault(self.screen.get_size(), self.get_empire_image())
        self.rect.size = (self.image.get_width() // 2, self.image.get_height())
        self.rect.x = math.ceil(self.rect.x * (self.screen.get_width() / self.screen_size[0]))
        self.rect.y = math.ceil(self.rect.y * (self.screen.get_height() / self.screen_size[1]))
        self.screen_size = self.screen.get_size()
        self.offset = self.map_offset[0]