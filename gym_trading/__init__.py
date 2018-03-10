from gym.envs.registration import register

register(
    id='trade-v0',
    entry_point='gym_trading.envs.trade_env:TradeEnv',
    timestep_limit=1000,
)