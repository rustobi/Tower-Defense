import pygame, re, configparser, json, os, time
from pygame.locals import *
from pathlib import Path

class PreLoad():
    def __init__(self, terms: list, blocksize, screen=None):
        self.terms = terms
        self.screen = screen
        self.loaded_images = {}
        self.projektils = {}
        self.status_speed = {}
        self.blocksize_x, self.blocksize_y = blocksize

        self.load_images()
        self.load_projektil_images()
        self.load_status_speed()
        self.load_masks()

    def load_status_speed(self):
        for term in self.terms:
            self.status_speed.update({term:{}})
            term_path = self.get_conf(term)
            conf = self.load_conf(term_path, term)
            try:
                for item in json.loads(conf.get("STATS", "CONTAINS")):
                    self.status_speed[term].update({item:json.loads(conf.get("STATS", item))})
            except (configparser.NoSectionError, configparser.NoOptionError):
                continue

    def load_projektil_images(self):
        for term in self.terms:
            term_path = self.get_conf(term)
            conf = self.load_conf(term_path, term)
            try:
                projektil_name = json.loads(conf.get("IMAGES", "projektil"))
            except (configparser.NoSectionError, configparser.NoOptionError):
                continue
            self.projektils.update({term:[]})
            for dateiname in os.listdir(os.path.join(term_path, projektil_name)):
                if dateiname.startswith(projektil_name):
                    voller_pfad = os.path.join(os.path.join(term_path, projektil_name), dateiname)
                    if os.path.isfile(voller_pfad):
                            image = pygame.image.load(voller_pfad).convert_alpha()
                            if not term.startswith("TIER"):
                                image = pygame.transform.rotate(image, 90)
                            self.projektils[term].append(image)

    def load_images(self):
        for term in self.terms:
            term_path = self.get_conf(term)
            conf = self.load_conf(term_path, term)
            self.loaded_images.update({term:{}})
            for item in json.loads(conf.get("IMAGES", "CONTAINS")):
                self.loaded_images[term].update({item:{}})
                for direction in json.loads(conf.get("IMAGES", item)):
                    if direction == "default":
                        concat = item
                    else:
                        concat = item + "_" + direction
                    self.loaded_images[term][item].update({concat:[]})
                    if direction == "direct":
                        path = os.path.join(term_path)
                    else:
                        path = os.path.join(term_path, item)
                    for dateiname in os.listdir(path):
                        if dateiname.startswith(direction) or dateiname.startswith(item):
                            voller_pfad = os.path.join(path, dateiname)
                            if os.path.isfile(voller_pfad):
                                self.loaded_images[term][item][concat].append(voller_pfad)
                    self.loaded_images[term][item][concat] = sorted(self.loaded_images[term][item][concat], key=lambda x: int(re.findall(r'\d+', x.split('.')[0])[-1]))
                    self.loaded_images[term][item][concat] = [pygame.image.load(pfad).convert_alpha() for pfad in self.loaded_images[term][item][concat]]
                    
                    if term.startswith("TIER"):
                        self.loaded_images[term][item][concat] = [pygame.transform.smoothscale(image, (self.blocksize_x * 0.5, self.blocksize_y * 0.5)) for image in self.loaded_images[term][item][concat]]
                    elif not term == "CONTROL":
                        self.loaded_images[term][item][concat] = [pygame.transform.smoothscale(image, (self.blocksize_x, self.blocksize_y)) for image in self.loaded_images[term][item][concat]]

    def load_masks(self):
        for k, v in self.loaded_images.items():
            for state, items_ in v.items():
                term_update = {}
                for term, values_ in items_.items():
                    term_update.update({term+"_masks":[]})
                    for value_ in values_:
                        term_update[term+"_masks"].append(pygame.mask.from_surface(value_))

                for term_u_k, term_u_v in term_update.items():
                    self.loaded_images[k][state].update({term_u_k:term_u_v})

                 

    def load_conf(self, term_path, term):
        conf = configparser.ConfigParser()
        conf.read(os.path.join(term_path, term + ".ini"))
        return conf
    
    def get_tower_specs(self):
        # ONLY FOR TOWERS
        tower_specs = {}
        for term in self.terms:
            term_path = self.get_conf(term)
            conf = self.load_conf(term_path, term)
            tower_specs.update({term:{}})
            tower_specs[term].update({"radius":json.loads(conf.get(term.upper(), "radius"))})
        return tower_specs

    def get_conf(self, name):
        for root, _, files in os.walk(Path(__file__).parent):
            for file in files:
                if file.startswith(name):
                    return os.path.join(root)
        return None
    
    def get_projektil_images(self): return self.projektils

    def get_image_list(self): return self.loaded_images
    
    def get_status_speed(self): return self.status_speed