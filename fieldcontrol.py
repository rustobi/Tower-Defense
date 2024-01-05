from pygame.locals import *
import pygame, math, tower

class FieldControl():
    def __init__(self, screen, blocksize, pre_load_towers, pre_load_projektils,
                 width, height, map, tower_specs, status_speed, next_shoot_dead_enemys,
                 sound_control, money_amount, y_offset, fps, clock, projektil_cache):
        # INIT Parameter
        self.screen = screen
        self.blocksize_x, self.blocksize_y = blocksize
        self.pre_load_towers = pre_load_towers
        self.pre_load_projektils = pre_load_projektils
        self.screen_size = self.screen.get_size()
        self.width = width
        self.height = height
        self.map = map
        self.tower_specs = tower_specs
        self.status_speed = status_speed
        self.next_shoot_dead_enemys = next_shoot_dead_enemys
        self.sound_control = sound_control
        self.money_amount = money_amount
        self.y_offset = y_offset
        self.fps = fps
        self.clock = clock

        self.rotation_cache_towers = {}
        self.projektil_cache = projektil_cache

        # CONFIGURE FIELD
        self.create_building_fields()
        self.mouse_clicked_tower = []
        self.placed_towers = pygame.sprite.Group()

        # COLLISION DETECTION MOUSE
        self.mouse_sprite = pygame.sprite.Sprite()
        self.mouse_sprite.image = pygame.Surface((10,10))
        self.mouse_sprite.rect = self.mouse_sprite.image.get_rect()

    def update(self, mouse_pos, mouse_press, colliding_tower, blocksize,
               enemys, pause, prices_towers, fast_forward, pre_load_towers):
        if self.screen_size != self.screen.get_size():
            self.blocksize_x, self.blocksize_y = blocksize
            self.pre_load_towers = pre_load_towers
            self.screen_size = self.screen.get_size()

        if self.mouse_clicked_tower or mouse_press[0]:
            building_field = self.get_building_field(mouse_pos, blocksize[0], blocksize[1])
            self.move_building(mouse_pos, mouse_press, building_field, colliding_tower, blocksize[0], blocksize[1], prices_towers)

        # CHECK COLLISION BETWEEN MOUSE AND PLACED TOWER
        self.mouse_sprite.rect.center = mouse_pos
        if mouse_press[0]:
            hovered_list = [i for i in self.placed_towers if i.name == "top" and i.get_hovered()]
            tower_collision = pygame.sprite.spritecollide(self.mouse_sprite, self.placed_towers, False)
            tower_collision = [i for i in tower_collision if i.name == "top"]
            if tower_collision and tower_collision[0] not in hovered_list and not hovered_list:
                tower_collision[0].set_hovered()
                for tower in hovered_list:
                    tower.set_hovered()

        # Setzt Auswahl zurück
        if mouse_press[2]:
            hovered_list = [i for i in self.placed_towers if i.name == "top" and i.get_hovered()]
            for tower in hovered_list:
                tower.set_hovered()

        selected_tower = self.get_hovered_tower()
        selled_towers = []
        
        # Zeichnet erst alle Unselektierten und dann den selektierten Tower
        for tower in self.placed_towers:
            if tower.selled:
                selled_towers.append(tower.rect.center)
            elif not tower == selected_tower:
                tower.update(enemys, self.mouse_sprite, mouse_press, pause, fast_forward, blocksize, pre_load_towers)
                self.screen.blit(tower.image, tower.rect)

        if selected_tower:
            selected_tower.update(enemys, self.mouse_sprite, mouse_press, pause, fast_forward, blocksize, pre_load_towers)
            self.screen.blit(selected_tower.image, selected_tower.rect)

        for selled_tower in selled_towers:
            for tower in self.placed_towers:
                if tower.rect.center == selled_tower:
                    tower.kill()

    def get_hovered_tower(self):
        for tower in self.placed_towers:
            if tower.get_hovered():
                return tower
        return None

    def get_building_field(self, position, blocksize_x, blocksize_y):
        x_pos, y_pos = position
        actual_point_x = math.ceil(x_pos / blocksize_x)
        actual_point_y = math.ceil((y_pos + self.y_offset[0]) / blocksize_y)

        if 0 <= actual_point_y -1 > len(self.map)-1 or 0 <= actual_point_x -1 > len(self.map[actual_point_y-1])-1:
            return None
        
        mouse_rect = pygame.Rect(x_pos, y_pos, 1,1)
        for sprite in self.placed_towers:
            if sprite.rect.colliderect(mouse_rect):
                return None

        if actual_point_y > 0 and self.map[actual_point_y-1][actual_point_x-1] == 3:
            return pygame.Rect(actual_point_x * blocksize_x - blocksize_x, actual_point_y * blocksize_y - blocksize_y - self.y_offset[0], blocksize_x, blocksize_y)
        return None

    def create_building_fields(self):
        def check_and_update_map(index_r, index_c, offset_r, offset_c):
            if (0 <= index_r + offset_r < len(self.map)) and (0 <= index_c + offset_c < len(self.map[0])):
                if self.map[index_r + offset_r][index_c + offset_c] == 1:
                    self.map[index_r][index_c] = 3

        for index_r, row in enumerate(self.map):
            for index_c, col in enumerate(row):
                if col == 0:
                    check_and_update_map(index_r, index_c, 0, 1)  # Rechtes-Feld
                    check_and_update_map(index_r, index_c, 0, -1)  # Linkes-Feld
                    check_and_update_map(index_r, index_c, 1, 0)  # Oberes-Feld
                    check_and_update_map(index_r, index_c, -1, 0)  # Unteres-Feld
                    check_and_update_map(index_r, index_c, 1, 1)  # Links-oben-Feld
                    check_and_update_map(index_r, index_c, 1, -1)  # Rechts-oben-Feld
                    check_and_update_map(index_r, index_c, -1, 1)  # Links-unten-Feld
                    check_and_update_map(index_r, index_c, -1, -1)  # Rechts-unten-Feld

        # Entfernt alle Building Field ober und unterhalb des Empires
        for index_r, row in enumerate(self.map):
            found = False
            for index_c, col in enumerate(row):
                if col == 2:
                    found = True
                    for i in range(0, len(self.map)):
                        if self.map[i][index_c] not in [0, 2]:
                            self.map[i][index_c] = 0
            if found:
                break
        
        for index in range(len(self.map)):
            if self.map[index][-1] == 3:
                self.map[index][-1] = 0


    def move_building(self, mouse_pos, mouse_press, building_field, colliding_tower, blocksize_x, blocksize_y, prices_towers):
        # Prüfe Klick auf Toolbar
        left_click = mouse_press[0]
        right_click = mouse_press[2]
        if left_click and colliding_tower:
            self.mouse_clicked_tower.clear()
            if colliding_tower[0].price <= self.money_amount[0]:
                for sprite in colliding_tower:
                    if sprite.get_name().lower() != "sign":
                        self.mouse_clicked_tower.append(sprite)
        elif (left_click or right_click) and not building_field and not colliding_tower:
            self.mouse_clicked_tower.clear()

        # Zeichne Tower auf Maus Position
        if self.mouse_clicked_tower and (not building_field or self.get_tower_placed_on_pos((building_field.x, building_field.y))):
            for sprite in self.mouse_clicked_tower:
                image = sprite.image
                image.set_alpha(175)
                self.screen.blit(image, (mouse_pos[0] - (sprite.rect.width / 2), mouse_pos[1] - (sprite.rect.height / 2)))

        # Zeichne Tower auf Building Place Position
        if self.mouse_clicked_tower and building_field and not self.get_tower_placed_on_pos((building_field.x, building_field.y)):
            building_field_sur = pygame.Surface((building_field.size[0], building_field.size[1]))
            building_field_sur.fill((0,255,55, 100))
            self.screen.blit(building_field_sur, building_field)

            # Zeichnen des Tower-Radius
            tower_radius_size = (blocksize_x + blocksize_y) // 2
            tower_radius = pygame.Surface((tower_radius_size * self.tower_specs[self.mouse_clicked_tower[0].parent_name]["radius"],
                                           tower_radius_size * self.tower_specs[self.mouse_clicked_tower[0].parent_name]["radius"]), pygame.SRCALPHA)
            pygame.draw.circle(tower_radius, (255, 0, 0, 75), (tower_radius.get_width() // 2, tower_radius.get_height() // 2), tower_radius.get_width() // 2)
            pygame.draw.circle(tower_radius, (255, 0, 0), (tower_radius.get_width() // 2, tower_radius.get_height() // 2), tower_radius.get_width() // 2 - 2, 2)
            self.screen.blit(tower_radius, (building_field.center[0] - (tower_radius.get_width() // 2), building_field.center[1] - (tower_radius.get_height() // 2)))

            for sprite in self.mouse_clicked_tower:
                self.screen.blit(sprite.image, (building_field.x, building_field.y))

            if left_click and self.set_building(building_field, tower_radius, prices_towers):
                self.mouse_clicked_tower.clear()

    def get_tower_placed_on_pos(self, pos):
        for tower in self.placed_towers:
            if tower.rect.x == pos[0] and tower.rect.y == pos[1]:
                return True
        return False

    def set_building(self, building_field, tower_radius, prices_towers):
        price = self.mouse_clicked_tower[0].price

        if price <= self.money_amount[0]:
            for sprite in self.mouse_clicked_tower:
                if sprite.name == "top":
                    self.rotation_cache_towers.setdefault(sprite.parent_name, {i:{} for i in range(len(self.pre_load_towers[sprite.parent_name]["shoot_" + sprite.name]["shoot_" + sprite.name]))})
                    self.projektil_cache.setdefault(sprite.parent_name, {})
                self.placed_towers.add(tower.Tower(self.screen, (self.blocksize_x, self.blocksize_y), sprite.get_name(), sprite.parent_name,
                                                self.pre_load_towers, (sprite.image.get_width(), sprite.image.get_height()),
                                                building_field.x, building_field.y, True, self.sound_control, tower_radius, self.pre_load_projektils[sprite.parent_name],
                                                self.tower_specs[sprite.parent_name], self.status_speed[sprite.parent_name], self.next_shoot_dead_enemys, prices_towers[sprite.parent_name.lower()],
                                                self.money_amount, self.y_offset, self.fps, self.clock, self.rotation_cache_towers, self.projektil_cache))
            self.money_amount[0] -= price
            return True
        return False