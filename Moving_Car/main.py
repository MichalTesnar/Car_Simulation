import gym
import numpy as np
import time
from path_planning import PathPlanning
import pygame
import pp_functions

class CustomEnv(gym.Env):
    def __init__(self):
        # action = [car_steering_angle, car_curr_velocity]
        # TODO check ranges for acc and rot
        self.action_space = gym.spaces.Box(low=-1., high=1., shape=(2,), dtype=np.float32)
        
        # observation = [car_angle, car_next_velocity, cone_list]
        # TODO: look for example where obs space varies in shape over time
        self.observation_space = gym.spaces.Box(low=-1., high=1., shape=(3,), dtype=np.float32)
        
        self.pp = PathPlanning()

    # optional for the Gym env
    def render(self):
        pp_functions.drawing.render(self.pp)
        
    # needed for the Gym env
    def step(self, time_start):
        dt = self.pp.clock.get_time() / 500 

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.pp.exit = True
        pp_functions.manual_controls.enable_dragging_screen(self.pp, events)

        time_running = time.time() - time_start

        self.pp.car.config_angle()

        #update target list
        self.pp.target.update_target_lists()
       
        #update cone list
        self.pp.cone.update_cone_list()
        
        #calculate closest target
        self.pp.target.update_closest_target()

        #reset targets for new lap
        self.pp.reset_new_lap()

        #automatic steering
        # probably wont need this
        self.pp.steering()
        
        #computing boundary estimation
        # TODO: decide to keep?
        self.pp.path.compute_boundaries(self.pp)

        #compute midpoint path
        # self.pp.path.generate_midpoint_path(self.pp)
               
        #implement track logic
        # might not need it
        self.pp.track_logic()

        #car crash logic 
        # TODO: include the spline crash from older version
        self.pp.car.car_crash_mechanic(self.pp.cone)

        #checking exit conditions
        # TODO: maybe put car_crash_mecahnic and compute_boundaries in here
        self.pp.set_done()
                
        # Logic
        self.pp.implement_main_logic(dt, time_running)

        # TODO: convert_cones(...); dist_car and alpha be careful!

        observation = [self.pp.car.angle, self.pp.car.velocity.x, self.pp.cone.cone_list]

        # TODO
        # observation should be of observation_space type and should represent the new state after action has been completed
        # reward should be the result of applying the reward function written by Alex
        # done should be the result of the set_done function from PathPlanning
        # info can be empty, only used for debugging 
        # return observation, reward, done, info
    
    # needed for the Gym env
    def reset(self):
        self.pp = PathPlanning()

        # TODO
        # state should be of observation space type
        # return state


env = CustomEnv()

time_start = time.time()

while True:
    env.step(time_start = time_start)
    env.render()


    if env.pp.exit:
        # env.reset()
        break

pygame.quit()


# ALex:
# TODO: update cone class for alpha and dist car
# TODO: convert_cone
# TODO: chack that generate_midpoint_path can just be taken out + think about repercussions
# TODO: make a function that generates random actions

# Andreea
# TODO: step function (return statements + action parameter)
# TODO: make a function that generates random actions
