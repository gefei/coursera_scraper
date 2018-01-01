import time
import re
import requests
import shutil
import argparse

from urllib.parse import urljoin

from selenium import webdriver


def get_parent(item):
    parent = item
    while parent.tag_name != 'a':
        parent = parent.find_element_by_xpath('parent::*')
    return parent


def get_week(browser, week_no, args):
    week_url = urljoin(args.home, 'week/{}'.format(week_no))
    browser.get(week_url)
    time.sleep(2)
    items = browser.find_elements_by_class_name('cif-item-video')
    urls = []
    for it in items:
        anchor = get_parent(it)
        href = anchor.get_attribute('href')
        urls.append(href)
    for idx, href in enumerate(urls):
        browser.get(href)
        time.sleep(1.5)
        download_li   = browser.find_element_by_class_name('rc-LectureDownloadItem')
        download_a    = download_li.find_element_by_tag_name('a')
        download_href = download_a.get_attribute('href')
        print('Downloading {}'.format(download_href))
        r = requests.get(download_href, auth=(args.user, args.password), stream=True)
        if r.status_code == 200:
            with open('week{}_{}.mp4'.format(week_no, idx), 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
                f.close()

if __name__ == '__main__':
    # login
    parser = argparse.ArgumentParser(description='Scrape a coursera course')
    parser.add_argument('--home', type=str, required=True, help='Home url of the course, e.g., https://www.coursera.org/learn/python-machine-learning/home/')
    parser.add_argument('--user', type=str, required=True, help='Coursera user name')
    parser.add_argument('--password', type=str, required=True, help='Coursera user password')
    args = parser.parse_args()

    profile  = webdriver.ChromeOptions()
    browser  = webdriver.Chrome(executable_path='/usr/local/bin/chromedriver')
    browser.implicitly_wait(10)
    browser.get(args.home)

    browser.find_element_by_id('emailInput-input').send_keys(args.user)
    browser.find_element_by_id('passwordInput-input').send_keys(args.password)
    browser.find_elements_by_xpath('//button')[1].click()

    # course hoome
    time.sleep(3)
    anchors = browser.find_elements_by_tag_name('a')
    reg = re.compile(r'Week (\d+)')

    count = 0
    for anchor in anchors:
        try:
            m = reg.match(anchor.text)
            if m:
                count += 1
        except Exception as e:
            print(e)

    for i in range(1, count+1):
        get_week(browser, i, args)
        time.sleep(2)

    browser.close()
