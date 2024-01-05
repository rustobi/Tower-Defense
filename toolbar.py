import pygame, tower, os, json, configparser, sys, time
from pygame._sdl2.video import Window, Renderer, Texture, Image
from pathlib import Path

class Toolbar():
    def __init__(self, sceen, pre_load_towers, blocksize_x, blocksize_y,
                 col_size, row_size, money_amount, sound_control):
        # INIT_PARAMETER
        self.name = "toolbar"
        self.screen = sceen
        self.pre_load_towers = pre_load_towers
        self.blocksize_x = blocksize_x
        self.blocksize_y = blocksize_y
        self.col_size = col_size
        self.row_size = row_size
        self.money_amount = money_amount
        self.sound_control = sound_control

        # TOOLBAR INITIALISIERUNG
        self.screen_size = self.screen.get_size()
        self.prices = {}
        term_path = self.get_conf(self.name)
        self.conf = configparser.ConfigParser()
        self.conf.read(os.path.join(term_path, self.name + ".ini"))
        self.building_container = {}
        self.price_font = None
        self.create_toolbar()
        self.mouse_clicked_tower = []
        self.temp_sprite = pygame.sprite.Sprite()
        self.temp_sprite.rect = pygame.rect.Rect(0, 0, 1, 1)

    def update(self, colliding_towers, blocksize, pre_load_towers):
        if self.screen_size != self.screen.get_size():
            self.set_screen(blocksize, pre_load_towers)

        prices = {}
        
        for name, building_group in self.building_container.items():
            for sprite in building_group:
                if type(sprite) == pygame.sprite.Sprite:
                    if self.prices[name.lower()] > self.money_amount[0]:
                        color = (255,0,0)
                    else:
                        color = (255,255,255)
                    price_img = self.price_font.render(str(self.prices[name.lower()]), True, color)
                    price_rect = price_img.get_rect()
                    price_rect.center = sprite.rect.center
                    prices[price_img] = price_rect
                else:
                    if (sprite not in colliding_towers and sprite.get_hovered()) or (sprite in colliding_towers and not sprite.get_hovered()):
                        if sprite.price <= self.money_amount[0]:
                            sprite.set_hovered()

            building_group.update()
            building_group.draw(self.screen)
            
        for price_img, price_rect in prices.items():
            self.screen.blit(price_img, price_rect)

    def create_toolbar(self):
        self.price_font = pygame.font.SysFont("arialblack.ttf", int(18 * (self.blocksize_x / 100)))
        for building_group in self.building_container.values():
            building_group.empty()

        available_towers = self.get_towers()
        available_towers.remove("CONTROL")
        for index, building in enumerate(available_towers):
            index += 1
            self.prices.update({building.lower():json.loads(self.conf.get("PRICE", building.lower()))})
            x_position = (self.row_size - index) * self.blocksize_x
            y_position = 0
            sprite1 = tower.Tower(self.screen, (self.blocksize_x, self.blocksize_y), "bottom", building, self.pre_load_towers,
                                  (self.blocksize_x, self.blocksize_y), x_position, y_position, False, self.sound_control, price=self.prices[building.lower()])
            sprite2 = tower.Tower(self.screen, (self.blocksize_x, self.blocksize_y), "top", building, self.pre_load_towers,
                                  (self.blocksize_x, self.blocksize_y), x_position, y_position, False, self.sound_control, price=self.prices[building.lower()])
            sprite3 = pygame.sprite.Sprite()
            sprite3.image = pygame.image.load(os.path.join(Path(__file__).parent, "tiles", "sign.png"))
            sprite3.image = pygame.transform.smoothscale(sprite3.image, (self.blocksize_x, self.blocksize_y))
            sprite3.rect = sprite3.image.get_rect()
            sprite3.rect.topleft = (x_position, y_position + self.blocksize_y - self.blocksize_y // 4)
            sprite2.image = pygame.transform.rotate(sprite2.image, 180)
            if not self.building_container.get(building):
                self.building_container.update({building:pygame.sprite.Group()})
            
            self.building_container[building].add(sprite1)
            self.building_container[building].add(sprite2)
            self.building_container[building].add(sprite3)

    def get_colliding_tower(self, pos):
        self.temp_sprite.rect.topleft = pos
        collided_sprites_wout_sign = []
        for building_group in self.building_container.values():
            collided_sprites = pygame.sprite.spritecollide(self.temp_sprite, building_group, False)
            for index, sprite in enumerate(collided_sprites):
                if not type(sprite) == pygame.sprite.Sprite:
                    collided_sprites_wout_sign.append(sprite)
        return collided_sprites_wout_sign

    def set_screen(self, blocksize, pre_load_towers):
        self.screen_size = self.screen.get_size()
        self.blocksize_x, self.blocksize_y = blocksize
        self.pre_load_towers = pre_load_towers
        self.create_toolbar()

    @staticmethod
    def get_towers():
        conf = configparser.ConfigParser()
        conf.read(os.path.join(Toolbar.get_conf("toolbar"), "toolbar.ini"))
        return [i.upper() for i in json.loads(conf.get("MENU", "towers"))]

    @staticmethod
    def get_conf(name):
        for root, dir, files in os.walk(Path(__file__).parent):
            for file in files:
                if file.startswith(name):
                    return os.path.join(root)
        return None
    
