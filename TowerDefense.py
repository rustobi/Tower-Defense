# GENERAL IMPORTS
import configparser
import pygame, os, io, cProfile, pstats, json, math
import gameloop
from pathlib import Path

# GAMELOOP CLASS
class TowerDefense():
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        self.WIDTH, self.HEIGHT = 1280, 720
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.clock = pygame.time.Clock()
        self.FPS = 60
        self.running = True

        # Loading Screen Images
        loading_screen_images = []
        for root, _, files in os.walk(os.path.join(Path(__file__).parent, "tiles", "loading_screen")):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    loading_screen_images.append(pygame.image.load(os.path.join(root, file)))

        level_data = self.get_level_data(1)

        loading_screen_images = [pygame.transform.scale(i, self.screen.get_size()) for i in loading_screen_images]

        # AUFRUF = (LEVEL_DATA, GELD, LADESCREEN BILDER)
        self.start_level(level_data, [175], loading_screen_images)

    def start_level(self, level_data, money_amount, loading_screen_images):
        gameloop_ = gameloop.Gameloop(self.screen, self.clock, self.FPS, level_data.get("level"), (self.WIDTH, self.HEIGHT), True)
        gameloop_.load_level(level_data, money_amount, loading_screen_images)

    def get_level_data(self, level):
        ini_path = None
        level_data = {"level":level}
        for root, folders, _ in os.walk(Path(__file__).parent):
            if "level" in folders:
                ini_path = os.path.join(root, "level", "level" + str(level), "init.ini")
                level_data.setdefault("level_path", os.path.join(root, "level", "level" + str(level)))

        if os.path.isfile(ini_path):
            conf = configparser.ConfigParser()
            conf.read(ini_path)
            waves = json.loads(conf.get("level".upper() + str(level), "waves"))
            enemys = json.loads(conf.get("level".upper() + str(level), "enemys"))
            level_data.update({"waves": waves, "enemys": enemys})

            for i in range(waves):
                i = i+1
                enemy = json.loads(conf.get("wave".upper() + str(i), "enemy"))
                enemy_count = json.loads(conf.get("wave".upper() + str(i), "enemy_count"))
                enemy_outcome_rate = json.loads(conf.get("wave".upper() + str(i), "enemy_outcome_rate"))
                level_data.update({"wave"+str(i):
                                   {"enemy": enemy,
                                    "enemy_count": enemy_count,
                                    "enemy_outcome_rate": enemy_outcome_rate,
                                    "money": math.ceil(enemy_count - enemy_outcome_rate // 100)}})
            return level_data
        else:
            return None


if __name__ == "__main__":
    TowerDefense()
    """profiler = cProfile.Profile()
    profiler.run("TowerDefense()")

    result = io.StringIO()
    pstats.Stats(profiler,stream=result).print_stats()
    result=result.getvalue()
    # chop the string into a csv-like buffer
    result='ncalls'+result.split('ncalls')[-1]
    result='\n'.join([','.join(line.rstrip().split(None,5)) for line in result.split('\n')])
    
    with open(os.path.join(Path(__file__).parent, 'auswertung.csv'), 'w+') as f:
        f.write(result)"""