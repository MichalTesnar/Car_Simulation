from ray import tune
from CarEnv import CarEnv
import gym
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env


#
# agent = gym.Agent(alpha=0.000025, beta=0.00025, input_dims=[8], tau=0.001, env=CustomEnv,
#                   batch_size=64,  layer1_size=400, layer2_size=300, n_actions=2,
#                   chkpt_dir='tmp/ddpg_final1')

#tune.run(
    #"SAC",
    #name="Training1",
    #config={"env": CarEnv},
    #local_dir = r'./ray_results/',
    #stop={"timesteps_total": 1000},
#)

if __name__ == "__main__":
    env = CarEnv()
    model = PPO("MlpPolicy", env, verbose=3)
    model.learn(total_timesteps=2500)
    model.save("car_model")

    #del model # remove to demonstrate saving and loading
    #model = PPO.load("car_model")

    obs = env.reset()
    done = False
    while not done:
        action, _states = model.predict(obs)
        observation, global_reward, done, info = env.step(action)
        env.render()