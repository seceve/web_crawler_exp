# -*- coding: utf-8 -*-

import re
import datetime
import config
import pymysql
from retrying import retry
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@retry(stop_max_attempt_number = 5, wait_fixed = 500)
def browser_get(browser, url):
    browser.get(url)


if __name__ == '__main__':

    # 连接数据库
    db = pymysql.connect(config.mysql_host, config.mysql_user, config.mysql_pass, config.mysql_db, charset='utf8mb4')
    cursor = db.cursor()
    db.commit()

    # Chrome Driver 设置
    chromeOptions = webdriver.ChromeOptions()
    # 关闭 “Chrome 正在受到自动化软件控制” 的显示
    chromeOptions._arguments = ['disable-infobars']
    # 启动 Chrome 浏览器
    browser = webdriver.Chrome(chrome_options=chromeOptions)
    wait = WebDriverWait(browser, 10)

    # 访问 Bilibili 热门视频排行榜
    browser_get(browser, 'https://www.bilibili.com/ranking/all/1/1/3')

    # 等待排行榜页面加载完成
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'ul.rank-list')))

    urls = []
    # 获取排行榜所有视频的 URL
    for rank_item in browser.find_elements_by_css_selector('ul.rank-list li.rank-item'):
        a = rank_item.find_element_by_css_selector('a.title')
        urls.append(a.get_attribute('href'))

    print '[+] Got %s video urls' % len(urls)

    for url in urls:

        # 获取视频 ID
        video_id = re.findall(r'video/([^/]+)/', url)[0]

        # 访问视频 URL
        browser_get(browser, url)
        # 等待网页加载完成
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[report-id="playpage_history"]')))
        # 浏览器滚动条滚动到底
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        # 等待评论加载完成
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.comment-list .list-item')))

        # 获取视频标题
        title = browser.find_element_by_css_selector('h1.video-title').get_attribute('title')
        user_name_elem = browser.find_element_by_css_selector('a.username')
        # 获取用户名
        user_name = user_name_elem.text
        # 获取用户 ID
        user_id = re.findall(r'/([\d]+)', user_name_elem.get_attribute('href'))[0]
        # 获取用户链接
        user_href = user_name_elem.get_attribute('href')

        print '=========================='
        print '[+] Title: %s' % title
        print '[+] Video id: %s' % video_id
        print '[+] Username: %s, UserID: %s' % (user_name, user_id)

        # 判断 user 表中用户是否已存在
        user_count = cursor.execute('SELECT * FROM user WHERE id=%s', user_id)
        if user_count == 0:
            # 不存在时添加用户（id, name, url, date）
            cursor.execute('INSERT INTO user (id,name,url,date) VALUES (%s,%s,%s,%s)',
                           (user_id, user_name, user_href, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            db.commit()
            print '[+] Insert user: %s' % user_name
        else:
            print '[-] Exist user: %s' % user_name

        # 判断 video 表中视频是否已存在
        video_count = cursor.execute('SELECT * FROM video WHERE id=%s', video_id)
        if video_count == 0:
            # 不存在时添加视频（id, name, url, user_id, date）
            cursor.execute('INSERT INTO video (id, name, url, user_id, date) VALUES (%s,%s,%s,%s,%s)',
                           (video_id, title, url, user_id, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            db.commit()
            print '[+] Insert video: %s' % title
        else:
            print '[-] Exist video: %s' % title

        # 获取视频所有评论
        all_comment_count = 0
        comment_list_items = browser.find_elements_by_css_selector('.comment-list .list-item')
        for list_item in comment_list_items:
            # 获取评论 ID
            comment_id = list_item.get_attribute('data-id')
            comment_user_name_elem = list_item.find_element_by_css_selector('a.name')
            # 获取评论用户名
            comment_user_name = comment_user_name_elem.text
            # 获取评论用户 ID
            comment_user_id = comment_user_name_elem.get_attribute('data-usercard-mid')
            # 获取评判用户链接
            comment_user_href = comment_user_name_elem.get_attribute('href')
            # 获取评论内容
            comment = list_item.find_element_by_css_selector('p.text').text

            # 判断 user 表中评论用户是否已存在
            comment_user_count = cursor.execute('SELECT * FROM user WHERE id=%s', comment_user_id)
            if comment_user_count == 0:
                # 不存在时添加用户（id, name, url, date）
                cursor.execute('INSERT INTO user (id,name,url,date) VALUES (%s,%s,%s,%s)',
                               (comment_user_id, comment_user_name, comment_user_href,
                                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                db.commit()

            # 判断 comment 表中评论是非已存在
            comment_count = cursor.execute('SELECT * FROM comment WHERE id=%s', comment_id)
            if comment_count == 0:
                # 不存在时添加评论（id, user_id, video_id, comment, date）
                cursor.execute('INSERT INTO comment (id,user_id,video_id,comment,date) VALUES (%s,%s,%s,%s,%s)',
                               (comment_id, comment_user_id, video_id, comment,
                                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                db.commit()
            all_comment_count += 1

        print '[+] Got %s comments' % all_comment_count

    browser.close()
    cursor.close()
    db.close()


