from playwright.sync_api import sync_playwright
pw = sync_playwright()
pw_s = pw.start()
chrome = pw_s.chromium.launch(headless=False)
context = chrome.new_context()
page = context.new_page()
# page.goto('https://www.artstation.com/artwork/3qAZoD', timeout=600000)


# import cloudscraper
# from lxml.html import fromstring
# import os, sys, re
# import requests
# scraper=cloudscraper.create_scraper(browser={
#         'browser': 'firefox',
#         'platform': 'windows',
#         'mobile': False
#     })
# resp = scraper.get('https://www.artstation.com/embed/15290171', proxies={"https": "127.0.0.1:7890"}, headers={"Referer":"https://www.artstation.com/artwork/9EN6qW"}).text
