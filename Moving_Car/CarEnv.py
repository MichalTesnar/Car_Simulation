import random

import gym
import numpy as np
import time
from path_planning import PathPlanning
import pygame
import pp_functions
from pp_functions.reward_function import calculate_reward
from stable_baselines3.common.env_checker import check_env

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

global global_reward
global_reward = 0

class CarEnv(gym.Env):
    def __init__(self):
        
        self.pp = PathPlanning()
        self.episode_time_start = time.time()
        #self.action_space = gym.spaces.Dict({
                #"steering" : gym.spaces.Box(low = -self.pp.car.max_steering, high = self.pp.car.max_steering, shape=(1,), dtype=np.float32),
                #"velocity" : gym.spaces.Box(low = 2, high=2, shape=(1,), dtype=np.float32) #self.pp.car.max_velocity
        #})

        self.action_space = gym.spaces.Box(low = -1, high = 1, shape=(1,), dtype=np.float32)

        global max_num_cones
        max_num_cones = 200
        orientation = gym.spaces.Box(low=-1., high=1., shape=(1,), dtype=np.float32)
        velocity = gym.spaces.Box(low=-1., high=1., shape=(1,), dtype=np.float32)
        angles = gym.spaces.Box(low=-1., high=1., shape=(max_num_cones,), dtype=np.float32)
        distances = gym.spaces.Box(low=0, high=1., shape=(max_num_cones,), dtype=np.float32)
        binary = gym.spaces.Box(low=0, high=1., shape=(max_num_cones,), dtype=np.float32)

        # spaces for different objects
        #self.observation_space =  gym.spaces.Dict({
            #"velocity": velocity,
            #"orientation": orientation,
            #"cone_angles": angles,
            #"cone_distances": distances,
            #"cone_category": binary,
            #"cone_place_holder": binary
        #})

        self.observation_space = gym.spaces.Box(low=np.array([-1,0]), high=np.array([1, 100]), shape=(2,), dtype=np.float32)

    def generate_random_action(self):
        car_steering_angle = random.uniform(-self.pp.car.max_steering, self.pp.car.max_steering)
        car_curr_velocity = self.pp.cruising_speed
        return [car_steering_angle, car_curr_velocity]

    def render(self, mode=None):
        pp_functions.drawing.render(self.pp)
        
    def step(self, action):
        self.pp.car.steering_angle = self.pp.car.max_steering * action[0]
        self.pp.car.velocity.x = 2
        
        dt = self.pp.clock.get_time() / 500 

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.pp.exit = True
        pp_functions.manual_controls.enable_dragging_screen(self.pp, events)

        episode_time_running = time.time() - self.episode_time_start

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
        self.pp.implement_main_logic(dt, episode_time_running)

        # Retrieve observation
        observation = self.pp.get_observation()
        observation[1] = episode_time_running

        done = self.pp.set_done()
        global global_reward

        global_reward += calculate_reward(self.pp.car)
        info = {}

        return observation, global_reward, done, info
    
    # needed for the Gym env
    def reset(self):
        self.pp = PathPlanning()
        
        global observation
        self.episode_time_start = time.time()

        observation = np.array([0,0])
        #observation = {
                        #"velocity": np.zeros(1),
                        #"orientation": np.zeros(1),
                        #"cone_angles": np.zeros(max_num_cones),
                        #"cone_distances": np.zeros(max_num_cones),
                        #"cone_category": np.zeros(max_num_cones),
                        #"cone_place_holder":np.zeros(max_num_cones)}
        return observation

if __name__ == "__main__":
    env = CarEnv()
    observation = env.reset()
    check_env(env)

    while True:
        action = env.action_space.sample()
        observation, global_reward, done, info = env.step(action)
        env.render()

        if done:
            break
            env.reset()
        if env.pp.exit:
            break

    pygame.quit()