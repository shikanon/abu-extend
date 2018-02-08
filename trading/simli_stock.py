#coding:utf-8
import requests
import pymongo
from concurrent.futures import ProcessPoolExecutor#多线程
from login import get_cookie #获取cookies
import time
from datetime import datetime
import redis
class mockTrading():
    def __init__(self):
        # cookies_dict = get_cookie()
        # self.cookies = dict(cookies_are ='searchGuide=sg; historystock=000807; spversion=20130314; PHPSESSID=326kig3g7mv5a2d8rq9jpkl0b1; ths_login_uname=useease; v=AuNE1C_MvaRgsXGQx-2JHEEceyyI2Hc7sWy7aBVAP8K5VA3YnagHasE8S9kn')
        self.cookies = dict(cookies_are='searchGuide=sg; spversion=20130314; isSaveAccount=1; PHPSESSID=9jibng91irpqugahrg5lfkj5b7; Hm_lvt_78c58f01938e4d85eaf619eae71b4ed1=1517560557; Hm_lpvt_78c58f01938e4d85eaf619eae71b4ed1=1517560557; historystock=000972%7C*%7C600036%7C*%7C600000%7C*%7C000807; v=AjifVShVluK1c_pmP6mSjT7lAO3PoZwc_gRwr3KphKAmENbZGrFsu04VQHvA; __utma=156575163.1849837646.1517897206.1517897206.1517897206.1; __utmc=156575163; __utmz=156575163.1517897206.1.1.utmcsr=10jqka.com.cn|utmccn=(referral)|utmcmd=referral|utmcct=/; user=MDp1c2VlYXNlOjpOb25lOjUwMDo0NDQ2MTA3OTE6NywxMTExMTExMTExMSw0MDs0NCwxMSw0MDs2LDEsNDA7NSwxLDQwOjI1Ojo6NDM0NjEwNzkxOjE1MTc4OTgwMjk6OjoxNTE2ODY4ODgwOjYwNDgwMDowOjFjNWE5YWMyODg4NTY4MWYyNjVlMTQ4YzFjNWJhYWM1ZjpkZWZhdWx0XzI6MA%3D%3D; userid=434610791; u_name=useease; escapename=useease; ticket=57c3fa375f7553b84ed467400c264955')
        # print (self.cookies)
        self.s = requests.Session()
        self.login_url = 'http://upass.10jqka.com.cn/login'
        self.payload = {'uname':'CuDATXeJPeRx2o1vCQht7RB0zHmcxTJ3pxxS2shoHHkBUr7KQVLdIRmRqSra7Q2JPxODspmLxQBzcmrh7bmV6PjcadEclY3GJNl1Y7E2XFYdDXKrezT3Pwiq0jpiDYXaTQ1qht+SYuZ4DDMIeXaAgEsh2UQUvQ7HkvwCggqdkbY=',
                   'passwd':'eYh1D8OtvbmRMEtZ6EuSEjtrg+y64GSoLkO5XhCxNQtURbg805HOYy4zGOIiMhK2RG5rklRSQF9UX2gG7V+qyS3bxzFuJXo6ykV0F9/wsOk0107bEdAAxQmFABtLCTJTHvYHCN1WLWQgGhB0XgpKuD25fYstpPwqUr0MfddgEu4=',
                   'longLogin':'on',
                   'act':'login_submit',
                   'rsa_version':'default_2',
                   'submit':'登　录'}
        self.headers = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'}
        # self.reque = self.s.post(self.login_url,data=self.payload,cookies=self.cookies,headers=self.headers)
        # print ('response',self.reque.content)
        self.trade_url = 'http://mncg.10jqka.com.cn/cgiwt/delegate/tradestock/'
        self.qichang_url = 'http://mncg.10jqka.com.cn/cgiwt/delegate/qryChicang'
        self.chenjiao_url ='http://mncg.10jqka.com.cn/cgiwt/delegate/qryChengjiao'
        self.delegated_url = 'http://mncg.10jqka.com.cn/cgiwt/delegate/qryDelegated'
        self.qicheng_payload = {'gdzh':'A476216366','mkcode':2}
        self.delegated_payload = {'gdzh':'A476216366','mkcode':1}

    def connect_database(self,name):
        self.connect = pymongo.MongoClient(host='localhost',port=27017)
        self.db = self.connect['stock']
        self.collection =self.db[name]
        return self.collection

    def store_queue(self,order):
        order_dict = {'buy_symbol': order.buy_symbol,
                      'buy_price': order.buy_price,
                      'buy_cnt': order.buy_cnt,
                      'buy_date': order.buy_date,
                      'buy_factor': order.buy_factor,
                      'sell_date': order.sell_date,
                      'sell_type': order.sell_type,
                      'sell_price':order.sell_price}
        self.connect_database('orders_queue').collection.insert(order_dict)

    def del_queue(self,order):
        self.connect_database('orders_queue').collection.remove({'buy_date':order.buy_date,'sell_date':order.sell_date})

    def qichange(self):
        qichang_result  = self.s.post(self.qichang_url,data=self.qicheng_payload,cookies=self.cookies,headers = self.headers)
        print ('qichang_result',qichang_result.text)
        qichang_list=  qichang_result.json()
        # print (qichang_list['result']['list'])
        for item  in qichang_list['result']['list']:
            # print (item)
            qichang_dict ={
                'code':item['d_2102'],
                'name':item['d_2103'],
                'voucher_balance':item['d_2117'],
                'balance':item['d_2121'],
                'frozen_quantity':item['d_2118'],
                'real_stock':item['d_2164'],
                'cost_price':item['d_2122'],
                'market_price':item['d_2124'],
                'market_capitalization':item['d_2125'],
                'float_loss':item['d_2147'],
                'loss':item['d_3616'],
                'currency':item['d_2172'],
                'trade_market':item['d_2108'],
                'account':item['d_2106']}
            print (qichang_dict)
            self.connect_database('qichang').collection.update({'code':item['d_2102']},qichang_dict,upsert=True)
            yield qichang_dict

    def chenjiao(self):
        chenjiao_result = requests.post(self.chenjiao_url,data=self.qicheng_payload,cookies=self.cookies)
        chenjiao_list = chenjiao_result.json()
        for item in  chenjiao_list['result']['list']:
            chenjiao_dict ={
                'time':item['d_2142'],
                'code':item['d_2102'],
                'name':item['d_2103'],
                'action':item['d_2109'],
                'amount':item['d_2128'],
                'avrage_price':item['d_2129'],
                'turover':item['d_2131'],
                'contract_num':item['d_2135'],
                'turover_num':item['d_2130'],
                'date':item['d_2141'],
                'mark':item['d_2108'],
                'balance':item['d_2117'],
                'orders_num':item['d_2120']
            }
            # print (chenjiao_dict)
            self.connect_database('chenjiao').collection.insert(chenjiao_dict)
            # yield chenjiao_dict
        # self.collection.insert(qichang_dict)
    def weituo(self):
        delegated_result = requests.post(self.delegated_url,data=self.delegated_payload,cookies=self.cookies)
        delegated_list = delegated_result.json()
        for item in delegated_list['result']['list']:
            delegated_dict = {
                'code': item['d_2102'],
                'name':item['d_2103'],
                'mark':item['d_2105'],
                'commission_num':item['d_2126'],
                'transactions_num':item['d_2128'],
                'commission_price':item['d_2127'],
                'avrage_price':item['d_2129'],
                'action':item['d_2109'],
                'time':item['d_2140'],
                'date':item['d_2139'],
                'num':item['d_2135'],
                'market':item['d_2108'],
                'account':item['d_2106']
        }
            print (delegated_dict)
            self.connect_database('weituo').collection.update(delegated_dict)
            yield delegated_dict

    def write_order(self,order,stat,msg):
        order_dict = {'buy_date':order.buy_date,
                      'code':order.buy_symbol[-6:],
                      'buy_price':order.buy_price,
                      'buy_factory':order.buy_factor,
                      'sell_date':order.sell_date,
                      'sell_type':order.sell_type,
                      'sell_price':order.sell_price,
                      'stat':stat,
                      'message':msg}
        self.connect_database('orders_sccuess').collection.update(order_dict.items(),order_dict,upsert=True)

    def buy(self):
        # print ('orders',order)
        order_list = list(self.connect_database('orders_queue').collection.find())
        payload = dict()
        market_dict= {'sz':'00100496243','sh':'A476216366'}
        for order in order_list:
        # db_result =  (list(self.connect_database('chenjiao').collection.find({'date':order.buy_date,'code':order.buy_symbol[-6:]})))
        # if db_result:
            if order['sell_type']=='keep' and order['buy_date'] == datetime.today().strftime('%Y%m%d'):
                # order.buy_date == db_result[0]['date'] and order.buy_symbol[-6:]==db_result[0]['code']:
                payload = {'amount': order.buy_cnt,
                           'gdzh': '00100496243',
                           'mkcode': 1,
                           'price': order.buy_price,
                           'stockcode': order.buy_symbol[-6:],
                           'type': 'cmd_wt_mairu'}
            else:
                payload = {'amount': order.buy_cnt,
                           'gdzh': '00100496243',
                           'mkcode': 1,
                           'price': order.sell_price,
                           'stockcode': order.buy_symbol[-6:],
                           'type': 'cmd_wt_maichu'}
            print ('payload',payload)
            try:
                buy_result = requests.post(self.trade_url,data=payload,cookies=self.cookies)
                response= (buy_result.json())
                print ('response',response)
                time.sleep(3)

                # today_result = list(self.chenjiao())
                if response['errorcode']==0 and payload['stockcode']==today['code'] and today['action']=='买入' and payload['amount']== today['amount']:
                    print ('买入成功')
                    message ='buy sccuess'
                    self.write_order(order,1,message)
                elif response['errorcode']==0 and payload['stockcode']==today['code'] and today['action']=='卖出':
                    print ('卖出成功')
                    message = 'sell sccuess'
                    self.write_order(order,2,message)
                    #删除order
                elif response['errorcode']==-99:
                    print ('失败')
                    message = response['errormsg']
                    self.write_order(order,3,message)
                    #删除order
            except Exception as e:
                errormsg = 'api error'
                self.write_order(order,4,errormsg)
                #删除order

    def multi_buy(self,n_jobs,orders):
        with ProcessPoolExecutor(max_workers=n_jobs) as pool:
            result = pool.map(self.buy,orders)

# if __name__ == '__main__':
#     trade = mockTrading()
#     chenjiao = trade.buy()
#     print ((chenjiao))
    # result = trade.connect_database('chenjiao').collection.find({'date':'20180201','code':'002230'})
    # print (list(result))
    # print (trade.weituo())


"""
{errorcode: -99, errormsg: "[002230:30.000]超过涨跌限制。56.2-45.98 ", result: null}
"""