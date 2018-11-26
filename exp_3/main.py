# -*- coding: utf-8 -*-

import config
import requests
from pyquery import PyQuery as pq


def discuz_login(req):

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
        return True
    else:
        return False


def discuz_post(req, title, content):

    # 打开发帖页，获取 formhash 与 posttime
    resp = req.get('%s/forum.php'
                   '?mod=post'
                   '&action=newthread'
                   '&fid=%s' % (config.discuz_url, config.discuz_post_fid))

    content_pq = pq(resp.content)

    # 获取 formhash
    formhash = content_pq('input[name="formhash"]').val()
    # 获取 posttime
    posttime = content_pq('input[name="posttime"]').val()

    # 构造发帖请求
    data = {
        'formhash': formhash,
        'posttime': posttime,
        'subject': title,
        'message': content
    }

    resp = req.post('%s/forum.php'
             '?mod=post'
             '&action=newthread'
             '&fid=%s'
             '&extra='
             '&topicsubmit=yes' % (config.discuz_url, config.discuz_post_fid), data)

    return True if resp.status_code == 200 else False


def bjcc_channel_12_spider(req, page):

    url = 'https://www.bjcc.gov.cn/channel/12/%s.html' % page

    resp = req.get(url)
    if resp.status_code != 200:
        print '[-] Page %s failed' % page
        return False

    data = []

    # 选取文章列表的父元素
    articles = pq(resp.content)('.recent-updates .panel-body ul').children()
    for article in articles:

        # 确定文章的 URL
        url = pq(article).find('a.news-title').attr('href')

        # 最大尝试5次
        for t in range(5):
            try:
                resp = req.get('https://www.bjcc.gov.cn' + url)
                break
            except Exception:
                resp = False
                pass

        # 成功请求文章页面
        if resp and resp.status_code == 200:
            article_pq = pq(resp.content)
            # 获取文章的标题
            title = article_pq.find('.big-title').text()
            # 获取文章内容
            content = article_pq.find('.article-content').text()
            print '[+] GET %s success: %s' % (url, title)
            data.append([title, content])
        else:
            print '[-] GET %s failed' % url

    return data


def main():

    discuz_req = requests.session()
    bjcc_req = requests.session()

    # 登陆 Dizcuz
    result = discuz_login(discuz_req)
    print '[+] Discuz login success' if result else '[-] Discuz login failed'
    if not result:
        exit(0)

    # 获取 时政要闻 1-10页的文章列表
    for page in range(1, 11):
        data = bjcc_channel_12_spider(bjcc_req, page)
        if not data:
            continue
        for d in data:
            # 发帖
            result = discuz_post(discuz_req, d[0], d[1])
            print '[+] Discuz post success: %s' % d[0] if result else '[-] Discuz post failed: %s' % d[0]


if __name__ == '__main__':
    main()