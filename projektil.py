from pygame.locals import *
import pygame, math

class Projektil(pygame.sprite.Sprite):
    def __init__(self, screen, pos, ziel, blocksize_x, blocksize_y, preload_images, projektil_decrease, damage, target, speed, map_offset,
                 fps, clock, projektil_cache, parent_name):
        # INIT_SPRITE
        pygame.sprite.Sprite.__init__(self)

        # INITIALISIERUNGS PARAMETER
        self.screen = screen
        self.pos = pos
        self.ziel = ziel
        self.blocksize_x = blocksize_x
        self.blocksize_y = blocksize_y
        self.preload_images = preload_images
        self.PROJEKTIL_DECREASE_width, self.PROJEKTIL_DECREASE_height  = projektil_decrease
        self.damage = damage
        self.target = target
        self.speed = speed
        self.map_offset = map_offset
        self.fps = fps
        self.clock = clock
        self.projektil_cache = projektil_cache
        self.parent_name = parent_name

        # PROJEKTIL INIT
        self.screen_size = self.screen.get_size()
        self.offset = self.map_offset[0]
        self.width = self.blocksize_x * self.PROJEKTIL_DECREASE_width
        self.height = self.blocksize_y * self.PROJEKTIL_DECREASE_height
        self.image = self.projektil_cache[self.parent_name].setdefault("projektil", pygame.transform.scale(self.preload_images[0], (self.width, self.height)))
        self.rect = self.image.get_rect()
        self.rect.center = self.pos
        y_dist, x_dist = self.ziel[1] - self.rect.centery, self.ziel[0] - self.rect.centerx
        self.angle = math.degrees(math.atan2(-y_dist, x_dist))
        self.image = pygame.transform.rotate(self.image, self.angle + 180)
        self.rect = self.image.get_rect()
        self.rect.center = self.pos
        self.cached_images = {}
        self.y_bewegung, self.y_anfangswert = 0, self.rect.centery

    def update(self, ff_increase, blocksize):
        if self.screen_size != self.screen.get_size():
            self.set_screen(blocksize)

        balanced_speed = self.speed * ff_increase * (self.fps / self.clock.get_fps())
        self.rect.centerx += math.cos(math.radians(self.angle)) * balanced_speed
        self.rect.centery -= math.sin(math.radians(self.angle)) * balanced_speed
        self.rect.y = self.rect.y - self.map_offset[0] + self.offset
        self.offset = self.map_offset[0]
        if self.target:
            resized_target = pygame.rect.Rect(0, 0, self.target.rect.width * 0.75, self.target.rect.height * 0.75)
            resized_target.center = self.target.rect.center
            if resized_target.colliderect(self.rect):
                self.target.damage(self.damage)
                self.kill()

    def set_screen(self, blocksize):
        multiplikator_x = self.screen.get_width() / self.screen_size[0]
        multiplikator_y = self.screen.get_height() / self.screen_size[1]
        self.screen_size = self.screen.get_size()
        self.rect.x = self.rect.x * multiplikator_x
        self.rect.y = self.rect.y * multiplikator_y
        self.offset = self.map_offset[0]
        self.blocksize_x, self.blocksize_y = blocksize