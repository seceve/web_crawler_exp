# -*- coding: utf-8 -*-

import config
import requests
import re
from pyquery import PyQuery as pq


def find_flag():

    # 获取 寻找 Flag 板块中的总页数
    resp = requests.get('%s/forum.php'
                        '?mod=forumdisplay'
                        '&fid=%s' % (config.discuz_url, config.discuz_post_fid))

    total_page = int(re.findall(r'title="共 ([\d]+) 页"', resp.content)[0])
    print '[+] Total page: %s' % total_page

    # 分页爬取帖子列表
    for page in range(1, total_page+1):

        print '[+] Page %s ------------------------------' % page

        resp = requests.get('%s/forum.php'
                            '?mod=forumdisplay'
                            '&fid=%s'
                            '&page=%s' % (config.discuz_url, config.discuz_post_fid, page))

        # 选取文章列表的父元素
        articles = pq(resp.content)('#threadlisttableid tbody')
        # 过滤第一个 tbody#separatorline
        for article in articles[1:]:
            tbody_pq = pq(article)

            # 确定 title 和 url
            title = tbody_pq.find('th a.xst').text()
            url = tbody_pq.find('th a.xst').attr('href')
            # 请求帖子的 url
            resp = requests.get('%s/%s' % (config.discuz_url, url))
            # 正则表达式寻找 flag
            flag = re.findall(r'({flag[^}]*})', resp.content)

            print '[+] Flag is %s, found in %s %s' % (flag[0], title, url) if len(flag) != 0 else '- Flag not found in %s' % title
            if len(flag) != 0:
                exit()


if __name__ == '__main__':

    find_flag()
