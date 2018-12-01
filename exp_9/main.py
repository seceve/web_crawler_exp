# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import os
import re
import sys
from gevent.threadpool import ThreadPool
import requests
from retrying import retry
from pyquery import PyQuery as pq
import gevent
import pandas


# 请求漏洞信息
@retry(stop_max_attempt_number = 2, wait_fixed = 200)
def _get_by_url_id(url_id):

    # 生成 URL
    if url_id >= 1000:
        url = 'http://www.cnnvd.org.cn/web/xxk/ldxqById.tag?CNNVD=CNNVD-%04d%02d-%04d' % (year, month, url_id)
    else:
        url = 'http://www.cnnvd.org.cn/web/xxk/ldxqById.tag?CNNVD=CNNVD-%04d%02d-%03d' % (year, month, url_id)

    resp = requests.get(url)

    # CNNVD ID 不存在
    if resp.status_code == 500:
        return False

    content_pq = pq(resp.content)

    # 获取漏洞标题
    title = content_pq.find('.detail_xq h2').text()
    # 获取漏洞 ID
    id_text = content_pq.find('.detail_xq ul li:nth-child(1)').text()
    id = re.findall(u'CNNVD编号：([A-Z0-9\-]+)', id_text)[0]
    # 获取漏洞危害等级
    rank = content_pq.find('.detail_xq ul li:nth-child(2) a').text()
    # 获取 CVE 编号
    cve_id = content_pq.find('.detail_xq ul li:nth-child(3) a').text()
    # 获取漏洞类型
    leak_type = content_pq.find('.detail_xq ul li:nth-child(4) a').text()
    # 获取发布时间
    release_date = content_pq.find('.detail_xq ul li:nth-child(5) a').text()
    # 获取威胁类型
    threat_type = content_pq.find('.detail_xq ul li:nth-child(6) a').text()
    # 获取更新时间
    update_date = content_pq.find('.detail_xq ul li:nth-child(7) a').text()
    # 获取厂商
    vendor = content_pq.find('.detail_xq ul li:nth-child(8) a').text()
    # 获取漏洞来源
    source = content_pq.find('.detail_xq ul li:nth-child(9) a').text()

    # 获取漏洞简介
    abbreviation = content_pq.find('.d_ldjj').eq(0).find('p').text()

    if url_id >= 1000:
        print('[+] CNNVD=CNNVD-%04d%02d-%04d' % (year, month, url_id))
    else:
        print('[+] CNNVD=CNNVD-%04d%02d-%03d' % (year, month, url_id))

    return [title, id, rank, cve_id, leak_type, release_date, threat_type, update_date, vendor, source, url, abbreviation]


if __name__ == '__main__':

    if len(sys.argv) != 3:
        print('[-] Please input the year and the month')
        exit(0)

    try:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
    except Exception as e:
        print('[-] Year and month must be a number')
        exit(0)

    excel = []

    # 线程池 20
    pool = ThreadPool(20)
    threads = []

    # 从 id 为 1 开始遍历
    url_id = 1
    break_flag = False
    while True:

        # 每 100 个统计一次结果
        if url_id % 100 == 1:

            gevent.joinall(threads)

            for t in threads:
                res = t.get()

                # id 不存在时退出循环
                if not res:
                    break_flag = True
                    break

                # 结果保存在 excel 中
                excel.append({
                    'title': res[0],
                    'id': res[1],
                    'rank': res[2],
                    'cve_id': res[3],
                    'leak_type': res[4],
                    'release_date': res[5],
                    'threat_type': res[6],
                    'update_date': res[7],
                    'vendor': res[8],
                    'source': res[9],
                    'url': res[10],
                    'abbreviation': res[11]
                })

            threads = []

        if break_flag:
            break

        # 获取漏洞信息
        threads.append(pool.spawn(_get_by_url_id, url_id))

        url_id += 1

    # 创建 output 文件夹
    if not os.path.exists('output'):
        os.mkdir('output')

    # 导出到 excel 文件
    df = pandas.DataFrame(excel)
    df.to_excel('output/%s_%s.xls' % (year, month), columns=['id', 'title', 'url', 'rank', 'cve_id', 'leak_type',
                                                             'release_date', 'threat_type', 'update_date',
                                                             'vendor', 'source', 'abbreviation'])

    print('===========')
    print('[+] Finished: output/%s_%s.xls' % (year, month))
    