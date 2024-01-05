import pygame
from pygame.locals import *

class Particle(pygame.sprite.Sprite):
    def __init__(self, pos_center, velocity, timer, size, map_offset):
        pygame.sprite.Sprite.__init__(self)

        # INIT PARAMETER
        self.x, self.y = pos_center
        self.velocity = velocity
        self.timer_start = timer
        self.timer = timer
        self.size_x, self.size_y = size[0] * 5, size[1] * 5
        self.map_offset = map_offset

        # PARTICLE CONF
        self.image = pygame.Surface((self.size_x, self.size_y))
        self.image.fill((255,0,0))
        self.rect = self.image.get_rect()
        self.rect.center = pos_center
        self.offset = self.map_offset[0]

    def update(self):
        old_position = self.rect.center
        self.image.set_alpha(int(255 * self.timer / self.timer_start) + 100)
        pygame.draw.circle(self.image, (255,0,0), (self.size_x + self.timer_start - self.timer, self.size_x + self.timer_start - self.timer), 5)
        self.rect = self.image.get_rect()
        self.rect.center = old_position
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        self.rect.y = self.rect.y - self.map_offset[0] + self.offset
        self.offset = self.map_offset[0]
        self.timer -= 0.2
        if self.timer <= 0:
            self.kill()