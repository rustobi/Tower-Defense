# GENERAL IMPORTS
import pygame, configparser, os, json, time, io, cProfile, pstats
import draw_map, enemy, fieldcontrol, toolbar, preload, sound_control, empire, button
import copy as copy_sprite
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from threading import Thread
from matplotlib.widgets import CheckButtons

class Gameloop():
    def __init__(self, screen, clock, fps: int, level: int, screen_size: tuple, fullscreen: bool):
        self.screen = screen
        self.fullscreen = fullscreen
        self.WIDTH, self.HEIGHT = screen_size

        self.clock = clock
        self.FPS = fps
        self.balanced_FPS = 60
        self.running = True
        self.level = level
        self.spawned_enemys = 0
        self.wave_pause_timer = 0
        self.wave_pause = False
        self.pause = False
        self.mouse_first_pos = []
        self.ms_per_frame = 0


    def load_level(self, level_data, money_amount, loading_screen_images):
        self.p_bar_value = 0
        p_bar_actual = 0
        loading_screen_image_timer = 0
        self.wave = 0

        # Loading Progress Bar
        kontur_sur = pygame.Surface((520, 50))
        kontur_sur.fill((0,0,0))
        kontur_rect = kontur_sur.get_rect()
        kontur_rect.center = (self.screen.get_width() // 2, self.screen.get_height() // 2 + 35)

        # Loading Font
        loading_font = pygame.font.SysFont("arialblack.ttf", 72)
        loading_font_image = loading_font.render("Lade Level: " + str(self.level), True, (0,0,0))
        loading_font_rect = loading_font_image.get_rect()
        loading_font_rect.center = (self.screen.get_width() // 2, self.screen.get_height() // 2 - 35)

        thread = Thread(target=self.perload_gameloop, args=(level_data, money_amount))
        thread.start()

        while thread.is_alive() or p_bar_actual < 100:
            if p_bar_actual < self.p_bar_value:
                p_bar_actual += 1
            if int(loading_screen_image_timer) >= len(loading_screen_images) - 1:
                loading_screen_image_timer = 0
            else:
                loading_screen_image_timer += 0.05

            # Loading Progress Bar
            progressbar_sur = pygame.Surface((500 * p_bar_actual / 100, 40))
            progressbar_sur.fill((126,231,1))
            progressbar_rect = progressbar_sur.get_rect()
            progressbar_rect.topleft = (kontur_rect.left + 5, kontur_rect.top + 5)

            self.screen.blit(loading_screen_images[int(loading_screen_image_timer)], (0, 0))
            self.screen.blit(kontur_sur, kontur_rect)
            self.screen.blit(progressbar_sur, progressbar_rect)
            self.screen.blit(loading_font_image, loading_font_rect)
            pygame.display.flip()
            self.clock.tick(300)
        self.start_gameloop()


    def perload_gameloop(self, level_data, money_amount):
        # LEVEL DATA
        self.level_data = level_data
        self.waves = level_data.get("waves")
        self.money_amount = money_amount
        MAP = os.path.join(self.level_data.get("level_path"), "map.ini")
        MAP_CONFIG = configparser.ConfigParser()
        MAP_CONFIG.read(MAP)
        self.FIXED_COLUMN_SIZE = json.loads(MAP_CONFIG.get("MAP", "column_size"))
        self.FIXED_ROW_SIZE = json.loads(MAP_CONFIG.get("MAP", "row_size"))
        self.blocksize_x, self.blocksize_y = self.get_blocksize()

        # PYGAME CLASSES
        self.sound_control = sound_control.SoundControl()
        self.enemys = pygame.sprite.Group()
        self.dead_enemys = pygame.sprite.Group()
        self.mouse_sprite = pygame.sprite.Sprite()          # MOUSE COLLIDING SPRITE
        self.mouse_color = pygame.Color(0)                  # GOD MODE COLOR

        # DICTS
        self.next_shoot_dead_enemys = {}
        self.projektil_cache = {}
        self.main_objects = {}
        self.analisierer = {"map":[], "enemys":[], "fieldcontrol":[],
                            "toolbar":[], "verb. ms":[], "objekte verb. ms":[], "fps_ms": []}

        self.p_bar_value += 10

        ####################################### HARD PRELOAD #######################################
        self.temp_map = json.loads(MAP_CONFIG.get("MAP", "tile_map"))
        self.map_drawer = draw_map.Draw_map(self.blocksize_x, self.blocksize_y, self.FIXED_COLUMN_SIZE,
                                            self.FIXED_ROW_SIZE, MAP_CONFIG, self.screen)
        self.y_offset = [self.map_drawer.get_max_y_offset() // 2]
        self.start_end_points = self.map_drawer.get_start_end_points()
        self.optimal_path, self.readable_path = self.create_move_path([])
        self.EMPIRE_KOORDINATE = self.get_empire_coordinate()

        self.timer = 0
        self.hue = 0
        
        self.empire = empire.Empire(self.screen, (self.EMPIRE_KOORDINATE), self.y_offset, (self.blocksize_x, self.blocksize_y))
        self.pre_load_enemys = preload.PreLoad(self.level_data.get("enemys"), (self.blocksize_x, self.blocksize_y))
        self.p_bar_value += 20

        self.pre_load_towers = preload.PreLoad(toolbar.Toolbar.get_towers(), (self.blocksize_x, self.blocksize_y), self.screen)
        self.p_bar_value += 20
        
        self.tool_bar = toolbar.Toolbar(self.screen, self.pre_load_towers.get_image_list(), self.blocksize_x, self.blocksize_y,
                                        self.FIXED_COLUMN_SIZE, self.FIXED_ROW_SIZE, self.money_amount, self.sound_control)
        self.p_bar_value += 20
        
        self.field_control = fieldcontrol.FieldControl(self.screen, (self.blocksize_x, self.blocksize_y), self.pre_load_towers.get_image_list(),
                                                       self.pre_load_towers.get_projektil_images(), self.WIDTH, self.HEIGHT,
                                                       self.readable_path, self.pre_load_towers.get_tower_specs(), self.pre_load_towers.get_status_speed(),
                                                       self.next_shoot_dead_enemys, self.sound_control, self.money_amount, self.y_offset, self.balanced_FPS,
                                                       self.clock, self.projektil_cache)
        self.p_bar_value += 20
        #######################################################################################

        # BOOLS
        self.fast_forward = False
        self.finisher = False       # GOD MODE
        self.cooldown = False       # Cooldown für Maus Klick

        # FONTS
        self.money_ui_font = pygame.font.SysFont("arialblack.ttf", int(28 * (self.blocksize_x / 60)))
        self.pause_font = pygame.font.SysFont("arialblack.ttf", 72)
        self.wave_font = pygame.font.SysFont("arialblack.ttf", 60)
        self.little_font = pygame.font.SysFont("arialblack.ttf", int(30 * (self.blocksize_x / 60)))

        # PYGAME IMAGES
        self.fast_forward_activated_image = self.pre_load_towers.get_image_list()["CONTROL"]["speed_up"]["speed_up_direct"][1]
        self.money_ui_image = self.pre_load_towers.get_image_list()["CONTROL"]["money_ui"]["money_ui_direct"][0]
        self.health_ui_image = self.pre_load_towers.get_image_list()["CONTROL"]["health_ui"]["health_ui_direct"][0]
        self.mouse_sprite.image = pygame.Surface((30, 30))

        # PYGAME METHODS
        self.fast_forward_activated_image = pygame.transform.scale(self.fast_forward_activated_image, (self.blocksize_x * 0.5, self.blocksize_x * 0.5))
        self.money_ui_image = pygame.transform.scale(self.money_ui_image, (self.blocksize_x * 4 *0.50, self.blocksize_x*0.45))
        self.health_ui_image = pygame.transform.scale(self.health_ui_image, (self.blocksize_x * 4 *0.50, self.blocksize_x*0.45))
        self.mouse_sprite.rect = self.mouse_sprite.image.get_rect()
        self.pause_img = self.pause_font.render("Pause", True, (255,255,255))
        self.p_bar_value += 10


    def get_blocksize(self):
        # Immer Angepasst an die Breite des Spielfeldes
        return (self.screen.get_width() // self.FIXED_ROW_SIZE, self.screen.get_width() // self.FIXED_ROW_SIZE)

    def create_move_path(self, map):
        for index_r, row in enumerate(self.temp_map):
            map.append([])
            for column in row:
                if column.startswith("p"):
                    map[index_r].append(1)
                elif column.startswith("e"):
                    map[index_r].append(2)
                else:
                    map[index_r].append(0)

        # Create move path
        grid = Grid(matrix=map)
        start = grid.node(self.start_end_points[0][0] - 1, self.start_end_points[0][1] - 1)
        end = grid.node(self.start_end_points[1][0] - 1, self.start_end_points[1][1] - 1)
        path, _ = AStarFinder().find_path(start, end, grid)

        for index, point in enumerate(path):
            if index == len(path)-1:
                direction = "left" # ENEMY SCHIESST IMMER VON LINKS
            else:
                next_point = path[index + 1]
                if point[0] < next_point[0]: direction = "right"
                elif point[0] > next_point[0]: direction = "left"
                elif point[1] < next_point[1]: direction = "down"
                elif point[1] > next_point[1]: direction = "up"
            path[index] = (point, direction)
        return path, map
    

    def get_sprites_in_range(group, rect):
        sprites = []
        for sprite in group.sprites():
            if sprite.rect.colliderect(rect):  # Kollision mit dem gesamten Bereich prüfen
                    sprites.append(sprite)
        return sprites
    
    def get_empire_coordinate(self):
        for index_r, row in enumerate(self.temp_map):
            if "empire_1" in row:
                return ((row.index("empire_1") + 1) * self.blocksize_x, (index_r + 1) * self.blocksize_y)

    def get_norm_multiplikator(self, norm):
        return self.screen.get_width() / norm

    def create_main_objects(self):
        health_bar_size = (self.health_ui_image.get_width() / 4 * 3 * self.empire.health / self.empire.max_health,
                           self.health_ui_image.get_height())
        self.health_bar_sur = pygame.Surface(health_bar_size, pygame.SRCALPHA, 32)
        pygame.draw.rect(self.health_bar_sur, (255, 0, 0), (0, 0, *health_bar_size), border_radius=6)
        self.money_ui_font_image = self.money_ui_font.render(str(self.money_amount[0]), True, (79,52,9))
        self.last_money = self.money_amount[0]
        self.main_objects.setdefault(self.money_ui_image,
                                     self.money_ui_image.get_rect(topleft=(self.blocksize_y // 4,
                                                                           self.blocksize_y // 4)))
        self.main_objects.setdefault(self.money_ui_font_image,
                                     self.money_ui_font_image.get_rect(centery=self.main_objects.get(self.money_ui_image).centery,
                                                                       right=self.main_objects.get(self.money_ui_image).right - 10 * self.blocksize_y / 100))
        
        self.main_objects.setdefault(self.health_bar_sur,
                                     self.health_bar_sur.get_rect(topleft=(self.blocksize_y // 4 + self.health_ui_image.get_width() / 4,
                                                                           self.main_objects.get(self.money_ui_image).y + self.blocksize_y // 16 + self.health_ui_image.get_height())))
        self.main_objects.setdefault(self.health_ui_image,
                                     self.health_ui_image.get_rect(topleft=(self.blocksize_y // 4,
                                                                            self.main_objects.get(self.money_ui_image).y + self.health_ui_image.get_height() + self.blocksize_y // 16)))

        self.fast_forward_button = button.Button((self.blocksize_x * 0.5, self.blocksize_y * 0.5),
                                                 (self.blocksize_y // 4, self.main_objects.get(self.health_ui_image).y + self.blocksize_y * 0.5 + self.blocksize_y // 16),
                                                 ["fast_forward", "fast_forward_activated"],
                                                 self.pre_load_towers.get_image_list()["CONTROL"]["speed_up"]["speed_up_direct"])

    def draw_mainloop_objects(self):
        if not self.main_objects:
            self.create_main_objects()

        # Handle Dynamic Surfaces
        health_bar_size = (self.health_ui_image.get_width() / 4 * 3 * self.empire.health / self.empire.max_health,
                           self.health_ui_image.get_height())
        if self.health_bar_sur.get_width() != int(health_bar_size[0]):
            health_bar_rect = self.main_objects.get(self.health_bar_sur)
            self.main_objects.pop(self.health_bar_sur)
            if health_bar_size[0] > 0:
                self.health_bar_sur = pygame.Surface(health_bar_size, pygame.SRCALPHA, 32)
            else:
                self.health_bar_sur = pygame.Surface((0,health_bar_size[1]), pygame.SRCALPHA, 32)
            pygame.draw.rect(self.health_bar_sur, (255, 0, 0), (0, 0, *health_bar_size), border_radius=6)
            self.main_objects = {**{self.health_bar_sur: health_bar_rect}, **self.main_objects}

        if self.last_money != self.money_amount[0]:
            self.main_objects.pop(self.money_ui_font_image)
            self.money_ui_font_image = self.money_ui_font.render(str(self.money_amount[0]), True, (79,52,9))
            self.main_objects.update({self.money_ui_font_image:
                                      self.money_ui_font_image.get_rect(centery=self.main_objects.get(self.money_ui_image).centery,
                                                                        right=self.main_objects.get(self.money_ui_image).right - 10 * self.blocksize_x / 60)})
            self.last_money = self.money_amount[0]

        for image, rect in self.main_objects.items():
            self.screen.blit(image, rect)

    def set_wave(self):
        if self.wave == self.waves:
            self.running = False

        if self.wave != 0:
            self.wave_money = self.level_data.get("wave" + str(self.wave)).get("money")
            self.wave_money_font_img = self.wave_font.render(str(self.wave_money) + "$", True, (79,52,9))
            self.money_amount[0] += self.wave_money
        self.timer = 0
        self.wave += 1
        self.wave_pause = True
        self.spawned_enemys = 0
        self.wave_font_img = self.wave_font.render("Wave " + str(self.wave), True, (79,52,9))
        self.wave_font_rect = self.wave_font_img.get_rect(center=(self.screen.get_width() // 2 + 20, self.screen.get_height() // 2))
        self.wave_font_f_pos = [self.wave_font_rect.center[0], self.wave_font_rect.center[1]]
        self.wave_font_timer = 0

    def draw_wave_pause(self):
        self.wave_pause_timer += 1
        if self.wave_pause_timer >= 83:
            self.wave_pause = False
            self.wave_pause_timer = 0
        else:
            self.wave_font_timer += 0.25
            self.wave_font_rect.centerx = self.wave_font_f_pos[0] - self.wave_font_timer
            self.screen.blit(self.wave_font_img, self.wave_font_rect)
            if self.wave != 1:
                wave_money_rect = self.wave_font_rect.copy()
                wave_money_rect.top = self.wave_font_rect.bottom + 10
                wave_money_rect.centerx = self.wave_font_rect.centerx
                self.screen.blit(self.wave_money_font_img, wave_money_rect)

    def offset_limiter(self):
        if self.y_offset[0] > self.map_drawer.get_max_y_offset():
                self.y_offset[0] = self.map_drawer.get_max_y_offset()
        if self.y_offset[0] < 0:
            self.y_offset[0] = 0

    def set_screen(self):
        old_size = (self.screen.get_width(), self.screen.get_height())
        if self.screen.get_flags() & pygame.FULLSCREEN == 0:
            pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        self.blocksize_x, self.blocksize_y = self.get_blocksize()
        self.EMPIRE_KOORDINATE = self.get_empire_coordinate()
        
        self.y_offset[0] = self.y_offset[0] * (self.screen.get_height() / old_size[1])

        ############ PRELOAD ############
        self.pre_load_enemys = preload.PreLoad(self.enemy, (self.blocksize_x, self.blocksize_y))
        self.pre_load_towers = preload.PreLoad(self.tool_bar.get_towers(), (self.blocksize_x, self.blocksize_y))
        #################################

        # FONTS
        self.money_ui_font = pygame.font.SysFont("arialblack.ttf", int(28 * (self.blocksize_x / 60)))
        self.little_font = pygame.font.SysFont("arialblack.ttf", int(30 * (self.blocksize_x / 60)))

        # IMAGES
        self.money_ui_image = self.pre_load_towers.get_image_list()["CONTROL"]["money_ui"]["money_ui_direct"][0]
        self.health_ui_image = self.pre_load_towers.get_image_list()["CONTROL"]["health_ui"]["health_ui_direct"][0]

        # PYGAME METHODS
        self.money_ui_image = pygame.transform.scale(self.money_ui_image, (self.blocksize_x * 4 * 0.5, self.blocksize_x * 0.45))
        self.health_ui_image = pygame.transform.scale(self.health_ui_image, (self.blocksize_x * 4 * 0.5, self.blocksize_x * 0.45))
        self.wave_font_rect.center = (self.wave_font_rect.centerx * (self.screen.get_width() / old_size[0]), self.screen.get_height() // 2)

        # WAVE CONFIGURE
        self.wave_font_f_pos = [self.wave_font_rect.center[0], self.wave_font_rect.center[1]]
        self.wave_font_timer = 0

        # CLEAR CACHE
        self.main_objects.clear()
        for values in self.projektil_cache.values():
            values.clear()

    def start_gameloop(self):
        self.set_wave()
        while self.running:
            t_gameloop = time.time()
            mouse_pos = pygame.mouse.get_pos()

            self.wave_information = self.level_data.get("wave" + str(self.wave))
            if self.wave_information:
                self.max_enemys = self.wave_information.get("enemy_count")
                self.enemy_outcome_td = self.wave_information.get("enemy_outcome_rate")
                self.enemy = self.wave_information.get("enemy")

            for event in pygame.event.get():

                # HANDLE QUIT
                if event.type == pygame.QUIT:
                    self.running = False

                # HANDLE MOUSEWHEEL
                if event.type == pygame.MOUSEWHEEL:
                    event.y = event.y * 20
                    self.y_offset[0] -= event.y
                    self.offset_limiter()

                # HANDLE KEYS
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        self.set_screen()

                    if event.key == pygame.K_g:
                        self.finisher = not self.finisher

                    if event.key == pygame.K_p:
                        self.pause = not self.pause

            # DYNAMIC VARIABLES
            mouse_press = pygame.mouse.get_pressed()
            self.mouse_sprite.rect.center = (mouse_pos[0], mouse_pos[1])
                
            # ADD ENEMYS ON TIME
            if not self.wave_pause and not self.pause and self.timer > self.enemy_outcome_td:
                self.timer = 0
                if self.spawned_enemys < self.max_enemys:
                    self.spawned_enemys += 1
                    self.enemys.add(enemy.Enemy(self.enemy[0], self.screen, self.blocksize_x, self.blocksize_y, self.start_end_points[0], self.optimal_path,
                                            self.empire, self.pre_load_enemys.get_image_list(), self.pre_load_enemys.get_projektil_images(),
                                            self.pre_load_enemys.get_status_speed(), self.enemys, self.dead_enemys, self.next_shoot_dead_enemys,
                                            self.sound_control, self.money_amount, self.y_offset, self.balanced_FPS, self.clock, self.projektil_cache))

            # DRAW MAP
            t_map1 = time.time()
            self.map_drawer.update(self.y_offset[0], (self.blocksize_x, self.blocksize_y))
            self.analisierer["map"].append((time.time() - t_map1) * 1000)

            if self.cooldown and mouse_press[0]:
                mouse_press = (False, mouse_press[1], mouse_press[2])

            # HANDLE TOOLBAR
            t_toolbar = time.time()
            colliding_towers = self.tool_bar.get_colliding_tower(mouse_pos)
            self.tool_bar.update(colliding_towers, (self.blocksize_x, self.blocksize_y), self.pre_load_towers.get_image_list())
            self.analisierer["toolbar"].append((time.time() - t_toolbar) * 1000)

            # HANDLE EMPIRE
            self.empire.update((self.blocksize_x, self.blocksize_y))
            self.screen.blit(self.empire.image, self.empire.rect)

            # HANDLE ENEMYS
            t_enemys = time.time()
            self.enemys.update(self.fast_forward, self.pause, (self.blocksize_x, self.blocksize_y),
                               self.pre_load_enemys.get_image_list(), self.pre_load_enemys.get_projektil_images())
            
            #- HANDLE MOUSE-HOVERED_ENEMS
            collided_sprites_mouse = pygame.sprite.spritecollide(self.mouse_sprite, self.enemys, False)
            if collided_sprites_mouse:
                sprite = collided_sprites_mouse[0]
                outline_surface = pygame.Surface(sprite.rect.size, pygame.SRCALPHA)
                for point in sprite.mask.outline(1):
                    pygame.draw.circle(outline_surface, (255,0,0), point, 1 * (self.blocksize_x / 64))
                if mouse_press[0] and not self.cooldown:
                    self.cooldown = True
                    sprite.damage(0.5)
                self.screen.blit(outline_surface, sprite.rect.topleft)
            #-

            self.dead_enemys.update(self.fast_forward, self.pause, (self.blocksize_x, self.blocksize_y),
                                    self.pre_load_enemys.get_image_list(), self.pre_load_enemys.get_projektil_images())
            self.dead_enemys.draw(self.screen)
            self.enemys.draw(self.screen)
            self.analisierer["enemys"].append((time.time() - t_enemys) * 1000)
            
            # HANDLE FIELDCONTROL
            t_field_control = time.time()
            self.field_control.update(mouse_pos, mouse_press, colliding_towers,
                                      (self.blocksize_x, self.blocksize_y), self.enemys, self.pause,
                                      self.tool_bar.prices, self.fast_forward, self.pre_load_towers.get_image_list())
            self.analisierer["fieldcontrol"].append((time.time() - t_field_control) * 1000)


            # HANDLE MAINLOOP OBJECTS
            self.draw_mainloop_objects()
            self.fast_forward_button.update(mouse_pos, mouse_press)
            if self.fast_forward_button.pressed and mouse_press[0]:
                self.fast_forward = not self.fast_forward
            if self.fast_forward: self.fast_forward_button.set_state(1)
            else: self.fast_forward_button.set_state(0)

            # DRAW BUTTONS
            self.screen.blit(self.fast_forward_button.image, self.fast_forward_button.rect)

            # DRAW FPS
            fps = self.little_font.render(f"FPS: {round(self.clock.get_fps(), 0)}", True, (79,52,9))
            self.screen.blit(fps, (self.blocksize_x / 4, self.screen.get_height() - fps.get_height() - self.blocksize_y / 4))

            # HANDLE GOD MODE
            if mouse_press[0] and self.finisher:
                self.mouse_first_pos = []
                self.mouse_color.hsla = (self.hue, 100, 50, 100)
                self.hue = self.hue + 1 if self.hue < 360 else 0 
                self.mouse_sprite.image.fill(self.mouse_color)
                self.mouse_sprite.rect = self.mouse_sprite.image.get_rect(center=(mouse_pos[0], mouse_pos[1]))
                self.screen.blit(self.mouse_sprite.image, self.mouse_sprite.rect)
                pygame.sprite.spritecollide(self.mouse_sprite, self.enemys, True)

            # HANDLE HOLDED MOUSE
            mouse_press = pygame.mouse.get_pressed()
            if mouse_press[0] and not self.cooldown:
                self.cooldown = True
                if not self.field_control.get_hovered_tower():
                    self.mouse_first_pos = mouse_pos
            elif not mouse_press[0]:
                self.cooldown = False
                self.mouse_first_pos = []

            # HANDLE OFFSET
            if self.mouse_first_pos:
                y_dist = mouse_pos[1] - self.mouse_first_pos[1]
                self.y_offset[0] -= y_dist
                self.mouse_first_pos = mouse_pos
                self.offset_limiter()

            # HANDLE PAUSE
            if self.pause and not self.wave_pause:
                self.screen.blit(self.pause_img, (25, 25))
            elif not self.pause and not self.wave_pause:
                if self.fast_forward:
                    self.timer += 2 * (self.FPS / self.clock.get_fps())
                else:
                    self.timer += 1 * (self.FPS / self.clock.get_fps())
            
            # HANDLE WAVE
            if self.wave_pause: self.draw_wave_pause()
            if self.spawned_enemys >= self.max_enemys and not self.enemys and not self.dead_enemys and not self.wave_pause:
                self.set_wave()

            # HANDLE LOOSING
            if self.empire.health <= 0: self.running = False

            pygame.display.flip()
            
            if self.running: self.ms_per_frame = (time.time() - t_gameloop) * 1000

            self.analisierer["verb. ms"].append(self.ms_per_frame)
            self.clock.tick(self.FPS)
            if self.running: self.ms_per_frame_fps = (time.time() - t_gameloop) * 1000
            self.analisierer["fps_ms"].append(self.ms_per_frame_fps)

        
        for k,v in self.analisierer.items():
            if k not in  ["verb. ms", "objekte verb. ms", "fps_ms"]:
                for index, value in enumerate(v):
                    try:
                        self.analisierer["objekte verb. ms"][index] += value
                    except Exception as e:
                        self.analisierer["objekte verb. ms"].append(value)

        zeit = [i for i in range(len(self.analisierer["enemys"]))]
        fig, ax = plt.subplots()

        plots = []
        labels = []

        for k, v in self.analisierer.items():
            line, = ax.plot(zeit, v, label=k)
            plots.append(line)
            labels.append(k)

            ax.axhline(y=np.nanmean(v), color=line.get_color(), linestyle='--', linewidth=2, label=f'Avg {k}')

        # Erstelle Checkboxen für jeden Plot
        rax = plt.axes([0.05, 0.75, 0.1, 0.1])
        check = CheckButtons(rax, labels, [True] * len(labels))  # Standardmäßig alle Plots eingeschaltet

        # Funktion zum Ein- und Ausblenden der Plots basierend auf Checkbox-Status
        def update_plots(label):
            for i, line in enumerate(plots):
                line.set_visible(check.get_status()[i])
            plt.draw()

        check.on_clicked(update_plots)

        # Weitere Anpassungen des Diagramms
        ax.set_xlabel("Frames")
        ax.set_ylabel("Vergangene Zeit in ms")
        ax.set_title(f"Analyse Tower Defense | TOTAL ENEMYS: {len(self.enemys)}")
        ax.legend()

        plt.show()