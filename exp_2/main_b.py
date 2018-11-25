# -*- coding: utf-8 -*-

import re
import requests
import config
from pyquery import PyQuery as pq


def find_flag_by_login():

    # 保证发出的请求带有 cookie 参数
    req = requests.session()

    # 构造登录 url
    url = '%s/member.php' \
          '?mod=logging' \
          '&action=login' \
          '&loginsubmit=yes' \
          '&infloat=yes' \
          '&lssubmit=yes' \
          '&inajax=1' % config.discuz_url

    # 构造登录 post 请求数据
    data = {
        'fastloginfield': 'username',
        'username': config.discuz_username,
        'password': config.discuz_password,
        'quickforward': 'yes',
        'handlekey': 'ls'
    }

    # 登录请求
    resp = req.post(url, data)

    # print resp.content
    # exit()

    # 判断是否成功登录
    if 'window.location.href' in resp.content:
        print '[+] Login success'
    else:
        print '[-] Login failed'
        exit()

    # 获取 寻找 Flag 板块中的总页数
    resp = req.get('%s/forum.php'
                        '?mod=forumdisplay'
                        '&fid=%s' % (config.discuz_url, config.discuz_post_login_fid))

    total_page = int(re.findall(r'title="共 ([\d]+) 页"', resp.content)[0])
    print '[+] Total page: %s' % total_page

    # 分页爬取帖子列表
    for page in range(1, total_page + 1):

        print '[+] Page %s ------------------------------' % page

        resp = req.get('%s/forum.php'
                            '?mod=forumdisplay'
                            '&fid=%s'
                            '&page=%s' % (config.discuz_url, config.discuz_post_login_fid, page))

        # 选取文章列表的父元素
        articles = pq(resp.content)('#threadlisttableid tbody')
        # 过滤第一个 tbody#separatorline
        for article in articles[1:]:
            tbody_pq = pq(article)

            # 确定 title 和 url
            title = tbody_pq.find('th a.xst').text()
            url = tbody_pq.find('th a.xst').attr('href')
            # 请求帖子的 url
            resp = req.get('%s/%s' % (config.discuz_url, url))
            # 正则表达式寻找 flag
            flag = re.findall(r'({flag[^}]*})', resp.content)

            print '[+] Flag is %s, found in %s %s' % (flag[0], title, url) if len(
                flag) != 0 else '- Flag not found in %s' % title
            if len(flag) != 0:
                exit()


if __name__ == '__main__':
    find_flag_by_login()