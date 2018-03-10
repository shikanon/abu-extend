import gym
import gym_trading
import trade_env
import pandas as pd
import numpy as np

env = gym.make('trade-v0')

# env.time_cost_bps = 0

Episodes = 3

obs = []

for _ in range(Episodes):
    observation = env.reset()
    done = False
    count = 0
    while not done:
        action = env.action_space.sample()  # random
        observation, reward, done, info = env.step(action)
        obs = obs + [observation]
        # print observation,reward,done,info
        count += 1
        if done:
            print
            reward
            print
            count

df = env.env.sim.to_df('..\..\data')
