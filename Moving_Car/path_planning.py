import os
import pygame
from math import sin, radians, degrees, copysign
from pygame.math import Vector2
import time
import numpy as np
from PIL import Image, ImageDraw
from scipy.interpolate import splprep, splev
import pandas as pd
import gym
import random

from car import Car
from target import Target
from cone import *
from path import *

from pp_functions import utils
import pp_functions.drawing
import pp_functions.reward_function 
        

class PathPlanning:
    def __init__(self, map_name = 'MAP_NULL'):
        # TODO: initialize target -> call generate_midpoint_path first?
        self.target = Target(0,0)
        self.car = Car(15,3)
        self.cone = Cone(0,0,Side.LEFT)
        self.path = Path()

        pygame.init()
        pygame.display.set_caption("Car")
        width = 1280
        height = 720
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.ticks = 60
        self.exit = False
        self.total_reward = 0
        self.cruising_speed = 2
        self.map_name = map_name

        self.view_offset = [0.0, 0.0]
        self.prev_view_offset = [0.0, 0.0]
        self.moving_view_offset = False
        self.view_offset_mouse_pos_start = [0.0,0.0]
        self.midpoint_created = False

        self.level_id = None
        self.track_number = -1
        self.track_number_changed = False
        self.time_start_track = None
        self.time_start_sim = None
        self.track = False
        self.ppu = 32

    def initialize_map(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "images/car_r_30.png")
        self.car.car_image = pygame.image.load(image_path)

        # image_path7 = os.path.join(current_dir, "explosion_image.png")
        # explosion_image = pygame.image.load(image_path7)
        
        image_path1 = os.path.join(current_dir, "images/target_r_t.png")
        self.target.image = pygame.image.load(image_path1)
        
        image_path3 = os.path.join(current_dir, "images/left_cone_s.png")
        self.cone.image[Side.LEFT] = pygame.image.load(image_path3)
        
        image_path4 = os.path.join(current_dir, "images/right_cone_s.png")
        self.cone.image[Side.RIGHT] = pygame.image.load(image_path4)

        image_path5 = os.path.join(current_dir, "images/left_spline_s.png")
        self.path.spline_image[Side.LEFT] = pygame.image.load(image_path5)
        
        image_path6 = os.path.join(current_dir, "images/right_spline_s.png")
        self.path.spline_image[Side.RIGHT] = pygame.image.load(image_path6)

        # while not self.exit:
        if self.level_id == None:
            random_number = random.randint(1, 5)
            self.level_id = f"MAP_{2}"

        left_cones, right_cones = pp_functions.utils.load_existing_map(self.level_id)
        self.cone.cone_list[Side.LEFT] = left_cones
        self.cone.cone_list[Side.RIGHT] = right_cones


    def set_done(self):
        self.car.car_crash_mechanic(self.cone)
        
        if self.car.crashed or self.track_number == 3:
            self.exit = True

        #reward function
        # reward, lap_reward = pp_functions.reward_function.calculate_reward(lap_reward, car, track_number, dt)
        # self.total_reward += reward

    def reset_new_lap(self):
        #reset targets for new lap
        if (len(self.target.targets) > 0
        and len(self.target.non_passed_targets) == 0 
        and self.track == True 
        and (self.path.spline_linked[Path_Side.LEFT] == True or self.path.spline_linked[Path_Side.RIGHT] == True)):
            self.target.reset_targets() 

    def track_logic(self):
        #Setting the finishing line/point
        if (self.cone.first_visible_cone[Side.LEFT] != 0 and self.cone.first_visible_cone[Side.RIGHT] != 0 
        and self.midpoint_created == False): 

            start_midpoint_x = np.mean([self.cone.first_visible_cone[Side.LEFT].position.x, self.cone.first_visible_cone[Side.RIGHT].position.x])
            start_midpoint_y = np.mean([self.cone.first_visible_cone[Side.LEFT].position.y, self.cone.first_visible_cone[Side.RIGHT].position.y])     
            self.midpoint_created = True
                
                
            #incrementing lap number by 1
            if (np.linalg.norm((start_midpoint_x, start_midpoint_y)-self.car.position) < 20/self.ppu 
            and self.track_number_changed == False 
            and self.track == True):
                self.track_number += 1
                print('TIME : ', time.time() - self.time_start_track)
                lap_reward = True
                self.track_number_changed = True
                
            #setting track_number_changed to false when not on finishing line
            elif (np.linalg.norm((start_midpoint_x, start_midpoint_y)-self.car.position) > 20/self.ppu 
            and self.track == True):
                self.track_number_changed = False  

    def steering(self):
        if (len(self.target.visible_targets) > 0 
        and np.linalg.norm(self.target.closest_target.position-self.car.position) < self.car.fov/self.ppu
        and np.linalg.norm(self.target.closest_target.position-self.car.position) > 20/self.ppu
        and self.car.auto == True 
        and self.target.closest_target.passed == False):
            
            dist = self.target.closest_target.dist_car
            alpha = self.target.closest_target.alpha
            self.car.steering_angle = (self.car.max_steering*2/np.pi)*np.arctan(alpha/dist**self.car.turning_sharpness)
            self.car.velocity.x = self.cruising_speed

        self.car.acceleration = max(-self.car.max_acceleration, min(self.car.acceleration, self.car.max_acceleration))
        self.car.steering_angle = max(-self.car.max_steering, min(self.car.steering_angle, self.car.max_steering))


    def implement_main_logic(self, dt, time_running):
        self.car.update(dt)
        
        for target in self.target.targets:
            target.update(self, time_running)

        for category in Side:
            for cone in self.cone.cone_list[category]:
                cone.update(self, time_running)
        

    def run(self):

        self.initialize_map()
        
        time_start = time.time()
        lap_reward = False
        time_start_sim = time.time()

        while not self.exit:
            dt = self.clock.get_time() / 500

            # Event queue
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.exit = True
                         
            #Defining the time running since simulation started
            time_running = time.time() - time_start

            #making car autonomous
            if self.car.auto == False:
                self.car.auto  = True
                self.time_start_track = time.time()
            
            #redefining the car angle so that it is in (-180,180)
            self.car.config_angle()

            #update target list
            self.target.update_target_lists()
           
            #update cone list
            self.cone.update_cone_list()
            
            #calculate closest target
            self.target.update_closest_target()
                
            #reset targets for new lap
            self.reset_new_lap()
            
            #automatic steering
            self.steering()
            
            #computing boundary estimation
            self.path.compute_boundaries(self)

            #compute midpoint path
            self.path.generate_midpoint_path(self)
                   
            #implement track logic
            self.track_logic()

            #car crash logic 
            self.car.car_crash_mechanic(self.cone)

            #checking exit conditions
            self.set_done()
                    
            # Logic
            self.implement_main_logic(dt, time_running)
            
            #Drawing
            pp_functions.drawing.render(self)

        pygame.quit()
        

if __name__ == '__main__':
    sim = PathPlanning()
    sim.run()