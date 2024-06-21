import pygame
import sys
import time
import glob
import os
import threading
import re


def natural_key(string_):
    """To naturally sort: http://stackoverflow.com/questions/2545532/python-analog-of-natsort-function-sort-a-list-using-a-natural-order-algorithm"""
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]

def load_image(name):
    image = pygame.image.load(name).convert_alpha()
    #image = pygame.image.load(name).convert()
    return image

class AnimatedSprite(pygame.sprite.Sprite):


    def __init__(self, face , interval=1, animated=True, loop=False): # old: interval=0.25, 0.1
        super(AnimatedSprite, self).__init__()
        # dont take first and last frame
        self.image_paths = sorted(glob.glob(face+"/out/frame*.png"), key=natural_key)
        self.image_paths = self.image_paths[1:len(self.image_paths)-1]
        self.loop = loop

        self.index = 0
        self.rect = pygame.Rect(5, 5, 500, 600)
        self.interval = interval
        self.images = []
        self.animated = animated

        self.loaded = 0.0
        self.loading = True

        if self.animated == True:
            #self.load_video()

            thread = threading.Thread(target=self.load_video)
            thread.daemon = True  # Daemonize thread
            thread.start()

            #for i in range(0,len(image_paths)):
            #    self.images.append(load_image(image_paths[i]))
            #self.image = self.images[self.index]
            #thread = threading.Thread(target=self.update)
            #thread.daemon = True  # Daemonize thread
            #thread.start()
        else:
            self.images.append(load_image(self.image_paths[len(self.image_paths)-1]))
            self.image = self.images[self.index]
            self.loading = False
            self.loaded = 1.0

    def get_loaded(self):
        return self.loaded

    def is_loading(self):
        return self.loading

    def load_video(self):
        for i in range(0, len(self.image_paths)):
            self.images.append(load_image(self.image_paths[i]))
            self.loaded = i / float (len(self.image_paths)-1)
        self.image = self.images[self.index]
        self.loading = False
        #self.restart()

    def restart(self):
        self.index = 0
        self.image = self.images[self.index]
        if self.animated == True:
            thread = threading.Thread(target=self.update)
            thread.daemon = True  # Daemonize thread
            thread.start()

    def update(self):
        while True:
          #print self.image_paths[self.index], self.index
          self.index += 1
          if self.index >= len(self.images): ### edited: indentation fixed
            if self.loop == False:
              return
              #break
            else:
                self.index = 0  
          self.image = self.images[self.index]
          time.sleep(self.interval)

