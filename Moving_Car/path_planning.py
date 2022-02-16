import os
import pygame
import time
import random

from car import Car
from cone import *
from path import *

from pp_functions import utils
import pp_functions.manual_controls
import pp_functions.drawing
import pp_functions.reward_function 
     
global LEVEL_ID
LEVEL_ID = None   

class PathPlanning:
    def __init__(self):
        self.target = Target(0,0)
        self.car = Car(15,3)
        self.cone = Cone(0,0,Side.LEFT)
        self.path = Path()
        self.initialize_images()
        self.initialize_map()

        pygame.init()
        pygame.display.set_caption("Car")
        width = 1280
        height = 720
        self.screen = pygame.display.set_mode((width, height))
        self.fullscreen = False
        self.clock = pygame.time.Clock()
        self.ticks = 60
        self.exit = False
        self.mouse_pos_list = []
        self.total_reward = 0
        self.cruising_speed = 2

        self.view_offset = [0.0, 0.0]
        self.prev_view_offset = [0.0, 0.0]
        self.moving_view_offset = False
        self.view_offset_mouse_pos_start = [0.0,0.0]
        self.midpoint_created = False
        self.undo_done = False

        self.track = True
        self.track_number = -1
        self.track_number_changed = False
        self.time_start_sim = None
        self.ppu = 32


    def initialize_images(self):
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

    def initialize_map(self):
        global LEVEL_ID
        if LEVEL_ID == None:
            random_number = random.randint(1, 5)
            LEVEL_ID = f"MAP_{random_number}"

        left_cones, right_cones = pp_functions.utils.load_existing_map(LEVEL_ID)
        self.cone.cone_list[Side.LEFT] = left_cones
        self.cone.cone_list[Side.RIGHT] = right_cones

    def set_done(self):
        self.path.compute_boundaries(self)
        self.car.car_crash_mechanic(self.cone, self.path)
        if self.car.crashed or self.track_number == 3:
            return True
        return False

    def reset_new_lap(self):
        # reset targets for new lap
        if (len(self.target.targets) > 0
        and len(self.target.non_passed_targets) == 0 
        and (self.path.spline_linked[Side.LEFT] == True or self.path.spline_linked[Side.RIGHT] == True)
        and self.track):
            self.target.reset_targets()

    def track_logic(self):
        if self.cone.first_visible_cone[Side.LEFT] != 0 and self.cone.first_visible_cone[Side.RIGHT] != 0: 
            
            #Setting the finishing line/point
            if not self.midpoint_created and self.track:
                self.path.start_midpoint_x = np.mean([self.cone.first_visible_cone[Side.LEFT].position.x, self.cone.first_visible_cone[Side.RIGHT].position.x])
                self.path.start_midpoint_y = np.mean([self.cone.first_visible_cone[Side.LEFT].position.y, self.cone.first_visible_cone[Side.RIGHT].position.y])     
                self.midpoint_created = True
                
            #Incrementing lap number by 1
            elif (np.linalg.norm((self.path.start_midpoint_x, self.path.start_midpoint_y)-self.car.position) < 20/self.ppu 
            and not self.track_number_changed and self.track):
                self.track_number += 1
                lap_reward = True
                self.track_number_changed = True
                
            #Setting track_number_changed to false when not on finishing line
            elif (np.linalg.norm((self.path.start_midpoint_x, self.path.start_midpoint_y)-self.car.position) > 20/self.ppu
            and self.track):
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
        

    def run(self, method = "autonomous"):

        self.initialize_images()

        if method == "autonomous":
            self.initialize_map()
        else:
            self.car.auto = False
        
        time_start = time.time()

        while not self.exit:

            dt = self.clock.get_time() / 500
            print(dt)

            # Event queue
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.exit = True

            if method == "autonomous":
                pp_functions.manual_controls.enable_dragging_screen(self, events)
            else:
                # user inputs
                pp_functions.manual_controls.user_input(self, events, dt)
                         
            # Defining the time running since simulation started
            time_running = time.time() - time_start
            
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

    # 2 methods:
    #   1) autonomous: no user inputs, only screen dragging
    #   2) user: old simulation with user inputs
    sim.run(method = "autonomous") 