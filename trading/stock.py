#coding:utf-8
import abupy
from abupy import EMarketDataFetchMode
from abupy import AbuMetricsBase
from abupy import EDataCacheType
from abupy import EMarketTargetType
from abupy import AbuDoubleMaBuy, AbuDoubleMaSell
from abupy import AbuPositionBase
from abupy import abu
from abupy.AlphaBu import ABuPickTimeWorker
from abupy import AbuBenchmark
from abupy.TradeBu import AbuKLManager
from abupy import AbuCapital
from abupy import AbuKellyPosition
from abupy import AbuFactorBuyBreak, AbuFactorAtrNStop, AbuFactorPreAtrNStop, AbuFactorCloseAtrNStop
from abupy.CoreBu import ABuParallel, ABuEnvProcess
# from datetime import datetime
import datetime
import time
from simli_stock import mockTrading
from abupy.TradeBu import AbuOrder

class stockBuy():
    def __init__(self,read_cash,buy_factors,sell_factors):
        # self.read_cash = read_cash
        # self.read_cash = 200000
        # 买入因子使用60日向上和42日突破因子
        # self.buy_factors = [{'fast': 5, 'slow': 20, 'class': AbuDoubleMaBuy}, {'xd': 60, 'class': AbuFactorBuyBreak},
        #             {'xd': 42, 'class': AbuFactorBuyBreak,
        #              'position': {'class': AbuKellyPosition}, }]
        self.buy_factors=buy_factors

        # 趋势跟踪策略止盈要大于止损设置值，这里1.0，3.0
        # 卖出因子并行生效
        # self.sell_factors = [
        #     {'stop_loss_n': 1.0, 'stop_win_n': 3.0,
        #      'class': AbuFactorAtrNStop},
        #     {'class': AbuFactorPreAtrNStop, 'pre_atr_n': 1.5},
        #     {'class': AbuFactorCloseAtrNStop, 'close_atr_n': 1.5}
        # ]
        self.sell_factors=sell_factors

        # self.sell_factors = [{'fast': 5, 'slow': 20, 'class': AbuDoubleMaSell},
        #                 {'stop_loss_n': 1.0, 'stop_win_n': 3.0,
        #                  'class': AbuFactorAtrNStop},
        #                 {'class': AbuFactorPreAtrNStop, 'pre_atr_n': 1.5},
        #                 {'class': AbuFactorCloseAtrNStop, 'close_atr_n': 1.5}]

        abupy.env.g_enable_ml_feature = True
        abupy.env.g_market_target = EMarketTargetType.E_MARKET_TARGET_CN
        self.commission_dict = {'buy_commission_func': self.buy_commission_ch, 'sell_commission_func': self.sell_commission_ch}
        self.benchmark = AbuBenchmark()
        self.capital = AbuCapital(self.read_cash, self.benchmark, self.commission_dict)
        self.kl_pd_manager = AbuKLManager(self.benchmark, self.capital)
        # self.time_work = stockSell(self.capital, kl_pd, self.benchmark, self.buy_factors,self.sell_factors)
    def buy_commission_ch(self,trade_cnt, price):
        """
        计算交易费用：每股0.001块，，最低消费1块；交易佣金：最高收费为3‰，最低收费5元；印花税：1‰
        :param trade_cnt: 交易的股数
        :param price: 每股的价格
        :return: 计算结果手续费
        """
        # 每股手续费0.01
        transfer_fees = trade_cnt * 0.001
        commission = price*trade_cnt*0.0003
        if transfer_fees < 1:
            transfer_fees = 1
        if commission < 5:
            # 最低消费2.99
            commission = 5
        return transfer_fees+commission

    def sell_commission_ch(self,trade_cnt, price):
        """
        计算交易费用：每股0.001块，，最低消费1块；交易佣金：最高收费为3‰，最低收费5元；印花税：1‰
        :param trade_cnt: 交易的股数
        :param price: 每股的价格
        :return: 计算结果手续费
        """
        # 每股手续费0.01
        transfer_fees = trade_cnt * 0.001
        commission = price*trade_cnt*0.0003
        stamp_duty = price*trade_cnt*0.001#算一半，因为只有卖出才收
        if transfer_fees < 1:
            transfer_fees = 1
        if commission < 5:
            commission = 5
        return transfer_fees+commission+stamp_duty

    def singnal_sell(self,code,date,env=None):
        # print (code,date)
        try:
            kl_pd = self.kl_pd_manager.get_pick_time_kl_pd(code)
            # print (kl_pd)
            time_work = stockSell(self.capital, kl_pd, self.benchmark, self.buy_factors,self.sell_factors)
            # time_work = ABuPickTimeWorker.AbuPickTimeWorker(self.capital, kl_pd, self.benchmark, self.buy_factors,self.sell_factors)
            if date == datetime.datetime.today().strftime('%Y%m%d'):
                today_time = kl_pd[:date].iloc[-1]
                # print (today_time)
                time_work._day_task(today_time)
                return time_work.orders
            else:
                today_time = kl_pd[:date].iloc[-2]
                # print (today_time)
                time_work._day_task(today_time)
                return time_work.orders
        except TypeError:
            pass

    def mulit_process_sell(self,codes,date,num_jobs):
        p_nev = ABuEnvProcess.AbuEnvProcess()
        parallel = ABuParallel.Parallel(
            n_jobs=num_jobs, verbose=0, pre_dispatch='2*n_jobs')
        result = parallel(ABuParallel.delayed(self.singnal_sell)(code,date,env=p_nev) for code in
                 codes)
        return result


