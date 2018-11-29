# -*- coding: utf-8 -*-

import config
import redis
import time
import json
import gevent
import requests
from retrying import retry
from pyquery import PyQuery as pq
from gevent.threadpool import ThreadPool


URL = 'https://www.kuaidaili.com/free/inha/{0}/'
SLEEP = 1.2


@retry(stop_max_attempt_number = 3, stop_max_delay = 10000, wait_fixed = SLEEP*1000)
def get_by_page(page):
    resp = requests.get(URL.format(page))
    return resp if resp.status_code == 200 else False


@retry(stop_max_attempt_number = 2, stop_max_delay = 10000, wait_fixed = 200)
def request_url(url, proxies):
    resp = requests.get(url, proxies=proxies, timeout=10)
    return resp if resp.status_code == 200 else False


def validate_ip_and_port(r, ip_and_port):
    try:
        t1 = time.time()
        resp = request_url('https://www.baidu.com', proxies={
            'http': 'http://%s:%s' % (ip_and_port[0], ip_and_port[1]),
            'https': 'http://%s:%s' % (ip_and_port[0], ip_and_port[1]),
        })
        t2 = time.time()

        # 存储
        if resp.status_code == 200:
            r.set(ip_and_port[0], json.dumps({'ip': ip_and_port[0], 'port': ip_and_port[1], 'time': t2-t1}))

    except Exception:
        pass


if __name__ == '__main__':

    # 连接 Redis
    r = redis.Redis(host=config.redis_host, port=config.redis_port)

    # 获取总页数
    resp = get_by_page(1)
    listnav_li = pq(resp.content).find('#listnav li')
    li_size = len(listnav_li)
    total_page = int(pq(listnav_li[li_size-2]).find('a').text())

    print '[+] Total page %s' % total_page

    # 请求间隔
    time.sleep(SLEEP)

    # 初始化线程池
    pool = ThreadPool(30)
    threads = []

    page = 1
    while page <= total_page:

        try:
            resp = get_by_page(page)
        except Exception:
            resp = False

        if resp:
            tbody_tr = pq(resp.content).find('table tbody tr')
            proxies = []
            for tr in tbody_tr:
                pq_tr = pq(tr)
                # 获取代理 IP
                ip = pq_tr.find('[data-title="IP"]').text()
                # 获取代理端口
                port = pq_tr.find('[data-title="PORT"]').text()
                proxies.append([ip, port])
            print '[+] Page %s got %s ips' % (page, len(proxies))

            # 验证代理信息
            for proxy in proxies:
                threads.append(pool.spawn(validate_ip_and_port, r, proxy))

        # 请求间隔
        time.sleep(SLEEP)
        page += 1

    gevent.joinall(threads)




