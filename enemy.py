from typing import Any
from pygame.locals import *
import pygame, random, math
import projektil, particle
from pygame._sdl2.video import Window, Renderer, Texture, Image

class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_name, screen, blocksize_x, blocksize_y, start_point,
                 path, ziel_gebaeude, preload_images, preload_projektil_images,
                 preload_status_speed, enemy_group, dead_group, next_shoot_dead_enemys,
                 sound_control, money_amount, map_offset, fps, clock, projektil_cache):
        # INIT_SPRITE
        pygame.sprite.Sprite.__init__(self)

        # INIT_PARAMETER
        self.name = enemy_name
        self.screen = screen
        self.screen_size = self.screen.get_size()
        self.blocksize_x = blocksize_x
        self.blocksize_y = blocksize_y
        self.start_point = start_point
        self.path = path
        self.preload_images = preload_images[self.name]
        self.preload_projektil_images = preload_projektil_images[self.name]
        self.preload_status_speed = preload_status_speed[self.name]
        self.max_health = 10
        self.health = 10
        self.enemy_group = enemy_group
        self.dead_group = dead_group
        self.next_shoot_dead_enemys = next_shoot_dead_enemys
        self.sound_control = sound_control
        self.money_amount = money_amount
        self.last_pos = [0,0]
        self.walked = [0, 0]
        self.map_offset = map_offset
        self.fps = fps
        self.clock = clock
        self.projektil_cache = projektil_cache

        # CHARAKTER CONF
        self.ENEMY_SIZE_DECREASE = 0.5
        self.speed = self.preload_status_speed["speed"] * (self.blocksize_x / 100)
        self.random_path_offset = random.randrange(-int(self.blocksize_x / 4), int(self.blocksize_x / 3), 10)
        self.width = blocksize_x * self.ENEMY_SIZE_DECREASE
        self.height = blocksize_y * self.ENEMY_SIZE_DECREASE
        self.direction = self.path[0][1]
        self.status = "walk"
        self.shooted = False
        self.animation_timer = 0
        self.ziel_gebaeude = ziel_gebaeude
        self.projektile = pygame.sprite.Group()
        self.deckkraft = 100
        self.ff_increase = 1
        self.price_font = pygame.font.SysFont("arialblack.ttf", int(18 * (self.blocksize_x / 60)))
        self.money_img = self.price_font.render(str(int(self.preload_status_speed["money"])), True, (255,255,0))
        self.money_kontur = pygame.mask.from_surface(self.money_img)
        self.money_kontur = self.money_kontur.to_surface()
        self.money_kontur.set_colorkey((255,255,255))
        self.money_rect = pygame.rect.Rect(0,0,self.money_img.get_width(), self.money_img.get_width())
        self.offset = self.map_offset[0]

        # PATHFINDING
        self.move_stat = 0
        self.start = True

        # CHARACTER INITIALISIERUNG
        self.image = self.get_current_image()
        self.rect = self.image.get_rect()

        # Particles
        self.particles = pygame.sprite.Group()

    def set_map_offset(self):
        self.rect.topleft = (self.rect.x, self.rect.y - self.map_offset[0] + self.offset)
        self.money_rect.y = self.money_rect.y - self.map_offset[0] + self.offset
        self.last_pos = [self.last_pos[0], self.last_pos[1] - self.map_offset[0] + self.offset]
        self.offset = self.map_offset[0]

    def set_fast_forward(self, fast_forward):
        if fast_forward:
            if self.ff_increase != 2:
                self.speed *= 2
            self.ff_increase = 2
        else:
            if self.ff_increase != 1:
                self.speed /= 2
            self.ff_increase = 1

    def handle_dead_enemy(self):
        self.money_amount[0] += self.preload_status_speed["money"]
        self.money_rect.center = (self.rect.centerx,
                                    self.rect.centery)
        self.status = "die"
        self.animation_timer = 0
        self.enemy_group.remove(self)
        self.dead_group.add(self)

    def handle_shoot_status(self):
        if self.animation_timer == 0:
            self.shooted = False
        self.animation_timer += self.preload_status_speed[self.status] * self.speed
        if int(self.animation_timer) == 9 and not self.shooted:
            self.shooted = True
            self.projektil_cache.setdefault(self.name, {})
            self.projektile.add(projektil.Projektil(self.screen, (self.rect.left, self.rect.centery),
                                                    self.ziel_gebaeude.rect.center, self.blocksize_x,
                                                    self.blocksize_y, self.preload_projektil_images,
                                                    (0.15, 0.05), self.preload_status_speed["damage"],
                                                    self.ziel_gebaeude, self.preload_status_speed["projektil_speed"],
                                                    self.map_offset, self.fps, self.clock, self.projektil_cache, self.name))

    def update(self, fast_forward, pause, blocksize, preload_images, preload_projektil_images):
        if self.screen_size != self.screen.get_size():
            self.set_screen(blocksize, preload_images, preload_projektil_images)

        if self.offset != self.map_offset[0]:
            self.set_map_offset()

        if pause:
            return

        self.set_fast_forward(fast_forward)

        if self.health <= 0 and not self.status == "die":
            self.handle_dead_enemy()

        if self.status == "shoot":
            self.handle_shoot_status()
        elif self.status == "die":
            self.draw_money()
            if not int(self.animation_timer) >= len(self.preload_images[self.status]["die"]):
                self.animation_timer += self.preload_status_speed[self.status] * self.speed
        else:
            self.move()
            self.animation_timer += self.preload_status_speed[self.status] * self.speed
        self.image = self.get_current_image()
        self.projektile.update(self.ff_increase, blocksize)
        self.particles.update()
        self.particles.draw(self.screen)
        if self.health < self.max_health:
            self.draw_lifebar()
        self.projektile.draw(self.screen)

    def draw_money(self):
        if self.money_rect.centery > self.rect.centery - 20:
            self.money_rect.centery -= 1
        self.money_img.set_alpha(self.money_img.get_alpha() - 2.5)
        self.screen.blit(self.money_img, self.money_rect)
        self.screen.blit(self.money_kontur, self.money_rect)

    def draw_lifebar(self):
        if self.health > 0:
            self.lifebar_img = pygame.Surface((int(self.image.get_size()[0] / 2) * (self.health / self.max_health), 5 * self.ENEMY_SIZE_DECREASE))
            self.lifebar_img.fill((255,0,0))
            self.lifebar_rect = self.lifebar_img.get_rect()
            self.lifebar_rect.topleft = (self.rect.x + self.image.get_size()[0] / 4, self.rect.y - 2.5)
            self.screen.blit(self.lifebar_img, self.lifebar_rect)

    def walk_into_direction(self, walked, speed, direction):
        # FPS ABHÄNGIGKEIT
        fps_abhaengig_speed = speed * (self.fps / self.clock.get_fps())
        if     direction == "left": walked[0] -= fps_abhaengig_speed
        elif   direction == "right": walked[0] += fps_abhaengig_speed
        elif   direction == "up": walked[1] -= fps_abhaengig_speed
        elif   direction == "down": walked[1] += fps_abhaengig_speed
        return walked

    def move(self):
        if self.start:
            self.start = False
            x_pos = self.start_point[0] * self.blocksize_x - self.blocksize_x // 2 - self.width // 2 + self.blocksize_x // 2
            y_pos = self.start_point[1] * self.blocksize_y - self.blocksize_y // 2 - self.height + self.random_path_offset - self.offset
            self.last_pos = [x_pos, y_pos]
            self.rect.move_ip([x_pos, y_pos])
            return
        
        self.direction = self.path[self.move_stat][1]
        self.walked = self.walk_into_direction(self.walked, self.speed, self.direction)
        self.rect.topleft = (int(self.last_pos[0] + self.walked[0]), int(self.last_pos[1] + self.walked[1]))

        if len(self.path) - 1 != self.move_stat:
            if self.check_passing_path(self.rect, self.move_stat):
                self.move_stat += 1
                self.direction = self.path[self.move_stat][1]
            if self.move_stat == len(self.path) - 1:
                self.status = "shoot"

    def get_pos_after_steps(self, projectil_rect, enemy_rect, projektil_speed):
        hit = False
        enemy_rect.center = self.rect.center
        enemy_last_pos = [enemy_rect.left, enemy_rect.top]
        enemy_walked = [0, 0]
        move_stat = self.move_stat
        direction = self.direction
        steps = 0 # Vielleicht zur Begrenzung
        path_len = len(self.path)
        projektil_speed = projektil_speed * 5

        while not hit:
            steps += 5
            if path_len - 1 == move_stat: break
            enemy_walked = self.walk_into_direction(enemy_walked, self.speed, direction)
            enemy_rect.topleft = (round(enemy_last_pos[0] + enemy_walked[0]), round(enemy_last_pos[1] + enemy_walked[1]))

            if path_len - 1 != move_stat:
                if self.check_passing_path(enemy_rect, move_stat):
                    move_stat += 1
                    direction = self.path[move_stat][1]

            y_dist = enemy_rect.centery - projectil_rect.centery
            x_dist = enemy_rect.centerx - projectil_rect.centerx
            hypotenuse = math.sqrt(y_dist ** 2 + x_dist ** 2)
            if hypotenuse // (projektil_speed) <= steps:
                hit = True
        return enemy_rect

    def check_passing_path(self, rect, move_stat):
        # RETURN TRUE, WENN DER NÄCHSTE SCHRITT DAS ZIEL ÜBERSPRINGT
        ziel = (float(self.path[move_stat + 1][0][0] + 1), float(self.path[move_stat + 1][0][1] + 1))
        ziel = (ziel[0] * self.blocksize_x - self.blocksize_x // 2 - self.width // 2 - self.random_path_offset // 2,
                ziel[1] * self.blocksize_y - self.blocksize_y // 2 - self.height + self.random_path_offset - self.offset)
        change = False
        match self.direction:
            case "right":
                if rect.x + self.speed > ziel[0]:
                    change = True
            case "left":
                if rect.x - self.speed < ziel[0]:
                    change = True
            case "down":
                if rect.y + self.speed > ziel[1]:
                    change = True
            case "up":
                if rect.y - self.speed < ziel[1]:
                    change = True
        return change

    def get_current_image(self):
        if self.status == "die":
            concat = self.status
        else:
            concat = self.status + "_" + self.direction

        images = self.preload_images[self.status][concat]
        masks = self.preload_images[self.status][concat + "_masks"]
        num_images = len(images)

        if int(self.animation_timer) < num_images:
            self.mask = masks[int(self.animation_timer)]
            return images[int(self.animation_timer)]
        
        if self.status == "die":
            self.deckkraft -= 10
            if self.deckkraft == 0:
                if self.next_shoot_dead_enemys.get(self) is not None:
                    self.next_shoot_dead_enemys.pop(self)
                self.kill()
            images[-1].set_alpha(self.deckkraft)
            self.mask = masks[-1]
            return images[-1]
        else:
            self.animation_timer = 0
            self.mask = masks[int(self.animation_timer)]
            return images[int(self.animation_timer)]
        
    def damage(self, damage_amount):
        if self.health > 0:
            self.health -= damage_amount
            self.create_particles(2)

    def create_particles(self, amount):
        for num in range(amount):
            particle_ = particle.Particle(self.rect.center, (random.randint(0, 20) / 10 - 1, random.randint(0, 6) / 2 - 1.5),
                                random.randint(2, 5), (self.blocksize_x / 100, self.blocksize_y / 100), self.map_offset)
            self.particles.add(particle_)
            
    def set_screen(self, blocksize, preload_images, preload_projektil_images):
        self.blocksize_x, self.blocksize_y = blocksize
        self.width = self.blocksize_x * self.ENEMY_SIZE_DECREASE
        self.height = self.blocksize_y * self.ENEMY_SIZE_DECREASE
        self.preload_images = preload_images[self.name]
        self.preload_projektil_images = preload_projektil_images[self.name]
        self.image = self.get_current_image()
        multiplikator_x = self.screen.get_width() / self.screen_size[0]
        multiplikator_y = self.screen.get_height() / self.screen_size[1]
        self.price_font = pygame.font.SysFont("arialblack.ttf", int(18 * (self.blocksize_x / 60)))
        self.money_img = self.price_font.render(str(int(self.preload_status_speed["money"])), True, (255,255,0))
        self.money_kontur = pygame.mask.from_surface(self.money_img)
        self.money_kontur = self.money_kontur.to_surface()
        self.money_kontur.set_colorkey((255,255,255))
        self.money_rect.x = math.ceil(self.money_rect.x * multiplikator_x)
        self.money_rect.y = math.ceil(self.money_rect.y * multiplikator_y)
        self.screen_size = pygame.display.get_surface().get_size()
        self.speed = self.preload_status_speed["speed"] * (self.blocksize_x / 100)
        self.ff_increase = 1
        self.rect = self.image.get_rect(topleft=(math.ceil(self.rect.x * multiplikator_x),
                                                 math.ceil(self.rect.y * multiplikator_y)))
        self.last_pos = [self.rect.x, self.rect.y]
        self.walked = [self.walked[0] - int(self.walked[0]), self.walked[1] - int(self.walked[1])]
        self.offset = self.map_offset[0]