def singleton(cls):
    instances = {}

    def wrapper(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return wrapper
@singleton
class stockSell(ABuPickTimeWorker.AbuPickTimeWorker):
    # def __init__(self):
    #     super().__init__(cap, kl_pd, benchmark, buy_factors, sell_factors)
    def _day_task(self, today):
        """
        日任务：迭代买入卖出因子序列进行择时
        :param today: 今日的交易数据
        :return:
        """
        sell = mockTrading()
        # 优先执行买入择时因子专属卖出择时因子，不受买入因子是否被锁的影响
        self._task_attached_sell(today, how='day')
        # 注意回测模式下始终非高频，非当日买卖，不区分美股，A股市场，卖出因子要先于买入因子的执行
        # new_orders = self.orders.copy()
        for sell_factor in self.sell_factors:
            # 迭代卖出因子，每个卖出因子针对今日交易数据，已经所以交易单进行择时
            sell_factor.read_fit_day(today, self.orders)


        # 买入因子行为要在卖出因子下面，否则为高频日交易模式
        for buy_factor in self.buy_factors:
            # 如果择时买入因子没有被封锁执行任务
            if not buy_factor.lock_factor:
                # 迭代买入因子，每个因子都对今天进行择时，如果生成order加入self.orders
                order = buy_factor.read_fit_day(today)
                if order and order.order_deal:
                    self.orders.append(order)
        # print ('self.orders',self.orders)
        if self.orders:
            # self.orders=[self.orders.remove(order)for order in self.orders if not sell.buy(order)]
            for order in self.orders:
                # print ('oders',order)
                sell.store_queue(order)
                #更新oders,读取数据库
                order_sell_sccusee = list(sell.connect_database('orders_sccuess').collection.find({'buy_date':order.buy_date,'stat':2}))
                order_fail = list(sell.connect_database('orders_sccuess').collection.find({'buy_date':order.buy_date,'stat':3}))
                if order_sell_sccusee or order_fail:
                    print ('remove orders')
                    self.orders.remove(order)






# if __name__ == '__main__':
#     buy = stockBuy()#实例化
#     start_day = datetime.date(2017,1,1)
#     while True:
#         for i in range(30):
#             start_day += datetime.timedelta(days=1)
#             """
#             methods:
#             buy.singnal_sell(code,date)
#             buy.mulit_process_sell(code_list,date,n_jobs)
#             """
#             result = (buy.mulit_process_sell(['002230','000725'],str(start_day.strftime('%Y%m%d')),4))
#             print ('result',result)
#         time.sleep(60)
