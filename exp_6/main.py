# -*- coding: utf-8 -*-

import sys
from retrying import retry
import gevent
from gevent.threadpool import ThreadPool
import requests


# 设置爬虫的 User Agent
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'
}


@retry(stop_max_attempt_number = 5, stop_max_delay = 10000, wait_fixed = 500)
def get_iamge_urls(keyword, page):

    # URL 编码关键词
    encoded_keyword = requests.utils.quote(keyword)
    # 发起请求
    resp = requests.get('https://www.vcg.com/api/common/searchImage'
                        '?page=%s'
                        '&phrase=%s'
                        '&keyword=%s' % (page, encoded_keyword, encoded_keyword), headers = headers)
    image_list = resp.json()
    # 获取图片链接
    images = ['https:%s' % elem['url800'] for elem in image_list['list']]
    print '[+] Page %s: %s iamges' % (page, len(images))
    return images


@retry(stop_max_attempt_number = 5, stop_max_delay = 10000, wait_fixed = 500)
def download_image(url):
    # 提取文件名
    file_name = url.split('/')[-1]
    # 写入文件
    with open('download/%s' % file_name, 'wb') as f:
        resp = requests.get(url, headers=headers, stream=True)
        for c in resp.iter_content(chunk_size=512):
            if c:
                f.write(c)
    print '[+] Successful save to download/%s' % file_name


if __name__ == '__main__':

    if len(sys.argv) != 3:
        print 'Please input keyword and pages'
        exit(0)

    s = sys.argv[1]
    p = int(sys.argv[2])

    # 线程池
    pool = ThreadPool(10)
    # 获取 图片 URL
    threads = [pool.spawn(get_iamge_urls, s, page) for page in range(1, p+1)]
    gevent.joinall(threads)

    image_urls = []
    for t in threads:
        image_urls += t.get()
    # 下载图片
    threads = [pool.spawn(download_image, url) for url in image_urls]
    gevent.joinall(threads)

    print '[+] Finished'

