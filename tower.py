import time
import pygame, math, math, projektil, random, sys

class Tower(pygame.sprite.Sprite):
    def __init__(self, screen, blocksize, name, parent_name, image, size, x_pos, y_pos, active, sound_control,
                 radius = pygame.Surface((0, 0)), projektil_images = None, tower_specs = None,
                 status_speed = None, next_shoot_dead_enemys = None, price = None, money_amount = None,
                 map_offset = None, fps = None, clock = None, rotation_cache = None, projektil_cache = None):
        # INIT_SPRITE
        pygame.sprite.Sprite.__init__(self)

        # INIT Parameter
        self.screen = screen
        self.screen_size = self.screen.get_size()
        self.blocksize_x, self.blocksize_y = blocksize
        self.name = name
        self.parent_name = parent_name
        self.x_pos, self.y_pos = x_pos, y_pos
        self.active = active
        self.full_preload = image
        self.image_preload = self.full_preload[self.parent_name]["idle_" + self.name]["idle_" + self.name][0]
        self.image = pygame.Surface.copy(self.image_preload)
        self.projektil_images_preload = projektil_images
        self.size = size
        self.animation_timer = 0
        self.tower_specs = tower_specs
        self.status_speed = status_speed
        self.projektil_images_preload = projektil_images
        self.next_shoot_dead_enemys = next_shoot_dead_enemys
        self.sound_control = sound_control
        self.price = price
        self.sell_price = self.price
        self.selled = False

        # Configure Tower
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.x_pos, self.y_pos)
        self.hoverd = False
        self.focused_enemy = None
        self.angle = 0
        self.speed_rotation = 5
        self.shooted = False
        self.focus_target = 0
        self.control_cache = {}
        self.cooldown = 0
        self.middle_contour_surface_angle = 0
        self.ff_increase = 1
        self.level = 1
        self.max_level = 3

        # Generate Radius Shape
        if self.active:
            self.offset = map_offset[0]
            self.map_offset = map_offset
        if self.active and self.name == "top":
            self.fps = fps
            self.clock = clock
            self.radius = self.tower_specs["radius"]
            self.animation_speed = self.status_speed["animation_speed"]
            self.damage = self.status_speed["damage"]
            self.projektil_speed = self.status_speed["projektil_speed"]
            self.money_amount = money_amount
            self.projektile = pygame.sprite.Group()
            self.animation_image_preload_list = image[self.parent_name]["shoot_" + self.name]["shoot_" + self.name]
            self.price_font = pygame.font.SysFont("arialblack.ttf", int(18 * (self.blocksize_x / 60)))
            self.radius_shape = None
            self.set_radius_shape()
            self.rotation_cache = rotation_cache
            self.projktil_cache = projektil_cache

    def set_radius_shape(self):
        if not self.radius_shape:
            self.radius_shape = pygame.sprite.Sprite()
            tower_radius_size = (self.blocksize_x + self.blocksize_y) // 2
            self.radius_shape = pygame.sprite.Sprite()
            shape_surf = pygame.Surface((tower_radius_size * self.radius,
                                        tower_radius_size * self.radius),
                                        pygame.SRCALPHA)
            pygame.draw.circle(shape_surf, (255,0,0), (shape_surf.get_rect().center), tower_radius_size * self.radius // 2)
            shape_surf_mask = pygame.mask.from_surface(shape_surf)
            self.radius_shape.image = shape_surf
            self.radius_shape.mask = shape_surf_mask
            pygame.draw.circle(self.radius_shape.image, (255,0,0, 25), (self.radius_shape.image.get_rect().center), self.radius_shape.image.get_width() // 2)
        self.radius_shape.rect = self.radius_shape.image.get_rect()
        self.radius_shape.rect.center = (self.rect.center)

    def set_rotation_top(self):
        if self.angle < 0:
            self.angle = 360 + self.angle

        if self.angle > 180 and self.angle not in [360, 0]:

            if self.angle + self.speed_rotation > 360:
                self.set_rotation(0)

            elif self.speed_rotation == 1:
                self.set_rotation(round(self.angle, 0) + self.speed_rotation)
            elif self.angle + self.speed_rotation > 320 and self.speed_rotation != 1:
                self.speed_rotation -= 0.5
                self.set_rotation(round(self.angle, 0) + self.speed_rotation)
            else:
                self.speed_rotation = 5
                self.set_rotation(round(self.angle, 0) + self.speed_rotation)

        elif self.angle <= 180 and self.angle not in [360, 0]:

            if self.angle - self.speed_rotation < 0:
                self.set_rotation(0)
            elif self.speed_rotation == 1:
                self.set_rotation(round(self.angle, 0) - self.speed_rotation)
            elif self.angle - self.speed_rotation < 40 and self.speed_rotation != 1:
                self.speed_rotation -= 0.5
                self.set_rotation(round(self.angle, 0) - self.speed_rotation)
            else:
                self.speed_rotation = 5
                self.set_rotation(round(self.angle, 0) - self.speed_rotation)

    def update(self, enemys=None, mouse_sprite=None, mouse_press=None, pause=None, fast_forward=None, blocksize=None, preload_images=None):
        if not self.active:
            if self.hoverd and self.image.get_alpha() >= 175:
                    self.set_highlighting(self.image.get_alpha() - 15)
            elif not self.get_hovered():
                self.set_highlighting(255)

        if self.active:
            if self.screen_size != self.screen.get_size():
                self.set_screen(blocksize, preload_images)
            self.rect.topleft = (self.rect.x, self.rect.y - self.map_offset[0] + self.offset)
            if self.name == "top":
                if self.map_offset[0] != self.offset:
                    self.set_radius_shape()
                if fast_forward:
                    self.ff_increase = 2
                else:
                    self.ff_increase = 1
                self.update_active_tower(enemys, mouse_sprite, mouse_press, pause, blocksize)
            self.offset = self.map_offset[0]
            

    def update_active_tower(self, enemys, mouse_sprite, mouse_press, pause, blocksize):
        balanced_speed = self.animation_speed * self.ff_increase * (self.fps / self.clock.get_fps())
        if not mouse_press[0]:
            self.cooldown = 0
        if self.hoverd:
            self.draw_tower_mods(mouse_sprite, mouse_press)
            if mouse_press[0] and not pygame.sprite.collide_mask(mouse_sprite, self.radius_shape):
                self.set_hovered()

        if not self.focused_enemy and self.angle not in [360, 0]:
            self.set_rotation_top()
        elif not self.focused_enemy and self.angle in [360, 0]:
            self.speed_rotation = 5
            self.angle = 0
            self.animation_timer = 0
        
        if pause:
            self.projektile.draw(self.screen)
            return
        else:
            self.projektile.update(self.ff_increase, blocksize)
            self.projektile.draw(self.screen)

        if self.shooted:
            self.animation_timer += balanced_speed
            if int(self.animation_timer) >= len(self.animation_image_preload_list):
                self.shooted = False
                self.animation_timer = 0
            return

        # Grobe Kollidierung
        kollidierung = self.get_collision(enemys)
        if not kollidierung: return

        self.speed_rotation = 5
        
        collision_method_enemy = self.handle_collision_mode(kollidierung, self.focus_target)
        if collision_method_enemy:
            self.focused_enemy = collision_method_enemy

        y_dist = self.focused_enemy.rect.centery - self.rect.centery
        x_dist = self.focused_enemy.rect.centerx - self.rect.centerx
        winkel = round(math.degrees(math.atan2(-y_dist, x_dist)), 0) - 90
        self.set_rotation(winkel)
        if int(self.animation_timer) >= len(self.animation_image_preload_list) - 1 and not self.shooted:
            self.shooted = True
            if self.next_shoot_dead_enemys.get(self.focused_enemy):
                self.next_shoot_dead_enemys[self.focused_enemy] = self.next_shoot_dead_enemys.get(self.focused_enemy)-self.damage
            else:
                self.next_shoot_dead_enemys.update({self.focused_enemy:self.focused_enemy.health-self.damage})
            self.create_projektil(winkel)
        self.animation_timer += balanced_speed

    def get_collision(self, enemys):
        kollidierung = pygame.sprite.Group(*pygame.sprite.spritecollide(self.radius_shape, enemys, False))
        kollidierung = [sprite for sprite in kollidierung if self.next_shoot_dead_enemys.get(sprite) != 0]

        # Feine Kollidierung
        if kollidierung:
            kollidierung = pygame.sprite.spritecollide(self.radius_shape, kollidierung, False, pygame.sprite.collide_mask)
            return kollidierung
        
        self.focused_enemy = None
        self.animation_timer = 0
        return None
    
    def handle_collision_mode(self, kollidierung, focus_target):
        # Ziel Methode
        if (not self.focused_enemy or self.focused_enemy not in kollidierung) and focus_target == 2:
            return kollidierung[-1]
        elif (not self.focused_enemy or self.focused_enemy not in kollidierung) and focus_target == 1:
            return min(kollidierung, key=lambda x: x.health)
        elif focus_target == 0:
            return min(kollidierung, key=lambda x: x.health)

    def draw_dotted_circle(self, size, angle_):
        middle_contour_surface = pygame.Surface(size, pygame.SRCALPHA)
        for angle in range(0, 360, 20):
            pygame.draw.arc(middle_contour_surface, (125, 0, 0, 50), middle_contour_surface.get_rect(), math.radians(angle), math.radians(angle + 10), 6)
        rotated_surface = pygame.transform.rotate(middle_contour_surface, angle_)
        temp_rect = rotated_surface.get_rect(center=self.radius_shape.rect.center)
        return rotated_surface, temp_rect
    
    def set_tower_mods_positions(self):
        self.tower_radius_size = (self.blocksize_x + self.blocksize_y) // 2
        self.positions = {0: (self.rect.centerx - self.tower_radius_size, self.rect.centery),
                     1: (self.rect.centerx, self.rect.centery + self.tower_radius_size),
                     2: (self.rect.centerx + self.tower_radius_size, self.rect.centery),
                     3: (self.rect.centerx, self.rect.centery - self.tower_radius_size)}

    def draw_tower_mods(self, mouse_sprite, mouse_press):
        self.set_tower_mods_positions()
        # Draw Radius
        pygame.draw.circle(self.radius_shape.image, (255,0,0, 50), (self.radius_shape.image.get_rect().center), self.radius_shape.image.get_width() // 2)
        pygame.draw.circle(self.radius_shape.image, (255,0,0, 200), (self.radius_shape.image.get_width() // 2, self.radius_shape.image.get_height() // 2), self.radius_shape.image.get_width() // 2 - 2, 3)
        self.screen.blit(self.radius_shape.image, self.radius_shape.rect)

        # Create Dotted_Circle
        dotted_sur, dotted_rect = self.draw_dotted_circle((self.radius_shape.image.get_width(),
                                                           self.radius_shape.image.get_height()),
                                                           self.middle_contour_surface_angle)
        self.screen.blit(dotted_sur, dotted_rect)
        self.middle_contour_surface_angle += 0.75
        if self.middle_contour_surface_angle == 360:
            self.middle_contour_surface_angle = 0

        # Draw Tower Mods
        size_mod = (self.tower_radius_size * 0.65, self.tower_radius_size * 0.65)

        self.control_cache.setdefault("sell_tower",
                                      pygame.transform.smoothscale(self.full_preload["CONTROL"]["sell_tower"]["sell_tower_direct"][0], size_mod))
        self.control_cache.setdefault("focus_target",
                                      [pygame.transform.smoothscale(self.full_preload["CONTROL"]["target_not_focused"]["target_not_focused_direct"][0], size_mod),
                                       pygame.transform.smoothscale(self.full_preload["CONTROL"]["target_focused"]["target_focused_direct"][0], size_mod),
                                       pygame.transform.smoothscale(self.full_preload["CONTROL"]["target_focus_last_enemy"]["target_focus_last_enemy_direct"][0], size_mod)])
        self.control_cache.setdefault("upgrade_tower",
                                      pygame.transform.smoothscale(self.full_preload["CONTROL"]["upgrade"]["upgrade_direct"][0], size_mod))
        
        temp_rects = []
        for index, (k, v) in enumerate(self.control_cache.items()):
            if k == "focus_target":
                v = v[self.focus_target]
            temp_rect = pygame.Rect(0, 0, v.get_width(), v.get_height())
            temp_rect.center = self.positions[index]
            temp_rects.append(temp_rect)

        sell_tower_index = list(self.control_cache.keys()).index("sell_tower")
        upgrade_tower_index = list(self.control_cache.keys()).index("upgrade_tower")
        sell_price_img = self.price_font.render(str(int(self.sell_price // 2)), True, (255,255,255))
        sell_price_rect = sell_price_img.get_rect(center=(temp_rects[sell_tower_index].centerx,
                                                          temp_rects[sell_tower_index].centery + int(20 * (self.tower_radius_size / 60) * 0.65)))
        
        upgrade_text = str(int(self.price * self.level))
        color = (255, 0, 0)
        if self.level >= self.max_level:
            upgrade_text = "MAX"
        elif self.money_amount[0] >= int(upgrade_text):
                color = (255, 255, 255)

        upgrade_price_img = self.price_font.render(upgrade_text, True, color)
        upgrade_price_rect = upgrade_price_img.get_rect(center=(temp_rects[upgrade_tower_index].centerx,
                                                             temp_rects[upgrade_tower_index].centery + int(20 * (self.tower_radius_size / 60) * 0.65)))
        collision = mouse_sprite.rect.collidelist(temp_rects)

        for index, (k, v) in enumerate(self.control_cache.items()):
            if k == "focus_target":
                v = v[self.focus_target]
            if index == collision and k == "upgrade_tower" and (self.level >= self.max_level or self.money_amount[0] < int(upgrade_text)):
                collision = -1
            if index == collision:
                copy_highlighting = v.copy()
                copy_highlighting.set_alpha(175)
                self.screen.blit(copy_highlighting, temp_rects[index].topleft)
                if k == "sell_tower":
                    sell_price_img = sell_price_img.copy()
                    sell_price_img.set_alpha(175)
                    self.screen.blit(sell_price_img, sell_price_rect)
                elif k == "upgrade_tower":
                    upgrade_price_img = upgrade_price_img.copy()
                    upgrade_price_img.set_alpha(175)
                    self.screen.blit(upgrade_price_img, upgrade_price_rect)
                if mouse_press[0] and not self.cooldown:
                    self.cooldown = 1
                    if k == "focus_target":
                        self.focus_target += 1
                        if self.focus_target > 2:
                            self.focus_target = 0
                    elif k == "sell_tower":
                        self.money_amount[0] += int(self.sell_price // 2)
                        self.selled = True
                    elif k == "upgrade_tower":
                        self.upgrade_tower()
                        self.money_amount[0] -= int(upgrade_text)
            else:
                self.screen.blit(v, temp_rects[index].topleft)
                if k == "sell_tower":
                    self.screen.blit(sell_price_img, sell_price_rect)
                if k == "upgrade_tower":
                    self.screen.blit(upgrade_price_img, upgrade_price_rect)
                      
    def create_projektil(self, winkel):
        x_pos = self.rect.centerx + math.cos(math.radians(winkel)) * 25
        y_pos = self.rect.centery - (math.sin(math.radians(winkel))) * 25
        temp_projectil_rect = pygame.rect.Rect(0,0, 25, 25)
        temp_enemy_rect = pygame.rect.Rect(0, 0, 25, 25)
        temp_projectil_rect.center = (x_pos, y_pos)
        predicted_target = self.focused_enemy.get_pos_after_steps(temp_projectil_rect, temp_enemy_rect, self.projektil_speed * self.ff_increase)
        enemy_center = self.focused_enemy.rect.center

        if predicted_target:
            # Runden zur Vermeidung von Unnötig vielen Rotationsmöglichkeiten
            winkel_predicted_target = round(math.degrees(math.atan2(-(predicted_target.centery - self.rect.centery),
                                                            predicted_target.centerx - self.rect.centerx)), 0)
            self.set_rotation(winkel_predicted_target - 90)
            x_pos = self.rect.centerx + math.cos(math.radians(winkel_predicted_target)) * 25
            y_pos = self.rect.centery - (math.sin(math.radians(winkel_predicted_target))) * 25
            enemy_center = predicted_target.center

        self.projektile.add(projektil.Projektil(self.screen, (x_pos, y_pos), enemy_center,
                                            self.blocksize_x, self.blocksize_y, self.projektil_images_preload,
                                            (0.45, 0.07), self.damage, self.focused_enemy, self.projektil_speed,
                                            self.map_offset, self.fps, self.clock, self.projktil_cache, self.parent_name))

        sound = self.sound_control.get_sound(self.parent_name.lower() + "_" + "shoot")
        if sound:
            pygame.mixer.Channel(1).fadeout(5)
            pygame.mixer.Channel(1).play(sound)
        

    def upgrade_tower(self):
        if self.level == 1:
            self.radius *= 1.15
            self.animation_speed *= 1.5
            self.damage *= 1.5
            self.sell_price *= 2
            self.radius_shape = None
            self.set_radius_shape()
        elif self.level == 2:
            self.radius *= 1.15
            self.animation_speed *= 2
            self.damage *= 2
            self.projektil_speed *= 1.5
            self.sell_price *= 2
            self.radius_shape = None
            self.set_radius_shape()
        else:
            return
        self.level += 1

    def set_rotation(self, rotation_: int):
        if rotation_ < 0:
            rotation_ = 360 + rotation_
        self.angle = rotation_

        #Handle big Animation_Timer Jumps:
        animation_timer = int(self.animation_timer)
        if int(self.animation_timer) >= len(self.animation_image_preload_list) - 1:
            animation_timer = len(self.animation_image_preload_list) - 1


        self.image = self.rotation_cache[self.parent_name][animation_timer].setdefault(self.angle,
                                                    pygame.transform.rotate(self.animation_image_preload_list[animation_timer], rotation_))
        self.rect = self.image.get_rect(center = self.rect.center)

    def set_highlighting(self, highlighting):
        self.image.set_alpha(highlighting)

    def get_name(self): return self.name

    def get_hovered(self): return self.hoverd
    
    def set_hovered(self):
        if not self.get_hovered() and not self.active:
            pygame.mixer.Sound.play(self.sound_control.get_sound("hover"))
        self.hoverd = not self.hoverd

    def set_screen(self, blocksize, image):
        self.control_cache.clear()
        self.blocksize_x, self.blocksize_y = blocksize
        self.price_font = pygame.font.SysFont("arialblack.ttf", int(18 * (self.blocksize_x / 60)))
        multiplikator_x = self.screen.get_width() / self.screen_size[0]
        multiplikator_y = self.screen.get_height() / self.screen_size[1]
        self.screen_size = self.screen.get_size()
        self.full_preload = image
        if self.name == "top":
            for v in self.rotation_cache[self.parent_name].values():
                v.clear()
            self.radius_shape = None
            self.set_radius_shape()
            self.animation_image_preload_list = self.full_preload[self.parent_name]["shoot_" + self.name]["shoot_" + self.name]
            if self.animation_timer > len(self.animation_image_preload_list):
                self.image = pygame.Surface.copy(self.animation_image_preload_list[-1])
            else:
                self.image = pygame.Surface.copy(self.animation_image_preload_list[int(self.animation_timer)])
        else:
            self.image_preload = self.full_preload[self.parent_name]["idle_" + self.name]["idle_" + self.name][0]
            self.image = pygame.Surface.copy(self.image_preload)
        self.rect = self.image.get_rect(center=(math.ceil(self.rect.centerx * multiplikator_x),
                                                math.ceil(self.rect.centery * multiplikator_y)))
        if self.name == "top" and self.active:
            self.radius_shape.rect.center = (self.rect.center)
        if self.active:
            self.offset = self.map_offset[0]