# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division


import sys
import urlparse
from pyquery import PyQuery as pq
from gevent.threadpool import ThreadPool
import gevent
from retrying import retry
import requests
import networkx as nx
import matplotlib.pyplot as plt


# User-Agent
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36'
}


# 请求函数
@retry(stop_max_attempt_number=2, wait_fixed=200)
def req(target):
    return requests.get(target, headers=HEADERS, timeout=10)


# 递归爬取函数
def _crawler(info, thread_param, pool, url_set, target):

    # 发起请求
    try:
        resp = req(target)
    except Exception as e:
        return

    if len(resp.content) == 0:
        return

    target = resp.url

    if resp.status_code == 200:

        if target in url_set:
            return

        print('[+] 200 {0}'.format(target))

        content_pq = pq(resp.content)

        # 保存结果
        url_set[target] = content_pq.find('title').text()

        # 提取网页中的所有链接
        urls = []
        for link in content_pq.find('link'):
            link_pq = pq(link)
            href = link_pq.attr('href')
            if href and len(href) > 0:
                urls.append(href)

        for script in content_pq.find('script'):
            script_pq = pq(script)
            src = script_pq.attr('src')
            if src and len(src) > 0:
                urls.append(src)

        for a in content_pq.find('a'):
            a_pq = pq(a)
            href = a_pq.attr('href')
            if href and len(href) > 0:
                urls.append(href)

        # 遍历所有链接
        for url in urls:

            url = urlparse.urljoin(target, url)
            parsed_url = urlparse.urlparse(url)

            # 跳过非 http / https 链接
            if not ('http://' in url or 'https://' in url):
                continue

            # 跳过包含 # 的链接
            if '#' in url.split('/')[-1]:
                continue

            # 跳过已存在的链接
            if url in url_set:
                continue

            # 当域名相同时
            if parsed_url.netloc == info.netloc:
                # 递归调用
                thread_param.next_call.append([_crawler, info, thread_param, pool, url_set, url])

    else:

        print('[-] {0} {1}'.format(resp.status_code, target))

        url_set[target] = None


def main():

    if len(sys.argv) != 2:

        print('[-] Please input the base URL of the target')

        exit(0)

    url = sys.argv[1]

    # 爬取结果
    url_set = {}

    info = urlparse.urlparse(url)

    print('[+] Protocol: {0}, domain: {1}'.format(info.scheme, info.netloc))

    # 线程参数类
    class ThreadParam:
        # 所有线程
        threads = []
        # 当前线程
        tmp_threads = []
        # 待递归调用的参数
        next_call = []

    thread_param = ThreadParam()

    # 线程池 20
    pool = ThreadPool(20)
    # 当前线程 <= 从提交的 URL 开始爬取
    thread_param.next_call.append([_crawler, info, thread_param, pool, url_set, url])

    while True:

        # 所有线程 <= 当前线程
        thread_param.threads += thread_param.tmp_threads

        # 没有新的链接时，结束循环
        if len(thread_param.next_call) == 0:
            break

        # 当前线程 <= 执行递归函数
        thread_param.tmp_threads = [pool.spawn(*call) for call in thread_param.next_call]
        # 待递归调用的参数置空，用于存储新参数
        thread_param.next_call = []

        gevent.joinall(thread_param.tmp_threads)

    # 按路径解析 URL
    def _parse_url(url):
        url = url.replace('https://', '')
        url = url.replace('http://', '')
        res = url.split('/')
        if len(res[-1]) == 0:
            res = res[:-1]
        return res

    # 定义 URL 路径节点
    class _Node:

        def __init__(self, name, title):
            # 序号
            self.index = -1
            # 路径名
            self.name = name
            # 标题
            self.title = title
            # 子节点
            self.children = {}
            # 父节点
            self.parent = None

        # 递归寻找跟节点
        def root_node(self):

            if not self.parent:
                return self
            else:
                return self.parent.root_node()

        # 深度优先遍历所有节点，并生成序号，节点放置到 dict 中
        def traverse(self, dict):
            self.index = len(dict)
            dict[self.index] = self
            for name in self.children.keys():
                self.children[name].traverse(dict)

        # 深度优先绘制节点间连边
        def traverse_graph(self, graph):
            for node in self.children.values():
                graph.add_edge(self.index, node.index)
                node.traverse_graph(graph)

    root_nodes = {}

    # 遍历所有 URL，生成所有路径节点
    for url in url_set.keys():

        title = url_set[url]
        parsed_url = _parse_url(url)

        parent_node = None
        for name in parsed_url:

            # 根节点
            if not parent_node:

                if name in root_nodes:
                    node = root_nodes[name]
                else:
                    node = _Node(name, None)
                    root_nodes[name] = node

            # 非根节点
            else:

                if name in parent_node.children:
                    node = parent_node.children[name]
                else:
                    node = _Node(name, None)
                    node.parent = parent_node
                    parent_node.children[name] = node

            # 在叶子节点上添加标题
            if name is parsed_url[-1] and not node.title:
                node.title = title

            parent_node = node

    # 节点字典 key：节点序号，value：节点
    node_index = {}

    for node in root_nodes.values():
        node.traverse(node_index)

    # networkx 初始化网络
    graph = nx.Graph()
    # 在网络中添加所有节点
    for i in node_index.keys():
        graph.add_node(i)

    # 添加节点连边
    for node in root_nodes.values():
        node.traverse_graph(graph)

    # 重命名节点
    graph = nx.relabel_nodes(graph, {node.index: '{0}'.format(node.title) for node in node_index.values()})

    # 绘制网络
    nx.draw_spring(graph, with_labels=True, font_size=8, node_color='g')
    # 保存在图片中
    plt.savefig('{0}.png'.format(info.netloc), bbox_inches='tight')

if __name__ == '__main__':

    main()












