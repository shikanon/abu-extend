# abu-extend
the functions for abupy extend, inclund real-time trading platform and some machine learning



### 模块使用示例
｀｀｀
from stock import stockBuy
buy = stockBuy(read_cash,buy_factors,sell_factors)#实例化
    start_day = datetime.date(2017,01,1)
    while True:
            start_day += datetime.timedelta(days=1)
            """
            methods:
            buy.singnal_sell(code,date)
            buy.mulit_process_sell(code_list,date,n_jobs)
            """
            result = (buy.mulit_process_sell(['002230','000725'],str(start_day.strftime('%Y%m%d')),4))
            print ('result',result)
            time.sleep(60)
｀｀｀