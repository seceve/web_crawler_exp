# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division

import requests

if __name__ == '__main__':

    print('\n\n\n\n================\n发起请求')

    # 发起 GET 请求
    resp = requests.get('https://api.github.com/events')
    print('[+] GET https://api.github.com/events | {0}\n'.format(resp.text))

    # 发起 POST 请求
    resp = requests.post('http://httpbin.org/post', data={'key': 'value'})
    print('[+] POST http://httpbin.org/post | {0}\n'.format(resp.text))

    # 发起 PUT 请求
    resp = requests.put('http://httpbin.org/put', data={'key': 'value'})
    print('[+] PUT http://httpbin.org/put | {0}\n'.format(resp.text))

    # 发起 DELETE 请求
    resp = requests.delete('http://httpbin.org/delete')
    print('[+] DELETE http://httpbin.org/delete | {0}\n'.format(resp.text))

    # 发起 HEAD 请求
    resp = requests.head('http://httpbin.org/get')
    print('[+] HEAD http://httpbin.org/get | {0}\n'.format(resp.text))

    print('\n\n\n\n================\n传递 URL 参数')

    # 传递的参数
    payload = {'key1': 'value1', 'key2': ['value2', 'value3']}
    # 发起请求
    resp = requests.get('http://httpbin.org/get', params=payload)
    print('[+] GET http://httpbin.org/get | {0}'.format(resp.text))

    print('\n\n\n\n================\n请求响应')

    # 发起请求
    resp = requests.get('http://httpbin.org/get')
    # 打印响应的文本内容
    print('[+] resp.text | {0}'.format(resp.text))
    # 打印响应的编码
    print('[+] resp.encoding | {0}'.format(resp.encoding))
    # 打印二进制响应内容
    print('[+] resp.content | {0}'.format(resp.content))
    # 打印 JSON 响应
    print('[+] resp.json() | {0}'.format(resp.json()))
    # 打印响应状态
    print('[+] resp.status_code | {0}'.format(resp.status_code))
    # 打印响应头
    print('[+] resp.headers | {0}'.format(resp.headers))

    print('\n\n\n\n================\n自定义请求头')

    # 自定义请求头
    headers = {
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36'}
    # 发起请求
    resp = requests.get('http://httpbin.org/get', headers=headers)
    print('[+] GET http://httpbin.org/get | {0}'.format(resp.text))

    print('\n\n\n\n================\nPOST 请求表单')

    # 请求表单
    data = {'key1': 'value1', 'key2': 'value2'}
    # 发起请求
    resp = requests.post('http://httpbin.org/post', data=data)
    print('[+] POST http://httpbin.org/post | {0}'.format(resp.text))

    print('\n\n\n\n================\nCOOKIE')

    # 设置 Cookies
    cookies = dict(cookie_are='working')
    # 发起请求
    resp = requests.get('http://httpbin.org/cookies', cookies=cookies)
    print('[+] GET http://httpbin.org/cookies | {0}'.format(resp.text))
    # 使用 RequestsCookieJar 设置 Cookeis
    jar = requests.cookies.RequestsCookieJar()
    jar.set('tasty_cookie', 'yum', domain='httpbin.org', path='/cookies')
    # 发起请求
    resp = requests.get('http://httpbin.org/cookies', cookies=jar)
    print('[+] GET http://httpbin.org/cookies | {0}'.format(resp.text))

    print('\n\n\n\n================\n禁止重定向')

    # 发起请求并禁止重定向
    resp = requests.get('http://github.com', allow_redirects=False)
    print('[+] GET http://github.com | status code {0}'.format(resp.status_code))

    print('\n\n\n\n================\n超时')

    # 发起请求，超过 0.001 秒则停止等待响应
    try:
        resp = requests.get('http://github.com', timeout=0.001)
    except Exception as e:
        print(e.message)



