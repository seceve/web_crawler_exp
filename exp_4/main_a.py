# -*- coding: utf-8 -*-


from retrying import retry
import re
import time
import pandas as pd
import requests


@retry(stop_max_attempt_number = 5, stop_max_delay = 10000, wait_fixed = 500)
def crawling(url):
    return requests.get(url)


if __name__ == '__main__':

    # 请求，为获取总页数
    resp = crawling('https://shop.10086.cn/list/134_200_200_1_0_0_0_0_0.html')
    if resp.status_code != 200:
        print '[-] Get total page error'
        exit()

    # 获取总页数
    total_page = int(re.findall(r'第1/([\d]+)页', resp.content)[0])
    print '[+] Total page: %s' % total_page

    time_start = time.time()

    # 抓取到的手机号放到 numbers 中
    numbers = []
    # 请求每个页面
    for page in range(1, total_page+1):
        resp = crawling('https://shop.10086.cn/list/134_200_200_1_0_0_0_0_0.html?p=%s' % page)
        # 获取手机号
        nums = re.findall(r'(0?1[345789][0-9]{9})', resp.content)
        print '[+] Page %s count: %s' % (page, len(nums))
        [numbers.append(num) for num in nums]

    time_stop = time.time()

    print '[+] Finished, %s phone numbers, %s seconds' % (len(numbers), time_stop-time_start)

    df = pd.DataFrame({'Phone Number': numbers}, index=list(range(1, len(numbers)+1)))
    df.to_excel('output/main_a.xls')

    print '[+] Saved to output/main_a.xls'
