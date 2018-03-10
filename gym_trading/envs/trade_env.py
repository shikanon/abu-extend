# -*- coding: UTF-8 -*-
import gym
from gym import spaces
from gym.utils import seeding

import quandl
import logging
import numpy as np
import pandas as pd

log = logging.getLogger()
log.info('%s logger started.', __name__)

class getStock:

    def __init__(self, name, auth, scale=True):
        self.df = quandl.get(name) if auth == '' else quandl.get(name, authtoken=auth) # 获取股票数据
        log.info('got data for %s from quandl...', QuandlEnvSrc.Name)
        self.df = self.df[~np.isnan(self.df.Volume)][['Open', 'High', 'Low', 'Close', 'Volume']] # 数据字段
        self.scale = scale

    def get_data(self):
        #特征
        self.df['Return_1'] = (self.df.Close - self.df.Close.shift()) / self.df.Close.shift()
        self.df['Return_3'] = (self.df.Close - self.df.Close.shift(3)) / self.df.Close.shift(3)
        self.df['Return_5'] = (self.df.Close - self.df.Close.shift(5)) / self.df.Close.shift(5)
        if self.scale:
            min_value = self.df.Close.min(axis=0)
            max_value = self.df.Close.max(axis=0)
            self.df.Close = (self.df.Close-(min_value-1))/(max_value-(min_value-1)) # -1: to advoid 0

        self.df = self.df.dropna(axis=0, how='any')
        self.df['volumn'] = 0
        self.df['cash'] = 1
        return self.df



class QuandlEnvSrc(object):
    '''
    Quandl-based implementation of a TradingEnv's data source.

    Pulls data from Quandl, preps for use by TradingEnv and then
    acts as data provider for each new episode.
    '''

    QuandlAuthToken = ""  # not necessary, but can be used if desired
    Name = "WIKI/AAPL"

    # Name = "TSE/9994" # https://www.quandl.com/search (use 'Free' filter)

    def __init__(self, days=253, name=Name, auth=QuandlAuthToken, scale=True):
        self.days = days
        log.info('getting data for %s from quandl...', QuandlEnvSrc.Name)
        #获取股票
        stock = getStock(name, auth, days)
        df = stock.get_data()
        self.data = df[['cash','volumn','Close','Return_1', 'Return_3', 'Return_5']]
        self.step = 0

    def reset(self):
        # we want contiguous data
        self.idx = np.random.randint(low=0, high=len(self.data.index) - self.days)  # 随机选择一个数字作为起始ID
        self.step = 0

    def _step(self):
        obs = self.data.iloc[self.idx]
        self.idx += 1
        self.step += 1
        done = self.step >= self.days
        return obs, done


class Investor(object):
    '''

    '''
    def __init__(self,steps, trading_cost_bps=1e-3):
        self.step             = 0
        self.cash             = 1
        self.volumn           = 0
        self.total_nav        = 1 # 总净资产
        self.trading_cost_bps = trading_cost_bps # 交易费用率
        self.cash_log         = np.zeros(steps) # 历史cash变化
        self.volumn_log       = np.zeros(steps) # 历史仓位
        self.costs_log        = np.zeros(steps)
        self.total_nav_log    = np.zeros(steps)
        self.action_log       = np.zeros(steps)

    def reset(self):
        self.step             = 0
        self.cash             = 1
        self.volumn           = 0
        self.total_nav        = 1
        self.cash_log.fill(0)
        self.volumn_log.fill(0)
        self.costs_log.fill(0)
        self.total_nav_log.fill(0)
        self.action_log.fill(0)

    def _step(self, action, next_observation, done):
        '''

        :param action: 动作，数据类型为数值型，主要有0 和 1 ， 0代表买入， 1 代码卖出
        :param next_observation: 下一刻的记录， 数据类型为series.
        :param done:
        :return:
        '''
        # first we meet today's observation, after the stock trade closed, next day come,
        #  then we apply action next day, then the next_observation update
        # 0: buy    2: sell
        self.costs = 0
        # 动作选择
        if self.volumn == 0:
            if action == 0:
                self.volumn= self.cash / next_observation['Close']
                self.costs= self.total_nav * self.trading_cost_bps
                self.cash = 0
        if self.cash == 0:
            if action == 2:
                self.cash= next_observation['Close'] * self.volumn
                self.costs= self.total_nav * self.trading_cost_bps
                self.volumn= 0

        next_observation.set_value('cash',self.cash)
        next_observation.set_value('volumn', self.volumn)
        self.total_nav= self.volumn*next_observation['Close'] + self.cash - self.costs
        new_observation = next_observation
        self.action_log[self.step]  = action
        self.cash_log[self.step] = self.cash
        self.volumn_log[self.step] = self.volumn
        self.costs_log[self.step] = self.costs
        self.total_nav_log[self.step] = self.total_nav
        info = { 'reward': self.total_nav, 'costs':self.costs }
        self.step += 1
        return new_observation, self.total_nav, info

    def to_df(self,filename):
        """returns internal state in new dataframe """
        cols = ['action','cash','volumn','cost','total_nav']

        df = pd.DataFrame({'action':   self.action_log,
                           'cash':     self.cash_log,
                           'volumn':   self.volumn_log,
                           'cost':     self.costs_log,
                           'total_nav':self.total_nav_log},
                          columns=cols)
        df.to_csv(filename)
        return df



class TradeEnv(gym.Env):
    def __init__(self):
        self.days = 252
        self.src = QuandlEnvSrc(days=self.days)
        self.sim = Investor(steps=self.days, trading_cost_bps=1e-3)
        self.action_space = spaces.Discrete(2)
        # self.observation_space = spaces.Box( self.src.min_values,
        #                                     self.src.max_values)
        self.reset()

    # get the first observation
    def _reset(self):
        self.src.reset()
        self.sim.reset()
        return self.src._step()[0]

    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    # recieve action, factor,which determine and agent state, return (reward, observations)
    # action 0:buy; 1:stay 2:sell;


    def _step(self, action):
        assert self.action_space.contains(action), "%r (%s) invalid" % (action, type(action))
        next_observation, done = self.src._step()
        # Close Return buy_thres  sell_thres
        observation_, reward, info = self.sim._step(action, next_observation, done)
        return observation_, reward, done, info





