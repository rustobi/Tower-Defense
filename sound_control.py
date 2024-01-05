from pygame.locals import *
import pygame, os
from pathlib import Path
from moviepy.editor import AudioFileClip as a_clip
import io
import numpy as np
import soundfile as sf


class SoundControl():
    def __init__(self):
        self.sounds = self.create_sound_pallet()

    def create_sound_pallet(self):
        # Preload
        main_dir = os.path.join(Path(__file__).parent, "sounds")
        found_sounds = {}
        for root, _, files in os.walk(main_dir):
            for file in files:
                try:
                    audio = a_clip(os.path.join(root, file))
                except Exception:
                    continue
                sound = pygame.mixer.Sound(self.normalize_audio(os.path.join(root, file), -25))
                sound.set_volume(0.1)
                found_sounds.update({file.split(".")[0] : sound})
        return found_sounds
        
    def normalize_audio(self, input_path, target_db):
        audio, samplerate = sf.read(input_path)

        rms = np.sqrt(np.mean(audio**2))
        gain = (10 ** (target_db / 20)) / rms
        normalized_audio = audio * gain

        output_stream = io.BytesIO()
        sf.write(output_stream, normalized_audio, samplerate, format='wav')
        output_stream.seek(0)

        return output_stream

    def set_sound_volume(self, sound, value):
        sound_get = self.sounds.get(sound)
        if sound_get:
            self.sounds[sound] = sound_get.set_volume(value)

    def get_sound(self, sound):
        sound_get = self.sounds.get(sound)
        if sound_get:
            return sound_get
        print(sound, "wurde nicht gefunden.")
        return None