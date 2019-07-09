#!/usr/bin/env python
# -*- encoding: utf-8 -*-

"""
@author: d00ms(--)
@file: testWater3.py
@time: 2019-7-8 16:53
@desc: 测试一下Cookie的装填，可能有些网站的校验会很严格，此时可采用别的登录方式替代。
"""

import asyncio
import datetime
from pyppeteer.launcher import launch

url = 'http://10.10.10.127:3000'
DOMcookie = 'cookieconsent_status=dismiss; language=zh_CN; welcome-banner-status=dismiss'
records = []

# DOMcookie= "csrftoken=J2VJVFPPgGgPi4myBkYtMMoR2P6eWJ3wBl8VoOX0rwR991kQUi1vBgfcXUclrSOh; cookieconsent_status=dismiss; language=zh_CN; continueCode=av8Mgk2ym59pwOlxDdzoH2hrcps5iySzuVcnhMgT3wGKrnVePq1jzJbW7XZQ; token=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdGF0dXMiOiJzdWNjZXNzIiwiZGF0YSI6eyJpZCI6MTQsInVzZXJuYW1lIjoiIiwiZW1haWwiOiJoamtsQDEyNi5jb20iLCJwYXNzd29yZCI6ImU5ZmQ1ODhiNTg3MjU0M2Q4NmM0NGU3NjMzNTZhNDk1IiwiaXNBZG1pbiI6ZmFsc2UsImxhc3RMb2dpbklwIjoiMC4wLjAuMCIsInByb2ZpbGVJbWFnZSI6ImRlZmF1bHQuc3ZnIiwiY3JlYXRlZEF0IjoiMjAxOS0wNy0wOSAwNTo1NTowOS43NDYgKzAwOjAwIiwidXBkYXRlZEF0IjoiMjAxOS0wNy0wOSAwNTo1NTowOS43NDYgKzAwOjAwIn0sImlhdCI6MTU2MjY1MzIwMSwiZXhwIjoxNTYyNjcxMjAxfQ.l63C1L93avxfJcpqCz8cNWs0ukmHAWnGdziT1O7feX0eOB6fXL-WKFFArMzg303E9fU2_xm2O6WC4SIOog9ikGdJBvbrJZBM0b0B23jVmsSy0hGqUGfB3j7TllssiJyWB55mQd8U9sQ9n7euoc8uUgxCua5DjQZodUhIIRxF8b8"

def cookieHandler(string):
    cookiebar = DOMcookie.split(';')
    result = []
    now = datetime.datetime.now()
    expire = now + datetime.timedelta(days=2)
    for cookie in cookiebar:
        k, v = cookie.strip().split('=')
        result.append(dict(name=k, value=v, expires=expire.timestamp()))
    return result


##########################################
#   功能点1：登录/cookie填充（并不万能）
##########################################

async def logOn(page, anchor, userId, passWd):
    #    await asyncio.gather(page.waitForNavigation(),page.goto(url+'/#/'+anchor))
    await page.goto(url + '/#/' + anchor)
    input1 = await page.waitForSelector('input#email')
    input2 = await page.waitForSelector('input#password')
    button = await page.waitForSelector('button#loginButton')
    await input1.type(userId)
    await input2.type(passWd)
    await button.click()
    # left server some time to finish authorization.
    await page.waitFor(3000)
    #    await asyncio.gather(page.waitForNavigation(), page.goto(url))



##########################################
#   功能点2：页面加载前注入
#   1. hook对象有：WebSocket, EventSource, fetch, close, open
#   2. 延时触发对象有：setTimeOut, setInternal
##########################################

async def hookJsOnNewPage(page):
    # in addtion, we inject those functions:
    await page.exposeFunction('PyLogWs',lambda url: records.append(dict(Protocal='ws', Url=url)))
    await page.exposeFunction('PyLogEs',lambda url: records.append(dict(Protocal='es', Url=url)))
    await page.exposeFunction('PyLogFetch',lambda url: records.append(dict(Protocal='fetch', Url=url)))
    await page.exposeFunction('PyLogOpen',lambda url: records.append(dict(Protocal='open', Url=url)))

    return await page.evaluateOnNewDocument('''()=>{
        var oldWebSocket = window.WebSocket;
        window.WebSocket = function(url, arg) {
            PyLogWs(url);
            // continue the original ws request
            return new oldWebSocket(url, arg);
        }
        var oldEventSource = window.EventSource;
        window.EventSource = function(url) {
            PyLogEs(url);
            return new oldEventSource(url);
        }
        var oldFetch = window.fetch;
        window.fetch = function(url) {
            PyLogFetch(url);
            return oldFetch(url);
        }

        window.close = function() {}
        window.open = function(url) { PyLogOpen(url); }

        window.__originalSetTimeout = window.setTimeout;
        window.setTimeout = function() {
            arguments[1] = 0;
            return window.__originalSetTimeout.apply(this, arguments);
        }
        window.__originalSetInterval = window.setInterval;
        window.setInterval = function() {
            arguments[1] = 0;
            return window.__originalSetInterval.apply(this, arguments);
        }
    }''')




async def main():
    browser = await launch(devtools=True) # args=["--start-maximized"]
    pages = await browser.pages()
    target = pages[0]
    await target.goto(url)

    cookies = cookieHandler(DOMcookie)
    for cookie in cookies:
        await target.setCookie(cookie)

    await logOn(target, 'login', 'hjkl@126.com', '543210')
    await hookJsOnNewPage(target)
    # emit Js function hooked just now.
    await target.reload()

    await browser.close()
    return records


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(main())
    loop.run_until_complete(task)
    print(task.result())
