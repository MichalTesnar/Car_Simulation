import gym
import numpy as np
import time
import pygame
import pp_functions
from pp_functions.reward_function import calculate_reward
from stable_baselines3.common.env_checker import check_env

from CarEnv import CarEnv

if __name__ == "__main__":
    env = CarEnv()
    check_env(env)
    observation, global_reward = env.reset()

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