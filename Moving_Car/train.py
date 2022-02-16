from ray import tune
from main import CustomEnv
import gym
#
# agent = gym.Agent(alpha=0.000025, beta=0.00025, input_dims=[8], tau=0.001, env=CustomEnv,
#                   batch_size=64,  layer1_size=400, layer2_size=300, n_actions=2,
#                   chkpt_dir='tmp/ddpg_final1')

tune.run(
    "SAC",
    name="Training1",
    config={"env": CustomEnv},
    local_dir = r'./ray_results/',
    stop={"timesteps_total": 1000},
)