# -*- coding: UTF-8 -*-
import os
import argparse
import gym
import numpy as np
import pandas as pd
from PolicyGradient import PolicyGradient
from itertools import count
import gym_trading
import trade_env

import torch
import torch.optim as optim
from torch.autograd import Variable
from torch.distributions import Categorical

from logger import Logger
logger = Logger('./logs')


parser = argparse.ArgumentParser(description='PyTorch policy gradient example at openai-gym pong')
''''decay_rate 权重衰减率，
 learning_rate 学习率
 batch_size 批大小
 seed 随机种子
'''
# parser.add_argument('--gamma', type=float, default=0.99, metavar='G',
#                     help='discount factor (default: 0.99')
parser.add_argument('--decay_rate', type=float, default=0.99, metavar='G',
                    help='decay rate for RMSprop (default: 0.99)')
parser.add_argument('--learning_rate', type=float, default=1e-4, metavar='G',
                    help='learning rate (default: 1e-4)')
parser.add_argument('--batch_size', type=int, default=5, metavar='G',
                    help='Every how many episodes to da a param update')
parser.add_argument('--seed', type=int, default=87, metavar='N',
                    help='random seed (default: 87)')

args= parser.parse_args()

policy = PolicyGradient()

# 环境声明
env = gym.make('trade-v0')
env.seed(args.seed)
torch.manual_seed(args.seed)
# 目标函数
optimizer = optim.RMSprop(policy.parameters(), lr=args.learning_rate, weight_decay=args.decay_rate)

# # check & load pretrain model
# if os.path.isfile('pg_params.pkl'):
#     print('Load Policy Network parameters ...')
#     policy.load_state_dict(torch.load('pg_params.pkl'))


def select_action(state):
    '''选择动作 '''
    state = torch.from_numpy(state.as_matrix()).float().unsqueeze(0)
    probs = policy(Variable(state))
    m = Categorical(probs)
    action = m.sample()
    policy.saved_log_probs.append(m.log_prob(action))
    return action.data[0]


def param_update():
    '''参数跟新'''
    R = 0
    policy_loss = []
    rewards = []
    for r in policy.rewards:
        R = r
        rewards.insert(0, R)
    # turn rewards to pytorch tensor and standardize
    rewards = torch.Tensor(rewards)
    # rewards = (rewards - rewards.mean()) / (rewards.std() + np.finfo(np.float32).eps)

    for log_prob, reward in zip(policy.saved_log_probs, rewards):
        loss = -log_prob * reward
        policy_loss.append(loss)

    # 清理optimizer的gradient是PyTorch制式動作，去他們官網學習一下即可
    optimizer.zero_grad()
    policy_loss = torch.cat(policy_loss).sum()
    policy_loss.backward()
    optimizer.step()

    # clean rewards and saved_actions
    del policy.rewards[:]
    del policy.saved_log_probs[:]
    loss_info = {'loss':policy_loss.data[0]}
    return loss_info

def to_np(x):
    return x.data.cpu().numpy()

def loss_visualize(loss_info,i_episode):
    '''使用tensorboard 进行可视化'''
    for tag, value in loss_info.items():
        logger.scalar_summary(tag, value,i_episode)

    for tag, value in policy.named_parameters():
        tag = tag.replace('.','/')
        logger.histo_summary(tag, to_np(value.grad),i_episode)
        logger.histo_summary(tag + '/grad', to_np(value.grad), i_episode)



if __name__ == "__main__":
    running_reward = None
    reward_sum = 0
    rewards = []
    episode = 0
    while True:
        episode += 1
        observation = env.reset()
        for t in range(1000):
            action = select_action(observation)
            observation_, reward, done, info = env.step(action)
            reward_sum += reward
            policy.rewards.append(reward)
            observation = observation_
            if done:
                running_reward = reward_sum
                print('resetting env. episode reward total was %f.' % reward_sum)
                reward_sum = 0
                break

        # 更新模型
        if episode % args.batch_size == 0:
            print('ep %d: policy network parameters updating...' % (episode))
            loss_info = param_update()
            loss_visualize(loss_info,episode)

        # 保存模型
        if episode % 100 == 0:
            print('ep %d: model saving...' % (episode))
            torch.save(policy.state_dict(), 'pg_params.pkl')
            filename = '../../data.csv'
            env.env.sim.to_df(filename)




