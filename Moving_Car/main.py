import random

import gym
import numpy as np
import time
from path_planning import PathPlanning
import pygame
import pp_functions
from pp_functions.reward_function import calculate_reward

global global_reward
global_reward = 0
global time_start


class CustomEnv(gym.Env):
    def __init__(self):
        # action = [car_steering_angle, car_curr_velocity]
        self.action_space = gym.spaces.Box(low=-1., high=1., shape=(2,), dtype=np.float32)
        
        # observation = [car_angle, car_next_velocity, cone_list]
        self.observation_space = gym.spaces.Box(low=-1., high=1., shape=(3,), dtype=np.float32)

        max_num_cones = 100
        orientation = gym.spaces.Box(low=-1., high=1., shape=(1,), dtype=np.float32)
        velocity = gym.spaces.Box(low=-1., high=1., shape=(1,), dtype=np.float32)
        angles = gym.spaces.Box(low=-1., high=1., shape=(max_num_cones,), dtype=np.float32)
        distances = gym.spaces.Box(low=0, high=1., shape=(max_num_cones,), dtype=np.float32)
        binary = gym.spaces.Discrete(2)
        place_holders = gym.spaces.MultiDiscrete([2 for _ in range(max_num_cones)])

        # spaces for different objects
        car_space = gym.spaces.Dict({
            "velocity": velocity,
            "orientation": orientation,
        })

        cone_space = gym.spaces.Dict({
            "angles": angles,
            "distances": distances,
            "category": binary,
            "place_holder": place_holders
        })

        # zipping the spaces into a tuple
        self.observation_space = gym.spaces.Tuple([
            car_space,
            cone_space])
        
        self.pp = PathPlanning()

    def generate_random_action(self):
        car_steering_angle = random.uniform(-self.pp.car.max_steering, self.pp.car.max_steering)
        car_curr_velocity = self.pp.cruising_speed
        return [car_steering_angle, car_curr_velocity]

    # optional for the Gym env
    def render(self, mode=None):
        pp_functions.drawing.render(self.pp)
        
    # needed for the Gym env
    def step(self, action):
        self.pp.car.steering_angle = action[0]
        self.pp.car.velocity.x = action[1]

        dt = self.pp.clock.get_time() / 500 

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.pp.exit = True
        pp_functions.manual_controls.enable_dragging_screen(self.pp, events)

        global time_start
        time_running = time.time() - time_start

        self.pp.car.config_angle()

        # update target list
        self.pp.target.update_target_lists()
       
        # update cone list
        self.pp.cone.update_cone_list()
        
        # calculate closest target
        self.pp.target.update_closest_target()

        # reset targets for new lap
        # self.pp.reset_new_lap()

        # implement track logic
        # might not need it
        # self.pp.track_logic()

        # Logic
        self.pp.implement_main_logic(dt, time_running)

        observation = [self.pp.car.angle, self.pp.car.velocity.x, self.pp.cone.polar_cone_list]
        done = self.pp.set_done()
        global global_reward
        global_reward += calculate_reward(self.pp.car)
        info = {}

        return observation, global_reward, done, info
    
    # needed for the Gym env
    def reset(self):
        self.pp = PathPlanning()

        global global_reward
        global_reward = 0


# if __name__ == "__main__":
#     env = CustomEnv()
#
#     global time_start
#     time_start = time.time()
#
#     while True:
#         action = env.generate_random_action()
#         _, _, done, _ = env.step(action)
#         env.render()
#
#         if done:
#             env.reset()
#         if env.pp.exit:
#             break
#
#     pygame.quit()
