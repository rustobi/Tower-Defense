from typing import Any
import pygame, os
from pygame.locals import *

class Button(pygame.sprite.Sprite):
    def __init__(self, size, position, states, images):
        # INIT_SPRITE
        pygame.sprite.Sprite.__init__(self)

        # INIT PARAMETER
        self.size = size
        self.position = position
        self.states = states
        self.preload_images = images

        # Resize images
        self.images = {}
        for index, image in enumerate(self.preload_images):
            self.images.update({self.states[index]:
                                pygame.transform.smoothscale(image, self.size)})

        # BUTTON CONF
        # First named state in States is the start state
        self.hovered = False
        self.pressed = False
        self.pressed_ = False
        self.state = self.states[0]
        self.image = self.images[self.state]
        self.rect = self.image.get_rect(topleft=self.position)
        self.screen_size = pygame.display.get_surface().get_size()

    def update(self, mouse_pos, mouse_press):
        if self.screen_size != pygame.display.get_surface().get_size():
            self.set_screen()

        mouse_rect = pygame.Rect(mouse_pos[0], mouse_pos[1], 5, 5)
        self.image = self.images[self.state]
        self.rect = self.image.get_rect(topleft=self.rect.topleft)

        if mouse_rect.colliderect(self.rect):
            self.hovered = True
            if not self.pressed:
                self.target_size = (int(self.size[0] * 1.1), int(self.size[1] * 1.1))
            if mouse_press[0]:
                self.pressed = True
                self.target_size = (int(self.size[0] * 0.95), int(self.size[1] * 0.95))
        else:
            self.hovered = False
            self.target_size = (int(self.size[0]), int(self.size[1]))
        self.animate()

    def set_state(self, state_index):
        self.state = self.states[state_index]

    def animate(self):
        current_size = self.image.get_size()
        if current_size != self.target_size:
            if current_size[0] < self.target_size[0]:
                current_size = (current_size[0] + 1, current_size[1])
            elif current_size[0] > self.target_size[0]:
                current_size = (current_size[0] - 1, current_size[1])
            if current_size[1] < self.target_size[1]:
                current_size = (current_size[0], current_size[1] + 1)
            elif current_size[1] > self.target_size[1]:
                current_size = (current_size[0], current_size[1] - 1)
            index_image = self.states.index(self.state)
            self.images[self.state] = pygame.transform.scale(self.preload_images[index_image], current_size)
            self.image = self.images[self.state]
            self.rect = self.image.get_rect(center=self.rect.center)
        else:
            if self.pressed:
                self.pressed = False

    def set_screen(self):
        # Define increment for resizing
        multiplikator_x = pygame.display.get_surface().get_size()[0] / self.screen_size[0]
        multiplikator_y = pygame.display.get_surface().get_size()[1] / self.screen_size[1]
        self.screen_size = pygame.display.get_surface().get_size()
        self.size = (self.size[0] * multiplikator_x, self.size[1] * multiplikator_y)
        self.images.clear()
        for index, image in enumerate(self.preload_images):
            self.images.update({self.states[index]:
                                pygame.transform.smoothscale(image, self.size)})
        self.image = self.images[self.state]
        self.rect = self.image.get_rect(topleft=(self.rect.x * multiplikator_x, self.rect.y * multiplikator_y))