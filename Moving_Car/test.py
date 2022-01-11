import gym
import numpy as np
from path_planning import PathPlanning
import pygame
import pp_functions.drawing

class CustomEnv(gym.Env):
    def __init__(self):
        # action = [acceleration, rotation]
        # TODO check ranges for acc and rot
        self.action_space = gym.spaces.Box(low=-1., high=1., shape=(2,), dtype=np.float32)
        #self.observation_space = gym.spaces.Box()

        self.pp = PathPlanning()
    
    def render(self):
        pp_functions.drawing.render(self.pp)
        

    def step(self):
        self.pp.run()
        # pass
        #return observation, reward, done, info
    
    def reset(self):
        pass
        # return observation


# env = CustomEnv()
# env.render()

pygame.init()
clock = pygame.time.Clock()
env = CustomEnv()

while True:
    clock.tick(30)
    # action = 
    # env.step(action)
    
    # stop condition
    if env.pp.exit:
        break

    env.step()
    env.render()
    pygame.display.update()

pygame.quit()
# from stable_baselines.common.env_checker import check_env
# check_env(env)