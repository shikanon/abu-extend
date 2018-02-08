#coding:utf-8
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import pickle, os, time
import requests


def get_cookie_from_network():
    # dcap = dict(DesiredCapabilities.PHANTOMJS)
    # dcap["phantomjs.page.settings.userAgent"] = \
    #     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:25.0) Gecko/20100101 Firefox/25.0 "
    # phantomjsPath = '/usr/bin/phantomjs'

    # driver = webdriver.PhantomJS(executable_path=phantomjsPath, desired_capabilities=dcap)
    driver = webdriver.PhantomJS()
    login_url = 'http://upass.10jqka.com.cn/login?redir=HTTP_REFERER'
    driver.get(login_url)


    idxpath = '//*[@id="username"]'
    paxpath = '//*[@id="password"]'
    rember= '/html/body/div[4]/div[2]/div/form/div/ul/li[4]/font'
    login_xpath = '//*[@id="loginBtn"]'
    click_xpath = '//*[@id="page"]/div[2]/ul/li[1]/a'
    other_click_xpath = '//*[@id="all-page"]/div[5]/div[2]/p[2]/a'
    driver.find_element_by_xpath(idxpath).send_keys('useease')
    driver.find_element_by_xpath(paxpath).send_keys('ue123456')
    driver.find_element_by_xpath(rember).click()
    driver.find_element_by_xpath(login_xpath).click()
    # cookie_list = driver.get_cookies()
    # print ('cookies_list',cookie_list)
    # driver.get('http://www.10jqka.com.cn/')
    # driver.get('http://stock.10jqka.com.cn/')
    # driver.find_element_by_xpath(click_xpath).click()
    # driver.get('http://moni.10jqka.com.cn/')


    # print ('cook_list',cookie_list)
    req = requests.Session()
    cookie_list = driver.get_cookies()
    for cookie in cookie_list:
        req.cookies.set(cookie['name'], cookie['value'])
    # print (req.cookies.items())
    qicheng_payload = {'gdzh':'A476216366','mkcode':2}
    new_cookies ="v=%s;log=;user=%s; userid=434610791; u_name=useease; escapename=useease; ticket=%s; PHPSESSID=%s; isSaveAccount=0"%(req.cookies['v'],req.cookies['user'],req.cookies['ticket'],req.cookies['PHPSESSID'])
    print('new_cookies',new_cookies)
    driver.add_cookie(new_cookies)
    driver.get('http://mncg.10jqka.com.cn/cgiwt/index/index')
    html = driver.page_source
    print('html', html)
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'}

    result = req.post('http://mncg.10jqka.com.cn/cgiwt/delegate/qryChicang',data=qicheng_payload,headers=headers)
    print (result.json())
        # driver.get('http://mncg.10jqka.com.cn/cgiwt/index/index')
    cookie_dict = {}
    # for cookie in cookie_list:
    cookie_dict['value']=cookie_list[-1]['value']
    cookie_dict['tricket'] = cookie_list[-5]['value']
    cookie_dict['expiry'] = cookie_list[-6]['expiry']
    cookie_dict['v'] = cookie_list[0]['value']
    print (cookie_dict)
    # session_id= get_session_id(cookie_dict)
    # cookie_dict['session_id'] = session_id
    with open('cookie.txt','wb')as f:
        pickle.dump(cookie_dict,f)

    return cookie_dict

def get_cookie_from_cache():
    cookie_dict = {}
    try:
        with open('cookie.txt', 'rb') as f:
            d = pickle.load(f)
            expiry_date = int(d['expiry'])
            if expiry_date > (int)(time.time()):
                cookie_dict = d
            else:
                return {}
    except Exception as e:
        return {}
    if timeout(cookie_dict):
        return cookie_dict

def get_cookie():
    cookie_dict = get_cookie_from_cache()
    if not cookie_dict :
        cookie_dict = get_cookie_from_network()
    print (cookie_dict)
    return cookie_dict
def timeout(cookies_dict):
    cookies = dict(
        cookies_are='searchGuide=sg; historystock=000807; spversion=20130314; PHPSESSID=9jibng91irpqugahrg5lfkj5b7; isSaveAccount=0; v=AuNE1C_MvaRgsXGQx-2JHEEceyyI2Hc7sWy7aBVAP8K5VA3YnagHasE8S9kn; user={}; userid=434610791; u_name=useease; escapename=useease; ticket={}; v=AnPUJN8cLWluHOE99UgZrFHMC3yYqAdqwTxLniUQzxLJJJ1orXiXutEM2-w3'.format(
            cookies_dict['value'], cookies_dict['tricket'],cookies_dict['v'] ))
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36'}

    url = 'http://mncg.10jqka.com.cn/cgiwt/delegate/qryChicang'
    response = requests.get(url, cookies=cookies, headers=headers)
    try:
        result = response.json()
        return True
    except Exception as e:
        click_url = 'http://moni.10jqka.com.cn/mncg/index/mncgerror'
        driver = webdriver.PhantomJS()
        driver.get(click_url)
        click_xpath ='//*[@id="page"]/div[2]/ul/li[1]/a'
        driver.find_element_by_xpath(click_xpath).click()
        return True

if __name__ == '__main__':
    get_cookie_from_network()
    # with open('cookie.txt', 'rb') as f:
    #     d = pickle.load(f)
    #     print (get_session_id(d))