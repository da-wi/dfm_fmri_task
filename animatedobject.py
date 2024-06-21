import pygame
import sys
import time
import glob
import os
import threading
import math
import random


class AnimatedObject(pygame.sprite.Sprite):


    def __init__(self, interval=0.05, iterations = 40,vertices = 4, animated = True, fixed_interval = False): # old: interval=0.12
        super(AnimatedObject, self).__init__()

        # Initialize sprite
        self.size = 300
        self.rect = pygame.Rect(5, 5, self.size, self.size)
        self.interval = interval
        self.vertices = vertices
        self.iterations = iterations
        self.image = pygame.Surface((self.size,self.size))
        self.figures = []
        self.animated = animated
        #self.interval_list = [0.1,0.1,0.1,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.1,0.1,0.1,0.1,0.1,0.1,0.1,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.01,0.02,0.07,0.12,0.14,0.16,0.16,0.16,0.17,0.18,0.19,0.19,0.19,0.19,0.19,0.19,0,0,0 ]
        

        #self.interval_list = [ 0.01 ]*10 + [ 0.05 ]*10 + [ 0.07 ]*10 + [ 0.12 ]*10 + [ 0.15 ]*10 + [ 0.01 ]*10 + [ 0.20 ]*10
        if fixed_interval == True:
            self.interval_list = [ 0.03 ]*30 + [ 0.05 ]*20 + [ 0.1 ]*20
        else:
            self.interval_list = [ 0.05 ]*70

        #print self.interval_list
        #print len (self.interval_list)
        self.norepeat = True

        # Initialize polygon
        self.circle = self.generate_circle(100,vertices)
        ngon_fitted = self.fit_polygon_to_circle(self.create_ngon(100,vertices),self.circle)
        self.figures.append(self.circle)
        self.figures.append(ngon_fitted)

        if self.animated:
            self.cur_points = self.figures[0]
        else:
            self.cur_points = self.figures[1]

        self.diff_points_rel = self.morph_two_objects(self.figures[0],self.figures[1],self.iterations)

        # Set background
        self.background = pygame.image.load("assets/quirl_alpha.png").convert_alpha()
        self.background = pygame.transform.smoothscale(self.background, (int(self.size), int(self.size)))


        #print self.diff_points_rel
#        self.draw_object(self.image,4)

        thread = threading.Thread(target=self.update)
        thread.daemon = True # Daemonize thread
        thread.start()


    # src & target must have same size
    # return: vector to go each iteration
    def morph_two_objects (self, points_src, points_tgt, iterations):
        if len(points_src) != len(points_tgt):
            return

        diff_points_abs = []
        diff_points_rel = []

        for i in range(0,len(points_src)):
          diff_points_abs.append((points_tgt[i][0] - points_src[i][0],points_tgt[i][1] - points_src[i][1]))
          diff_points_rel.append((float(diff_points_abs[i][0])/iterations,float(diff_points_abs[i][1])/iterations))
        # pro iteration die distanz gehen
        return diff_points_rel
        # return diff_points_rel

    # creates a polygon with radius r and n vertices
    def create_ngon (self,r,n):
        color = (255, 255, 0) # yellow

        point_list = []
        center_x = self.image.get_width() // 2
        center_y =  self.image.get_height() // 2
        angoffset = random.uniform(-2,0)

        for i in range(2*n):
                ang = (2*i*3.14159) / n
                x = center_x + int(math.cos(ang) * r)
                y = center_y + int(math.sin(ang) * r)
                point_list.append((x, y))
        return point_list

    def draw_object(self, surface):
           #color = (19, 160, 23) # green
           color = (25, 20, 25) # black
           thickness = 8
           #self.image.unlock()
           #self.image.blit(self.background,(0,0))
           self.image = self.background
           pygame.draw.polygon(surface, color, self.cur_points, thickness)
           #pygame.gfxdraw.aapolygon(surface, self.cur_points, color, thickness)

    def generate_circle (self,radius,n):
        return self.create_ngon(radius,n*n*2)

    def fit_polygon_to_circle(self,polygon,circle):
        new_list = []
        num_groups = len(polygon)
        num_elements = len(circle) / len (polygon)

        for i in range (num_groups):
            for j in range (int(round(num_elements))): ### edited
                new_list.append(polygon[i])
        return new_list

    def update(self):
        n = self.iterations-2

        index_figures = 0
        while True:
          # draw object
          #self.image.fill(60,60,60)
          #self.image.fill(0,0,0)
          self.draw_object(self.image)


          #print n,len(self.interval_list)
          self.interval = self.interval_list[int(n)]
          #print "sleeping ", self.interval
          time.sleep(self.interval)

          if self.animated:
              # calculate new points for iteration and set current points
              tmp = []
              for i in range(0,len(self.diff_points_rel)):
                #print str(i)+": "
                #print (self.cur_points[i][0] + self.diff_points_rel[i][0],self.cur_points[i][1] + self.diff_points_rel[i][1])
                tmp.append((self.cur_points[i][0] + self.diff_points_rel[i][0],self.cur_points[i][1] + self.diff_points_rel[i][1]))
              self.cur_points = tmp

              # check if we are on the end of the iterations
              # if no : decrease n
              if (n > 0):
                n = n - 1
              # else (we are at the end): start over
              else:
                if self.norepeat == True:
                    return
                if index_figures < len (self.figures) - 2:
                  index_figures = index_figures + 1
                  self.diff_points_rel = self.morph_two_objects(self.figures[index_figures],self.figures[index_figures+1],40)
                else:
                  # special case: last and first
                  if index_figures < len (self.figures) - 1:
                    index_figures = index_figures + 1
                    self.diff_points_rel = self.morph_two_objects(self.figures[index_figures],self.figures[0],40)
                  else:
                    index_figures = 0
                    self.diff_points_rel = self.morph_two_objects(self.figures[index_figures],self.figures[index_figures+1],40)

                # reset iterations
                n = self.iterations
