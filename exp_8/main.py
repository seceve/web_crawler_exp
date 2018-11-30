# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division


import os
import re
import sys
import requests
from retrying import retry
from gevent.threadpool import ThreadPool
import gevent


from pyquery import PyQuery as pq


# 下载图片
@retry(stop_max_attempt_number = 5, wait_fixed = 500)
def download_pic(req, url, path):

    # 请求图片
    resp = req.get(url, stream=True)
    content_type = resp.headers['content-Type']
    # 提取图片扩展名
    content_type_ext = content_type.split('/')[-1]
    # 生成图片名称
    img_name = re.findall('.net/([^?/]+)[?]?', url)[0]
    img_name = img_name + '.' + content_type_ext

    # 写入图片
    with open('{0}/{1}'.format(path, img_name), 'wb') as f:
        for c in resp.iter_content(chunk_size=512):
            if c:
                f.write(c)

    print('[+] Downloaded {0}'.format('{0}/{1}'.format(path, img_name)))

    return url, img_name


if __name__ == '__main__':

    if len(sys.argv) != 2:
        print('Please input the URL of CSDN')
        exit(0)

    URL = sys.argv[1]

    # 判断是否是 CSDN 博客链接
    if not re.match('http[s]?://blog.csdn.net/[^/]+/article/details/[\d]+[/]?', URL):
        print('Please input the URL of CSDN blog')

    req = requests.session()

    # 发起请求
    resp = req.get(URL)

    if resp.status_code != 200:
        print('[-] {0} Response code: {1}'.format(URL, resp.status_code))
        exit(0)

    content_pq = pq(resp.content)

    # 获取标题
    title = content_pq.find('h1.title-article').text()
    # 获取用户
    author = content_pq.find('a.follow-nickName').text()
    # 获取用户链接
    author_url = content_pq.find('a.follow-nickName').attr('href')

    print('[+] Title: {0}'.format(title))
    print('[+] Author: {0}'.format(author))

    # 文章内容
    content_views_pq = content_pq.find('#content_views')

    images = {}

    def _each(i, e):
        e_pq = pq(e)
        images[e_pq.attr('src')] = None

    # 获取所有图片链接
    content_views_pq.find('img').each(_each)

    print('[+] Got {0} images'.format(len(images)))

    # 文章文件夹
    path = title
    # 文章图片文件夹
    img_path = '{0}/{1}'.format(title, 'img')

    # 判断文章文件夹是否存在
    if os.path.exists(title):
        print('[-] Dir {0} existed.'.format(path))
        exit(0)

    # 创建文章文件夹
    os.mkdir(path)
    # 创建文章图片文件夹
    os.mkdir(img_path)

    print('[+] Create dir {0}'.format(path))
    print('[+] Create dir {0}'.format(img_path))

    # 下载图片线程池
    pool = ThreadPool(5)
    # 下载图片
    threads = [pool.spawn(download_pic, req, img_url, img_path) for img_url in images.keys()]
    gevent.joinall(threads)

    for th in threads:
        images[th.get()[0]] = th.get()[1]

    def _each(i, e):
        e_pq = pq(e)
        e_pq.attr('src', 'img/{0}'.format(images[e_pq.attr('src')]))

    # 改写图片链接
    content_views_pq.find('img').each(_each)

    # html 中添加标题、作者、文章 html
    html = '<h1>{0}</h1>'.format(title)
    html += '<a href="{0}">Author: {1}</a>'.format(author_url, author)
    html += '<hr>'
    html += content_views_pq.html()

    # html 写入 index.html
    with open('{0}/index.html'.format(path), 'wb') as f:
        f.write(html.encode('utf-8'))

    print('[+] HTML save to {0}/index.html'.format(path))

    print('[+] Finished')
